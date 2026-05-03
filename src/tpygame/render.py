
"""Render: terminal display manager with frame buffering and pixel-level rendering."""
import os
import random
import sys



from frame import Frame
from term_utils import (
    init_terminal,
    clear,
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

    def refresh(self):
        """
        Refreshes the terminal screen by comparing the current frame with the previous one
        and outputting only the changes, or a full refresh if too many changes occur.
        """
        self.hide_cursor()

        changes = self.f1.compare(self.p1)

        if len(changes) > (self.width * self.height) // 2:
            # Full refresh
            self.home_cursor()
            output = [
                build_pixel(
                    self.f1.pixels[vy * 2 * self.width + x],
                    self.f1.pixels[(vy * 2 + 1) * self.width + x],
                )
                if x < self.width - 1
                else build_pixel(
                    self.f1.pixels[vy * 2 * self.width + x],
                    self.f1.pixels[(vy * 2 + 1) * self.width + x],
                ) + "\n"
                for vy in range(self.height)
                for x in range(self.width)
            ]
            self.__out("".join(output) + "\033[0m", end="")
        else:
            # Partial refresh
            output = []
            for (x, vy), (top, bottom) in changes.items():
                output.append(generate_move_string(x, vy) + build_pixel(top, bottom))
            self.__out("".join(output) + "\033[0m", end="")

        self.p1 = self.f1
        self.f1 = Frame(self.width, self.height * 2)

        self.move_to_bottom()

        if self.is_cursor_visible:
            self.show_cursor()

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