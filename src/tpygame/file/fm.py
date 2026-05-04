"""
This module provides the FileManager class for file and folder operations.
"""
import json
import logging
import pathlib
import shutil
from typing import Any
from .whitelist import WhiteList


class FileManager:
    """
    A class to manage file and folder operations, including whitelisting.
    """
    def __init__(self, wl: bool = False):
        """
        Represents an initializer for configuring internal components.

        This initializer sets up a whitelist used to manage allowed items
        and internally configures a mechanism to track blocked extensions.

        Attributes:
            whitelist (WhiteList): The object responsible for managing and
                maintaining the list of allowed items.

        """

        self.created_files: list[pathlib.Path] = []

        self.wl: bool = wl
        self.whitelist: WhiteList = WhiteList()
        self._blocked_exts: list[str] = []
        self._asset_dir: pathlib.Path | None = None
        self._loggers: dict[str, logging.Logger] = {}

    def __repr__(self) -> str:
        """
        Returns a string representation of the FileManager instance.
        """
        return f"<FileManager: {self.wl}>"

    @staticmethod
    def _normalize_path(path: str | pathlib.Path) -> pathlib.Path:
        """Return a normalized absolute path for all internal checks."""
        if isinstance(path, str):
            path = pathlib.Path(path)
        return path.expanduser().resolve(strict=False)

    @staticmethod
    def _normalize_ext(ext: str) -> str:
        """Convert extensions to normalized lowercase '.ext' format."""
        if not ext:
            return ""
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext.lower()

    def _is_blocked(self, path: pathlib.Path) -> bool:
        return path.suffix.lower() in self._blocked_exts

    def _is_allowed(self, path: pathlib.Path) -> bool:
        if not self.wl:
            return True
        return path in self.whitelist

    def block_extension(self, ext: str) -> bool:
        """Block an extension from file access operations."""
        normalized = self._normalize_ext(ext)
        if not normalized:
            return False
        if normalized not in self._blocked_exts:
            self._blocked_exts.append(normalized)
        return True

    def unblock_extension(self, ext: str) -> bool:
        """Remove an extension from the blocked list."""
        normalized = self._normalize_ext(ext)
        if not normalized or normalized not in self._blocked_exts:
            return False
        self._blocked_exts.remove(normalized)
        return True

    def __create_file(self, path: pathlib.Path) -> bool:
        """
        Creates a new file at the specified path if it does not already exist,
        is not in the blocked extensions list, and is allowed by the optional whitelist.

        :param path: Path to the file to be created.
        :type path: pathlib.Path
        :return: True if the file was successfully created, False otherwise.
        :rtype: bool
        """
        path = self._normalize_path(path)

        if path.exists() or self._is_blocked(path) or (not self._is_allowed(path)):
            return False

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        except OSError:
            return False

        self.created_files.append(path)
        return True



    def __does_file_exist(self, path: pathlib.Path) -> bool:
        """
        Check if a file exists at the given path and verify it is a file.

        :param path: The path of the file to check.
        :type path: pathlib.Path
        :return: True if the file exists and is a valid file, otherwise False.
        :rtype: bool
        """
        path = self._normalize_path(path)
        return path.exists() and path.is_file()

    def __does_folder_exist(self, path: pathlib.Path) -> bool:
        """
        Checks if the specified folder exists and is a directory.

        This method verifies the existence of a folder at the given path
        and ensures that it is a directory.

        :param path: The path to the folder being checked.
        :type path: pathlib.Path
        :return: True if the folder exists and is a directory, False otherwise.
        :rtype: bool
        """
        path = self._normalize_path(path)
        return path.exists() and path.is_dir()

    def create_file(self, path: str) -> bool:
        """
        Creates a file at the specified path.

        If the file already exists, this method does nothing. Otherwise, it creates
        a new file at the specified location, including any necessary but missing
        parent directories.

        :param path: The file path where the file should be created.
        :type path: str

        :return: True if the file was created successfully or already exists;
            False if an error occurred during the file creation process.
        :rtype: bool
        """
        return self.__create_file(pathlib.Path(path))

    def read_text(self, path: str, encoding: str = "utf-8") -> str | None:
        """Read text content from a file if allowed."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return None
        try:
            return path_obj.read_text(encoding=encoding)
        except (OSError, UnicodeDecodeError):
            return None

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """Write text content to a file if allowed."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return False

        try:
            existed = path_obj.exists()
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content, encoding=encoding)
            if not existed and path_obj not in self.created_files:
                self.created_files.append(path_obj)
            return True
        except OSError:
            return False

    def read_bytes(self, path: str) -> bytes | None:
        """Read binary content from a file if allowed."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return None
        try:
            return path_obj.read_bytes()
        except OSError:
            return None

    def write_bytes(self, path: str, data: bytes) -> bool:
        """Write binary content to a file if allowed."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return False

        try:
            existed = path_obj.exists()
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_bytes(data)
            if not existed and path_obj not in self.created_files:
                self.created_files.append(path_obj)
            return True
        except OSError:
            return False

    def read_json(self, path: str, encoding: str = "utf-8") -> Any | None:
        """Read and decode JSON from a file if allowed."""
        text = self.read_text(path, encoding=encoding)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def write_json(self, path: str, data: Any, encoding: str = "utf-8", indent: int = 2) -> bool:
        """Encode and write JSON data to a file if allowed."""
        try:
            text = json.dumps(data, ensure_ascii=True, indent=indent)
        except (TypeError, ValueError):
            return False
        return self.write_text(path, text, encoding=encoding)

    def create_directory(self, path: str) -> bool:
        """Create a directory and all parents if allowed."""
        path_obj = self._normalize_path(path)
        if not self._is_allowed(path_obj):
            return False
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    def list_directory(self, path: str) -> list[pathlib.Path] | None:
        """Return the children of a directory if allowed."""
        path_obj = self._normalize_path(path)
        if not self._is_allowed(path_obj) or not path_obj.is_dir():
            return None
        try:
            return sorted(path_obj.iterdir())
        except OSError:
            return None

    def delete_file(self, path: str) -> bool:
        """Delete a file if it exists and is allowed."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return False
        if not path_obj.exists() or not path_obj.is_file():
            return False

        try:
            path_obj.unlink()
            if path_obj in self.created_files:
                self.created_files.remove(path_obj)
            return True
        except OSError:
            return False

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete a directory if allowed; optionally recursive."""
        path_obj = self._normalize_path(path)
        if not self._is_allowed(path_obj) or not path_obj.exists() or not path_obj.is_dir():
            return False

        try:
            if recursive:
                shutil.rmtree(path_obj)
            else:
                path_obj.rmdir()
            self.created_files = [p for p in self.created_files if not p.is_relative_to(path_obj)]
            return True
        except OSError:
            return False

    def cleanup(self) -> int:
        """Delete files created during the active FileManager session."""
        removed = 0
        for path_obj in list(dict.fromkeys(self.created_files)):
            try:
                if path_obj.exists() and path_obj.is_file():
                    path_obj.unlink()
                    removed += 1
            except OSError:
                continue
        self.created_files.clear()
        return removed

    def set_asset_dir(self, path: str) -> bool:
        """Set and create the base directory used for asset loading."""
        path_obj = self._normalize_path(path)
        if not self.create_directory(str(path_obj)):
            return False
        self._asset_dir = path_obj
        if self.wl:
            self.whitelist.add(path_obj)
        return True

    def load_asset(self, filename: str, binary: bool = True, encoding: str = "utf-8") -> bytes | str | None:
        """Load an asset relative to the configured asset directory."""
        if self._asset_dir is None:
            return None

        candidate = self._normalize_path(self._asset_dir / filename)
        if not candidate.is_relative_to(self._asset_dir):
            return None

        if self.wl:
            self.whitelist.add(candidate)

        if binary:
            return self.read_bytes(str(candidate))
        return self.read_text(str(candidate), encoding=encoding)

    def get_logger(self, path: str, level: int = logging.INFO, name: str | None = None) -> logging.Logger | None:
        """Return a file-backed logger suitable for terminal-safe debugging."""
        path_obj = self._normalize_path(path)
        if self._is_blocked(path_obj) or (not self._is_allowed(path_obj)):
            return None

        cache_key = str(path_obj)
        if cache_key in self._loggers:
            return self._loggers[cache_key]

        try:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            logger_name = name or f"tpygame.file.{cache_key}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            logger.propagate = False

            existing = [
                handler
                for handler in logger.handlers
                if isinstance(handler, logging.FileHandler)
                and pathlib.Path(handler.baseFilename) == path_obj
            ]
            if not existing:
                handler = logging.FileHandler(path_obj, encoding="utf-8")
                handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
                logger.addHandler(handler)

            self._loggers[cache_key] = logger
            return logger
        except OSError:
            return None


    def does_file_exist(self, path: str) -> bool:
        """
        Checks whether the specified file exists in the given path.

        This method determines if a file exists at the specified
        path by leveraging the `pathlib.Path` module. The check
        is performed using an internal helper function.

        :param path: The file path to check for existence.
        :type path: str
        :return: True if the file exists, False otherwise.
        :rtype: bool
        """
        path_obj = self._normalize_path(path)
        return self.__does_file_exist(path_obj)

    def does_folder_exist(self, path: str) -> bool:
        """
        Checks if a folder exists at the given path.

        This method evaluates whether the specified folder exists by processing
        the path provided as input.

        :param path: The path to the folder as a string.
        :type path: str
        :return: True if the folder exists, False otherwise.
        :rtype: bool
        """
        path_obj = self._normalize_path(path)
        return self.__does_folder_exist(path_obj)

    def does_exist(self, path: str) -> bool:
        """
        Checks the existence of a file or folder at the given path.

        This method determines whether the specified path points to an existing
        file or directory. It relies on private methods to separately verify
        if the path corresponds to a file or a folder.

        :param path: The file system path to check.
        :type path: str
        :return: A boolean value indicating whether a file or folder exists
            at the specified path.
        :rtype: bool
        """
        path_obj = self._normalize_path(path)
        return self.__does_file_exist(path_obj) or self.__does_folder_exist(path_obj)
