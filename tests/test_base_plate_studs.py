"""Fast checks for base_plate_studs.py."""
import json

import pytest
import trimesh

import base_plate_studs as bp


@pytest.fixture
def plate_run(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bp, "EXPORT_3MF", False)
    monkeypatch.setattr(bp, "THREAD_STEPS_PER_TURN", 12)   # coarser thread, faster test
    bp.main()
    return tmp_path


def test_plate_is_one_printable_piece(plate_run):
    mesh = trimesh.load(plate_run / bp.OUT_STL)
    assert mesh.is_watertight
    assert len(mesh.split(only_watertight=False)) == 1


def test_plate_has_one_stud_per_position(plate_run):
    record = json.loads((plate_run / bp.OUT_JSON).read_text())
    assert len(record["results"]["stud_centres_mm"]) == bp.STUD_COLUMNS * bp.STUD_ROWS


def test_stud_is_smaller_than_the_hole():
    major = bp.HOLE_MAJOR_DIA_MM - 2 * bp.FIT_CLEARANCE_MM
    minor = bp.HOLE_MINOR_DIA_MM - 2 * bp.FIT_CLEARANCE_MM
    assert major < bp.HOLE_MAJOR_DIA_MM and minor < bp.HOLE_MINOR_DIA_MM


def test_scripts_share_the_same_thread():
    import coral_reef as cr
    assert bp.THREAD_PITCH_MM == cr.THREAD_PITCH_MM
    assert bp.HOLE_MINOR_DIA_MM == cr.THREAD_MINOR_DIA_MM
    assert bp.HOLE_MAJOR_DIA_MM == cr.THREAD_MAJOR_DIA_MM


def test_plate_fits_the_coral_footprint():
    import coral_reef as cr
    assert bp.MODEL_FOOTPRINT_MM >= cr.DIAMETER_MM, \
        "MODEL_FOOTPRINT_MM must be at least the coral's DIAMETER_MM, or models will overlap"
