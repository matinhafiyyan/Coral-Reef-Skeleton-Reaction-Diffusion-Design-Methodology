"""
coral_reef.py — 3D Gray-Scott reaction-diffusion coral settlement structure.
Cylinder with thick walls, a capped overhang angle for support-free FDM
printing, a light mesh and an M3 threaded hole for mounting.

Pipeline
  1. Simulate Gray-Scott in a 3D voxel grid  -> sponge-like labyrinth
  2. Threshold the field to a target solid fraction (porosity control)
  3. Clip to a cylinder, optionally add a solid base
  4. Keep only the largest solid piece (no loose fragments)
  5. Find voids that cannot reach the outside and fill them
  5b. Remove overhangs steeper than MAX_OVERHANG_DEG so no supports are needed
  6. Measure strut thickness and channel width (mm)
  7. Mesh with marching cubes and export STL + a JSON record of every parameter
  8. Add a solid screw boss under the centre of the base (voxel step) and cut a
     real threaded M3 hole into it (exact mesh boolean, after simplification)

Requirements:  pip install numpy scipy scikit-image trimesh matplotlib fast_simplification manifold3d
Run:           python coral_reef.py
Outputs:       coral_cylinder_seed<N>.stl, _params.json, _preview.png
"""

import json
import time

import numpy as np
from scipy import ndimage
from skimage import measure
import trimesh

# =====================================================================
# SETTINGS — change these
# =====================================================================

# --- Physical size (mm) ---
DIAMETER_MM = 30.0      # footprint diameter
HEIGHT_MM = 30.0        # TOTAL height, base included
BASE_MM = 3.0           # solid base plate thickness, part of HEIGHT_MM (0 = no base)

# --- Simulation ---
GRID = 96               # voxels per side. Higher = finer but slower (time ~ GRID^3)
STEPS = 6000            # simulation iterations. Too few = pattern not settled
SEED = 42               # random seed: change for a new variant, keep for reproducibility

# Gray-Scott parameters. F = feed rate, K = kill rate.
# F=0.030, K=0.058 gives meandering, brain-coral-like interconnected channels.
# Wall thickness is set by SOLID_FRACTION and VOXELS_ACROSS, not by K.
# Lower K gives blobbier, closed pockets; F=0.030 with K<=0.053 dies out.
F = 0.030
K = 0.058
DU = 0.16               # diffusion rate of chemical U
DV = 0.08               # diffusion rate of chemical V (keep about half of DU)

# --- Pattern scale ---
# How many simulation voxels span the cylinder diameter. The labyrinth
# wavelength is fixed in voxels, so FEWER voxels across the diameter
# means BIGGER channels in mm.
VOXELS_ACROSS = 43      # keeps ~0.7 mm per simulation voxel (scale with DIAMETER_MM)

# --- Porosity ---
SOLID_FRACTION = 0.55   # fraction of the cylinder that is solid (0.3–0.6 sensible)

# --- Surface skin ---
# Closes up the outer surface so the top isn't a sponge sliced open.
# SKIN_MM = how deep the effect reaches; SKIN_STRENGTH = 0 (off) to 1 (nearly
# sealed). Too strong seals the channels and the trapped-void step fills them.
SKIN_MM = 3.0
SKIN_STRENGTH = 0.5

# --- Printability (mm) ---
MIN_STRUT_MM = 3.0      # thinnest wall: ~7 perimeters with a 0.4 mm nozzle
MIN_CHANNEL_MM = 3.5    # narrowest channel (room for settlement; avoids stringing)
MAX_OVERHANG_DEG = 45   # steepest allowed overhang, measured from vertical.
                        # 45 prints support-free on most FDM printers. Set to None to disable.
ENFORCE_MIN_FEATURES = True   # remove thinner struts / fill narrower channels automatically

# --- Meshing ---
UPSAMPLE = 2            # voxel refinement before meshing (keeps the overhang rule accurate)
TARGET_TRIANGLES = 60_000   # mesh is simplified to about this many triangles (None = keep all)

