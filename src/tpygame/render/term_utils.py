"""Utilities for terminal control: ANSI escape sequences, color generation, and cursor management.
"""
import os
from functools import lru_cache
import random

TOP_HALF_BLOCK = "▀"


def init_terminal():
    """Initialize the terminal for ANSI escape code support on Windows."""
    if os.name == 'nt':
        try:
            import ctypes  # pylint: disable=import-outside-toplevel
            from ctypes import wintypes  # pylint: disable=import-outside-toplevel

            kernel32 = ctypes.windll.kernel32
            # STD_OUTPUT_HANDLE = -11
            h_stdout = kernel32.GetStdHandle(-11)
            # STD_INPUT_HANDLE = -10
            h_stdin = kernel32.GetStdHandle(-10)

            # Enable ANSI support
            mode = wintypes.DWORD()
            if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)

            # Disable QuickEdit Mode
            if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
                # ENABLE_QUICK_EDIT_MODE = 0x0040, ENABLE_EXTENDED_FLAGS = 0x0080
                new_mode = (mode.value & ~0x0040) | 0x0080
                kernel32.SetConsoleMode(h_stdin, new_mode)
        except OSError:
            pass


def clear():
    """Clear the terminal screen."""
    print("\033[2J", end="")


def hide_cursor():
    """Hide the terminal cursor."""
    print("\033[?25l", end="")


def show_cursor():
    """Show the terminal cursor."""
    print("\033[?25h", end="")


@lru_cache(maxsize=4096)
def generate_move_string(x: int, y: int):
    """Return an ANSI escape string that moves the cursor to (x, y)."""
    return f"\033[{y + 1};{x + 1}H"


@lru_cache(maxsize=4096)
def generate_fore_color(color: tuple[int, int, int]):
    """Return an ANSI escape string that sets the foreground color."""
    return f"\033[38;2;{color[0]};{color[1]};{color[2]}m"


@lru_cache(maxsize=4096)
def generate_back_color(color: tuple[int, int, int]):
    """Return an ANSI escape string that sets the background color."""
    return f"\033[48;2;{color[0]};{color[1]};{color[2]}m"


@lru_cache(maxsize=32678)
def build_pixel(
    top_color: tuple[int, int, int] = (0, 0, 0),
    bottom_color: tuple[int, int, int] = (0, 0, 0),
):
    """Build a two-pixel-high terminal cell using the half-block character."""
    top = f"\033[38;2;{top_color[0]};{top_color[1]};{top_color[2]}m"
    bottom = f"\033[48;2;{bottom_color[0]};{bottom_color[1]};{bottom_color[2]}m"
    return top + bottom + TOP_HALF_BLOCK


def random_color():
    """Return a random (R, G, B) color tuple."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
