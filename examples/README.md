# Reference outputs

These files were made by running the scripts in this repository with their default settings. Use them to see what the scripts produce, and to check that your own run reproduces the published result.

| File                                             | Made by                                                                                      |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `coral_cylinder_seed9_bayonet.stl`               | `python coral_reef.py` (seed 9, 50 mm wide x 30 mm tall cylinder, bayonet socket)            |
| `coral_cylinder_seed9_bayonet_params.json`       | the same run: settings, measurements and software versions                                   |
| `coral_cylinder_seed9_bayonet_preview.png`       | the same run: two cross-sections and a 3D view                                               |
| `baseplate_130x130x5_4studs_bayonet.stl`         | `python base_plate_studs.py` (130 x 130 x 5 mm plate, 4 bayonet studs)                       |
| `baseplate_130x130x5_4studs_bayonet_params.json` | the same run                                                                                 |
| `baseplate_130x130x5_4studs_bayonet_preview.png` | the same run: stud layout and a 3D view                                                      |
| `bayonet_joint_views.png`                        | `tools/joint_views.py`: the socket from below, one stud, and the locked joint cut in half    |
| `bayonet_assembly.glb`                           | `tools/joint_views.py`: the plate with one coral locked on, as two objects (open in Blender) |

## Checking your run

**Automatically:** run the full reproduction test, which compares your result with `coral_cylinder_seed9_bayonet_params.json`:

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
python tools/joint_fit.py examples/coral_cylinder_seed9_bayonet.stl examples/coral_cylinder_seed9_bayonet_params.json examples/baseplate_130x130x5_4studs_bayonet.stl examples/baseplate_130x130x5_4studs_bayonet_params.json
```

**Exact file match:** on the same platform and library versions, the STL files are byte-for-byte identical. Their SHA-256 checksums are:

```
4e65dbac8db2ed60a5a4d197ba69a0f5b1c1327a9cf532729329760866fa48b3  coral_cylinder_seed9_bayonet.stl
1bbb358350ae2ad37534bf60f401d20217c4421cdab3a524cf7704698ae1bce4  baseplate_130x130x5_4studs_bayonet.stl
```

Check yours with `shasum -a 256 <file>` (macOS), `sha256sum <file>` (Linux) or `certutil -hashfile <file> SHA256` (Windows).
