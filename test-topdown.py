from arcade import Window
from lib.foundation import *
from config import *
import random

class TestCharVanila(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1):
        super().__init__(filename, scale)

class TestCharActor(Actor2D):
    def __init__(self, **kwargs) -> None:
        self.filename = None
        super().__init__(**kwargs)
        self.set_body(Sprite(filename=self.filename))
    
    def spawn(self, actor_list:arcade.SpriteList, lifetime=0) -> None:
        actor_list.append(self.body)
        return super().spawn(lifetime)
        

class MyGame(arcade.Window):
    image_source = ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
    
    def __init__(self):
        super().__init__(*default_settings.screen_size, 'test')
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        
        self.actor_list = None
        self.player_sprite = None
    
    def setup(self):
        self.actor_list = arcade.SpriteList()
        self.player_sprite = arcade.Sprite(self.image_source, 1)
        self.player_sprite.center_x = 64
        self.player_sprite.center_y = 128
        self.actor_list.append(self.player_sprite)
        pass
    
    def test_spawn_character(self):
        # new_char = TestCharVanila(self.image_source, 1)
        new_actor = TestCharActor(filename = self.image_source)
        new_char = new_actor.body
        new_char.center_x = random.randint(0, default_settings.screen_size.x)
        new_char.center_y = random.randint(0, default_settings.screen_size.y)
        # self.actor_list.append(new_char)
        new_actor.spawn(self.actor_list)
    
    def on_draw(self):
        self.clear()
        
        self.actor_list.draw()
    
    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.Q and modifiers & arcade.key.MOD_CTRL:
            arcade.exit()
        
        if symbol == arcade.key.C:
            self.test_spawn_character()
    
def main():
    window = MyGame()
    window.setup()
    arcade.run()
    
if __name__ == '__main__':
    main()