"""
joint_views.py — Picture of the joint and an assembly file for Blender.

Writes <out_prefix>_joint_views.png (the coral's socket from below, one stud,
and the locked joint cut in half) and <out_prefix>_assembly.glb (the whole
plate with this coral locked on the first stud, as two objects).

Run:   python tools/joint_views.py coral.stl coral_params.json plate.stl plate_params.json out_prefix
"""
import sys
import numpy as np
import trimesh
import manifold3d as mf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def to_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=m.vertices.astype(np.float32), tri_verts=m.faces.astype(np.uint32)))


def to_tm(M):
    o = M.to_mesh()
    return trimesh.Trimesh(np.array(o.vert_properties)[:, :3].astype(float), np.array(o.tri_verts), process=False)


import json
if len(sys.argv) != 6:
    print(__doc__); sys.exit(2)
coral_path, cparams, plate_path, pparams, out = sys.argv[1:]
cp, pp = json.load(open(cparams)), json.load(open(pparams))
lock = cp["parameters"]["joint"]["twist_deg"]
t = pp["parameters"]["plate_mm"][2]
sx, sy = pp["results"]["stud_centres_mm"][0]
title = "Bayonet joint: slide the coral down through the slots, then turn it a quarter turn clockwise to lock"

coral = trimesh.load(coral_path)
plate = trimesh.load(plate_path)
zb = coral.vertices[:, 2].min()
foot = coral.vertices[coral.vertices[:, 2] < zb + 0.5]
cx, cy = (foot[:, :2].min(0) + foot[:, :2].max(0)) / 2

# Local frame: stud axis at origin, plate top at z = 0
C = to_mf(coral).translate([-cx, -cy, -zb])
P = to_mf(plate).translate([-sx, -sy, -t])
patch = mf.Manifold.cube([40, 40, 40], False).translate([-20, -20, -t - 1])
P_local = P ^ patch                                   # one stud and a square of plate
C_locked = C.rotate([0, 0, -lock])                    # coral turned clockwise to lock

COR, PLA = np.array([0.93, 0.86, 0.76]), np.array([0.55, 0.72, 0.80])


def draw(ax, parts, elev, azim, lim):
    e, a = np.radians(elev), np.radians(azim)
    cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    light = cam + np.array([0.25, 0.15, 0.35]); light /= np.linalg.norm(light)
    tris, cols = [], []
    for M, col in parts:                      # one collection, so faces are depth-sorted together
        m = to_tm(M)
        if len(m.faces) == 0:
            continue
        v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=1.0)
        m = trimesh.Trimesh(v, f, process=False)
        sh = 0.3 + 0.7 * np.clip(m.face_normals @ light, 0, 1)
        tris.append(m.vertices[m.faces]); cols.append(np.outer(sh, col))
    ax.add_collection3d(Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), linewidths=0))
    (x0, x1), (y0, y1), (z0, z1) = lim
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1)
    ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0))
    ax.view_init(elev=elev, azim=azim); ax.axis("off")


fig = plt.figure(figsize=(15, 5.2))

# 1. Coral seen from below: the socket
ax = fig.add_subplot(1, 3, 1, projection="3d")
draw(ax, [(C, COR)], elev=-89, azim=-90, lim=((-16, 16), (-16, 16), (0, 30)))
ax.set_title("Coral from below: the socket")

# 2. The stud on the plate
ax = fig.add_subplot(1, 3, 2, projection="3d")
draw(ax, [(P_local, PLA)], elev=28, azim=-60, lim=((-10, 10), (-10, 10), (-3, 12)))
ax.set_title("Base plate stud")

# 3. Locked assembly, cut in half through the stud axis (plane y = 0, along the lugs or key)
keep = mf.Manifold.cube([60, 60, 60], False).translate([-30, 0, -10])   # keep y >= 0
ax = fig.add_subplot(1, 3, 3, projection="3d")
draw(ax, [(C_locked ^ keep, COR), (P_local ^ keep, PLA)], elev=4, azim=-90,
     lim=((-12, 12), (-12, 12), (-3, 16)))
ax.set_title("Locked, cut in half (coral beige, plate blue)")

fig.suptitle(title)
plt.tight_layout()
plt.savefig(out + "_joint_views.png", dpi=120)
plt.close(fig)

# Assembly for Blender: whole plate + this coral locked on the chosen stud (two objects)
scene = trimesh.Scene()
plate_obj = trimesh.load(plate_path)
coral_obj = to_tm(C_locked.translate([sx, sy, t]))
plate_obj.visual.face_colors = (PLA * 255).astype(np.uint8).tolist() + [255]
coral_obj.visual.face_colors = (COR * 255).astype(np.uint8).tolist() + [255]
scene.add_geometry(plate_obj, node_name="base_plate")
scene.add_geometry(coral_obj, node_name="coral_locked")
scene.export(out + "_assembly.glb")
print("wrote", out + "_joint_views.png", out + "_assembly.glb")
