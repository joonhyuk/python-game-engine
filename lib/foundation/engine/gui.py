import arcade.gui

from .object import *

from config.engine import *


class GUI(arcade.gui.UIManager):
    
    def test_popup(self, text : str = 'hello'):
        label = arcade.gui.UITextArea(
            text = text,
            width = CONFIG.screen_size.x,
            height = CONFIG.screen_size.y,
            font_size = 16,
        )
        