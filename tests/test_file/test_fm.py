import os
import pathlib
import sys

# make sure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/tpygame/file")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from tpygame.file.fm import FileManager


def test_init_defaults_and_wl_flag_enabled():
    """
    Tests the initialization of `FileManager` with default parameters and with
    the `wl` flag enabled. Confirms correct attribute states and instances.

    The function verifies:
    1. Default `wl` value is `False`.
    2. The `whitelist` attribute's type is `WhiteList`.
    3. The `whitelist` attribute has the method `add`.
    4. The `_blocked_exts` list is initialized empty.
    5. When `wl=True` is passed, the `wl` value is set to `True`.

    :return: None
    """
    fm_default = FileManager()
    assert fm_default.wl is False
    assert fm_default.whitelist.__class__.__name__ == "WhiteList"
    assert hasattr(fm_default.whitelist, "add")
    assert fm_default._blocked_exts == []

    fm_wl = FileManager(wl=True)
    assert fm_wl.wl is True
    assert fm_wl.whitelist.__class__.__name__ == "WhiteList"


def test_create_file_success(tmp_path):
    """
    Tests the successful creation of a file using the `FileManager` class.

    The test verifies that the `create_file` method creates a file at the
    specified path, and ensures that the file exists and is a valid file
    after creation.

    :param tmp_path: Temporary directory provided by pytest to create
        file paths for testing.
    :type tmp_path: pathlib.Path
    :return: None
    """
    fm = FileManager()
    target = tmp_path / "new_file.txt"

    assert fm.create_file(str(target)) is True
    assert target.exists()
    assert target.is_file()


def test_create_file_rejects_existing_file(tmp_path):
    """
    Tests the create_file method of FileManager to ensure it rejects attempts to
    create a file if a file with the same name already exists. The method should
    return False in such cases.

    :param tmp_path: A temporary directory provided by pytest for creating
        temporary files and directories during the test.
    :type tmp_path: pathlib.Path
    :return: None
    """
    fm = FileManager()
    target = tmp_path / "already_exists.txt"
    target.write_text("data", encoding="utf-8")

    assert fm.create_file(str(target)) is False


def test_create_file_rejects_blocked_extensions(tmp_path):
    """
    Test the behavior of the `create_file` method when attempting to create a file with a
    blocked file extension. Ensures that files with extensions present in the list of
    blocked extensions cannot be created and that the method returns `False` in such
    cases.

    :param tmp_path: Temporary directory path provided by the test framework. This is
        used as the base path for creating the file during testing.
    :type tmp_path: Path
    :return: None
    """
    fm = FileManager()
    fm._blocked_exts.append(".tmp")

    target = tmp_path / "blocked.tmp"
    assert fm.create_file(str(target)) is False
    assert not target.exists()


def test_create_file_respects_whitelist_when_enabled(tmp_path):
    """
    Test that the `create_file` method respects the whitelist when it is enabled.

    This test verifies that files not included in the whitelist are not created,
    while files explicitly added to the whitelist are successfully created. It
    also confirms that enabling the whitelist functionality prevents unauthorized
    file creation.

    :param tmp_path: Temporary directory path provided by pytest for creating
        and managing files during the test.
    :type tmp_path: Path
    :return: None
    """
    fm = FileManager(wl=True)
    denied = tmp_path / "denied.txt"
    allowed = tmp_path / "allowed.txt"

    assert fm.create_file(str(denied)) is False

    fm.whitelist.add(allowed)
    assert fm.create_file(str(allowed)) is True
    assert allowed.exists()


def test_file_and_folder_existence_checks(tmp_path):
    """
    Tests file and folder existence checks for `FileManager` class.

    This function evaluates the existence check methods of a `FileManager` instance
    for files and folders in various scenarios. It ensures that files, folders,
    and non-existent paths are correctly identified by their respective methods.

    :param tmp_path: Temporary directory path provided by the testing framework.
    :type tmp_path: pathlib.Path
    :return: None
    """
    fm = FileManager()
    file_path = tmp_path / "item.txt"
    folder_path = tmp_path / "folder"
    missing = tmp_path / "missing"

    file_path.write_text("x", encoding="utf-8")
    folder_path.mkdir()

    assert fm.does_file_exist(str(file_path)) is True
    assert fm.does_file_exist(str(folder_path)) is False
    assert fm.does_file_exist(str(missing)) is False

    assert fm.does_folder_exist(str(folder_path)) is True
    assert fm.does_folder_exist(str(file_path)) is False
    assert fm.does_folder_exist(str(missing)) is False

    assert fm.does_exist(str(file_path)) is True
    assert fm.does_exist(str(folder_path)) is True
    assert fm.does_exist(str(missing)) is False


