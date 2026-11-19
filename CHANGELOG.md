# Changelog

How the design evolved, newest first. Each version lists what changed and why.

## v2.1.0: a more natural lattice (unreleased)

- The unstretched overhang rule was found to damage the pattern (it is now used only together with the vertical stretch, below). The rule works bottom-up, so trimming one unsupported wall also removes everything resting on it. On a 50 mm, seed 7 coral it removed 487,146 voxels, raising porosity from 47% to 60% and cutting caves into the sides, with rows of 45-degree slanted walls. The JSON now records `overhang_trimmed_percent`, and the script warns when the rule removes more than 10% of the solid.
- Finer pattern by default, matching the early lattice that looked most natural: `VOXELS_ACROSS` 43 to 70 (0.70 to 0.43 mm per simulation voxel), minimum wall and channel 1.5 mm and 2.0 mm, and `TARGET_TRIANGLES` 60,000 to 250,000 so the smoother shapes are kept. Reference example: 47% porosity, median wall 2.6 mm, median channel 3.0 mm.
- The side skin is now off by default (`SKIN_STRENGTH = 0`).
- Added an optional top skin (`TOP_SKIN_MM`, `TOP_SKIN_STRENGTH`) and crest band (`CREST_MM`, `CREST_TAPER`), both off by default. The original skin only measured depth from the curved wall, so it never reached the top face; the top skin covers it, and the crest band raises rounded ridges from it. Both are recorded in the JSON, and a new test checks that the top skin closes the top.
- Added `sizing_guide.md`: which settings to change, and to what, for corals from 30 to 60 mm across.
- One geometry for PLA and binder jetting: new `VERTICAL_STRETCH` setting, default 2.0, with the overhang rule back on at 45 degrees. Stretching the pattern vertically makes the walls steeper, so the rule removes very little (1.3% on the 30 mm reference, 2.3% on a 50 mm coral instead of 8.1% unstretched) and leaves no slanted "fence". The same STL now prints support-free in PLA and in binder-jet CaCO3. `MAX_OVERHANG_DEG = True` is now refused, because Python reads it as 1 degree, which removed 52% of a 50 mm model.
- Default coral is now 50 mm across (seed 9, `VOXELS_ACROSS` 116, `GRID` 128, `TARGET_TRIANGLES` 700,000), with a matching 130 x 130 x 5 mm base plate (`MODEL_FOOTPRINT_MM` 50). Reference example: 45% porosity, median wall 3.0 mm, median channel 3.5 mm; the overhang rule trims 1.4%.
- GitHub Actions updated to `actions/checkout@v6` and `actions/setup-python@v6`, which run on Node.js 24.
- Stronger bayonet joint after test prints proved too brittle: stud 5 to 10 mm across and 8 to 15 mm tall (half the coral's height), lugs 2.5 to 7.5 mm tall (half the stud) and 8 to 15 mm across, base fillet 0.5 to 1.5 mm with a matching 1.5 mm socket mouth chamfer, lug root fillet 0.5 to 1.0 mm, and base plate 3 to 5 mm thick. The locking shelf is now 6.95 mm thick (was 4.95 mm). The larger socket needs a solid boss 21.6 mm across and 17.5 mm tall, which lowers the reference coral's porosity from 47% to 36%.
- Reference coral and plate in `examples/` regenerated. The coral STL is now about 12.5 MB because of the finer mesh, and the plate files are renamed `baseplate_90x90x5_...`.

## v2.0.0: bayonet joint (November 2026)

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
