"""
joint_fit.py — Check that a coral fits, turns and locks on a base plate stud.

Simulates the bayonet joint with exact solid geometry (manifold3d): the coral is
lowered onto one stud, turned to the locked position, then pulled upwards. At
each step it measures how much the two parts overlap (interference, mm^3).
About zero means the parts move freely; above zero means they collide.

Run:   python tools/joint_fit.py coral.stl coral_params.json plate.stl plate_params.json
       (the JSON files are the records the two scripts write next to each STL)
"""
import json
import sys

import numpy as np
import trimesh

TOUCH_MM3 = 1e-3   # overlaps smaller than this count as no contact


def _to_manifold(mesh):
    import manifold3d as mf
    return mf.Manifold(mf.Mesh(vert_properties=mesh.vertices.astype(np.float32),
                               tri_verts=mesh.faces.astype(np.uint32)))


def joint_frames(coral, plate, plate_thickness_mm, stud_xy):
    """Return (coral, stud) as manifolds in a shared frame: stud axis at the
    origin, plate top at z = 0, coral bottom face at z = 0 on its socket axis."""
    import manifold3d as mf
    zb = coral.vertices[:, 2].min()
    foot = coral.vertices[coral.vertices[:, 2] < zb + 0.5]
    cx, cy = (foot[:, :2].min(0) + foot[:, :2].max(0)) / 2
    sx, sy = stud_xy
    box = mf.Manifold.cube([20, 20, 40], False).translate([sx - 10, sy - 10, plate_thickness_mm + 0.01])
    stud = (_to_manifold(plate) ^ box).translate([-sx, -sy, -plate_thickness_mm])
    body = _to_manifold(coral).translate([-cx, -cy, -zb])
    return body, stud


def interference(body, stud, turn_deg, lift_mm):
    """Overlap (mm^3) with the coral turned clockwise by turn_deg (seen from above)
    and lifted lift_mm off the plate."""
    return (body ^ stud.rotate([0, 0, turn_deg]).translate([0, 0, -lift_mm])).volume()


def play(body, stud, turn_deg, max_mm=1.0, step=0.01):
    """How far the coral can lift at this turn before it touches the stud (mm)."""
    for lift in np.arange(0.0, max_mm + step, step):
        if interference(body, stud, turn_deg, lift) > TOUCH_MM3:
            return round(float(max(lift - step, 0.0)), 2)
    return None   # lifts freely


def fit_report(coral, plate, plate_thickness_mm, stud_xy, twist_deg):
    body, stud = joint_frames(coral, plate, plate_thickness_mm, stud_xy)
    hit = lambda a, l: interference(body, stud, a, l)
    r = {
        "insert_clear": all(hit(0, l) < TOUCH_MM3 for l in (8.0, 6.0, 4.0, 2.0, 0.0)),
        "turn_clear": all(hit(a, 0) < TOUCH_MM3 for a in np.linspace(0, twist_deg, 7)),
        "play_mm": {f"{a:g}": play(body, stud, a) for a in (twist_deg / 3, 2 * twist_deg / 3, twist_deg)},
        "pull_out_blocked_at_0_5mm": hit(twist_deg, 0.5) > TOUCH_MM3,
        "overturn_blocked": hit(twist_deg + 15, 0) > TOUCH_MM3,
        "lifts_out_at_entry": hit(0, 2.0) < TOUCH_MM3,
    }
    r["pass"] = all([r["insert_clear"], r["turn_clear"], r["pull_out_blocked_at_0_5mm"], r["overturn_blocked"]])
    return r


def main(argv):
    if len(argv) != 5:
        print(__doc__)
        return 2
    coral, cparams, plate, pparams = argv[1:]
    cp, pp = json.load(open(cparams)), json.load(open(pparams))
    twist = cp["parameters"]["joint"]["twist_deg"]
    t = pp["parameters"]["plate_mm"][2]
    stud_xy = pp["results"]["stud_centres_mm"][0]
    r = fit_report(trimesh.load(coral), trimesh.load(plate), t, stud_xy, twist)
    print(f"Slides down through the slots without touching: {r['insert_clear']}")
    print(f"Turns {twist:g} deg to lock without touching:   {r['turn_clear']}")
    print(f"Up-and-down play while turning (mm):           {r['play_mm']}")
    print(f"Locked coral cannot be pulled off (0.5 mm):    {r['pull_out_blocked_at_0_5mm']}")
    print(f"Stops at the locked position:                  {r['overturn_blocked']}")
    print(f"Lifts straight off when turned back:           {r['lifts_out_at_entry']}")
    print("RESULT:", "PASS" if r["pass"] else "FAIL")
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
