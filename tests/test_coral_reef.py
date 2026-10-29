"""Fast checks for coral_reef.py.

These run the full pipeline on a small simulation grid so they finish in
about a minute. They check that every exported model is printable and that
the same settings always give the same model.
"""
import hashlib
import json

import numpy as np
import pytest
import trimesh

import coral_reef as cr


@pytest.fixture
def small_run(monkeypatch, tmp_path):
    """Run coral_reef.main() on a small grid inside a temporary folder."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cr, "GRID", 32)
    monkeypatch.setattr(cr, "STEPS", 400)
    cr.main()
    return tmp_path


def test_outputs_are_written(small_run):
    for name in (cr.OUT_STL, cr.OUT_JSON, cr.OUT_PNG):
        assert (small_run / name).is_file(), f"{name} was not written"


def test_model_is_printable(small_run):
    mesh = trimesh.load(small_run / cr.OUT_STL)
    assert mesh.is_watertight, "the model must be a closed surface"
    assert len(mesh.split(only_watertight=False)) == 1, "the model must be one piece"


def test_model_has_the_requested_size(small_run):
    mesh = trimesh.load(small_run / cr.OUT_STL)
    (x0, y0, z0), (x1, y1, z1) = mesh.bounds
    voxel = cr.DIAMETER_MM / cr.VOXELS_ACROSS / cr.UPSAMPLE
    assert abs((x1 - x0) - cr.DIAMETER_MM) < 2 * voxel
    assert abs((y1 - y0) - cr.DIAMETER_MM) < 2 * voxel
    assert abs((z1 - z0) - cr.HEIGHT_MM) < 2 * voxel


def test_record_contains_every_setting(small_run):
    record = json.loads((small_run / cr.OUT_JSON).read_text())
    params = record["parameters"]
    for key in ("diameter_mm", "height_mm", "base_mm", "seed", "F", "K", "DU", "DV",
                "voxels_across", "target_solid_fraction", "skin_mm", "skin_strength",
                "min_strut_mm", "min_channel_mm", "max_overhang_deg", "target_triangles"):
        assert key in params, f"{key} missing from the JSON record"
    assert record["software"]["numpy"], "library versions must be recorded"
    assert record["results"]["mesh_watertight"] is True
    assert record["results"]["trapped_voids_filled"] >= 0


def test_same_seed_gives_the_same_pattern():
    a = cr.simulate(24, 300, cr.F, cr.K, cr.DU, cr.DV, seed=7)
    b = cr.simulate(24, 300, cr.F, cr.K, cr.DU, cr.DV, seed=7)
    assert np.array_equal(a, b)


def test_different_seeds_give_different_patterns():
    a = cr.simulate(24, 300, cr.F, cr.K, cr.DU, cr.DV, seed=7)
    b = cr.simulate(24, 300, cr.F, cr.K, cr.DU, cr.DV, seed=8)
    assert not np.array_equal(a, b)


def test_same_settings_give_the_same_file(monkeypatch, tmp_path):
    hashes = []
    for run in ("a", "b"):
        folder = tmp_path / run
        folder.mkdir()
        monkeypatch.chdir(folder)
        monkeypatch.setattr(cr, "GRID", 24)
        monkeypatch.setattr(cr, "STEPS", 300)
        cr.main()
        hashes.append(hashlib.sha256((folder / cr.OUT_STL).read_bytes()).hexdigest())
    assert hashes[0] == hashes[1]
