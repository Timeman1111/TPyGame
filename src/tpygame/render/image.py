"""
This module provides functionality for loading and displaying images using
numpy arrays and efficient rendering techniques.

The module includes methods to load images and a class to represent an image
surface for rendering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import cv2

from .parallel import _worker_convert_chunk

if TYPE_CHECKING:
    from .parallel import ParallelConfig


def load_img(img_path: str):
    """Load an image from disk and return it as an RGB numpy array."""
    img_arr = cv2.imread(img_path)  # pylint: disable=no-member
    img_rgb_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
    return img_rgb_arr


def _build_pixels(scaled_array: np.ndarray, parallel: ParallelConfig | None) -> list:
    """Convert a scaled H×W×3 numpy array to a flat list of ``(R, G, B)`` tuples.

    When *parallel* is ``None`` or ``parallel.enabled`` is ``False``, the
    existing single-threaded list-comprehension is used.  When parallel is
    enabled the array is split into row-chunks and each chunk is converted
    inside a worker process, then the results are concatenated.

    Graceful degradation: if the process pool raises for any reason the
    function falls back to the sequential path automatically.

    :param scaled_array: Image array already resized to target dimensions.
    :param parallel: Optional :class:`~tpygame.render.parallel.ParallelConfig`.
    :return: Flat list of ``(R, G, B)`` integer tuples.
    """
    flat = scaled_array.reshape(-1, 3)

    if parallel is None or not parallel.enabled:
        return [tuple(x) for x in flat]

    num_chunks = min(parallel.num_processes, scaled_array.shape[0])
    chunk_size = scaled_array.shape[0] // num_chunks

    chunks_bytes = []
    chunks_sizes = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = scaled_array.shape[0] if i == num_chunks - 1 else start + chunk_size
        chunk = scaled_array[start:end].reshape(-1, 3)
        chunks_bytes.append(chunk.tobytes())
        chunks_sizes.append(chunk.shape[0])

    try:
        pool = parallel.get_process_pool()
        results = list(pool.map(_worker_convert_chunk, chunks_bytes, chunks_sizes))
        out = []
        for part in results:
            out.extend(part)
        return out
    except Exception:  # pylint: disable=broad-except
        return [tuple(x) for x in flat]


class ImageSurface:
    """
    A surface that can display an image from a numpy array.
    """

    @staticmethod
    def _scale_image_array(
        image_array: np.ndarray, target_height: int, target_width: int
    ) -> np.ndarray:
        """
        Scales an image array to target dimensions using nearest-neighbor interpolation.

        :param image_array: Input image array (H, W, 3).
        :param target_height: Target height in pixels.
        :param target_width: Target width in pixels.
        :return: Scaled image array (target_height, target_width, 3).
        """
        h, w = image_array.shape[:2]
        if h == target_height and w == target_width:
            return image_array

        # Generate indices for nearest-neighbor interpolation
        y_indices = (np.arange(target_height) * (h / target_height)).astype(int)
        x_indices = (np.arange(target_width) * (w / target_width)).astype(int)
        # Clip indices to ensure they are within bounds
        y_indices = np.clip(y_indices, 0, h - 1)
        x_indices = np.clip(x_indices, 0, w - 1)
        return image_array[y_indices[:, None], x_indices]

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        image_array: np.ndarray,
        parallel: ParallelConfig | None = None,
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
        scaled_array = self._scale_image_array(image_array, height, width)

        self._parallel = parallel

        # Pre-convert to a flat list of tuples for maximum drawing efficiency.
        # When a ParallelConfig is provided and enabled, the conversion is spread
        # across worker processes to reduce latency for large images.
        self.pixels = _build_pixels(scaled_array, parallel)

    def _draw_sparse(self, t_screen: 'Screen'):
        """
        Draws the image onto a sparse (dictionary-based) screen frame.
        Fallback path for non-flat frame storage.

        :param t_screen: The Screen object to draw on.
        """
        for i in range(self.height):
            sy = self.y + i
            if 0 <= sy < t_screen.height * 2:
                for j in range(self.width):
                    sx = self.x + j
                    if 0 <= sx < t_screen.width:
                        t_screen[(sx, sy)] = self.pixels[i * self.width + j]

    def _draw_flat(self, t_screen: 'Screen'):
        """
        Draws the image onto a flat (list-based) screen frame.
        Optimized path using direct list slicing for contiguous memory access.

        :param t_screen: The Screen object to draw on.
        """
        sw = t_screen.f1.width
        sh = t_screen.f1.height
        target_pixels = t_screen.f1.pixels

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

    def draw(self, t_screen: 'Screen'):
        """
        Draws the image on the provided screen as efficiently as possible.
        Dispatches to either sparse or flat implementation based on frame type.

        :param t_screen: The Screen object to draw on.
        """
        f1 = t_screen.f1
        if not f1.is_flat:
            self._draw_sparse(t_screen)
        else:
            self._draw_flat(t_screen)

    def update(self, image_array: np.ndarray):
        """
        Updates the pixel buffer in-place from a new image array.
        Automatically scales to match stored dimensions.

        :param image_array: A numpy array representing the image (H, W, 3).
        """
        scaled_array = self._scale_image_array(image_array, self.height, self.width)

        # Optimization: use _build_pixels so parallelism is used when available.
        # build_pixel in term_utils is cached and requires hashable tuples.
        self.pixels[:] = _build_pixels(scaled_array, self._parallel)

    def move(self, x_pos: int, y_pos: int):
        """Shift the surface's position by (x_pos, y_pos)."""
        self.x += x_pos
        self.y += y_pos
