"""
base_plate_studs.py — Flat base plate with BAYONET studs, made to carry the
coral models from coral_reef.py. Each coral slides down over one stud and is
locked with a quarter turn (clockwise, seen from above).

Pipeline
  1. Work out the stud grid: evenly spaced, with the models' footprint and the
     edge margin taken into account
  2. Check the layout (edge margin, gap between neighbouring models, lug size)
  3. Build the plate and one bayonet stud (round shaft, two lugs near the tip,
     chamfered tip, filleted base and lug roots)
  4. Fuse the studs into the plate with exact mesh booleans (one solid piece)
  5. Export STL (+ optional 3MF) and a JSON record of every parameter
  6. Render a preview (top-down layout + 3D)

Requirements:  pip install numpy trimesh matplotlib manifold3d
               (optional: lxml for 3MF export)
Run:           python base_plate_studs.py
Outputs:       baseplate_<X>x<Y>x<T>_<N>studs_bayonet.stl, _params.json, _preview.png
"""

import json

import numpy as np
import trimesh

# =====================================================================
# SETTINGS — change these
# =====================================================================

# --- Plate (mm) ---
PLATE_X_MM = 90.0           # plate size along X
PLATE_Y_MM = 90.0           # plate size along Y
PLATE_THICKNESS_MM = 3.0    # plate thickness (printed flat on the bed)

# --- Stud layout ---
# Studs sit on an evenly spaced grid. The first and last stud in each row or
# column are placed so that a model of MODEL_FOOTPRINT_MM leaves EDGE_MARGIN_MM
# of free plate beyond its edge. Spacing between studs follows from that.
STUD_COLUMNS = 2            # studs along X
STUD_ROWS = 2               # studs along Y
MODEL_FOOTPRINT_MM = 30.0   # widest footprint of one model once locked on (square box)
EDGE_MARGIN_MM = 10.0       # minimum free plate between a model and the plate edge
MIN_GAP_MM = 10.0           # minimum free space between neighbouring models (warning only)

# --- Bayonet stud ---
# These MUST match the bayonet settings in coral_reef.py (the tests check this).
JOINT_TYPE = "bayonet"
STUD_DIA_MM = 5.0           # round shaft of the stud
STUD_HEIGHT_MM = 8.0        # stud height above the plate
LUG_SPAN_MM = 8.0           # tip-to-tip width across both lugs (each lug sticks out 1.5 mm)
LUG_WIDTH_MM = 3.0          # lug width
LUG_HEIGHT_MM = 2.5         # lug height
LUG_TOP_BELOW_TIP_MM = 0.5  # gap from the top of the lugs to the stud tip
JOINT_CLEARANCE_MM = 0.3    # gap on every side between stud and socket (set in coral_reef.py)
STUD_TIP_CHAMFER_MM = 0.6   # lead-in chamfer at the top of each stud
STUD_BASE_FILLET_MM = 0.5   # 45-degree fillet where the stud meets the plate (strength in bending).
                            # Must stay inside the coral's 0.6 mm socket mouth chamfer.
LUG_ROOT_FILLET_MM = 0.5    # 45-degree fillet on top of each lug where it meets the shaft.
                            # Under the lug it is limited to fit inside the socket's bore.
STUD_EMBED_MM = 2.0         # how far the stud runs down into the plate (fuses it)

# --- Meshing / output ---
EXPORT_3MF = True           # also write a 3MF (needs lxml); the STL is always written
_name = f"baseplate_{PLATE_X_MM:g}x{PLATE_Y_MM:g}x{PLATE_THICKNESS_MM:g}_{STUD_COLUMNS * STUD_ROWS}studs_bayonet"
OUT_STL = _name + ".stl"
OUT_3MF = _name + ".3mf"
OUT_JSON = _name + "_params.json"
OUT_PNG = _name + "_preview.png"


# =====================================================================
# 1-2. Stud layout and checks
# =====================================================================
def axis_positions(plate_mm, count):
    """Evenly spaced stud centres along one axis, centred on the plate middle."""
    first = EDGE_MARGIN_MM + MODEL_FOOTPRINT_MM / 2          # distance from plate edge
    if count == 1:
        return np.array([0.0]), 0.0
    span = plate_mm - 2 * first
    if span <= 0:
        raise ValueError(f"A {plate_mm:g} mm plate is too small for a {MODEL_FOOTPRINT_MM:g} mm model "
                         f"with a {EDGE_MARGIN_MM:g} mm margin")
    pitch = span / (count - 1)
    return -span / 2 + pitch * np.arange(count), pitch