# --- M3 screw hole (auto-generated at the centre of the bottom face) ---
# A solid boss is grown up from the base so the thread has plastic to bite
# into, then a helical thread is cut into it. Sizes are in real mm, so print
# at 100 % scale (scaling the model in the slicer scales the thread too).
ADD_SCREW_HOLE = True
SCREW_BOSS_OD_MM = 9.0      # outside diameter of the solid boss around the hole
SCREW_BOSS_HEIGHT_MM = 8.0  # boss height, measured from the bottom face
SCREW_DEPTH_MM = 7.0        # threaded depth (blind hole, entered from the bottom)
THREAD_PITCH_MM = 0.5       # M3 coarse pitch
THREAD_MINOR_DIA_MM = 2.6   # M3 minor diameter + printing clearance (nominal 2.39-2.5)
THREAD_MAJOR_DIA_MM = 3.2   # M3 major diameter + printing clearance (nominal 3.0)
THREAD_CHAMFER_MM = 0.4     # lead-in chamfer at the hole mouth
_name = f"coral_cylinder_seed{SEED}"
OUT_STL = _name + ".stl"
OUT_JSON = _name + "_params.json"
OUT_PNG = _name + "_preview.png"


# =====================================================================
# 1. Gray-Scott reaction-diffusion in 3D
# =====================================================================
def laplacian(a):
    """7-point 3D Laplacian with wrap-around (periodic) edges."""
    return (np.roll(a, 1, 0) + np.roll(a, -1, 0) +
            np.roll(a, 1, 1) + np.roll(a, -1, 1) +
            np.roll(a, 1, 2) + np.roll(a, -1, 2) - 6.0 * a)


