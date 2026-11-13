"""Fast checks for base_plate_studs.py."""
import json

import pytest
import trimesh

import base_plate_studs as bp


@pytest.fixture
def plate_run(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(bp, "EXPORT_3MF", False)
    bp.main()
    return tmp_path


def test_plate_is_one_printable_piece(plate_run):
    mesh = trimesh.load(plate_run / bp.OUT_STL)
    assert mesh.is_watertight
    assert len(mesh.split(only_watertight=False)) == 1


def test_plate_has_one_stud_per_position(plate_run):
    record = json.loads((plate_run / bp.OUT_JSON).read_text())
    assert len(record["results"]["stud_centres_mm"]) == bp.STUD_COLUMNS * bp.STUD_ROWS


JOINT_KEYS = ("JOINT_TYPE", "STUD_DIA_MM", "STUD_HEIGHT_MM", "LUG_SPAN_MM", "LUG_WIDTH_MM",
              "LUG_HEIGHT_MM", "LUG_TOP_BELOW_TIP_MM", "JOINT_CLEARANCE_MM")


def test_scripts_share_the_same_joint():
    import coral_reef as cr
    for key in JOINT_KEYS:
        assert getattr(bp, key) == getattr(cr, key), f"{key} differs between the scripts"


def test_socket_leaves_a_locking_shelf():
    import coral_reef as cr
    shelf = cr.STUD_HEIGHT_MM - cr.LUG_TOP_BELOW_TIP_MM - cr.LUG_HEIGHT_MM - cr.JOINT_CLEARANCE_MM
    assert shelf >= 2.0, "the shelf that holds the lugs down must be at least 2 mm thick"
    assert cr.SOCKET_DEPTH_MM > cr.STUD_HEIGHT_MM, "the stud must not bottom out in the socket"
    assert 0 < cr.LOCK_PLAY_MM < cr.JOINT_CLEARANCE_MM, "the ramp must reduce the play, not remove it"


def test_base_fillet_fits_the_socket_mouth():
    import coral_reef as cr
    assert bp.STUD_BASE_FILLET_MM < cr.JOINT_CHAMFER_MM + cr.JOINT_CLEARANCE_MM, \
        "the stud's base fillet would stop the coral sitting flat on the plate"


def test_plate_fits_the_coral_footprint():
    import coral_reef as cr
    assert bp.MODEL_FOOTPRINT_MM >= cr.DIAMETER_MM, \
        "MODEL_FOOTPRINT_MM must be at least the coral's DIAMETER_MM, or models will overlap"
