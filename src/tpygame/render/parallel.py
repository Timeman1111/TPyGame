"""Parallel processing configuration and worker functions for TPyGame rendering.

Provides :class:`ParallelConfig`, a dataclass that lazily manages a
:class:`~concurrent.futures.ProcessPoolExecutor` (for CPU-bound pixel
conversion and frame comparison) and a
:class:`~concurrent.futures.ThreadPoolExecutor` (for building ANSI escape
strings during full-screen refreshes).

All worker functions are defined at module level so they are picklable and
can be dispatched to the process pool.

Usage example::

    from tpygame.render.parallel import ParallelConfig
    from tpygame.render.screen import Screen

    cfg = ParallelConfig(enabled=True, num_processes=4)
    screen = Screen(parallel=cfg)
    # ... render loop ...
    cfg.shutdown()
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np


# ---------------------------------------------------------------------------
# Module-level picklable worker functions
# ---------------------------------------------------------------------------


def _worker_convert_chunk(flat_bytes: bytes, n_pixels: int) -> list:
    """Convert a raw RGB byte buffer into a list of ``(R, G, B)`` tuples.

    Intended to run inside a :class:`~concurrent.futures.ProcessPoolExecutor`
    worker.  Byte buffers are used instead of numpy arrays to minimise pickle
    overhead over the process boundary.

    :param flat_bytes: Raw bytes of shape ``(n_pixels, 3)`` in C order.
    :param n_pixels: Number of pixels encoded in *flat_bytes*.
    :return: List of ``(R, G, B)`` integer tuples.
    """
    arr = np.frombuffer(flat_bytes, dtype=np.uint8).reshape(n_pixels, 3)
    return [tuple(int(v) for v in row) for row in arr]


def _worker_compare_chunk(
    self_bytes: bytes,
    other_bytes: bytes,
    width: int,
    vy_range: tuple[int, int],
    bitrate: int,
) -> tuple[dict, bool]:
    """Compare a horizontal strip of two frames and return changed terminal cells.

    Each terminal cell ``(x, vy)`` covers two consecutive pixel rows.
    *vy_range* contains (start_vy, end_vy) in terminal-cell coordinates.

    :param self_bytes: Raw pixel bytes for the current frame strip.
    :param other_bytes: Raw pixel bytes for the previous frame strip.
    :param width: Frame width in pixels.
    :param vy_range: Tuple of (start_vy, end_vy).
    :param bitrate: Maximum changed cells before early exit (0 = unlimited).
    :return: ``(changes, truncated)`` where *changes* maps ``(x, vy)`` to
        ``(top_colour, bottom_colour)`` tuples and *truncated* is ``True``
        when the bitrate limit was reached inside this chunk.
    """
    self_arr = np.frombuffer(self_bytes, dtype=np.uint8).reshape(
        (vy_range[1] - vy_range[0]) * 2, width, 3
    )
    other_arr = np.frombuffer(other_bytes, dtype=np.uint8).reshape(
        (vy_range[1] - vy_range[0]) * 2, width, 3
    )

    changes: dict = {}
    count = 0
    for vy_local in range(vy_range[1] - vy_range[0]):
        vy = vy_range[0] + vy_local
        row0 = vy_local * 2
        row1 = row0 + 1
        for x in range(width):
            if not (np.array_equal(self_arr[row0, x], other_arr[row0, x]) and
                    np.array_equal(self_arr[row1, x], other_arr[row1, x])):
                changes[(x, vy)] = (tuple(int(v) for v in self_arr[row0, x]),
                                    tuple(int(v) for v in self_arr[row1, x]))
                count += 1
                if 0 < bitrate <= count:
                    return changes, True
    return changes, False


def _worker_build_rows(
    pixels: list,
    width: int,
    start_vy: int,
    end_vy: int,
) -> str:
    """Build ANSI escape strings for a band of terminal rows.

    Intended to run inside a :class:`~concurrent.futures.ThreadPoolExecutor`
    worker.  Because threads share the same process memory, *pixels* is the
    actual flat pixel list — no serialisation is needed.

    :param pixels: Flat list of ``(R, G, B)`` tuples for the whole frame.
    :param width: Frame width in terminal columns.
    :param start_vy: First terminal row (inclusive).
    :param end_vy: Last terminal row (exclusive).
    :return: Concatenated ANSI string for the given row band.
    """
    # Lazy import so this symbol can live in parallel.py without creating an
    # import cycle when the module is loaded in a worker process.
    from tpygame.render.term_utils import (  # pylint: disable=import-outside-toplevel
        build_pixel,
        generate_move_string,
    )

    parts = []
    for vy in range(start_vy, end_vy):
        top_base = vy * 2 * width
        bottom_base = top_base + width
        parts.append(generate_move_string(0, vy))
        for x in range(width):
            parts.append(build_pixel(pixels[top_base + x], pixels[bottom_base + x]))
        parts.append("\n")
    return "".join(parts)


# ---------------------------------------------------------------------------
# ParallelConfig
# ---------------------------------------------------------------------------


@dataclass
class ParallelConfig:
    """Configuration for optional parallel rendering in TPyGame.

    Pass a ``ParallelConfig(enabled=True)`` instance to :class:`~tpygame.render.screen.Screen`,
    :class:`~tpygame.render.image.ImageSurface`, or
    :meth:`~tpygame.render.frame.Frame.compare` to enable multiprocessing and
    threading.  All defaults (``enabled=False``) reproduce the existing
    single-threaded behaviour exactly.

    The executor pools are created lazily on first use and must be released
    by calling :meth:`shutdown` when rendering is complete.

    Example::

        cfg = ParallelConfig(enabled=True, num_processes=4)
        try:
            screen = Screen(parallel=cfg)
            surface = ImageSurface(0, 0, 640, 480, img, parallel=cfg)
            while True:
                surface.update(new_img)
                surface.draw(screen)
                screen.refresh()
        finally:
            cfg.shutdown()

    Attributes:
        enabled: Master switch.  When ``False`` pools are never created and
            all code paths fall back to sequential execution.
        num_processes: Maximum worker processes for CPU-bound tasks (pixel
            conversion, frame comparison).  Defaults to :func:`os.cpu_count`.
        num_threads: Worker threads for I/O-adjacent tasks (ANSI string
            building in full-refresh).  Defaults to ``2``.
    """

    enabled: bool = False
    num_processes: int = field(default_factory=lambda: os.cpu_count() or 1)
    num_threads: int = 2

    _process_pool: ProcessPoolExecutor | None = field(
        default=None, init=False, repr=False
    )
    _thread_pool: ThreadPoolExecutor | None = field(
        default=None, init=False, repr=False
    )

    def get_process_pool(self) -> ProcessPoolExecutor:
        """Return the shared :class:`~concurrent.futures.ProcessPoolExecutor`.

        The pool is created on first call.
        """
        if self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(max_workers=self.num_processes)
        return self._process_pool

    def get_thread_pool(self) -> ThreadPoolExecutor:
        """Return the shared :class:`~concurrent.futures.ThreadPoolExecutor`.

        The pool is created on first call.
        """
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.num_threads)
        return self._thread_pool

    def shutdown(self, wait: bool = True) -> None:
        """Shut down both executor pools and release their resources.

        Call this when rendering is complete to free worker processes and
        threads.

        :param wait: If ``True`` (default) block until all pending futures
            finish before returning.
        """
        if self._process_pool is not None:
            self._process_pool.shutdown(wait=wait)
            self._process_pool = None
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=wait)
            self._thread_pool = None
