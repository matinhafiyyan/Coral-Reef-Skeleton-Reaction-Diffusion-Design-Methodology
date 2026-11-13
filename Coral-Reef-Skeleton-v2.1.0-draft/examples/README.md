# Reference outputs

These files were made by running the scripts in this repository with their default settings. Use them to see what the scripts produce, and to check that your own run reproduces the published result.

| File                                           | Made by                                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `coral_cylinder_seed23_bayonet.stl`            | `python coral_reef.py` (seed 23, 30 x 30 mm cylinder, bayonet socket, top skin and crest band) |
| `coral_cylinder_seed23_bayonet_params.json`    | the same run: settings, measurements and software versions                                     |
| `coral_cylinder_seed23_bayonet_preview.png`    | the same run: two cross-sections and a 3D view                                                 |
| `baseplate_90x90x3_4studs_bayonet.stl`         | `python base_plate_studs.py` (90 x 90 mm plate, 4 bayonet studs)                               |
| `baseplate_90x90x3_4studs_bayonet_params.json` | the same run                                                                                   |
| `baseplate_90x90x3_4studs_bayonet_preview.png` | the same run: stud layout and a 3D view                                                        |
| `bayonet_joint_views.png`                      | `tools/joint_views.py`: the socket from below, one stud, and the locked joint cut in half      |
| `bayonet_assembly.glb`                         | `tools/joint_views.py`: the plate with one coral locked on, as two objects (open in Blender)   |

## Checking your run

**Automatically:** run the full reproduction test, which compares your result with `coral_cylinder_seed23_bayonet_params.json`:

```bash
RUN_SLOW=1 pytest tests/test_reproduce_example.py
```

On Windows (Anaconda Prompt), run the two commands separately:

```bat
set RUN_SLOW=1
pytest tests/test_reproduce_example.py
```

**By hand:** compare the `results` section of your JSON with the one here. With the same library versions (listed under `software` in the JSON) the numbers should match exactly. On a different operating system or library version, the mesh can differ very slightly, so expect the measurements to agree to within a few percent rather than exactly.

**Joint fit:** check that your coral and plate fit, turn and lock:

```bash
python tools/joint_fit.py examples/coral_cylinder_seed23_bayonet.stl examples/coral_cylinder_seed23_bayonet_params.json examples/baseplate_90x90x3_4studs_bayonet.stl examples/baseplate_90x90x3_4studs_bayonet_params.json
```

**Exact file match:** on the same platform and library versions, the STL files are byte-for-byte identical. Their SHA-256 checksums are:

```
1754e4cc213e801e458a81ab53610fe839367d53a33841eed578658c8bcdd13f  coral_cylinder_seed23_bayonet.stl
110c92e17afeb74ddd0d6f6e32ae6086cce4ebc8c7cd48a63e2ca01caca9a970  baseplate_90x90x3_4studs_bayonet.stl
```

Check yours with `shasum -a 256 <file>` (macOS), `sha256sum <file>` (Linux) or `certutil -hashfile <file> SHA256` (Windows).
