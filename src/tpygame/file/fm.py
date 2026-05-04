"""
This module provides the FileManager class for file and folder operations.
"""
import pathlib
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

    def __repr__(self) -> str:
        """
        Returns a string representation of the FileManager instance.
        """
        return f"<FileManager: {self.wl}>"

    def __create_file(self, path: pathlib.Path) -> bool:
        """
        Creates a new file at the specified path if it does not already exist,
        is not in the blocked extensions list, and is allowed by the optional whitelist.

        :param path: Path to the file to be created.
        :type path: pathlib.Path
        :return: True if the file was successfully created, False otherwise.
        :rtype: bool
        """
        if path.exists() or (path.suffix in self._blocked_exts) or \
                (self.wl and path not in self.whitelist):
            return False

        path.touch()

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
        path_obj = pathlib.Path(path)
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
        path_obj = pathlib.Path(path)
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
        path_obj = pathlib.Path(path)
        return self.__does_file_exist(path_obj) or self.__does_folder_exist(path_obj)
