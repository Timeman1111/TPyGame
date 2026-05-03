"""Render: terminal display manager with frame buffering and pixel-level rendering."""

import os
import sys



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

    def __init__(self, last_pos: tuple[int, int] = (0, 0)):
        """
        Initializes the Screen.
        :param last_pos: Initial cursor position (y, x).
        """
        init_terminal()
        self.last_pos = last_pos
        self.width, self.height = os.get_terminal_size()

        self.p1: Frame = Frame(self.width, self.height * 2)
        self.f1: Frame = Frame(self.width, self.height * 2)

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

    def refresh(self, force_full: bool = False, color_closeness: int = 0, bitrate: int = 0):
        """
        Refreshes the terminal screen by comparing the current frame with the previous one
        and outputting only the changes, or a full refresh if too many changes occur.

        If force_full is True, the comparison is skipped and the entire frame is always
        written — use this when the caller knows every pixel has changed (e.g. video).

        :param force_full: Whether to force a full redraw.
        :param color_closeness: Tolerance for color difference when comparing frames.
        :param bitrate: Maximum number of cells to update in a partial refresh.

        All output is batched into a single write + flush to minimise I/O syscalls.
        The cursor is hidden for the duration of the write and restored to its prior
        visible/hidden state afterwards.
        """
        cursor_was_visible = self.is_cursor_visible
        parts = ["\033[?25l"]  # Hide cursor at the start of every refresh

        if force_full:
            do_full = True
            changes = None
        else:
            changes = self.f1.compare(self.p1, color_closeness=color_closeness, bitrate=bitrate)
            do_full = len(changes) > (self.width * self.height) // 2

        if do_full:
            # Full refresh — build output row by row (one terminal row = two pixel rows).
            parts.append(generate_move_string(0, 0))
            width = self.width
            height = self.height
            pixels = self.f1.pixels
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
