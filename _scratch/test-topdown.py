import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from arcade import Window
from lib.foundation import *
from config import *
import random, time


class MyWindow(arcade.Window):
    run_counter:int = 0
    
    def __init__(self):
        super().__init__(*default_settings.screen_size, 'test')
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        self.prev_key = None
        self.game = MyGame(self)
        self.title = TitleScreen(self)
        # self.set_update_rate(1/2)
        print(f'init-window[{self.get_run_counter()}]')
    
    def get_run_counter(self):
        rc = self.__class__.run_counter
        self.__class__.run_counter += 1
        return rc
    
    def check_prev_key(self, state:str):
        if self.prev_key:
            print(f'{state} ---------- prev_key is {self.prev_key}')
            self.prev_key = None
    
    def on_show(self):
        print(f'show-window[{self.get_run_counter()}]')
        self.check_prev_key('show-window')
    
    def on_update(self, delta_time: float):
        print(f'update-window[{self.get_run_counter()}]')
        self.check_prev_key('update-window')
    
    def on_draw(self):
        print(f'draw-window[{self.get_run_counter()}]')
        self.check_prev_key('draw-window')
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        print(f'mousebutton-window[{self.get_run_counter()}]')
        
    def on_key_press(self, symbol: int, modifiers: int):
        print(f'keypress-window[{self.get_run_counter()}]')

        
class TitleScreen(arcade.View):
    
    def __init__(self, window: MyWindow = None):
        super().__init__(window)
        self.window = window
    
    def on_show(self):
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)
    
    def on_draw(self):
        self.clear()
        arcade.draw_text('TEST_STRUCTURE',
                         self.window.width // 2, self.window.height // 2,
                         arcade.color.CYAN,
                         font_size=50,
                         anchor_x='center')
        arcade.draw_text('PRESS ANY KEY' ,
                         self.window.width // 2, self.window.height // 2 - 75, 
                         arcade.color.WHITE, 
                         font_size=20, 
                         anchor_x='center')
        
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.start_game()
        
    def on_key_press(self, symbol: int, modifiers: int):
        self.start_game()
    
    def start_game(self):
        print('start or resume game')
        if not self.window.game._setup: self.window.game.setup()
        self.window.game._pause = False
        self.window.show_view(self.window.game)

class MyGame(arcade.View):
    image_source = ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
    
    def __init__(self, window: MyWindow = None):
        super().__init__(window)
        self.window:MyWindow = window
        self.prev_key = None
        self.actor_list = None
        self.player_sprite = None
        self._setup:bool = False
        self.counter:int = 0
        # self.set_update_rate(1/60)
        # self.run_counter = 0
    
    def setup(self):
        print(f'setup-view[{self.window.get_run_counter()}]')
        # self.actor_list = arcade.SpriteList()
        # self.player_sprite = arcade.Sprite(self.image_source, 1)
        # self.player_sprite.center_x = 64
        # self.player_sprite.center_y = 128
        # self.actor_list.append(self.player_sprite)
        # print(f'setup[{self.get_run_counter()}]')
        self._setup = True
        self._pause = False
    
    def test_spawn_character(self):
        # new_char = TestCharVanila(self.image_source, 1)
        # new_actor = TestCharActor(filename = self.image_source)
        # new_actor = TestCircleActor()
        # new_char = new_actor.body
        # new_char.center_x = random.randint(0, default_settings.screen_size.x)
        # new_char.center_y = random.randint(0, default_settings.screen_size.y)
        # self.actor_list.append(new_char)
        # new_actor.spawn(self.actor_list)
        print('spawn_something')
    
    def on_draw(self):
        self.clear()
        arcade.draw_text(str(self.counter) ,
                         self.window.width // 2, self.window.height // 2 - 75, 
                         arcade.color.WHITE, 
                         font_size=20, 
                         anchor_x='center')
        # self.actor_list.draw()
        print(f'draw-view[{self.window.get_run_counter()}]')
        self.check_prev_key('draw-view')
        
    
    def on_key_press(self, symbol: int, modifiers: int):
        print(f'keypress-view[{self.window.get_run_counter()}]')
        if symbol == arcade.key.ESCAPE:
            arcade.exit()
        
        if symbol == arcade.key.P:
            self._pause = True
            self.window.show_view(self.window.title)
        
        if symbol == arcade.key.C:
            self.test_spawn_character()
        self.prev_key = symbol
        
    def on_update(self, delta_time: float):
        print(f'update-view[{self.window.get_run_counter()}]')
        self.check_prev_key('update-view')

        while self._pause:
            pass
        self.counter += 1
        
    def check_prev_key(self, state:str):
        if self.prev_key:
            print(f'{state} ---------- prev_key is {self.prev_key}')
            self.prev_key = None
        
def main():
    window = MyWindow()
    window.show_view(window.title)
    arcade.run()
    
if __name__ == '__main__':
    main()