def layout():
    xs, px = axis_positions(PLATE_X_MM, STUD_COLUMNS)
    ys, py = axis_positions(PLATE_Y_MM, STUD_ROWS)
    centres = np.array([(x, y) for x in xs for y in ys])

    gaps = [p - MODEL_FOOTPRINT_MM for p in (px, py) if p > 0]
    gap = min(gaps) if gaps else float("inf")
    margin_x = PLATE_X_MM / 2 - (abs(xs).max() + MODEL_FOOTPRINT_MM / 2)
    margin_y = PLATE_Y_MM / 2 - (abs(ys).max() + MODEL_FOOTPRINT_MM / 2)
    margin = min(margin_x, margin_y)

    print(f"  {len(centres)} studs, pitch {px:g} x {py:g} mm, "
          f"edge margin {margin:.1f} mm, gap between models {gap:.1f} mm")
    if gap < MIN_GAP_MM:
        print(f"  WARNING: models are only {gap:.1f} mm apart (wanted {MIN_GAP_MM:g} mm)")
    if LUG_SPAN_MM >= MODEL_FOOTPRINT_MM:
        print("  WARNING: the lugs are wider than the model footprint")
    return centres, (px, py), margin, gap


# =====================================================================
# 3-4. Plate + studs
# =====================================================================
def clean_mesh(mesh):
    """Drop zero-area sliver triangles the boolean can leave behind and merge
    duplicate points, so the mesh stays watertight after it is saved as STL."""
    m = trimesh.Trimesh(mesh.vertices.copy(), mesh.faces.copy(), process=True)
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    m.merge_vertices()
    m.fix_normals()
    return m if m.is_watertight else mesh   # never trade a closed mesh for an open one


def build_mesh(centres):
    try:
        import manifold3d as mf
    except ImportError:
        raise ImportError("This script needs manifold3d:  pip install manifold3d")

    # One stud: a round shaft from inside the plate to the tip, with a bevelled
    # tip, plus two lugs (one bar through the shaft) just below the tip.
    r = STUD_DIA_MM / 2
    c = STUD_TIP_CHAMFER_MM
    z0 = PLATE_THICKNESS_MM - STUD_EMBED_MM
    top = PLATE_THICKNESS_MM + STUD_HEIGHT_MM
    shaft = (mf.Manifold.cylinder(top - c - z0, r, r, 96, False).translate([0, 0, z0]) +
             mf.Manifold.cylinder(c, r, r - c, 96, False).translate([0, 0, top - c]))
    lug_top = top - LUG_TOP_BELOW_TIP_MM
    lugs = mf.Manifold.cube([LUG_SPAN_MM, LUG_WIDTH_MM, LUG_HEIGHT_MM], False) \
        .translate([-LUG_SPAN_MM / 2, -LUG_WIDTH_MM / 2, lug_top - LUG_HEIGHT_MM])
    # Fillets (45-degree, as cones) to take the sharp inside corners out:
    #  - stud base, where bending from water drag concentrates;
    #  - lug roots, top and underside, where the lugs carry the pull-out load.
    #    Under the lug the fillet must fit inside the coral's bore, so it is
    #    limited to just under the clearance.
    f = STUD_BASE_FILLET_MM
    base_fillet = mf.Manifold.cylinder(f, r + f, r, 96, False).translate([0, 0, PLATE_THICKNESS_MM])
    slab = mf.Manifold.cube([LUG_SPAN_MM, LUG_WIDTH_MM, 30], False).translate([-LUG_SPAN_MM / 2, -LUG_WIDTH_MM / 2, 0])
    g_top = LUG_ROOT_FILLET_MM
    g_low = min(LUG_ROOT_FILLET_MM, JOINT_CLEARANCE_MM - 0.05)
    top_fillet = mf.Manifold.cylinder(g_top, r + g_top, r, 96, False).translate([0, 0, lug_top])
    low_fillet = mf.Manifold.cylinder(g_low, r, r + g_low, 96, False) \
        .translate([0, 0, lug_top - LUG_HEIGHT_MM - g_low])
    stud = shaft + lugs + base_fillet + ((top_fillet + low_fillet) ^ slab)

    plate = mf.Manifold.cube([PLATE_X_MM, PLATE_Y_MM, PLATE_THICKNESS_MM], False) \
        .translate([-PLATE_X_MM / 2, -PLATE_Y_MM / 2, 0])
    for x, y in centres:
        plate = plate + stud.translate([x, y, 0])

    out = plate.to_mesh()
    mesh = trimesh.Trimesh(np.array(out.vert_properties)[:, :3].astype(float),
                           np.array(out.tri_verts), process=False)
    return clean_mesh(mesh), (STUD_DIA_MM, LUG_SPAN_MM)


