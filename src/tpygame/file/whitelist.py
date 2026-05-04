"""
This module provides the WhiteList class for managing allowed file paths.
"""
import pathlib


class WhiteList:
    """
    A class to maintain a list of allowed file paths.
    """
    def __init__(self):
        self.__allowed: list[pathlib.Path] = []


    def add(self, path: pathlib.Path):
        """
        Adds a file type suffix to the allowed list.

        This method takes a file path, converts it to a `pathlib.Path` object if it is
        provided as a string, extracts its suffix, and appends the suffix to the allowed
        list. If an error occurs during this process, the method returns False.

        :param path: The file path whose suffix is to be added.
        :type path: pathlib.Path
        :return: True if the suffix was successfully added, False if an error occurred.
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
        Retrieves the list of allowed file type suffixes.

        This method returns the current list of allowed file type suffixes that have been
        added to the whitelist.

        :return: A list of allowed file type suffixes.
        :rtype: list[str]
        """
        return self.__allowed

    def __contains__(self, item: pathlib.Path) -> bool:
        return item in self.__allowed

    def __iter__(self):
        return iter(self.__allowed)

    def __len__(self):
        return len(self.__allowed)