def simulate(n, steps, f, k, du, dv, seed):
    rng = np.random.default_rng(seed)
    u = np.ones((n, n, n), dtype=np.float32)
    v = np.zeros((n, n, n), dtype=np.float32)

    # Seed V in many small random cubes so the pattern grows everywhere at once
    for _ in range(max(20, n // 3)):
        c = rng.integers(0, n, 3)
        s = 3
        sl = tuple(slice(max(ci - s, 0), min(ci + s, n)) for ci in c)
        u[sl] = 0.5
        v[sl] = 0.25
    v += rng.uniform(0, 0.02, v.shape).astype(np.float32)

    t0 = time.time()
    for i in range(steps):
        uvv = u * v * v
        u += du * laplacian(u) - uvv + f * (1.0 - u)
        v += dv * laplacian(v) + uvv - (f + k) * v
        if (i + 1) % 1000 == 0:
            print(f"  step {i + 1}/{steps}  ({time.time() - t0:.0f}s)")
    return v


# =====================================================================
# 2-5. Build a clean, printable solid
# =====================================================================
def open_mm(phase, r_mm, voxel_mm, outside=False):
    """Morphological opening with a sphere of radius r_mm, done exactly with
    distance transforms: keeps every part of `phase` that a ball of radius r_mm
    can reach while staying inside `phase`. `outside` = value beyond the box."""
    pad = int(np.ceil(r_mm / voxel_mm)) + 1
    p = np.pad(phase, pad, constant_values=outside)
    centres = ndimage.distance_transform_edt(p) * voxel_mm >= r_mm
    if not centres.any():
        return np.zeros_like(phase)
    reach = ndimage.distance_transform_edt(~centres) * voxel_mm <= r_mm
    return reach[pad:-pad, pad:-pad, pad:-pad]


def build_solid(field):
    # Resample the simulation field onto the physical box
    voxel_mm = DIAMETER_MM / VOXELS_ACROSS
    nx = VOXELS_ACROSS
    nz = int(round(HEIGHT_MM / voxel_mm))
    reps = [int(np.ceil(s / GRID)) for s in (nx, nx, nz)]
    field = np.tile(field, reps)[:nx, :nx, :nz]   # periodic, so tiling is seamless

    # Upsample for a smoother surface
    field = ndimage.zoom(field, UPSAMPLE, order=3)
    voxel_mm /= UPSAMPLE
    nx, _, nz = field.shape

    # Cylinder mask: a disc in every layer
    r = (np.arange(nx) + 0.5) * voxel_mm - DIAMETER_MM / 2
    xx, yy = np.meshgrid(r, r, indexing="ij")
    disc = (xx ** 2 + yy ** 2) <= (DIAMETER_MM / 2) ** 2
    cyl = np.repeat(disc[:, :, None], nz, axis=2)

    # Threshold to hit the target solid fraction inside the cylinder
    thr = np.quantile(field[cyl], 1.0 - SOLID_FRACTION)

    # Surface skin: within SKIN_MM of the outer surface, raise the field so
    # walls thicken and channel mouths narrow. The outside then reads as a
    # mostly closed surface with winding grooves and openings (like a brain
    # coral) instead of a sponge sliced open. The bottom face is excluded.
    if SKIN_MM > 0 and SKIN_STRENGTH > 0:
        below = np.concatenate([np.ones_like(cyl[:, :, :1]), cyl], axis=2)
        depth = ndimage.distance_transform_edt(below)[:, :, 1:] * voxel_mm
        w = np.clip(1.0 - depth / SKIN_MM, 0.0, 1.0)
        field = field + SKIN_STRENGTH * (field.max() - thr) * w

    solid = (field > thr) & cyl

    # Solid base plate
    base_vox = int(round(BASE_MM / voxel_mm))
    if base_vox > 0:
        solid[:, :, :base_vox] |= disc[:, :, None]

    # Solid screw boss on the centre axis, standing on the bottom face
    boss = (xx ** 2 + yy ** 2) <= (SCREW_BOSS_OD_MM / 2) ** 2
    boss_vox = min(int(round(SCREW_BOSS_HEIGHT_MM / voxel_mm)), nz) if ADD_SCREW_HOLE else 0
    if boss_vox > 0:
        solid[:, :, :boss_vox] |= boss[:, :, None]

    # Enforce printable feature sizes.
    #  - "Opening" the solid with a ball removes any wall thinner than MIN_STRUT_MM
    #    (e.g. slivers left where the cylinder cuts through the lattice).
    #  - "Closing" the solid fills any channel narrower than MIN_CHANNEL_MM,
    #    so no crevice is too tight to clear of powder.
    if ENFORCE_MIN_FEATURES:
        # closing the solid = opening the empty space (open air outside the box)
        solid = ~open_mm(~solid, MIN_CHANNEL_MM / 2, voxel_mm, outside=True) & cyl
        if base_vox > 0:
            solid[:, :, :base_vox] |= disc[:, :, None]
        if boss_vox > 0:
            solid[:, :, :boss_vox] |= boss[:, :, None]
        solid = open_mm(solid, MIN_STRUT_MM / 2, voxel_mm, outside=False)

    # Self-supporting rule: every solid voxel must sit on solid in the layer
    # below, within a horizontal reach of tan(angle) x layer height. Built
    # bottom-up, so anything that would need a support is trimmed away.
    if MAX_OVERHANG_DEG is not None:
        reach = np.tan(np.radians(MAX_OVERHANG_DEG))   # in voxels per layer
        before = solid.sum()
        for z in range(1, solid.shape[2]):
            below = solid[:, :, z - 1]
            if below.any():
                ok = ndimage.distance_transform_edt(~below) <= reach + 1e-6
            else:
                ok = np.zeros_like(below)
            solid[:, :, z] &= ok
        print(f"  overhang limit {MAX_OVERHANG_DEG} deg: trimmed {int(before - solid.sum())} voxels")

    # Keep the largest face-connected solid piece
    lab, n = ndimage.label(solid)
    sizes = ndimage.sum(solid, lab, range(1, n + 1))
    keep = 1 + int(np.argmax(sizes))
    removed = int(solid.sum() - sizes[keep - 1])
    solid = lab == keep
    print(f"  solid pieces found: {n}  -> kept largest, removed {removed} loose voxels")

    # Trapped voids: empty regions not connected to the outside air.
    padded = np.pad(solid, 1, constant_values=False)
    vlab, vn = ndimage.label(~padded)
    outside = vlab[0, 0, 0]
    trapped = (vlab != outside) & (vlab > 0)
    n_trapped = vn - 1
    trapped_vol = trapped.sum() * voxel_mm ** 3
    solid = solid | trapped[1:-1, 1:-1, 1:-1]   # fill them so no powder is locked in
    print(f"  trapped voids: {n_trapped}  ({trapped_vol:.1f} mm^3) -> filled")

    return solid, cyl, voxel_mm, thr, n_trapped, trapped_vol, removed


# =====================================================================
# 6. Feature-size measurements
# =====================================================================
def local_thickness(phase, voxel_mm, outside):
    """Local thickness (as used for bone and tissue scaffolds): at each voxel,
    the diameter of the largest sphere that fits inside the phase and covers it."""
    d_max = ndimage.distance_transform_edt(np.pad(phase, 1, constant_values=outside)).max() * voxel_mm
    th = np.zeros(phase.shape, dtype=np.float32)
    for r in np.arange(voxel_mm, d_max + voxel_mm, voxel_mm):
        th[open_mm(phase, r, voxel_mm, outside)] = 2 * r
    return th


def feature_sizes(solid, cyl, voxel_mm):
    """Volume-weighted strut thickness and channel (pore) width, in mm."""
    strut = local_thickness(solid, voxel_mm, outside=False)[solid]
    # Channels are measured inside the cylinder only, treating its outer
    # surface as a wall. This is conservative: channels that open onto the
    # side of the cylinder read slightly narrower than they really are.
    void = (~solid) & cyl
    channel = local_thickness(void, voxel_mm, outside=False)[void]
    return strut, channel


# =====================================================================
# 7. Mesh and export
# =====================================================================
def to_mesh(solid, voxel_mm):
    vol = np.pad(solid.astype(np.float32), 2)   # pad so the surface closes
    vol = ndimage.gaussian_filter(vol, 0.8)     # light smoothing
    verts, faces, _, _ = measure.marching_cubes(vol, 0.5, spacing=(voxel_mm,) * 3)
    verts -= 2 * voxel_mm                       # undo padding offset
    verts[:, :2] -= DIAMETER_MM / 2             # centre on the origin
    mesh = trimesh.Trimesh(verts, faces, process=True)
    mesh.fix_normals()
    if TARGET_TRIANGLES and len(mesh.faces) > TARGET_TRIANGLES:
        try:  # needs: pip install fast_simplification
            simple = mesh.simplify_quadric_decimation(face_count=TARGET_TRIANGLES)
            simple.fix_normals()
            if simple.is_watertight:
                mesh = simple
            else:
                print("  simplified mesh not watertight - keeping full-resolution mesh")
        except Exception as e:
            print(f"  could not simplify mesh ({e}) - keeping full resolution")
    return mesh


def add_screw_hole(mesh):
    """Cut a right-handed M3 internal thread into the centre of the bottom face.

    The thread is a circle offset from the axis and extruded with a twist, which
    gives a smooth helical groove whose radius swings between the minor and major
    diameter once per pitch. Cut with an exact boolean (manifold3d)."""
    try:
        import manifold3d as mf
    except ImportError:
        raise ImportError("ADD_SCREW_HOLE needs manifold3d:  pip install manifold3d "
                          "(or set ADD_SCREW_HOLE = False)")
    if SCREW_DEPTH_MM > SCREW_BOSS_HEIGHT_MM - 1.0:
        raise ValueError("SCREW_DEPTH_MM must be at least 1 mm shorter than SCREW_BOSS_HEIGHT_MM")

    # Hole axis = centre of the bottom face (robust to the half-voxel offset of the mesh)
    zb = float(mesh.vertices[:, 2].min())
    foot = mesh.vertices[mesh.vertices[:, 2] < zb + 0.5]
    cx, cy = (foot[:, :2].min(0) + foot[:, :2].max(0)) / 2

    r_min, r_maj = THREAD_MINOR_DIA_MM / 2, THREAD_MAJOR_DIA_MM / 2
    a, e = (r_min + r_maj) / 2, (r_maj - r_min) / 2
    ext = 0.05                                   # start below the face for a clean cut
    height = SCREW_DEPTH_MM + ext
    turns = height / THREAD_PITCH_MM
    t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    outline = np.column_stack([e + a * np.cos(t), a * np.sin(t)])
    thread = mf.Manifold.extrude(mf.CrossSection([outline]), height,
                                 int(turns * 32), 360.0 * turns, (1.0, 1.0))
    mouth = mf.Manifold.cylinder(THREAD_CHAMFER_MM + ext, r_maj + THREAD_CHAMFER_MM + ext,
                                 r_maj, 96, False)       # wide at the face, narrowing in
    cutter = (thread + mouth).translate([cx, cy, zb - ext])

    body = mf.Manifold(mf.Mesh(vert_properties=mesh.vertices.astype(np.float32),
                               tri_verts=mesh.faces.astype(np.uint32)))
    if body.is_empty():
        raise RuntimeError("mesh is not a valid solid for the boolean; try TARGET_TRIANGLES = None")
    out = (body - cutter).to_mesh()
    result = trimesh.Trimesh(np.array(out.vert_properties)[:, :3].astype(float),
                             np.array(out.tri_verts), process=False)
    print(f"  M3x{THREAD_PITCH_MM:g} hole: {SCREW_DEPTH_MM:g} mm deep at "
          f"x={cx:.2f}, y={cy:.2f}  (watertight: {result.is_watertight})")
    return result


def preview(solid, mesh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12, 4.2))
    nz = solid.shape[2]
    for i, (z, label) in enumerate([(nz // 3, "slice 1/3 up"), (2 * nz // 3, "slice 2/3 up")]):
        ax = fig.add_subplot(1, 3, i + 1)
        ax.imshow(solid[:, :, z].T, cmap="Greys", origin="lower")
        ax.set_title(f"Cross-section ({label})")
        ax.axis("off")

    ax = fig.add_subplot(1, 3, 3, projection="3d")
    m = mesh
    if len(m.faces) > 80_000:
        try:  # pip install fast_simplification
            m = m.simplify_quadric_decimation(face_count=80_000)
        except Exception:
            pass
    faces, normals = m.faces, m.face_normals
    light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
    shade = 0.25 + 0.75 * np.clip(normals @ light, 0, 1)
    cols = np.c_[shade * 0.93, shade * 0.86, shade * 0.76, np.ones_like(shade)]
    pc = Poly3DCollection(m.vertices[faces], facecolors=cols, linewidths=0)
    ax.add_collection3d(pc)
    lo, hi = m.bounds
    c = (lo + hi) / 2; r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=25, azim=-60)
    ax.set_title("3D mesh"); ax.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig)


def software_versions():
    """Library versions used for this run, so the result can be reproduced."""
    import platform
    from importlib.metadata import version, PackageNotFoundError
    out = {"python": platform.python_version()}
    for pkg in ("numpy", "scipy", "scikit-image", "trimesh", "fast_simplification", "manifold3d"):
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None
    return out


# =====================================================================
def main():
    print(f"1. Simulating Gray-Scott on a {GRID}^3 grid (F={F}, K={K}, seed={SEED})")
    field = simulate(GRID, STEPS, F, K, DU, DV, SEED)

    print("2-5. Thresholding, clipping, cleaning")
    solid, cyl, voxel_mm, thr, n_trapped, trapped_vol, removed = build_solid(field)

    print("6. Measuring feature sizes")
    strut, channel = feature_sizes(solid, cyl, voxel_mm)
    pct = lambda a, p: float(np.percentile(a, p)) if len(a) else float("nan")
    thin_struts = float((strut < MIN_STRUT_MM).mean() * 100)
    narrow_ch = float((channel < MIN_CHANNEL_MM).mean() * 100)

    print("7. Meshing")
    mesh = to_mesh(solid, voxel_mm)
    if ADD_SCREW_HOLE:
        print("7b. Cutting the M3 screw hole")
        mesh = add_screw_hole(mesh)
    mesh.export(OUT_STL)

    solid_frac = float(solid[cyl].mean())
    report = {
        "parameters": {
            "shape": "cylinder", "diameter_mm": DIAMETER_MM, "height_mm": HEIGHT_MM, "base_mm": BASE_MM,
            "grid": GRID, "steps": STEPS, "seed": SEED, "F": F, "K": K, "DU": DU, "DV": DV,
            "voxels_across": VOXELS_ACROSS, "target_solid_fraction": SOLID_FRACTION, "skin_mm": SKIN_MM, "skin_strength": SKIN_STRENGTH,
            "upsample": UPSAMPLE, "min_strut_mm": MIN_STRUT_MM, "min_channel_mm": MIN_CHANNEL_MM,
            "max_overhang_deg": MAX_OVERHANG_DEG, "enforce_min_features": ENFORCE_MIN_FEATURES,
            "target_triangles": TARGET_TRIANGLES,
            "screw_hole": ({"thread": f"M3x{THREAD_PITCH_MM:g}", "depth_mm": SCREW_DEPTH_MM,
                            "minor_dia_mm": THREAD_MINOR_DIA_MM, "major_dia_mm": THREAD_MAJOR_DIA_MM,
                            "boss_od_mm": SCREW_BOSS_OD_MM, "boss_height_mm": SCREW_BOSS_HEIGHT_MM,
                            "chamfer_mm": THREAD_CHAMFER_MM}
                           if ADD_SCREW_HOLE else None),
        },
        "software": software_versions(),
        "results": {
            "actual_solid_fraction": round(solid_frac, 3),
            "porosity": round(1 - solid_frac, 3),
            "loose_voxels_removed": removed,
            "trapped_voids_filled": int(n_trapped),
            "trapped_void_volume_mm3": round(float(trapped_vol), 2),
            "strut_thickness_mm": {"p10": round(pct(strut, 10), 2), "median": round(pct(strut, 50), 2), "p90": round(pct(strut, 90), 2)},
            "channel_width_mm": {"p10": round(pct(channel, 10), 2), "median": round(pct(channel, 50), 2), "p90": round(pct(channel, 90), 2)},
            "percent_struts_below_min": round(thin_struts, 1),
            "percent_channels_below_min": round(narrow_ch, 1),
            "mesh_watertight": bool(mesh.is_watertight),
            "mesh_volume_mm3": round(float(mesh.volume), 1),
            "mesh_surface_area_mm2": round(float(mesh.area), 1),
            "surface_area_to_volume_per_mm": round(float(mesh.area / mesh.volume), 3),
            "triangles": int(len(mesh.faces)),
            "channel_width_distribution": {
                f"{lo:.0f}-{lo + 1:.0f} mm": round(float(((channel >= lo) & (channel < lo + 1)).mean() * 100), 1)
                for lo in range(0, int(np.ceil(channel.max())))
            },
        },
    }
    with open(OUT_JSON, "w") as fh:
        json.dump(report, fh, indent=2)

    print("Rendering preview")
    preview(solid, mesh, OUT_PNG)

    r = report["results"]
    print("\n=== Summary ===")
    print(f"Porosity: {r['porosity']:.0%}   Watertight: {r['mesh_watertight']}")
    print(f"Strut thickness (mm):  median {r['strut_thickness_mm']['median']}  "
          f"(10th pct {r['strut_thickness_mm']['p10']})  -> {r['percent_struts_below_min']}% below {MIN_STRUT_MM} mm")
    print(f"Channel width (mm):    median {r['channel_width_mm']['median']}  "
          f"(10th pct {r['channel_width_mm']['p10']})  -> {r['percent_channels_below_min']}% below {MIN_CHANNEL_MM} mm")
    print(f"Surface area: {r['mesh_surface_area_mm2']} mm^2   SA:V = {r['surface_area_to_volume_per_mm']} /mm")
    print(f"Saved {OUT_STL}, {OUT_JSON}, {OUT_PNG}")


if __name__ == "__main__":
    main()
