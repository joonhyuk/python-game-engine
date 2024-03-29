"""
Basic "Hello, World!" program in Arcade

This program is designed to demonstrate the basic capabilities
of Arcade. It will:
- Create a game window
- Fill the background with white
- Draw some basic shapes in different colors
- Draw some text in a specified size and color
"""

# Import arcade allows the program to run in Python IDLE
import arcade, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.foundation import *

# Set the width and height of your output window, in pixels
WIDTH = 800
HEIGHT = 600

# Classes
class ArcadeBasic(arcade.Window):
    """Main game window"""

    def __init__(self, width: int, height: int, title: str):
        """Initialize the window to a specific size

        Arguments:
            width {int} -- Width of the window
            height {int} -- Height of the window
            title {str} -- Title for the window
        """

        # Call the parent class constructor
        super().__init__(width, height, title)

        # Set the background window
        arcade.set_background_color(color=arcade.color.WHITE)

    def on_draw(self):
        """Called once per frame to render everything on the screen"""

        # Start rendering
        arcade.start_render()

        # Draw a blue circle with a radius of 50 in the center of the screen
        arcade.draw_circle_filled(
            center_x=WIDTH // 2,
            center_y=HEIGHT // 2,
            radius=50,
            color=arcade.color.BLUE,
            num_segments=50,
        )

        # Draw a red-outlined square in the top-left corner of the screen
        arcade.draw_lrtb_rectangle_outline(
            left=50,
            top=HEIGHT - 50,
            bottom=HEIGHT - 100,
            right=100,
            color=arcade.color.RED,
            border_width=3,
        )

        # Draw an orange caption along the bottom in 60-point font
        arcade.draw_text(
            text="Hello, World! From Arcade!",
            start_x=100,
            start_y=50,
            font_size=28,
            color=arcade.color.ORANGE,
        )
        
    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q and modifiers & arcade.key.MOD_CTRL:
            print('mod is ' + str(modifiers))
            arcade.exit()
        # arcade.draw_text()

class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(WIDTH, HEIGHT, "SCREEN_TITLE")

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        pass
    
    def on_draw(self):
        """Render the screen."""

        self.clear()
        # Code to draw the screen goes here
    

# Run the program
if __name__ == "__main__":
    arcade_game = ArcadeBasic(WIDTH, HEIGHT, "Arcade Basic Game")
    # window = MyGame()
    # window.setup()
    # ag2 = ArcadeBasic(WIDTH / 2, HEIGHT / 2, "ttt")
    arcade.run()