import sys
import os
import pytest

# make sure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tpygame.render.frame import Frame


def test_flat_set_get_contains_len_and_iter():
    f = Frame(4, 4)
    assert f.is_flat
    # initially all black
    assert len(f) == 16
    assert (1, 1) not in f or f[(1, 1)] == (0, 0, 0)

    f[(1, 1)] = (10, 20, 30)
    assert (1, 1) in f
    assert f[(1, 1)] == (10, 20, 30)
    # iter yields non-black coordinates
    coords = list(f)
    assert (1, 1) in coords

    # reset should clear back to black
    f.reset()
    assert f[(1, 1)] == (0, 0, 0)


def test_sparse_mode_behavior():
    f = Frame()  # sparse
    assert not f.is_flat
    f[(2, 3)] = (1, 2, 3)
    assert (2, 3) in f
    assert f.get((2, 3)) == (1, 2, 3)
    assert f.get((9, 9), default=(5, 5, 5)) == (5, 5, 5)
    assert len(f) == 1
    f.reset()
    assert len(f) == 0


def test_compare_detects_changes_and_bitrate_truncation():
    # create two flat frames
    a = Frame(4, 4)
    b = Frame(4, 4)

    # no changes
    changes, truncated = a.compare(b)
    assert changes == {}
    assert truncated is False

    # set a single pixel in the top-left cell (cell vy=0)
    a[(0, 0)] = (1, 1, 1)
    changes, truncated = a.compare(b)
    # change should be reported for the cell (x=0, vy=0)
    assert (0, 0) in changes
    assert changes[(0, 0)][0] == (1, 1, 1)
    assert truncated is False

    # make many changes and enforce bitrate truncation
    a.reset(); b.reset()
    for x in range(4):
        for y in range(0, 4):
            if (x + y) % 2 == 0:
                a[(x, y)] = (x + 1, y + 2, 3)

    # With bitrate=1 we should return at most 1 change and truncated=True
    changes, truncated = a.compare(b, bitrate=1)
    assert isinstance(changes, dict)
    assert len(changes) <= 1
    assert truncated is True

