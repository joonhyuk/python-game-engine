"""
Show a timer on-screen.

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.timer
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import arcade
from lib.foundation.clock import Clock
from config import *

DEFAULT_SCREEN_WIDTH = 800
DEFAULT_SCREEN_HEIGHT = 600
SCREEN_TITLE = "Timer Example"


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        super().__init__(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT, SCREEN_TITLE)
        
        self.total_time = 0.0
        self.total_time_mash = 0.0
        self.time_diff = 0.0
        self.delta_time = 0.0
        self.output = "00:00:00"
        self.output_mash = "00:00:00"
        self.pause = False
        

    def setup(self):
        """
        Set up the application.
        """
        self.clock = Clock()
        self.clock.timer_start('shoot')
        arcade.set_background_color(arcade.color.ALABAMA_CRIMSON)
        self.total_time = 0.0
        arcade.load_font(RESOURCE_PATH + 'font/AppleII.ttf')
        self.testlabel = arcade.Text('TEST\nFONT', 50, 50, 
                                     width = 10, 
                                     multiline = True, 
                                     font_size = 50, 
                                     font_name = 'Apple ][')
        self.testnumber = arcade.Text('',
                                      DEFAULT_SCREEN_WIDTH // 2, DEFAULT_SCREEN_HEIGHT // 2 + 200,
                                      arcade.color.WHITE, 100,
                                      anchor_x="center")

        
    def on_draw(self):
        """ Use this function to draw everything to the screen. """

        # Start the render. This must happen before any drawing
        # commands. We do NOT need an stop render command.
        self.clear()
        self.testlabel.draw()
        self.testlabel.position = (60, 150)
        # Output the timer text.
        # arcade.draw_text(self.output,
        #                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200,
        #                  arcade.color.WHITE, 100,
        #                  anchor_x="center")
        self.testnumber.value = self.output
        self.testnumber.draw()
        arcade.draw_text(self.output_mash,
                         DEFAULT_SCREEN_WIDTH // 2, DEFAULT_SCREEN_HEIGHT // 2 + 100,
                         arcade.color.YELLOW, 100,
                         anchor_x="center")
        arcade.draw_text(str(self.time_diff),
                         0, DEFAULT_SCREEN_HEIGHT // 2,
                         arcade.color.YELLOW_ORANGE, 100,
                         anchor_x='left')
        arcade.draw_text(str(self.delta_time),
                         0, DEFAULT_SCREEN_HEIGHT // 2 - 100,
                         arcade.color.YELLOW_GREEN, 100,
                         anchor_x='left')
        # arcade.draw_text('test', 
        #                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200, 
        #                  font_size = 50, 
        #                  font_name=RESOURCE_PATH + 'font/AppleII.ttf')

    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        """
        if not self.pause:
            # self.total_time += self.clock.delta_time
            self.total_time += delta_time
            self.delta_time = delta_time
            # self.total_time_mash += self.clock.delta_time
            self.total_time_mash = self.clock.timer_get('shoot')
            self.time_diff = self.total_time - self.total_time_mash
            # self.time_diff = abs(delta_time - self.clock.delta_time)
            # self.time_diff = self.clock.delta_time
            # Calculate minutes
            minutes = int(self.total_time) // 60
            minutes_mash = int(self.total_time_mash) // 60

            # Calculate seconds by using a modulus (remainder)
            seconds = int(self.total_time) % 60
            seconds_mash = int(self.total_time_mash) % 60

            # Calculate 100s of a second
            seconds_100s = int((self.total_time - seconds) * 100)
            seconds_100s_mash = int((self.total_time_mash - seconds_mash) * 100)

            # Figure out our output
            self.output = f"{minutes:02d}:{seconds:02d}:{seconds_100s:02d}"
            self.output_mash = f"{minutes_mash:02d}:{seconds_mash:02d}:{seconds_100s_mash:02d}"
            # self.output_mash = str(self.total_time_mash)
        # self.clock.tick(60)
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.P:
            self.pause = not self.pause
            self.clock.timer_pause_all(self.pause)
        if key in (arcade.key.Q, arcade.key.ESCAPE):
            arcade.exit()
            

def main():
    window = MyGame()
    window.setup()
    ttt = get_iter([123, 456])
    print(ttt, type(ttt))
    arcade.run()


if __name__ == "__main__":
    main()
    arcade.Vector
