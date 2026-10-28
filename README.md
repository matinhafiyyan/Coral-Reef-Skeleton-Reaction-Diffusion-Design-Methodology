# Reaction-Diffusion Coral Skeleton

Python scripts that grow a 3D-printable coral settlement structure from a Gray-Scott reaction-diffusion simulation, plus a base plate with threaded M3 studs to mount the printed corals on.

The lattice is inspired by the meandering valleys of *Platygyra* (brain coral). It is designed for binder-jet printing in calcium carbonate, and can be prototyped in PLA on an FDM printer without supports.

| Script                | Makes                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------- |
| `coral_reef.py`       | The coral skeleton: a porous cylinder (or dome) with an M3 threaded hole in the bottom |
| `base_plate_studs.py` | A flat plate with threaded M3 studs; each coral screws onto one stud                   |

## Quick start

```bash
# 1. Create an environment (Anaconda Prompt on Windows, Terminal on macOS)
conda create -n coral python=3.13 -y
conda activate coral
pip install -r requirements.txt

# 2. Generate a coral (about 3-5 minutes)
python coral_reef.py

# 3. Generate the base plate (under a minute)
python base_plate_studs.py
```

Each script writes three files to the folder it runs in:

| File            | What it is                                                 |
| --------------- | ---------------------------------------------------------- |
| `*.stl`         | The printable model, in millimetres. Import at 100% scale. |
| `*_params.json` | Every setting used, plus measurements of the result        |
| `*_preview.png` | A quick picture to check the result before slicing         |

## Making your own variants

All settings are at the top of each script, in the block marked `SETTINGS - change these`. Most people only need these:

| Setting (`coral_reef.py`)        | What it does                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `SEED`                           | Picks a different random starting point: a new pattern with the same statistics |
| `SHAPE`                          | `"cylinder"` (prints without supports) or `"dome"`                              |
| `DIAMETER_MM`, `HEIGHT_MM`       | Outer size. `HEIGHT_MM` already includes the base                               |
| `VOXELS_ACROSS`                  | Pattern scale. Smaller number = bigger channels                                 |
| `SOLID_FRACTION`                 | How much of the part is solid. Lower = more porous                              |
| `SKIN_STRENGTH`                  | 0 = open lattice on the surface; higher = more closed, brain-coral-like surface |
| `MIN_STRUT_MM`, `MIN_CHANNEL_MM` | Thinnest wall and narrowest channel allowed. Set from your printer's limits     |

| Setting (`base_plate_studs.py`) | What it does                                                        |
| ------------------------------- | ------------------------------------------------------------------- |
| `PLATE_X_MM`, `PLATE_Y_MM`      | Plate size                                                          |
| `STUD_COLUMNS`, `STUD_ROWS`     | Number of studs                                                     |
| `MODEL_FOOTPRINT_MM`            | Width of one coral. **Must match `DIAMETER_MM` in `coral_reef.py`** |

The thread settings (`THREAD_PITCH_MM` and the minor and major diameters) must match between the two scripts, or the corals will not screw on.

## Reproducing a result

A design is fully defined by its `_params.json`. To rebuild one exactly:

1. Check out the version of the code the design was made with (its Git tag or commit).
2. Install the same library versions from `requirements.txt`.
3. Copy the values from `parameters` in the JSON into the settings block.
4. Run the script. The same `SEED` and settings give the same pattern.

## How it works

See [docs/code_walkthrough.md](docs/code_walkthrough.md) for a plain-language explanation of every part of both scripts and how it maps to the methodology.

In short, `coral_reef.py`:

1. Simulates two virtual chemicals reacting and spreading in a 3D grid (Gray-Scott model).
2. Turns high-concentration regions into solid and the rest into open channels.
3. Cuts the result to a cylinder or dome and adds a solid base.
4. Fixes anything unprintable: walls too thin, channels too narrow, overhangs, loose bits, sealed pockets.
5. Measures wall and channel sizes.
6. Converts the voxels to a smooth mesh, cuts an M3 thread into the bottom and saves an STL.

## Acknowledgements and references

- Karl Sims, [Reaction-Diffusion Tutorial](https://karlsims.com/rd.html): the reference for the Gray-Scott model used here.
- Gray, P. and Scott, S. K. (1984). Autocatalytic reactions in the isothermal, continuous stirred tank reactor. *Chemical Engineering Science*, 39(6), 1087-1097.
- Pearson, J. E. (1993). Complex patterns in a simple system. *Science*, 261(5118), 189-192.
- Inspired by Alex Schofield's Coral Carbonate project.
