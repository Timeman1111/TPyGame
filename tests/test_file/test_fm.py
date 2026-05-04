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


def test_create_file_creates_missing_parent_directories(tmp_path):
    fm = FileManager()
    target = tmp_path / "nested" / "deeper" / "new_file.txt"

    assert fm.create_file(str(target)) is True
    assert target.exists()
    assert target.parent.exists()


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
    assert fm.block_extension("tmp") is True

    target = tmp_path / "blocked.tmp"
    assert fm.create_file(str(target)) is False
    assert not target.exists()
    assert fm.unblock_extension(".tmp") is True
    assert fm.create_file(str(target)) is True


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


def test_create_file_normalizes_path_for_whitelist(tmp_path):
    fm = FileManager(wl=True)
    allowed = tmp_path / "allowed" / "inside.txt"
    disallowed_via_dotdot = tmp_path / "allowed" / ".." / "outside.txt"

    fm.whitelist.add(allowed)

    assert fm.create_file(str(allowed)) is True
    assert fm.create_file(str(disallowed_via_dotdot)) is False


def test_text_and_bytes_io(tmp_path):
    fm = FileManager()
    text_target = tmp_path / "save" / "state.txt"
    bytes_target = tmp_path / "save" / "raw.bin"

    assert fm.write_text(str(text_target), "hello") is True
    assert fm.read_text(str(text_target)) == "hello"

    assert fm.write_bytes(str(bytes_target), b"\x00\x01") is True
    assert fm.read_bytes(str(bytes_target)) == b"\x00\x01"


def test_json_io_and_malformed_input(tmp_path):
    fm = FileManager()
    target = tmp_path / "save" / "data.json"

    payload = {"score": 42, "name": "player"}
    assert fm.write_json(str(target), payload) is True
    assert fm.read_json(str(target)) == payload

    target.write_text("{bad json", encoding="utf-8")
    assert fm.read_json(str(target)) is None


def test_directory_operations(tmp_path):
    fm = FileManager()
    target_dir = tmp_path / "assets" / "sprites"
    file_a = target_dir / "a.txt"
    file_b = target_dir / "b.txt"

    assert fm.create_directory(str(target_dir)) is True
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    entries = fm.list_directory(str(target_dir))
    assert entries is not None
    assert {entry.name for entry in entries} == {"a.txt", "b.txt"}

    assert fm.delete_directory(str(target_dir)) is False
    assert fm.delete_directory(str(target_dir), recursive=True) is True
    assert not target_dir.exists()


def test_delete_file_and_cleanup(tmp_path):
    fm = FileManager()
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"

    assert fm.create_file(str(a)) is True
    assert fm.write_text(str(b), "temp") is True
    assert fm.delete_file(str(a)) is True
    assert not a.exists()

    removed = fm.cleanup()
    assert removed >= 1
    assert not b.exists()


def test_asset_directory_and_loader(tmp_path):
    fm = FileManager()
    asset_dir = tmp_path / "game_assets"
    texture = asset_dir / "textures" / "player.txt"

    assert fm.set_asset_dir(str(asset_dir)) is True
    texture.parent.mkdir(parents=True, exist_ok=True)
    texture.write_text("sprite", encoding="utf-8")

    assert fm.load_asset("textures/player.txt", binary=False) == "sprite"
    assert fm.load_asset("../outside.txt", binary=False) is None


def test_get_logger_writes_to_file(tmp_path):
    fm = FileManager()
    log_file = tmp_path / "logs" / "debug.log"

    logger = fm.get_logger(str(log_file), name="test-file-manager-logger")
    assert logger is not None
    logger.info("terminal-safe debug line")
    for handler in logger.handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "terminal-safe debug line" in content


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


