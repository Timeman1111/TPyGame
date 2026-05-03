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
            self._black = self.pixels[:]  # reusable zero-filled reference list for reset
            self.is_flat = True
        else:
            self.pixels: dict[tuple[int, int], tuple[int, int, int]] = {}
            self._black = None
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

    def reset(self):
        """
        Resets all pixels to (0, 0, 0) in-place, avoiding a new allocation.
        Uses the precomputed _black reference list so no temporary list is created.
        """
        if self.is_flat:
            self.pixels[:] = self._black
        else:
            self.pixels.clear()

    def compare(self, other: "Frame", color_closeness: int = 0, bitrate: int = 0):
        """
        Compares the current frame with another frame and returns a dictionary of changed cells.
        Each cell (x, vy) corresponds to two pixels.
        :param other: The previous frame to compare against.
        :param color_closeness: The threshold for color difference (sum of absolute differences).
        :param bitrate: The maximum number of changed cells to return.
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
            
            count = 0
            for vy in range(self.height // 2):
                base_idx = vy * 2 * width
                idx2_offset = width
                for x in range(width):
                    idx1 = base_idx + x
                    idx2 = idx1 + idx2_offset

                    p1_1, p1_2 = self_pixels[idx1], self_pixels[idx2]
                    p2_1, p2_2 = other_pixels[idx1], other_pixels[idx2]

                    if color_closeness == 0:
                        changed = (p1_1 != p2_1 or p1_2 != p2_2)
                    else:
                        diff1 = abs(p1_1[0]-p2_1[0]) + abs(p1_1[1]-p2_1[1]) + abs(p1_1[2]-p2_1[2])
                        diff2 = abs(p1_2[0]-p2_2[0]) + abs(p1_2[1]-p2_2[1]) + abs(p1_2[2]-p2_2[2])
                        changed = (diff1 > color_closeness or diff2 > color_closeness)

                    if changed:
                        changes[(x, vy)] = (p1_1, p1_2)
                        count += 1
                        if 0 < bitrate <= count:
                            return changes
        return changes
