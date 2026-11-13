# Sizing guide: changing the diameter

`coral_reef.py` is set up for a 30 mm coral. To make a bigger or smaller one, several settings have to change together. This guide lists them.

## The rule behind it

The size of the walls and valleys is set by the **pattern scale**: how many millimetres one simulation voxel covers.

```
pattern scale (mm) = DIAMETER_MM / VOXELS_ACROSS
```

If you change `DIAMETER_MM` and leave `VOXELS_ACROSS` alone, the whole pattern is stretched: a 50 mm coral with `VOXELS_ACROSS = 43` has walls and channels about 1.7 times as wide as the 30 mm one. So choose a pattern scale first, then work out the other settings from the diameter.

Two pattern scales are worth using:

| Pattern  | Scale  | Typical valley width | Look                                                                                  |
| -------- | ------ | -------------------- | ------------------------------------------------------------------------------------- |
| Standard | 0.7 mm | about 5 mm           | The v2.0.0 reference example                                                          |
| Fine     | 0.5 mm | about 4 mm           | Closer to *Platygyra daedalea*, whose valleys are 4 to 5 mm wide (Salimi et al. 2018) |

## Settings that change with the diameter

### `coral_reef.py`

| Diameter | Pattern  | `VOXELS_ACROSS` | `GRID`       | `TARGET_TRIANGLES` | STL size (approx.) |
| -------- | -------- | --------------- | ------------ | ------------------ | ------------------ |
| 30 mm    | Standard | 43 (tested)     | 96           | 60_000 (tested)    | 3 MB               |
| 30 mm    | Fine     | 60              | 96           | 120_000            | 6 MB               |
| 40 mm    | Standard | 57              | 96           | 110_000            | 5 MB               |
| 40 mm    | Fine     | 80              | 96           | 210_000            | 10 MB              |
| 50 mm    | Standard | 72 (tested)     | 96           | 170_000            | 8 MB               |
| 50 mm    | Fine     | 100 (tested)    | 128 (tested) | 330_000            | 16 MB              |
| 60 mm    | Standard | 86              | 96           | 240_000            | 12 MB              |
| 60 mm    | Fine     | 120             | 128          | 470_000            | 23 MB              |

"(tested)" marks values that have been run. The others follow from these rules:

- **`VOXELS_ACROSS`** = diameter / pattern scale (0.7 or 0.5 mm).
- **`GRID`** must be at least `VOXELS_ACROSS`. If it is smaller, the simulated pattern is repeated side by side and the same pattern appears twice. Going from 96 to 128 makes the simulation about 2.4 times slower.
- **`TARGET_TRIANGLES`** grows with the square of the diameter, and again as the pattern gets finer, because smaller features need more triangles to keep rounded ridge tops instead of flat facets. Halve the number for a smaller file with less detail.

### `base_plate_studs.py` (2 x 2 plate)

| Diameter | `MODEL_FOOTPRINT_MM` | `PLATE_X_MM` and `PLATE_Y_MM` |
| -------- | -------------------- | ----------------------------- |
| 30 mm    | 30                   | 90                            |
| 40 mm    | 40                   | 110                           |
| 50 mm    | 50                   | 130                           |
| 60 mm    | 60                   | 150                           |

Plate size = 2 x edge margin (`EDGE_MARGIN_MM`, 10) + 2 x diameter + one gap between corals (`MIN_GAP_MM`, 10). For other stud counts: plate size = 2 x margin + columns x diameter + (columns - 1) x gap.

## Settings that follow the pattern scale, not the diameter

These are all in millimetres and should match the size of the valleys:

| Setting          | Standard (0.7 mm) | Fine (0.5 mm) |
| ---------------- | ----------------- | ------------- |
| `MIN_STRUT_MM`   | 2.0               | 1.2           |
| `MIN_CHANNEL_MM` | 2.5               | 1.5           |
| `SKIN_MM`        | 3.5               | 2.5           |
| `TOP_SKIN_MM`    | 4.0               | 4.0           |
| `CREST_MM`       | 3.0               | 3.0           |

The 1.2 mm wall and 1.5 mm channel limits in the fine column are about as small as the method should go. Check them against what your printer can hold and, for binder jetting, what can still be cleared of loose powder.

## Settings that do not change

- `HEIGHT_MM` (30, base included) and `BASE_MM`.
- `STEPS`, `F`, `K`, `DU` and `DV`. These decide the type of pattern, not its size: changing them can turn the labyrinth into spots or blobs.
- `SOLID_FRACTION`, `SKIN_STRENGTH`, `TOP_SKIN_STRENGTH` and `CREST_TAPER`.
- All joint settings. The 14.6 mm boss around the socket fits every diameter from 30 mm up.

## Example: a 50 mm coral with the fine pattern

In `coral_reef.py`:

```python
DIAMETER_MM = 50.0
GRID = 128
VOXELS_ACROSS = 100
SKIN_MM = 2.5
MIN_STRUT_MM = 1.2
MIN_CHANNEL_MM = 1.5
TARGET_TRIANGLES = 330_000
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
