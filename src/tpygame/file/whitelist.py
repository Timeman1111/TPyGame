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

    @staticmethod
    def _normalize(path: pathlib.Path | str) -> pathlib.Path:
        """Normalize a path for safe comparisons."""
        if isinstance(path, str):
            path = pathlib.Path(path)
        return path.expanduser().resolve(strict=False)


    def add(self, path: pathlib.Path | str) -> bool:
        """
        Adds a file path to the allowed list.

        :param path: The file path to be added.
        :type path: pathlib.Path
        :return: True if the path was successfully added, False if an error occurred.
        :rtype: bool
        """
        if not isinstance(path, (str, pathlib.Path)):
            return False

        normalized = self._normalize(path)
        if normalized in self.__allowed:
            return True

        self.__allowed.append(normalized)
        return True

    def get(self) -> list[pathlib.Path]:
        """
        Retrieves the list of allowed file paths.

        This method returns the current list of allowed file paths that have been
        added to the whitelist.

        :return: A list of allowed file paths.
        :rtype: list[pathlib.Path]
        """
        return list(self.__allowed)

    def __contains__(self, item: pathlib.Path) -> bool:
        """
        Checks if a path is in the whitelist.
        """
        if not isinstance(item, (str, pathlib.Path)):
            return False
        return self._normalize(item) in self.__allowed

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
