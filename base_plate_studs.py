"""
base_plate_studs.py — Flat base plate with threaded M3 studs, made to carry
the coral models from coral_reef_two.py (each model screws onto one stud).

Pipeline
  1. Work out the stud grid: evenly spaced, with the models' footprint and the
     edge margin taken into account
  2. Check the layout (edge margin, gap between neighbouring models, thread sizes)
  3. Build the plate and one helical M3 stud (circle offset from the axis,
     extruded with a twist = smooth right-handed thread, chamfered tip)
  4. Fuse the studs into the plate with exact mesh booleans (one solid piece)
  5. Export STL (+ optional 3MF) and a JSON record of every parameter
  6. Render a preview (top-down layout + 3D)

Requirements:  pip install numpy trimesh matplotlib manifold3d
               (optional: lxml for 3MF export)
Run:           python base_plate_studs.py
Outputs:       baseplate_<X>x<Y>x<T>_<N>studs.stl, _params.json, _preview.png
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
MODEL_FOOTPRINT_MM = 30.0   # widest footprint of one model once screwed on (square box)
EDGE_MARGIN_MM = 10.0       # minimum free plate between a model and the plate edge
MIN_GAP_MM = 10.0           # minimum free space between neighbouring models (warning only)

# --- M3 thread ---
# Keep these two in step with the hole settings in coral_reef_two.py
# (THREAD_MINOR_DIA_MM / THREAD_MAJOR_DIA_MM / THREAD_PITCH_MM).
HOLE_MINOR_DIA_MM = 2.6     # minor diameter of the threaded hole in the model
HOLE_MAJOR_DIA_MM = 3.2     # major diameter of the threaded hole in the model
THREAD_PITCH_MM = 0.5       # M3 coarse pitch
FIT_CLEARANCE_MM = 0.1      # radial gap between stud and hole (stud = hole - this)

# --- Stud shape ---
STUD_HEIGHT_MM = 6.0        # height of the threaded part above the plate.
                            # Keep it about 1 mm under the model's SCREW_DEPTH_MM (7)
                            # so the model can sit flat on the plate
STUD_TIP_CHAMFER_MM = 0.45  # lead-in chamfer at the top of each stud
STUD_EMBED_MM = 1.5         # how far the thread runs down into the plate (fuses it)

# --- Meshing / output ---
THREAD_SEGMENTS = 64        # points around the thread outline
THREAD_STEPS_PER_TURN = 32  # slices per thread turn (higher = smoother, heavier)
EXPORT_3MF = True           # also write a 3MF (needs lxml); the STL is always written
_name = f"baseplate_{PLATE_X_MM:g}x{PLATE_Y_MM:g}x{PLATE_THICKNESS_MM:g}_{STUD_COLUMNS * STUD_ROWS}studs"
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
    if STUD_HEIGHT_MM > 6.5:
        print("  WARNING: tall studs may bottom out in the model's 7 mm hole")
    return centres, (px, py), margin, gap


# =====================================================================
# 3-4. Plate + studs
# =====================================================================
def build_mesh(centres):
    try:
        import manifold3d as mf
    except ImportError:
        raise ImportError("This script needs manifold3d:  pip install manifold3d")

    r_minor = HOLE_MINOR_DIA_MM / 2 - FIT_CLEARANCE_MM
    r_major = HOLE_MAJOR_DIA_MM / 2 - FIT_CLEARANCE_MM
    a, e = (r_minor + r_major) / 2, (r_major - r_minor) / 2

    # One stud: a circle offset from the axis, extruded with a twist. Its radius
    # swings between r_minor and r_major once per pitch (right-handed thread).
    z0 = PLATE_THICKNESS_MM - STUD_EMBED_MM
    height = STUD_HEIGHT_MM + STUD_EMBED_MM
    turns = height / THREAD_PITCH_MM
    t = np.linspace(0, 2 * np.pi, THREAD_SEGMENTS, endpoint=False)
    outline = np.column_stack([e + a * np.cos(t), a * np.sin(t)])
    stud = mf.Manifold.extrude(mf.CrossSection([outline]), height,
                               int(turns * THREAD_STEPS_PER_TURN), 360.0 * turns,
                               (1.0, 1.0)).translate([0, 0, z0])

    # Chamfered tip: trim the thread with a cylinder whose top edge is bevelled
    top = PLATE_THICKNESS_MM + STUD_HEIGHT_MM
    c = STUD_TIP_CHAMFER_MM
    envelope = (mf.Manifold.cylinder(top - c - z0, r_major + 0.5, r_major + 0.5, 96, False).translate([0, 0, z0]) +
                mf.Manifold.cylinder(c, r_major, r_major - c, 96, False).translate([0, 0, top - c]))
    stud = stud ^ envelope

    plate = mf.Manifold.cube([PLATE_X_MM, PLATE_Y_MM, PLATE_THICKNESS_MM], False) \
        .translate([-PLATE_X_MM / 2, -PLATE_Y_MM / 2, 0])
    for x, y in centres:
        plate = plate + stud.translate([x, y, 0])

    out = plate.to_mesh()
    mesh = trimesh.Trimesh(np.array(out.vert_properties)[:, :3].astype(float),
                           np.array(out.tri_verts), process=False)
    return mesh, (2 * r_minor, 2 * r_major)


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
        ax.add_patch(Circle((x, y), HOLE_MAJOR_DIA_MM / 2 - FIT_CLEARANCE_MM, fc="k"))
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

    print("3-4. Building plate and threaded studs")
    mesh, (stud_minor, stud_major) = build_mesh(centres)
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
            "hole_minor_dia_mm": HOLE_MINOR_DIA_MM, "hole_major_dia_mm": HOLE_MAJOR_DIA_MM,
            "thread_pitch_mm": THREAD_PITCH_MM, "fit_clearance_mm": FIT_CLEARANCE_MM,
            "stud_height_mm": STUD_HEIGHT_MM, "stud_tip_chamfer_mm": STUD_TIP_CHAMFER_MM,
            "stud_embed_mm": STUD_EMBED_MM,
        },
        "results": {
            "stud_centres_mm": [[round(float(x), 3), round(float(y), 3)] for x, y in centres],
            "stud_pitch_mm": [round(float(px), 3), round(float(py), 3)],
            "stud_minor_dia_mm": round(stud_minor, 2), "stud_major_dia_mm": round(stud_major, 2),
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
    print(f"Plate {PLATE_X_MM:g} x {PLATE_Y_MM:g} x {PLATE_THICKNESS_MM:g} mm, {len(centres)} M3 studs "
          f"({r['stud_minor_dia_mm']}-{r['stud_major_dia_mm']} mm dia, {STUD_HEIGHT_MM:g} mm tall)")
    print(f"Stud pitch {r['stud_pitch_mm']} mm   Edge margin {r['edge_margin_mm']} mm   "
          f"Model gap {r['gap_between_models_mm']} mm")
    print(f"Watertight: {r['mesh_watertight']}   Solid pieces: {r['solid_pieces']}")
    print(f"Saved {OUT_STL}" + (f", {OUT_3MF}" if EXPORT_3MF else "") + f", {OUT_JSON}, {OUT_PNG}")


if __name__ == "__main__":
    main()
