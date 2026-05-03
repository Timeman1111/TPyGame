import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to sys.path to import tpygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tpygame.render import Screen
from tpygame.frame import Frame

@pytest.fixture
def mock_terminal():
    with patch('tpygame.render.init_terminal') as mock_init, \
         patch('os.get_terminal_size', return_value=(80, 24)) as mock_size, \
         patch('sys.stdout.write') as mock_write, \
         patch('sys.stdout.flush') as mock_flush:
        yield {
            'init': mock_init,
            'size': mock_size,
            'write': mock_write,
            'flush': mock_flush
        }

def test_init(mock_terminal):
    screen = Screen()
    assert screen.width == 80
    assert screen.height == 24
    assert screen.last_pos == (0, 0)
    assert screen.is_cursor_visible is True
    mock_terminal['init'].assert_called_once()
    # Screen initializes p1 and f1 with height * 2
    assert isinstance(screen.p1, Frame)
    assert isinstance(screen.f1, Frame)
    assert screen.f1.width == 80
    assert screen.f1.height == 48

def test_cursor_visibility(mock_terminal):
    screen = Screen()
    
    with patch('tpygame.render.hide_cursor') as mock_hide:
        screen.hide_cursor()
        mock_hide.assert_called_once()
        assert screen.is_cursor_visible is False
        
    with patch('tpygame.render.show_cursor') as mock_show:
        screen.show_cursor()
        mock_show.assert_called_once()
        assert screen.is_cursor_visible is True

def test_move_cursor(mock_terminal):
    screen = Screen()
    screen.move_cursor(10, 5)
    assert screen.last_pos == (5, 10)
    # ANSI escape for moving to (10, 5) is \033[6;11H (1-indexed)
    mock_terminal['write'].assert_any_call("\033[6;11H")

def test_home_cursor(mock_terminal):
    screen = Screen()
    screen.home_cursor()
    assert screen.last_pos == (0, 0)
    mock_terminal['write'].assert_any_call("\033[1;1H")

def test_move_to_bottom(mock_terminal):
    screen = Screen() # height 24
    screen.move_to_bottom()
    # moves to (0, height-1) -> (0, 23) -> \033[24;1H
    mock_terminal['write'].assert_any_call("\033[24;1H")

def test_pixel_manipulation(mock_terminal):
    screen = Screen()
    color = (255, 0, 0)
    screen[(5, 10)] = color
    assert screen[(5, 10)] == color
    assert screen.get((5, 10)) == color
    assert screen.get((100, 100), default=(1, 2, 3)) == (1, 2, 3)

def test_draw_line(mock_terminal):
    screen = Screen()
    color = (0, 255, 0)
    # Horizontal line
    screen.draw_line(0, 0, 5, 0, color)
    for x in range(6):
        assert screen[(x, 0)] == color
        
    # Vertical line
    screen.draw_line(10, 10, 10, 15, color)
    for y in range(10, 16):
        assert screen[(10, y)] == color

@patch('tpygame.render.build_pixel', return_value="X")
def test_refresh_full(mock_build, mock_terminal):
    screen = Screen()
    # Force full refresh by setting many pixels
    with patch.object(Frame, 'compare', return_value={(x, y): ((0,0,0), (0,0,0)) for x in range(80) for y in range(20)}):
        screen.refresh()
        # It should have called home_cursor
        mock_terminal['write'].assert_any_call("\033[1;1H")

@patch('tpygame.render.build_pixel', return_value="P")
def test_refresh_partial(mock_build, mock_terminal):
    screen = Screen()
    # Force partial refresh by setting few pixels
    with patch.object(Frame, 'compare', return_value={(5, 5): ((255,0,0), (0,255,0))}):
        screen.refresh()
        # Partial refresh calls self.__out("".join(output) + "\033[0m", end="")
        # output.append(generate_move_string(x, vy) + build_pixel(top, bottom))
        # so it should be \033[6;6HP\033[0m
        mock_terminal['write'].assert_any_call("\033[6;6HP\033[0m")
