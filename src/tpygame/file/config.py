class Config:
    """
    A base configuration class that provides a dictionary-like interface.
    """
    def __init__(self):
        """
        Initializes an empty configuration.
        """
        self._config: dict[str, object] = {}

    def __getitem__(self, key: str) -> object:
        """
        Gets a configuration value by key.

        Args:
            key: The configuration key.

        Returns:
            The value associated with the key.
        """
        return self._config[key]

    def __setitem__(self, key: str, value) -> object:
        """
        Sets a configuration value by key.

        Args:
            key: The configuration key.
            value: The value to set.
        """
        self._config[key] = value

    def __contains__(self, key: str) -> bool:
        """
        Checks if a key exists in the configuration.

        Args:
            key: The configuration key.

        Returns:
            True if the key exists, False otherwise.
        """
        return key in self._config



class FileConfig(Config):
    """
    A configuration class that is backed by a JSON file.
    Changes to the configuration are automatically saved to the file.
    """
    def __init__(self, path: str = None, fm: "FileManager" = None):
        """
        Initializes the file-backed configuration.

        Args:
            path: The path to the JSON configuration file.
            fm: An instance of FileManager to handle I/O operations.
        """
        super().__init__()
        self.file_path = path
        self.fm: "FileManager" = fm

        if self.file_path is not None and self.fm is not None:
            self._config = self.fm.read_json(self.file_path)


    def save(self, fm: "FileManager" = None):
        """
        Saves the current configuration to the file.

        Args:
            fm: Optional FileManager instance. If not provided, uses the one passed during initialization.

        Raises:
            ValueError: If file_path is not set.
        """
        fm = fm or self.fm
        if self.file_path is None:
            raise ValueError("file_path must be set before saving")
        if fm is None:
            raise ValueError("FileManager must be provided or set during initialization")
        
        fm.write_json(self.file_path, self._config)

    def __setitem__(self, key: str, value) -> object:
        """
        Sets a configuration value and automatically saves it to the file.
        If the key is "file_path", updates the underlying file path.

        Args:
            key: The configuration key.
            value: The value to set.

        Raises:
            TypeError: If key is "file_path" and value is not a string.
        """
        if key == "file_path":
            if not isinstance(value, str):
                raise TypeError("file_path must be a string")
            self.file_path = value
            
        super().__setitem__(key, value)

        if self.file_path is not None and self.fm is not None:
            self.save(self.fm)
