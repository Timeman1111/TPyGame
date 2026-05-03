"""
This module provides functionality for loading and displaying images using
numpy arrays and efficient rendering techniques.

The module includes methods to load images and a class to represent an image
surface for rendering.
"""

import numpy as np
import cv2


def load_img(img_path: str):
    """Load an image from disk and return it as an RGB numpy array."""
    img_arr = cv2.imread(img_path)  # pylint: disable=no-member
    img_rgb_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
    return img_rgb_arr


class ImageSurface:
    """
    A surface that can display an image from a numpy array.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        image_array: np.ndarray,
    ):
        """
        Initializes an ImageSurface.
        :param x: Initial X-coordinate.
        :param y: Initial Y-coordinate.
        :param width: Target width of the image.
        :param height: Target height of the image.
        :param image_array: A numpy array representing the image (H, W, 3).
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Efficiently resize the image to the target dimensions using nearest neighbor interpolation
        h, w = image_array.shape[:2]
        if h != height or w != width:
            # Generate indices for interpolation
            y_indices = (np.arange(height) * (h / height)).astype(int)
            x_indices = (np.arange(width) * (w / width)).astype(int)
            # Clip indices to ensure they are within bounds
            y_indices = np.clip(y_indices, 0, h - 1)
            x_indices = np.clip(x_indices, 0, w - 1)
            scaled_array = image_array[y_indices[:, None], x_indices]
        else:
            scaled_array = image_array

        # Pre-convert to a flat list of tuples for maximum drawing efficiency
        # This allows using list slicing during the draw call
        self.pixels = [
            tuple(scaled_array[py, px])
            for py in range(height)
            for px in range(width)
        ]

    def draw(self, t_screen: 'Screen'):  # pylint: disable=too-many-locals
        """
        Draws the image on the provided screen as efficiently as possible.
        :param t_screen: The Screen object to draw on.
        """
        f1 = t_screen.f1
        if not f1.is_flat:
            # Fallback for sparse frames
            for i in range(self.height):
                sy = self.y + i
                if 0 <= sy < t_screen.height * 2:
                    for j in range(self.width):
                        sx = self.x + j
                        if 0 <= sx < t_screen.width:
                            t_screen[(sx, sy)] = self.pixels[i * self.width + j]
            return

        # Direct access to the flat pixel list for speed
        sw = f1.width
        sh = f1.height
        target_pixels = f1.pixels

        # Calculate overlap bounds
        start_y = max(0, self.y)
        end_y = min(sh, self.y + self.height)
        start_x = max(0, self.x)
        end_x = min(sw, self.x + self.width)

        if start_y >= end_y or start_x >= end_x:
            return

        # Copy rows using list slicing
        copy_width = end_x - start_x
        img_x_offset = start_x - self.x

        for i in range(start_y, end_y):
            target_offset = i * sw + start_x
            img_y = i - self.y
            img_offset = img_y * self.width + img_x_offset

            target_pixels[target_offset: target_offset + copy_width] = (
                self.pixels[img_offset: img_offset + copy_width]
            )

    def update(self, image_array: np.ndarray):
        """
        Updates the pixel buffer in-place from a new image array.
        Reuses the existing list to avoid allocating a new ImageSurface per frame.
        :param image_array: A numpy array representing the image (H, W, 3).
        """
        h, w = image_array.shape[:2]
        if h != self.height or w != self.width:
            y_indices = (np.arange(self.height) * (h / self.height)).astype(int)
            x_indices = (np.arange(self.width) * (w / self.width)).astype(int)
            y_indices = np.clip(y_indices, 0, h - 1)
            x_indices = np.clip(x_indices, 0, w - 1)
            scaled_array = image_array[y_indices[:, None], x_indices]
        else:
            scaled_array = image_array
        self.pixels[:] = [
            tuple(scaled_array[py, px])
            for py in range(self.height)
            for px in range(self.width)
        ]

    def move(self, x_pos: int, y_pos: int):
        """Shift the surface's position by (x_pos, y_pos)."""
        self.x += x_pos
        self.y += y_pos
