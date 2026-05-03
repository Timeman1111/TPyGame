
from collections import deque
import numpy as np
from .image import ImageSurface


class Video:
    """
    Manages a queue of image frames and renders them sequentially using ImageSurface.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initializes the Video object.
        :param x: Initial X-coordinate.
        :param y: Initial Y-coordinate.
        :param width: Target width for all frames.
        :param height: Target height for all frames.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.queue = deque()
        self.cursor = 0

    def input(self, img: np.ndarray):
        """
        Adds a new frame to the video queue.
        :param img: A numpy array representing the image frame.
        """
        # Pre-process the image into an ImageSurface for efficient rendering.
        # This handles resizing once upon input.
        surface = ImageSurface(self.x, self.y, self.width, self.height, img)
        self.queue.append(surface)

    def draw(self, t_screen: 'Screen'):
        """
        Renders the next frame from the queue and advances the cursor.
        :param t_screen: The Screen object to draw on.
        """
        if not self.queue:
            return

        # Get the next frame (FIFO)
        surface = self.queue.popleft()

        # Ensure it's drawn at the Video's current coordinates
        surface.x = self.x
        surface.y = self.y

        surface.draw(t_screen)
        self.cursor += 1

    def reset(self):
        """
        Resets the frame cursor.
        """
        self.cursor = 0

    def move(self, x: int, y: int):
        """
        Updates the position of the object by a specified offset in both the x and y axes.

        :param x: The offset by which the x-coordinate should be incremented.
        :param y: The offset by which the y-coordinate should be incremented.
        :return: None
        """

        self.x += x
        self.y += y


