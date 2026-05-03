"""Frame: pixel buffer for terminal rendering, supporting flat and sparse storage."""


class Frame:
    """
    Represents a single frame of pixels.
    Can be stored as a flat list for efficiency if dimensions are known,
    or as a dictionary for sparse storage.
    """

    def __init__(self, width: int = 0, height: int = 0):
        """
        Initializes a Frame.
        :param width: Width of the frame in pixels.
        :param height: Height of the frame in pixels.
        """
        self.width = width
        self.height = height
        # Use a list for flat storage if dimensions are known, else fallback to dict
        if width > 0 and height > 0:
            self.pixels = [(0, 0, 0)] * (width * height)
            self.is_flat = True
        else:
            self.pixels: dict[tuple[int, int], tuple[int, int, int]] = {}
            self.is_flat = False

    def __setitem__(self, key: tuple[int, int], value: tuple[int, int, int]):
        """
        Sets the pixel color at the given (x, y) coordinate.
        :param key: A tuple of (x, y) coordinates.
        :param value: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                self.pixels[y * self.width + x] = value
        else:
            self.pixels[key] = value

    def __getitem__(self, key: tuple[int, int]):
        """
        Gets the pixel color at the given (x, y) coordinate.
        :param key: A tuple of (x, y) coordinates.
        :return: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                return self.pixels[y * self.width + x]
            return (0, 0, 0)
        return self.pixels.get(key, (0, 0, 0))

    def __iter__(self):
        """
        Iterates over the coordinates of non-black pixels.
        :return: An iterator of (x, y) tuples.
        """
        if self.is_flat:
            for y in range(self.height):
                for x in range(self.width):
                    if self.pixels[y * self.width + x] != (0, 0, 0):
                        yield (x, y)
        else:
            yield from self.pixels

    def get(self, key: tuple[int, int], default: tuple[int, int, int] = (0, 0, 0)):
        """
        Gets the pixel color at the given (x, y) coordinate with a default value.
        :param key: A tuple of (x, y) coordinates.
        :param default: Default color to return if the pixel is not set.
        :return: A tuple of (R, G, B) color values.
        """
        if self.is_flat:
            x, y = key
            if 0 <= x < self.width and 0 <= y < self.height:
                return self.pixels[y * self.width + x]
            return default
        return self.pixels.get(key, default)

    def __contains__(self, key: tuple[int, int]):
        """
        Checks if the given (x, y) coordinate is within the frame's bounds or set.
        :param key: A tuple of (x, y) coordinates.
        :return: True if the coordinate exists, False otherwise.
        """
        if self.is_flat:
            x, y = key
            return 0 <= x < self.width and 0 <= y < self.height
        return key in self.pixels

    def __repr__(self):
        """
        Returns a string representation of the frame's pixels.
        """
        return str(self.pixels)

    def __len__(self):
        """
        Returns the number of pixels in the frame.
        """
        return len(self.pixels)

    def compare(self, other: "Frame"):
        """
        Compares the current frame with another frame and returns a dictionary of changed cells.
        Each cell (x, vy) corresponds to two pixels.
        """
        changes = {}
        if (
            self.is_flat
            and other.is_flat
            and self.width == other.width
            and self.height == other.height
        ):
            # Optimize for terminal cell comparison (2 pixels at a time)
            self_pixels = self.pixels
            other_pixels = other.pixels
            width = self.width
            for vy in range(self.height // 2):
                base_idx = vy * 2 * width
                idx2_offset = width
                for x in range(width):
                    idx1 = base_idx + x
                    idx2 = idx1 + idx2_offset

                    if (
                        self_pixels[idx1] != other_pixels[idx1]
                        or self_pixels[idx2] != other_pixels[idx2]
                    ):
                        changes[(x, vy)] = (self_pixels[idx1], self_pixels[idx2])
        return changes
