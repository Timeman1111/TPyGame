"""
Manages a video frame source and renders it using a reusable ImageSurface.

This module provides the `Video` class, which keeps a single `ImageSurface` whose
pixel buffer is updated in-place on every `input()` call.  This eliminates the
per-frame allocation of a new surface and pixel list that would otherwise create
GC pressure at video framerates.
"""

import numpy as np
from .image import ImageSurface


class Video:
    """
    Renders video frames onto a Screen using a single reusable ImageSurface.

    Frames are written into the surface's pixel buffer in-place, so no new
    list or object is allocated between frames.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initializes the Video object.
        :param x: Initial X-coordinate.
        :param y: Initial Y-coordinate.
        :param width: Target width for all frames.
        :param height: Target height for all frames.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._surface: ImageSurface | None = None
        self.cursor = 0

    def input(self, img: np.ndarray):
        """
        Loads a new frame into the reusable surface buffer.
        :param img: A numpy array representing the image frame.
        """
        if self._surface is None:
            self._surface = ImageSurface(self.x, self.y, self.width, self.height, img)
        else:
            self._surface.update(img)

    def draw(self, t_screen: 'Screen'):
        """
        Renders the current frame onto the screen and advances the cursor.
        :param t_screen: The Screen object to draw on.
        """
        if self._surface is None:
            return

        self._surface.x = self.x
        self._surface.y = self.y
        self._surface.draw(t_screen)
        self.cursor += 1

    def reset(self):
        """
        Resets the frame cursor.
        """
        self.cursor = 0

    def move(self, x: int, y: int):
        """
        Updates the position of the object by a specified offset in both the x and y axes.
        :param x: The offset by which the x-coordinate should be incremented.
        :param y: The offset by which the y-coordinate should be incremented.
        :return: None
        """
        self.x += x
        self.y += y

