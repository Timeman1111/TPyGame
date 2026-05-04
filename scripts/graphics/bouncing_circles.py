"""
This script simulates bouncing circles on the terminal screen.
"""
import tpygame as tpy
import random

class Circle:
    """
    Represents a bouncing circle on the screen.
    """
    def __init__(self, x: int, y: int, radius: int, color: tuple[int, int, int] = (255, 255, 255)):
        """
        Initializes a Circle object.

        :param x: Initial X-coordinate.
        :param y: Initial Y-coordinate.
        :param radius: Radius of the circle.
        :param color: RGB color tuple.
        """

        self.x =x
        self.y = y
        self.radius = radius
        self.color = color

        self.x_vel = 0
        self.y_vel = 0

        self.velocity_timer = random.randint(0, 40)


    def update(self, screen: tpy.render.screen.Screen = None):
        """
        Updates the circle's position based on its velocity.

        :param screen: The Screen object to use for boundary checks.
        """


        self.x += self.x_vel
        self.y += self.y_vel

        if self.x < 0 or self.x > screen.width:
            self.x = round(screen.width / 2)
            self.y = round(screen.height / 2)

            self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


    def draw(self, screen: tpy.render.screen.Screen):
        """
        Draws the circle on the provided screen.

        :param screen: The Screen object to draw on.
        """

        self.update(screen)


        screen.draw_circle(self.x, self.y, self.radius, self.color, fill=True)



def create_circles(n: int, max_x_y: tuple[tuple[int, int], tuple[int, int]], radius: int = 5):
    """
    Creates a list of random Circle objects.

    :param n: Number of circles to create.
    :param max_x_y: Bounds for random X and Y positions.
    :param radius: Radius of each circle.
    :return: A list of Circle objects.
    """
    circles = []

    for i in range(n):

        x = random.randint(max_x_y[0][0], max_x_y[0][1])
        y = random.randint(max_x_y[1][0], max_x_y[1][1])
        circles.append(Circle(x=x, y=y, radius=radius))

    return circles


def main():
    """
    Main entry point for the bouncing circles simulation.
    """

    screen = tpy.render.screen.Screen()
    tpy.render.term_utils.clear()

    circle_count = 200
    circles = create_circles(circle_count, ((0, screen.width), (0, screen.height)), radius = 5)

    ticktimer = {}

    for circle in circles:
        ticktimer[circle] = random.randint(0, 20)

    while True:

        for circle in circles:
            ticktimer[circle] -= 1

            if ticktimer[circle] <= 0:
                circle.x_vel = random.randint(-1, 1)
                circle.y_vel = random.randint(-1, 1)
                ticktimer[circle] = random.randint(0, 20)

            circle.draw(screen)
        screen.refresh()




if __name__ == "__main__":
    main()