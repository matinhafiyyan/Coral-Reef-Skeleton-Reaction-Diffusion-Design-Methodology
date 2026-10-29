# Reference outputs

These files were made by running the scripts in this repository with their default settings. Use them to check that your own run reproduces the published result.

| File | Made by |
| ---- | ------- |
| `coral_cylinder_seed42.stl` | `python coral_reef.py` (seed 42, 30 x 30 mm cylinder) |
| `coral_cylinder_seed42_params.json` | the same run: settings, measurements and software versions |
| `coral_cylinder_seed42_preview.png` | the same run: two cross-sections and a 3D view |
| `baseplate_90x90x3_4studs_params.json` | `python base_plate_studs.py` |
| `baseplate_90x90x3_4studs_preview.png` | the same run |

The base plate STL is not included because it is about 10 MB and takes under a minute to regenerate.

## Checking your run

**Automatically:** run the full reproduction test, which compares your result with `coral_cylinder_seed42_params.json`:

```bash
RUN_SLOW=1 pytest tests/test_reproduce_example.py
```

On Windows (Anaconda Prompt), run the two commands separately:

```bat
set RUN_SLOW=1
pytest tests/test_reproduce_example.py
```

**By hand:** compare the `results` section of your JSON with the one here. With the same library versions (listed under `software` in the JSON) the numbers should match exactly. On a different operating system or library version, the mesh can differ very slightly, so expect the measurements to agree to within a few percent rather than exactly.

**Exact file match:** on the same platform and library versions, the STL is byte-for-byte identical. Its SHA-256 checksum is:

```
bda98e37d19c4239377c83fbdfcc8d3e14ec67ccf4e6cd6efe02fa826ffd4f0b
```

Check yours with `shasum -a 256 coral_cylinder_seed42.stl` (macOS), `sha256sum coral_cylinder_seed42.stl` (Linux) or `certutil -hashfile coral_cylinder_seed42.stl SHA256` (Windows).
