# Changelog

How the design evolved, newest first. Each version lists what changed and why.

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
