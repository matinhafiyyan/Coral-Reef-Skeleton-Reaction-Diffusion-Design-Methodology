"""Full reproduction of the published example (slow, about 2-5 minutes).

Runs coral_reef.py with its default settings and compares the result with
examples/coral_cylinder_seed42_params.json. Skipped unless RUN_SLOW=1:

    RUN_SLOW=1 pytest tests/test_reproduce_example.py
"""
import json
import os
from pathlib import Path

import pytest

import coral_reef as cr

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "coral_cylinder_seed42_params.json"


@pytest.mark.skipif(os.environ.get("RUN_SLOW") != "1", reason="slow; set RUN_SLOW=1 to run")
def test_default_run_matches_published_example(monkeypatch, tmp_path):
    expected = json.loads(EXAMPLE.read_text())
    monkeypatch.chdir(tmp_path)
    cr.main()
    got = json.loads((tmp_path / cr.OUT_JSON).read_text())

    assert got["parameters"] == expected["parameters"], \
        "settings differ from the example; reset coral_reef.py to its published defaults"

    # Same platform and library versions give identical numbers. Other systems
    # may differ very slightly in the mesh, so allow a small tolerance.
    r, e = got["results"], expected["results"]
    assert r["mesh_watertight"] is True
    for key in ("actual_solid_fraction", "porosity"):
        assert r[key] == pytest.approx(e[key], abs=0.01), key
    for key in ("mesh_volume_mm3", "mesh_surface_area_mm2"):
        assert r[key] == pytest.approx(e[key], rel=0.02), key
    for stat in ("p10", "median", "p90"):
        assert r["strut_thickness_mm"][stat] == pytest.approx(e["strut_thickness_mm"][stat], abs=0.5)
        assert r["channel_width_mm"][stat] == pytest.approx(e["channel_width_mm"][stat], abs=0.5)
