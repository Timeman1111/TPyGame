"""Render: terminal display manager with frame buffering and pixel-level rendering."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parallel import ParallelConfig


from .frame import Frame
from .term_utils import (
    init_terminal,
    hide_cursor,
    show_cursor,
    generate_move_string,
    build_pixel,
)


class Screen:
    """
    Manages the terminal display, including cursor control and frame refreshing.
    """

    def __init__(self, last_pos: tuple[int, int] = (0, 0), parallel: ParallelConfig | None = None):
        """
        Initializes the Screen.
        :param last_pos: Initial cursor position (y, x).
        :param parallel: Optional :class:`~tpygame.render.parallel.ParallelConfig` for
            parallel rendering.  Pass ``ParallelConfig(enabled=True)`` to use a thread
            pool for full-frame refreshes and a process pool for frame comparison.
        """
        init_terminal()
        self.last_pos = last_pos
        self.width, self.height = os.get_terminal_size()
        self._parallel = parallel

        self.p1: Frame = Frame(self.width, self.height * 2)
        self.f1: Frame = Frame(self.width, self.height * 2)

        # Force the first refresh to be a full redraw to avoid "spottiness"
        # when the initial terminal state is not black.
        self._first_refresh = True

        self.is_cursor_visible = True

    def hide_cursor(self):
        """
        Hides the terminal cursor.
        """
        hide_cursor()
        self.is_cursor_visible = False

    def show_cursor(self):
        """
        Shows the terminal cursor.
        """
        show_cursor()
        self.is_cursor_visible = True

    def home_cursor(self):
        """
        Moves the terminal cursor to the top-left corner (0, 0).
        """
        self.move_cursor(0, 0)

    def move_cursor(self, x: int, vy: int):
        """
        Moves the terminal cursor to the specified position.
        :param x: X-coordinate.
        :param vy: Y-coordinate.
        """
        move_str = generate_move_string(x, vy)
        self.last_pos = (vy, x)
        self.__out(move_str, end="")

    def __getitem__(self, key: tuple[int, int]):
        """
        Gets the pixel color from the current frame.
        :param key: A tuple of (x, y) coordinates.
        :return: A tuple of (R, G, B) color values.
        """
        return self.f1[key]

    def get(self, key: tuple[int, int], default: tuple[int, int, int] = (0, 0, 0)):
        """
        Gets the pixel color from the current frame with a default value.
        :param key: A tuple of (x, y) coordinates.
        :param default: Default color to return if the pixel is not set.
        :return: A tuple of (R, G, B) color values.
        """
        return self.f1.get(key, default)

    # noinspection PyShadowingNames
    def __setitem__(self, key: tuple[int, int], value: tuple[int, int, int]):
        """
        Sets the pixel color in the current frame.
        :param key: A tuple of (x, y) coordinates.
        :param value: A tuple of (R, G, B) color values.
        """
        self.f1[key] = value

    def __out(self, text: str, end: str = "\n"):
        """
        Writes text to stdout and flushes.
        :param text: The text to write.
        :param end: The string to append at the end (default is newline).
        """
        sys.stdout.write(text + end)
        sys.stdout.flush()

    def refresh(self, force_full: bool = False, bitrate: int = 0):
        """
        Refreshes the terminal screen by comparing the current frame with the previous one
        and outputting only the changes, or a full refresh if too many changes occur.

        If force_full is True, the comparison is skipped and the entire frame is always
        written — use this when the caller knows every pixel has changed (e.g. video).

        :param force_full: Whether to force a full redraw.
        :param bitrate: Maximum number of cells to update in a partial refresh.

        All output is batched into a single write + flush to minimise I/O syscalls.
        The cursor is hidden for the duration of the write and restored to its prior
        visible/hidden state afterwards.
        """
        # Detect terminal resize
        current_width, current_height = os.get_terminal_size()
        if current_width != self.width or current_height != self.height:
            self.width = current_width
            self.height = current_height
            self.p1 = Frame(self.width, self.height * 2)
            self.f1 = Frame(self.width, self.height * 2)
            self._first_refresh = True

        if self._first_refresh:
            # Clear terminal on first refresh to ensure a clean state
            # This helps avoid "spottiness" if the terminal background is not black.
            # Use \033[H\033[2J to move to home and clear.
            sys.stdout.write("\033[H\033[2J")

        cursor_was_visible = self.is_cursor_visible
        parts = ["\033[?25l"]  # Hide cursor at the start of every refresh

        if force_full or self._first_refresh:
            do_full = True
            changes = None
            truncated = False
            self._first_refresh = False
        else:
            changes, truncated = self.f1.compare(self.p1, bitrate=bitrate, parallel=self._parallel)
            do_full = len(changes) > (self.width * self.height) // 2

        if do_full:
            # Full refresh — build output row by row (one terminal row = two pixel rows).
            parts.append(generate_move_string(0, 0))
            width = self.width
            height = self.height
            pixels = self.f1.pixels
            parallel = self._parallel
            if parallel is not None and parallel.enabled and height >= parallel.num_threads:
                from .parallel import _worker_build_rows  # pylint: disable=import-outside-toplevel
                thread_pool = parallel.get_thread_pool()
                num_threads = max(1, min(parallel.num_threads, height))
                chunk_size = height // num_threads
                futures = []
                for i in range(num_threads):
                    start = i * chunk_size
                    end = height if i == num_threads - 1 else start + chunk_size
                    futures.append(
                        thread_pool.submit(_worker_build_rows, pixels, width, start, end)
                    )
                for f in futures:
                    parts.append(f.result())
            else:
                for vy in range(height):
                    top_base = vy * 2 * width
                    bottom_base = top_base + width
                    row_parts = [
                        build_pixel(pixels[top_base + x], pixels[bottom_base + x])
                        for x in range(width)
                    ]
                    parts.append("".join(row_parts) + "\n")
            parts.append("\033[0m")
        else:
            # Partial refresh — sort by (vy, x) and skip move escapes for adjacent cells.
            prev_vy = -1
            prev_x = -1
            for (x, vy), (top, bottom) in sorted(changes.items()):
                if vy == prev_vy and x == prev_x + 1:
                    parts.append(build_pixel(top, bottom))
                else:
                    parts.append(generate_move_string(x, vy) + build_pixel(top, bottom))
                prev_vy = vy
                prev_x = x
            parts.append("\033[0m")

        # Move to bottom, restore cursor visibility, and emit everything in one syscall
        parts.append(generate_move_string(0, self.height - 1))
        if cursor_was_visible:
            parts.append("\033[?25h")
        sys.stdout.write("".join(parts))
        sys.stdout.flush()

        # Swap frames and reset the new f1 in-place — no new Frame allocation
        if truncated:
            # If truncated, p1 and terminal are out of sync. 
            # We must only update p1 for pixels we actually drew.
            # Easiest way: p1 already has the old state. f1 has the new state.
            # We want to move only the drawn pixels from f1 to p1.
            # BUT we swap them below. So after swap, p1 is the new state, f1 is the old state.
            # We then need to restore UNDRAWN pixels from f1 (old state) to p1 (new state).
            self.p1, self.f1 = self.f1, self.p1
            
            p1_pixels = self.p1.pixels
            f1_pixels = self.f1.pixels
            width = self.width
            for (x, vy) in changes:
                base = vy * 2 * width + x
                p1_pixels[base] = f1_pixels[base]
                p1_pixels[base + width] = f1_pixels[base + width]
            
            # Now p1 correctly matches terminal (it was old p1, now updated with changes).
            # f1 is still old p1. We can reset it.
        else:
            self.p1, self.f1 = self.f1, self.p1

        self.f1.reset()

    def move_to_bottom(self):
        """
        Moves the terminal cursor to the bottom of the screen.
        """
        move_str = generate_move_string(0, self.height - 1)
        self.__out(move_str, end="")

    def draw_line(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        x: int,
        y: int,
        x2: int,
        y2: int,
        color: tuple[int, int, int],
    ):
        """
        Draws a line on the current frame using Bresenham's line algorithm.
        :param x: Starting X-coordinate.
        :param y: Starting Y-coordinate.
        :param x2: Ending X-coordinate.
        :param y2: Ending Y-coordinate.
        :param color: A tuple of (R, G, B) color values.
        """
        dx = abs(x2 - x)
        dy = abs(y2 - y)
        sx = 1 if x < x2 else -1
        sy = 1 if y < y2 else -1
        err = dx - dy

        while True:
            self[(x, y)] = color
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
