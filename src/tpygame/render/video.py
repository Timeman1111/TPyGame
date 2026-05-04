"""
Manages a video frame source and renders it using a reusable ImageSurface.

This module provides the `Video` class, which keeps a single `ImageSurface` whose
pixel buffer is updated in-place on every `input()` call.  This eliminates the
per-frame allocation of a new surface and pixel list that would otherwise create
GC pressure at video framerates.
"""

import os
import cv2
import numpy as np
from .image import ImageSurface


class Video:  # pylint: disable=too-many-instance-attributes
    """
    Renders video frames onto a Screen using a single reusable ImageSurface.
    Can also manage its own cv2.VideoCapture source.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
        source: str | int | None = None,
        bitrate: int = 0,
        auto_resize: bool = False
    ):
        """
        Initializes the Video object.
        :param x: X-coordinate on screen.
        :param y: Y-coordinate on screen.
        :param width: Target width (if None and source exists, uses source width).
        :param height: Target height (if None and source exists, uses source height).
        :param source: Path to video file or camera index.
        :param bitrate: Maximum pixels to update per frame in partial refresh.
        :param auto_resize: If True, automatically resizes to terminal dimensions on every frame.
        """
        self.pos = [x, y]
        self.size = [width, height]
        self.config = {'bitrate': bitrate, 'auto_resize': auto_resize}
        self._surface: ImageSurface | None = None
        self.cursor = 0
        self.cap = None
        self.fps = 30  # Default fallback

        if source is not None:
            self.cap = cv2.VideoCapture(source)  # pylint: disable=no-member
            if self.cap.isOpened():
                if self.size[0] is None:
                    self.size[0] = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # pylint: disable=no-member
                if self.size[1] is None:
                    self.size[1] = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # pylint: disable=no-member

                source_fps = self.cap.get(cv2.CAP_PROP_FPS)  # pylint: disable=no-member
                if source_fps > 0:
                    self.fps = source_fps

    @property
    def x(self):
        """X-coordinate."""
        return self.pos[0]

    @x.setter
    def x(self, value):
        self.pos[0] = value

    @property
    def y(self):
        """Y-coordinate."""
        return self.pos[1]

    @y.setter
    def y(self, value):
        self.pos[1] = value

    @property
    def width(self):
        """Width."""
        return self.size[0]

    @width.setter
    def width(self, value):
        self.size[0] = value

    @property
    def height(self):
        """Height."""
        return self.size[1]

    @height.setter
    def height(self, value):
        self.size[1] = value

    @property
    def bitrate(self):
        """Bitrate."""
        return self.config['bitrate']

    @bitrate.setter
    def bitrate(self, value):
        self.config['bitrate'] = value

    @property
    def auto_resize(self):
        """Auto resize flag."""
        return self.config['auto_resize']

    @auto_resize.setter
    def auto_resize(self, value):
        self.config['auto_resize'] = value

    def next_frame(self) -> bool:
        """
        Reads the next frame from the source, if it exists.
        :return: True if a frame was read, False otherwise.
        """
        if self.auto_resize:
            tw, th = os.get_terminal_size()
            self.width = tw
            self.height = th * 2

        if self.cap is None or not self.cap.isOpened():
            return False
        ret, frame = self.cap.read()
        if not ret:
            return False

        # Pre-process: BGR to RGB and resize for better performance
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
        if self.width and self.height:
            frame = cv2.resize(frame, (self.width, self.height))  # pylint: disable=no-member

        self.input(frame)
        return True

    def input(self, img: np.ndarray):
        """
        Loads a new frame into the reusable surface buffer.
        :param img: A numpy array representing the image frame.
        """
        if self._surface is None:
            # If width/height weren't set, use image shape
            if self.width is None:
                self.width = img.shape[1]
            if self.height is None:
                self.height = img.shape[0]
            self._surface = ImageSurface(self.x, self.y, self.width, self.height, img)
        else:
            # Ensure surface dimensions match Video object's current dimensions
            if self.width is not None and self.height is not None:
                self._surface.width = self.width
                self._surface.height = self.height
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

    def refresh(self, t_screen: 'Screen', force_full: bool = False):
        """
        Helper to refresh the screen with this video's bitrate settings.
        """
        t_screen.refresh(
            force_full=force_full,
            bitrate=self.bitrate
        )

    def reset(self):
        """
        Resets the frame cursor and video capture.
        """
        self.cursor = 0
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # pylint: disable=no-member

    def move(self, x: int, y: int):
        """
        Updates the position of the object by a specified offset.
        """
        self.x += x
        self.y += y

    def __del__(self):
        if self.cap:
            self.cap.release()
