"""Render: terminal display manager with frame buffering and pixel-level rendering."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from .frame import Frame
from .term_utils import (
    init_terminal,
    hide_cursor,
    show_cursor,
    generate_move_string,
    build_pixel,
)

if TYPE_CHECKING:
    from .parallel import ParallelConfig


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
        w, h = os.get_terminal_size()
        self.size = (w, h)
        self._parallel = parallel

        self.p1: Frame = Frame(w, h * 2)
        self.f1: Frame = Frame(w, h * 2)

        # Force the first refresh to be a full redraw to avoid "spottiness"
        # when the initial terminal state is not black.
        self._first_refresh = True

        self.is_cursor_visible = True

    @property
    def width(self):
        """Returns the current terminal width."""
        return self.size[0]

    @property
    def height(self):
        """Returns the current terminal height."""
        return self.size[1]

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

    def _handle_terminal_resize(self):
        """
        Detects terminal resize and reallocates frames if needed.
        :return: True if a resize occurred, False otherwise.
        """
        current_width, current_height = os.get_terminal_size()
        if current_width != self.width or current_height != self.height:
            self.size = (current_width, current_height)
            self.p1 = Frame(self.width, self.height * 2)
            self.f1 = Frame(self.width, self.height * 2)
            self._first_refresh = True
            return True
        return False

    def _build_full_frame_output(self) -> list[str]:
        """
        Builds ANSI escape sequences for a complete frame redraw.
        Used when too many pixels have changed or on first refresh.

        :return: List of string parts to be concatenated and written.
        """
        from .parallel import _worker_build_rows  # pylint: disable=import-outside-toplevel
        parts = [generate_move_string(0, 0)]
        pixels = self.f1.pixels

        if (self._parallel is not None and self._parallel.enabled and
                self.height >= self._parallel.num_threads):
            thread_pool = self._parallel.get_thread_pool()
            num_threads = max(1, min(self._parallel.num_threads, self.height))
            chunk_size = self.height // num_threads
            futures = []
            for i in range(num_threads):
                start = i * chunk_size
                end = self.height if i == num_threads - 1 else start + chunk_size
                futures.append(
                    thread_pool.submit(_worker_build_rows, pixels, self.width, start, end)
                )
            for f_res in futures:
                parts.append(f_res.result())
        else:
            for vy in range(self.height):
                top_base = vy * 2 * self.width
                row_parts = [
                    build_pixel(pixels[top_base + x], pixels[top_base + self.width + x])
                    for x in range(self.width)
                ]
                parts.append("".join(row_parts) + "\n")

        parts.append("\033[0m")
        return parts

    def _build_partial_frame_output(self, changes: dict) -> list[str]:
        """
        Builds ANSI escape sequences for a partial frame update (changed cells only).
        Optimizes output by skipping move sequences for adjacent cells.

        :param changes: Dictionary mapping (x, vy) cell coords to (top_color, bottom_color).
        :return: List of string parts to be concatenated and written.
        """
        parts = []
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
        return parts

    def _swap_frames_and_reset(self, changes: dict | None, truncated: bool):
        """
        Swaps frame buffers and resets f1, handling truncation logic.
        When truncated, only sync drawn pixels from p1 to maintain terminal coherence.

        :param changes: Dictionary of changed cells (None for full refresh).
        :param truncated: Whether the partial refresh was truncated by bitrate.
        """
        if truncated and changes is not None:
            # If truncated, p1 and terminal are out of sync.
            # We must only update p1 for pixels we actually drew.
            # After swap, p1 is the new state, f1 is the old state.
            # We restore UNDRAWN pixels from f1 (old state) to p1 (new state).
            self.p1, self.f1 = self.f1, self.p1

            p1_pixels = self.p1.pixels
            f1_pixels = self.f1.pixels
            width = self.width
            for (x, vy) in changes:
                base = vy * 2 * width + x
                p1_pixels[base] = f1_pixels[base]
                p1_pixels[base + width] = f1_pixels[base + width]
        else:
            self.p1, self.f1 = self.f1, self.p1

        self.f1.reset()

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
        # Detect terminal resize and reallocate frames if needed
        self._handle_terminal_resize()

        if self._first_refresh:
            # Clear terminal on first refresh to ensure a clean state
            sys.stdout.write("\033[H\033[2J")

        cursor_was_visible = self.is_cursor_visible
        parts = ["\033[?25l"]  # Hide cursor at the start of every refresh

        # Determine if we need a full or partial refresh
        if force_full or self._first_refresh:
            do_full = True
            changes = None
            truncated = False
            self._first_refresh = False
        else:
            changes, truncated = self.f1.compare(self.p1, bitrate=bitrate, parallel=self._parallel)
            do_full = len(changes) > (self.width * self.height) // 2

        # Build output based on refresh type
        if do_full:
            parts.extend(self._build_full_frame_output())
        else:
            parts.extend(self._build_partial_frame_output(changes))

        # Move to bottom, restore cursor visibility, and emit everything in one syscall
        parts.append(generate_move_string(0, self.height - 1))
        if cursor_was_visible:
            parts.append("\033[?25h")
        sys.stdout.write("".join(parts))
        sys.stdout.flush()

        # Swap frames and reset the new f1 in-place — no new Frame allocation
        self._swap_frames_and_reset(changes, truncated)

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

    def draw_circle(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        x: int,
        y: int,
        radius: int,
        color: tuple[int, int, int],
        fill: bool = False,
        border_color: tuple[int, int, int] | None = None,
    ):
        """
        Draws a circle on the current frame.
        :param x: Center X-coordinate.
        :param y: Center Y-coordinate.
        :param radius: Radius of the circle.
        :param color: Color of the circle (fill color if filled, else outline color).
        :param fill: Whether to fill the circle.
        :param border_color: Optional color for the circle's border.
        """
        if fill:
            cx = radius
            cy = 0
            err = 0

            while cx >= cy:
                # Draw horizontal lines between symmetric points
                for i in range(x - cx, x + cx + 1):
                    self[(i, y + cy)] = color
                    self[(i, y - cy)] = color
                for i in range(x - cy, x + cy + 1):
                    self[(i, y + cx)] = color
                    self[(i, y - cx)] = color

                cy += 1
                if err <= 0:
                    err += 2 * cy + 1
                else:
                    cx -= 1
                    err += 2 * (cy - cx) + 1

        if border_color is not None or not fill:
            outline_color = border_color if border_color is not None else color
            cx = radius
            cy = 0
            err = 0

            while cx >= cy:
                self[(x + cx, y + cy)] = outline_color
                self[(x + cy, y + cx)] = outline_color
                self[(x - cy, y + cx)] = outline_color
                self[(x - cx, y + cy)] = outline_color
                self[(x - cx, y - cy)] = outline_color
                self[(x - cy, y - cx)] = outline_color
                self[(x + cy, y - cx)] = outline_color
                self[(x + cx, y - cy)] = outline_color

                cy += 1
                if err <= 0:
                    err += 2 * cy + 1
                else:
                    cx -= 1
                    err += 2 * (cy - cx) + 1
