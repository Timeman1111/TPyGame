"""Frame: pixel buffer for terminal rendering, supporting flat and sparse storage."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parallel import ParallelConfig


class Frame:
    """
    Represents a single frame of pixels.
    Can be stored as a flat list for efficiency if dimensions are known,
    or as a dictionary for sparse storage.
    """

    def __init__(self, width: int = 0, height: int = 0):
        """
        Initializes a Frame.
        :param width: Width of the frame in pixels.
        :param height: Height of the frame in pixels.
        """
        self.width = width
        self.height = height
        # Use a list for flat storage if dimensions are known, else fallback to dict
        if width > 0 and height > 0:
            self.pixels = [(0, 0, 0)] * (width * height)
            self._black = self.pixels[:]  # reusable zero-filled reference list for reset
            self.is_flat = True
        else:
            self.pixels: dict[tuple[int, int], tuple[int, int, int]] = {}
            self._black = None
            self.is_flat = False

    def __setitem__(self, key: tuple[int, int], value: tuple[int, int, int]):
        """
        Sets the pixel color at the given (x, y) coordinate.
        :param key: A tuple of (x, y) coordinates.
        :param value: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                self.pixels[y * self.width + x] = value
        else:
            self.pixels[key] = value

    def __getitem__(self, key: tuple[int, int]):
        """
        Gets the pixel color at the given (x, y) coordinate.
        :param key: A tuple of (x, y) coordinates.
        :return: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                return self.pixels[y * self.width + x]
            return (0, 0, 0)
        return self.pixels.get(key, (0, 0, 0))

    def __iter__(self):
        """
        Iterates over the coordinates of non-black pixels.
        :return: An iterator of (x, y) tuples.
        """
        if self.is_flat:
            for y in range(self.height):
                for x in range(self.width):
                    if self.pixels[y * self.width + x] != (0, 0, 0):
                        yield (x, y)
        else:
            yield from self.pixels

    def get(self, key: tuple[int, int], default: tuple[int, int, int] = (0, 0, 0)):
        """
        Gets the pixel color at the given (x, y) coordinate with a default value.
        :param key: A tuple of (x, y) coordinates.
        :param default: Default color to return if the pixel is not set.
        :return: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                return self.pixels[y * self.width + x]
            return default
        return self.pixels.get(key, default)

    def __contains__(self, key: tuple[int, int]):
        """
        Checks if the given (x, y) coordinate is within the frame's bounds or set.
        :param key: A tuple of (x, y) coordinates.
        :return: True if the coordinate exists, False otherwise.
        """
        if self.is_flat:
            x, y = key
            return 0 <= x < self.width and 0 <= y < self.height
        return key in self.pixels

    def __repr__(self):
        """
        Returns a string representation of the frame's pixels.
        """
        return str(self.pixels)

    def __len__(self):
        """
        Returns the number of pixels in the frame.
        """
        return len(self.pixels)

    def reset(self):
        """
        Resets all pixels to (0, 0, 0) in-place, avoiding a new allocation.
        Uses the precomputed _black reference list so no temporary list is created.
        """
        if self.is_flat:
            self.pixels[:] = self._black
        else:
            self.pixels.clear()

    def _compare_sequential(self, other: "Frame", bitrate: int, height_cells: int, width: int):
        """
        Sequential (single-threaded) frame comparison for changed cells.
        Each cell (x, vy) covers two consecutive pixel rows.

        Uses a random starting row when bitrate is set to avoid top-to-bottom
        scanline bias during partial updates.

        :param other: The previous frame to compare against.
        :param bitrate: Maximum changed cells before early exit (0 = unlimited).
        :param height_cells: Number of terminal-cell rows (height // 2).
        :param width: Frame width in pixels.
        :return: (changes, truncated) where changes is a dict and truncated is a bool.
        """
        changes = {}
        self_pixels = self.pixels
        other_pixels = other.pixels

        # Use a random starting row to avoid top-to-bottom scanline bias when bitrate is low
        start_vy = random.randint(0, height_cells - 1) if bitrate > 0 else 0

        count = 0
        for i in range(height_cells):
            vy = (start_vy + i) % height_cells
            base_idx = vy * 2 * width
            idx2_offset = width
            for x in range(width):
                idx1 = base_idx + x
                idx2 = idx1 + idx2_offset

                p1_1, p1_2 = self_pixels[idx1], self_pixels[idx2]
                p2_1, p2_2 = other_pixels[idx1], other_pixels[idx2]

                if p1_1 != p2_1 or p1_2 != p2_2:
                    changes[(x, vy)] = (p1_1, p1_2)
                    count += 1
                    if 0 < bitrate <= count:
                        return changes, True
        return changes, False

    def compare(self, other: "Frame", bitrate: int = 0, parallel: ParallelConfig | None = None):
        """
        Compares the current frame with another frame and returns a dictionary of changed cells.
        Each cell (x, vy) corresponds to two pixels.
        :param other: The previous frame to compare against.
        :param bitrate: The maximum number of changed cells to return.
        :param parallel: Optional :class:`~tpygame.render.parallel.ParallelConfig`.  When
            enabled, the comparison is distributed across worker processes.
        :return: (changes, truncated) where changes is a dict and truncated is a bool.
        """
        changes = {}
        if (
            self.is_flat
            and other.is_flat
            and self.width == other.width
            and self.height == other.height
        ):
            height_cells = self.height // 2
            width = self.width

            if (
                parallel is not None
                and parallel.enabled
                and height_cells >= parallel.num_processes
            ):
                return self._compare_parallel(other, bitrate, parallel, height_cells, width)

            # Sequential path
            return self._compare_sequential(other, bitrate, height_cells, width)

        return changes, False

    def _compare_parallel(
        self,
        other: "Frame",
        bitrate: int,
        parallel: ParallelConfig,
        height_cells: int,
        width: int,
    ):
        """Parallel implementation of :meth:`compare` using a process pool.

        Splits the frame into horizontal strips and dispatches each strip to a
        worker process via :func:`~tpygame.render.parallel._worker_compare_chunk`.
        The full pixel buffers are converted to numpy byte arrays once upfront to
        avoid redundant allocations per chunk.
        """
        import numpy as np  # pylint: disable=import-outside-toplevel
        from .parallel import _worker_compare_chunk  # pylint: disable=import-outside-toplevel

        num_proc = min(parallel.num_processes, height_cells)
        chunk_size = height_cells // num_proc
        pool = parallel.get_process_pool()

        # Convert entire buffers to numpy arrays once to avoid per-chunk allocation
        self_arr = np.array(self.pixels, dtype=np.uint8).reshape(self.height, width, 3)
        other_arr = np.array(other.pixels, dtype=np.uint8).reshape(other.height, width, 3)

        futures = []
        for i in range(num_proc):
            start_vy = i * chunk_size
            end_vy = height_cells if i == num_proc - 1 else start_vy + chunk_size
            futures.append(
                pool.submit(
                    _worker_compare_chunk,
                    self_arr[start_vy * 2 : end_vy * 2].tobytes(),
                    other_arr[start_vy * 2 : end_vy * 2].tobytes(),
                    width,
                    start_vy,
                    end_vy,
                    0,  # per-chunk bitrate disabled; enforce in main process
                )
            )

        changes: dict = {}
        for f in futures:
            chunk_changes, _ = f.result()
            changes.update(chunk_changes)
            if 0 < bitrate <= len(changes):
                # Cancel any pending futures and return early
                for pending in futures:
                    pending.cancel()
                return changes, True
        return changes, False
