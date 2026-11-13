# Changelog

How the design evolved, newest first. Each version lists what changed and why.

## v2.1.0: brain-coral top surface (unreleased)

- Added a top skin (`TOP_SKIN_MM` 4.0, `TOP_SKIN_STRENGTH` 0.85). The surface skin was meant to close every face except the bottom, but it only measured depth from the curved wall, so the top was a flat cut through the lattice that left loose-looking posts. The top skin closes it.
- Added a crest band (`CREST_MM` 3.0, `CREST_TAPER` 0.5). The top few millimetres are rebuilt from the flat pattern of the layer below, so rounded, meandering ridges with valleys between them rise from the closed surface, like the ridges and valleys of *Platygyra*, instead of a flat slab with holes in it.
- Both are recorded in the JSON. A new test checks that the top skin closes the top.
- Added `sizing_guide.md`: which settings to change, and to what, for corals from 30 to 60 mm across.
- Reference coral in `examples/` regenerated with the new top.

: bayonet joint (November 2026)

The mounting joint was redesigned twice after v1.0.0. A printed M5 thread (developed in place of the M3 thread, but never released) was replaced by a quarter-turn bayonet, because a joint for binder-jet calcium carbonate parts cannot rely on screws, nuts or adhesive: metal or nylon hardware would not survive sintering, and glue would add a second material to the structure.

Joint:

- Replaced the threaded hole and threaded studs with a bayonet joint. Each stud is a 5 mm shaft, 8 mm tall, with two lugs (8 mm across, 3 mm wide, 2.5 mm tall). The coral has a matching socket: bore, two entry slots and a 90-degree locking pocket. Push on, turn 90 degrees clockwise to lock.
- The locking shelf is ramped: 0.3 mm clear of the lugs at entry, 0.05 mm when locked (`LOCK_PLAY_MM`), so the coral tightens onto the plate as it turns. The end of the pocket stops it from being over-turned.
- Added 0.5 mm fillets at the base of each stud and on top of each lug, where they are most likely to break.
- The solid boss around the socket is sized from the joint settings (14.6 mm across, 10.5 mm tall by default).
- New joint settings in both scripts (`STUD_DIA_MM`, `STUD_HEIGHT_MM`, `LUG_SPAN_MM`, `LUG_WIDTH_MM`, `LUG_HEIGHT_MM`, `LUG_TOP_BELOW_TIP_MM`, `JOINT_CLEARANCE_MM`) replace the thread settings. Coral-only settings: `TWIST_DEG`, `LOCK_PLAY_MM`, `JOINT_WALL_MM`, `JOINT_ROOF_MM`, `JOINT_CHAMFER_MM`, `RAMP_STEPS`. The JSON record saves them all, plus the derived socket sizes.
- Fixed STL files that were watertight in memory but not after saving: the socket shapes are now offset very slightly so no surfaces coincide after the STL rounds its coordinates.
- Output files are now named `..._bayonet.stl`, `..._bayonet_params.json` and `..._bayonet_preview.png`.

Lattice:

- Lowered the solid fraction from 0.55 to 0.45 and relaxed the minimum wall and channel sizes to 2.0 mm and 2.5 mm, giving a more open lattice (45% porosity; median wall 4.2 mm, median channel 4.9 mm for the reference example).
- Strengthened the surface skin (3.5 mm, 0.7) so channel openings narrow at the surface, reducing the open surface area from about 38% to about 23% so larvae are less likely to be washed out.
- Default seed changed from 42 to 23.

Tools, tests and examples:

- Added `tools/joint_fit.py`, which checks that a coral and a plate fit, turn, lock and come apart again, and measures the play at the joint.
- Added `tools/joint_views.py`, which draws the socket, a stud and a half-section of the locked joint, and exports the assembly as a `.glb` file.
- Added `tests/test_joint_fit.py` and tests that the joint settings match between the scripts, that the socket leaves a locking shelf, and that the stud fillet fits the socket mouth.
- Reference outputs in `examples/` regenerated for seed 23 with the bayonet joint, plus the joint views and assembly.

## Repository: tests and reference outputs (October 2026)

- Renamed `REQUIREMENTS` to `requirements.txt` so the install command in the README works.
- Added automated tests (`tests/`) that check every model is one watertight piece, has the requested size, records all its settings, and comes out identical for the same settings.
- Added reference outputs (`examples/`) and a test that reproduces them from scratch.
- Added a GitHub Actions workflow that runs the tests on every push.
- Fixed old file names in `base_plate_studs.py`.

## v5: cylinder with M3 mounting (October 2026)

- Added a threaded M3 hole in the base of each model and `base_plate_studs.py`, a plate with matching studs for mounting several models together.
- Chose the cylinder as the only shape. The dome needed support material when sliced for FDM printing; the cylinder did not.
- Reduced the diameter to 30 mm and halved `VOXELS_ACROSS` (85 to 43) so walls and channels keep the same size in millimetres.
- The JSON record now also saves the overhang setting, mesh target, thread chamfer and the Python and library versions used.

## v4: 30 mm height limit (October 2026)

- Capped the total height at 30 mm, base included, to fit the binder-jet printer's build volume.
- Made the pattern finer (`VOXELS_ACROSS` 60 to 85) so a 30 mm part holds several layers of channels instead of two.
- Added a surface skin that partly closes the outside, so the top no longer looks like a sponge sliced open.

## v3: back to the labyrinth pattern, dome option (October 2026)

- Returned to `F = 0.030`, `K = 0.058`. The v2 pattern looked blocky and less coral-like.
- Thickened walls through the solid fraction (0.60) and pattern scale instead of the reaction parameters.
- Added a dome shape alongside the cylinder.

## v2: PLA prototype (October 2026)

- Slicing for PLA printing showed heavy overhangs that needed support material.
- Added a 45-degree overhang rule so models print without supports.
- Lowered the reaction parameters (`F = 0.022`, `K = 0.051`) for larger, fewer channels.
- Added mesh simplification: file size went from 31 MB to 3 MB.

## v1: first 3D lattice (October 2026)

- Gray-Scott reaction-diffusion simulated in 3D (`F = 0.030`, `K = 0.058`) and clipped to a 50 x 50 mm cylinder.
- Automatic removal of loose pieces and sealed pockets, minimum wall and channel sizes, and measurement of both.
- Each model saved with a JSON record of its settings and results.
