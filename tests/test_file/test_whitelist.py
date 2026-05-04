import os
import pathlib
import sys

# make sure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from tpygame.file.whitelist import WhiteList


def test_add_path_and_membership():
    """
    Tests the addition of a path to a WhiteList object and verifies its membership,
    along with checking the length of the WhiteList after addition.

    :return: None
    """
    wl = WhiteList()
    path = pathlib.Path("allowed/video.mp4")

    assert wl.add(path) is True
    assert path in wl
    assert len(wl) == 1


def test_add_string_coerces_to_path():
    """
    Tests adding a string path to the WhiteList object. Ensures that the string
    is coerced into a `pathlib.Path` object and correctly added to the list.

    :return: None
    """
    wl = WhiteList()

    assert wl.add("assets/image.png") is True
    assert wl.get() == [pathlib.Path("assets/image.png")]


def test_iteration_preserves_insert_order():
    """
    Tests that the iteration over the WhiteList object preserves the order
    of inserted elements.

    This function creates a `WhiteList` instance, adds `pathlib.Path` objects
    to it in a specific order, and then asserts that, when iterating over the
    `WhiteList`, the elements are yielded in the same order they were inserted.

    :return: None
    """
    wl = WhiteList()
    first = pathlib.Path("a.txt")
    second = pathlib.Path("b.txt")

    wl.add(first)
    wl.add(second)

    assert list(iter(wl)) == [first, second]