# =====================================================================
# 6. Preview
# =====================================================================
def preview(mesh, centres, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12, 5.4))
    ax = fig.add_subplot(1, 2, 1)
    ax.add_patch(Rectangle((-PLATE_X_MM / 2, -PLATE_Y_MM / 2), PLATE_X_MM, PLATE_Y_MM,
                           fc="#e9dcc3", ec="k", lw=1.2))
    for x, y in centres:
        s = MODEL_FOOTPRINT_MM
        ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, fc="none", ec="tab:blue", ls="--", lw=1))
        ax.add_patch(Circle((x, y), STUD_DIA_MM / 2, fc="k"))
        ax.add_patch(Rectangle((x - LUG_SPAN_MM / 2, y - LUG_WIDTH_MM / 2), LUG_SPAN_MM, LUG_WIDTH_MM, fc="k"))
    ax.set_xlim(-PLATE_X_MM / 2 - 5, PLATE_X_MM / 2 + 5)
    ax.set_ylim(-PLATE_Y_MM / 2 - 5, PLATE_Y_MM / 2 + 5)
    ax.set_aspect("equal")
    ax.set_title(f"Layout (mm): {PLATE_X_MM:g} x {PLATE_Y_MM:g}, studs black, model footprint dashed")
    ax.set_xlabel("X"); ax.set_ylabel("Y")

    ax = fig.add_subplot(1, 2, 2, projection="3d")
    # matplotlib sorts triangles by depth, and the plate's huge flat triangles would
    # be drawn over the studs. Split them for the picture only (the STL is unchanged).
    v, f = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=4.0)
    m = trimesh.Trimesh(v, f, process=False)
    faces, normals = m.faces, m.face_normals
    light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
    shade = 0.25 + 0.75 * np.clip(normals @ light, 0, 1)
    cols = np.c_[shade * 0.93, shade * 0.86, shade * 0.76, np.ones_like(shade)]
    ax.add_collection3d(Poly3DCollection(m.vertices[faces], facecolors=cols, linewidths=0))
    lo, hi = m.bounds
    c = (lo + hi) / 2; r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.view_init(elev=28, azim=-60)
    ax.set_title("3D mesh"); ax.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig)


# =====================================================================
def main():
    print("1-2. Stud layout")
    centres, (px, py), margin, gap = layout()

    print("3-4. Building plate and bayonet studs")
    mesh, (stud_dia, lug_span) = build_mesh(centres)
    bodies = len(mesh.split(only_watertight=False))
    print(f"  watertight: {mesh.is_watertight}   solid pieces: {bodies}   triangles: {len(mesh.faces)}")

    print("5. Exporting")
    mesh.export(OUT_STL)
    if EXPORT_3MF:
        try:
            mesh.export(OUT_3MF)
        except Exception as e:
            print(f"  could not write 3MF ({e}) - STL only")

    report = {
        "parameters": {
            "plate_mm": [PLATE_X_MM, PLATE_Y_MM, PLATE_THICKNESS_MM],
            "stud_columns": STUD_COLUMNS, "stud_rows": STUD_ROWS,
            "model_footprint_mm": MODEL_FOOTPRINT_MM, "edge_margin_mm": EDGE_MARGIN_MM,
            "joint": {"type": JOINT_TYPE, "stud_dia_mm": STUD_DIA_MM, "stud_height_mm": STUD_HEIGHT_MM,
                      "lug_span_mm": LUG_SPAN_MM, "lug_width_mm": LUG_WIDTH_MM, "lug_height_mm": LUG_HEIGHT_MM,
                      "lug_top_below_tip_mm": LUG_TOP_BELOW_TIP_MM, "clearance_mm": JOINT_CLEARANCE_MM,
                      "stud_tip_chamfer_mm": STUD_TIP_CHAMFER_MM, "stud_embed_mm": STUD_EMBED_MM,
                      "stud_base_fillet_mm": STUD_BASE_FILLET_MM, "lug_root_fillet_mm": LUG_ROOT_FILLET_MM},
        },
        "results": {
            "stud_centres_mm": [[round(float(x), 3), round(float(y), 3)] for x, y in centres],
            "stud_pitch_mm": [round(float(px), 3), round(float(py), 3)],
            "edge_margin_mm": round(float(margin), 2),
            "gap_between_models_mm": None if gap == float("inf") else round(float(gap), 2),
            "mesh_watertight": bool(mesh.is_watertight),
            "solid_pieces": bodies,
            "mesh_volume_mm3": round(float(mesh.volume), 1),
            "triangles": int(len(mesh.faces)),
            "bounds_mm": [[round(float(v), 2) for v in b] for b in mesh.bounds],
        },
    }
    with open(OUT_JSON, "w") as fh:
        json.dump(report, fh, indent=2)

    print("6. Rendering preview")
    preview(mesh, centres, OUT_PNG)

    r = report["results"]
    print("\n=== Summary ===")
    print(f"Plate {PLATE_X_MM:g} x {PLATE_Y_MM:g} x {PLATE_THICKNESS_MM:g} mm, {len(centres)} bayonet studs "
          f"({STUD_DIA_MM:g} mm shaft, {LUG_SPAN_MM:g} mm across lugs, {STUD_HEIGHT_MM:g} mm tall)")
    print(f"Stud pitch {r['stud_pitch_mm']} mm   Edge margin {r['edge_margin_mm']} mm   "
          f"Model gap {r['gap_between_models_mm']} mm")
    print(f"Watertight: {r['mesh_watertight']}   Solid pieces: {r['solid_pieces']}")
    print(f"Saved {OUT_STL}" + (f", {OUT_3MF}" if EXPORT_3MF else "") + f", {OUT_JSON}, {OUT_PNG}")


if __name__ == "__main__":
    main()
