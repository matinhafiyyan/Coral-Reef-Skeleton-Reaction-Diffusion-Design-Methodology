"""Checks that the coral and base plate actually fit together as a bayonet joint.

Builds a coral on a small simulation grid (the joint is the same size as in a
full run) and the default base plate, then simulates the joint with exact
solid geometry: slide down, turn to lock, try to pull off.
"""
import os
import sys

import pytest
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import base_plate_studs as bp   # noqa: E402
import coral_reef as cr          # noqa: E402
from joint_fit import fit_report  # noqa: E402


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    folder = tmp_path_factory.mktemp("joint")
    cwd = os.getcwd()
    grid, steps, export_3mf = cr.GRID, cr.STEPS, bp.EXPORT_3MF
    try:
        os.chdir(folder)
        cr.GRID, cr.STEPS, bp.EXPORT_3MF = 32, 400, False
        cr.main()
        bp.main()
        coral = trimesh.load(folder / cr.OUT_STL)
        plate = trimesh.load(folder / bp.OUT_STL)
        centres, *_ = bp.layout()
        return fit_report(coral, plate, bp.PLATE_THICKNESS_MM, centres[0], cr.TWIST_DEG)
    finally:
        cr.GRID, cr.STEPS, bp.EXPORT_3MF = grid, steps, export_3mf
        os.chdir(cwd)


def test_coral_slides_onto_the_stud(report):
    assert report["insert_clear"]


def test_coral_turns_to_lock_without_binding(report):
    assert report["turn_clear"]


def test_locked_coral_cannot_be_pulled_off(report):
    assert report["pull_out_blocked_at_0_5mm"]


def test_turn_stops_at_the_locked_position(report):
    assert report["overturn_blocked"]


def test_ramp_reduces_play_as_it_turns(report):
    plays = [p for p in report["play_mm"].values()]
    assert all(p is not None for p in plays)
    assert plays[0] > plays[-1], "play should shrink as the coral turns"
    assert plays[-1] <= cr.LOCK_PLAY_MM + 0.05


def test_coral_can_be_removed_by_turning_back(report):
    assert report["lifts_out_at_entry"]
