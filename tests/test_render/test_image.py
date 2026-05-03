import sys
import os
import numpy as np
import pytest

# ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import types

# Some environments running tests may not have opencv installed. The module
# `tpygame.render.image` imports `cv2` at import-time; inject a lightweight
# fake module into sys.modules so tests can import the image module without
# requiring the real OpenCV wheel.
fake_cv2 = types.ModuleType("cv2")
def _fake_imread(path):
    # return a tiny placeholder RGB-like array when called
    return np.zeros((1, 1, 3), dtype=np.uint8)
def _fake_cvtColor(arr, flag):
    return arr
fake_cv2.imread = _fake_imread
fake_cv2.cvtColor = _fake_cvtColor
fake_cv2.COLOR_BGR2RGB = 0
sys.modules.setdefault('cv2', fake_cv2)

from tpygame.render.image import _build_pixels, ImageSurface
from tpygame.render.frame import Frame
from tpygame.render.screen import Screen


def test__build_pixels_flattening():
    arr = np.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]], dtype=np.uint8)
    out = _build_pixels(arr, None)
    # flattened order should match row-major
    expected = [ (1,2,3), (4,5,6), (7,8,9), (10,11,12) ]
    assert out == expected


def test_imagesurface_scaling_and_draw_and_update(monkeypatch):
    # simple 2x2 input image with distinct colors
    img = np.zeros((2, 2, 3), dtype=np.uint8)
    img[0, 0] = [10, 0, 0]
    img[0, 1] = [0, 20, 0]
    img[1, 0] = [0, 0, 30]
    img[1, 1] = [40, 40, 40]

    # create a surface that scales the 2x2 -> 4x4 using nearest-neighbor logic
    surf = ImageSurface(0, 0, 4, 4, img, parallel=None)
    # pixels should be length 16
    assert len(surf.pixels) == 16
    # top-left quadrant should map to img[0,0]
    assert surf.pixels[0] == (10, 0, 0)
    assert surf.pixels[1] == (10, 0, 0)
    # a pixel in the bottom-right quadrant should be img[1,1]
    assert surf.pixels[-1] == (40, 40, 40)

    # draw onto a Screen and verify Frame pixels updated
    # patch terminal initialization and size to run headless in pytest
    import tpygame.render.screen as screen_mod
    monkeypatch.setattr(screen_mod, 'init_terminal', lambda: None)
    monkeypatch.setattr(__import__('os'), 'get_terminal_size', lambda: (80, 24))
    screen = Screen()
    # ensure target frame is flat
    assert screen.f1.is_flat
    surf.draw(screen)
    # screen top-left should now be the same as image top-left
    assert screen[(0, 0)] == (10, 0, 0)

    # update surface with a new image and ensure pixels change
    new_img = np.full((2, 2, 3), 77, dtype=np.uint8)
    old_first = surf.pixels[0]
    surf.update(new_img)
    assert surf.pixels[0] == (77, 77, 77)
    assert surf.pixels[0] != old_first



