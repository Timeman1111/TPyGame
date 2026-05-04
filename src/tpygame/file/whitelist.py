"""
This module provides the WhiteList class for managing allowed file paths.
"""
import pathlib


class WhiteList:
    """
    A class to maintain a list of allowed file paths.
    """
    def __init__(self):
        """
        Initializes an empty WhiteList.
        """
        self.__allowed: list[pathlib.Path] = []


    def add(self, path: pathlib.Path):
        """
        Adds a file path to the allowed list.

        :param path: The file path to be added.
        :type path: pathlib.Path
        :return: True if the path was successfully added, False if an error occurred.
        :rtype: bool
        """
        try:
            if isinstance(path, str):
                path = pathlib.Path(path)
            self.__allowed.append(path)

            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def get(self) -> list[pathlib.Path]:
        """
        Retrieves the list of allowed file paths.

        This method returns the current list of allowed file paths that have been
        added to the whitelist.

        :return: A list of allowed file paths.
        :rtype: list[pathlib.Path]
        """
        return self.__allowed

    def __contains__(self, item: pathlib.Path) -> bool:
        """
        Checks if a path is in the whitelist.
        """
        return item in self.__allowed

    def __iter__(self):
        """
        Returns an iterator for the allowed paths.
        """
        return iter(self.__allowed)

    def __len__(self):
        """
        Returns the number of allowed paths.
        """
        return len(self.__allowed)
