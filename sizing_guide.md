# Sizing guide: changing the diameter

`coral_reef.py` is set up for a 30 mm coral. To make a bigger or smaller one, several settings have to change together. This guide lists them.

## The rule behind it

The size of the walls and valleys is set by the **pattern scale**: how many millimetres one simulation voxel covers.

```
pattern scale (mm) = DIAMETER_MM / VOXELS_ACROSS
```

If you change `DIAMETER_MM` and leave `VOXELS_ACROSS` alone, the whole pattern is stretched: a 50 mm coral with `VOXELS_ACROSS = 43` has walls and channels about 1.7 times as wide as the 30 mm one. So choose a pattern scale first, then work out the other settings from the diameter.

Two pattern scales are worth using:

| Pattern | Scale   | Typical channel width | Look                                                                                  |
| ------- | ------- | --------------------- | ------------------------------------------------------------------------------------- |
| Default | 0.43 mm | about 3 mm            | Fine, open and natural-looking; the script's default                                  |
| Coarser | 0.5 mm  | about 3.5 to 4 mm     | Closer to *Platygyra daedalea*, whose valleys are 4 to 5 mm wide (Salimi et al. 2018) |

(Version 2.0.0 used 0.7 mm. It looked blocky, especially at larger diameters.)

## Settings that change with the diameter

### `coral_reef.py`

| Diameter | Pattern | `VOXELS_ACROSS` | `GRID`       | `TARGET_TRIANGLES` | STL size (approx.) |
| -------- | ------- | --------------- | ------------ | ------------------ | ------------------ |
| 30 mm    | Default | 70 (tested)     | 96 (tested)  | 250_000 (tested)   | 12 MB              |
| 30 mm    | Coarser | 60              | 96           | 185_000            | 9 MB               |
| 40 mm    | Default | 93              | 96           | 450_000            | 22 MB              |
| 40 mm    | Coarser | 80              | 96           | 330_000            | 16 MB              |
| 50 mm    | Default | 116             | 128          | 700_000            | 35 MB              |
| 50 mm    | Coarser | 100 (tested)    | 128 (tested) | 515_000            | 26 MB              |
| 60 mm    | Default | 140             | 160          | 1_000_000          | 50 MB              |
| 60 mm    | Coarser | 120             | 128          | 740_000            | 37 MB              |

"(tested)" marks values that have been run. The others follow from these rules:

- **`VOXELS_ACROSS`** = diameter / pattern scale (0.43 or 0.5 mm).
- **`GRID`** must be at least `VOXELS_ACROSS`. If it is smaller, the simulated pattern is repeated side by side and the same pattern appears twice. Simulation time grows with the cube of `GRID`: 128 takes about 2.4 times as long as 96, and 160 about 4.6 times.
- **`TARGET_TRIANGLES`** grows with the square of the diameter, and again as the pattern gets finer, because smaller features need more triangles to keep rounded shapes instead of flat facets. Halve the number for a smaller file with less detail. GitHub warns about files over 50 MB, so keep very large STLs out of the repository.

### `base_plate_studs.py` (2 x 2 plate)

| Diameter | `MODEL_FOOTPRINT_MM` | `PLATE_X_MM` and `PLATE_Y_MM` |
| -------- | -------------------- | ----------------------------- |
| 30 mm    | 30                   | 90                            |
| 40 mm    | 40                   | 110                           |
| 50 mm    | 50                   | 130                           |
| 60 mm    | 60                   | 150                           |

Plate size = 2 x edge margin (`EDGE_MARGIN_MM`, 10) + 2 x diameter + one gap between corals (`MIN_GAP_MM`, 10). For other stud counts: plate size = 2 x margin + columns x diameter + (columns - 1) x gap.

## Settings that follow the pattern scale, not the diameter

These are in millimetres and should match the size of the channels:

| Setting          | Default (0.43 mm) | Coarser (0.5 mm) |
| ---------------- | ----------------- | ---------------- |
| `MIN_STRUT_MM`   | 1.5 (tested)      | 1.2 (tested)     |
| `MIN_CHANNEL_MM` | 2.0 (tested)      | 1.5 (tested)     |

Only if you turn the optional skins on: `SKIN_MM` about 2.5, `TOP_SKIN_MM` about 4.0 and `CREST_MM` about 3.0 suit both scales.

Check the minimum wall and channel sizes against what your printer can hold and, for binder jetting, what can still be cleared of loose powder.

## One geometry for PLA and binder jetting

The defaults (`VERTICAL_STRETCH = 2.0`, `MAX_OVERHANG_DEG = 45`) make a single geometry that prints support-free in PLA and identically in binder-jet CaCO3, so prototypes match the final parts. Keep both settings when you change the diameter.

The overhang rule works from the bottom up, so removing one unsupported wall also removes everything resting on it. Without the stretch it can cut caves into the sides and leave rows of 45-degree slanted walls, especially on large, finely patterned corals. Check `overhang_trimmed_percent` in the JSON; the script warns above 10%. Always give it an angle: `MAX_OVERHANG_DEG = True` is read by Python as 1 degree and removes about half the model, so the script refuses it.

### Why the stretch

On a 50 mm coral (default pattern, seed 23):

| Settings                  | Solid removed by the rule | Downward surface needing support |
| ------------------------- | ------------------------- | -------------------------------- |
| No rule                   | 0%                        | 907 mm2                          |
| Rule at 45 degrees        | 8.1%                      | 69 mm2, slanted "fence" walls    |
| Stretch 2.0 + rule at 45  | 2.3%                      | 24 mm2                           |
| `MAX_OVERHANG_DEG = True` | 51.8%                     | 0 (most of the model gone)       |

From above, the stretched pattern is the same labyrinth; from the side, the valleys run upright, as on a brain coral. The only remaining large overhang is the flat roof of the bayonet socket (a 10.6 mm bridge), which PLA bridges without support. In Bambu Studio, turn supports off (or use "On build plate only" with a support blocker over the socket), so no supports are placed inside the model.

## Settings that do not change

- `HEIGHT_MM` (30, base included) and `BASE_MM`.
- `STEPS`, `F`, `K`, `DU` and `DV`. These decide the type of pattern, not its size: changing them can turn the labyrinth into spots or blobs.
- `SOLID_FRACTION`, `SKIN_STRENGTH`, `TOP_SKIN_STRENGTH` and `CREST_TAPER`.
- `MAX_OVERHANG_DEG` (45) and `VERTICAL_STRETCH` (2.0).
- All joint settings. The 21.6 mm boss around the socket fits every diameter from 30 mm up, but at 30 mm it takes up much of the centre (see the CHANGELOG).

## Example: a 50 mm coral with the coarser pattern

In `coral_reef.py`:

```python
DIAMETER_MM = 50.0
GRID = 128
VOXELS_ACROSS = 100
MIN_STRUT_MM = 1.2
MIN_CHANNEL_MM = 1.5
TARGET_TRIANGLES = 515_000
```

In `base_plate_studs.py`:

```python
PLATE_X_MM = 130.0
PLATE_Y_MM = 130.0
MODEL_FOOTPRINT_MM = 50.0
```

Expect the coral to take noticeably longer than the 30 mm default, mostly in the simulation step.

## Reference

Salimi, P. A., Mostafavi, P. G., Chen, C. A., Fatemi, S. M. R. and Pichon, M. (2018). *Zoological Studies*, 57, 56. Description of *Platygyra daedalea*: valley width 4-5 mm, valley depth 4.5-6 mm. https://doi.org/10.6620/ZS.2018.57-56
