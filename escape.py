from config import *
from lib.foundation import *
import random, math

# --- Constants ---
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_COIN = .25
COIN_COUNT = 50

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600




class TitleScreen(View):
    
    def on_show_view(self):
        """run once when switched to"""
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
        # reset viewport
        arcade.set_viewport(0, self.window.width, 0, self.window.height)
        self.shadertoy = Shadertoy(size = self.window.get_framebuffer_size(), main_source = open(RESOURCE_PATH + 'shader/title_planet.glsl').read())
        self.fade_in = 0.5
        self.time = 0
    
    def draw_contents(self):
        self.shadertoy.render(time=self.time)
        arcade.draw_text(PROJECT_NAME, 
                         self.window.width // 2, self.window.height // 2, 
                         arcade.color.CYAN, 
                         font_size = 50, 
                         anchor_x = 'center')
        arcade.draw_text('PRESS ANY KEY' ,
                         self.window.width // 2, self.window.height // 2 - 75, 
                         arcade.color.WHITE, 
                         font_size=20, 
                         anchor_x='center')
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.start_game()
    
    def on_key_press(self, symbol: int, modifiers: int):
        self.start_game()
    
    def on_update(self, delta_time: float):
        self.time += delta_time
        # print('titleview.onupdate')
        # print(CLOCK.delta_time)
        CLOCK.tick()
        
    def start_game(self):
        game = EscapeGameView()
        game.setup()
        self.window.show_view(game)
        
    
class GameScreen(arcade.View):
    def __init__(self):
        """ Initializer """
        # Call the parent class initializer
        super().__init__()

        # Variables that will hold sprite lists
        self.player_list = None
        self.coin_list = None

        # Set up the player info
        self.player_sprite = None
        self.score = 0

        # Don't show the mouse cursor
        self.window.set_mouse_visible(False)

        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()

        # Score
        self.score = 0

        # Set up the player
        # Character image from kenney.nl
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png",
                                           SPRITE_SCALING_PLAYER)
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.player_list.append(self.player_sprite)

        # Create the coins
        for i in range(COIN_COUNT):

            # Create the coin instance
            # Coin image from kenney.nl
            coin = arcade.Sprite(":resources:images/items/coinGold.png",
                                 SPRITE_SCALING_COIN)

            # Position the coin
            coin.center_x = random.randrange(SCREEN_WIDTH)
            coin.center_y = random.randrange(SCREEN_HEIGHT)

            # Add the coin to the lists
            self.coin_list.append(coin)

    def on_draw(self):
        """ Draw everything """
        self.clear()
        self.coin_list.draw()
        self.player_list.draw()

        # Put the text on the screen.
        output = f"Score: {self.score}"
        arcade.draw_text(output, 10, 20, arcade.color.WHITE, 14)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Handle Mouse Motion """

        # Move the center of the player sprite to match the mouse x, y
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y

    def on_key_press(self, symbol: int, modifiers: int):
        return super().on_key_press(symbol, modifiers)
    
    def on_key_release(self, _symbol: int, _modifiers: int):
        return super().on_key_release(_symbol, _modifiers)
    
    def on_update(self, delta_time):
        """ Movement and game logic """
        print('gameview.onupdate')
        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.coin_list.update()

        # Generate a list of all sprites that collided with the player.
        coins_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)

        # Loop through each colliding sprite, remove it, and add to the score.
        for coin in coins_hit_list:
            coin.remove_from_sprite_lists()
            self.score += 1

        # Check length of coin list. If it is zero, flip to the
        # game over view.
        if len(self.coin_list) == 0:
            view = GameOverScreen()
            self.window.show_view(view)

class EscapeGameView(View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        # Sprites and sprite lists
        self.field_list = arcade.SpriteList()
        self.player_sprite = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList()
        self.physics_engine = None

        # Create cameras used for scrolling
        self.camera_sprites = arcade.Camera(*CONFIG.screen_size)
        self.camera_gui = arcade.Camera(*CONFIG.screen_size)
        
        self.mousex = 64
        self.mousey = 64
        self.fps = 0
        self.render_ratio = self.window.render_ratio
        
        self.channel_static = None
        self.channel_dynamic = None
        self.channels:list[arcade.Texture] = [self.channel_static, self.channel_dynamic]
        self.shader = None
        self.light_layer = None
        
    def setup(self):
        
        self.player_sprite = arcade.Sprite(RESOURCE_PATH + '/art/player_handgun.png')
        self.player_sprite.position = -100, -100
        self.player_list.append(self.player_sprite)
        
        self.light_layer = lights.LightLayer(*self.window.get_framebuffer_size())
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.shader = load_shader(RESOURCE_PATH + '/shader/rtshadow.glsl', self.window, self.channels)
        
        self._draw_random_level()
        
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        
            
    def _draw_random_level(self, wall_prob = 0.2):
        field_size = CONFIG.screen_size * 4
        field_center = field_size * 0.5
        
        for x in range(0, field_size.x, 64):
            for y in range(0, field_size.y, 64):
                ground = arcade.Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                
                ground.position = x, y
                ground.color = (30, 30, 30)
                self.field_list.append(ground)
                
                if flip_coin(wall_prob):
                    wall = arcade.Sprite(':resources:images/tiles/boxCrate_double.png', 0.5)
                    
                    wall.position = x, y
                    self.wall_list.append(wall)
        
        for _ in range(30):
            bomb = arcade.Sprite(":resources:images/tiles/bomb.png", 0.125)
            
            placed = False
            while not placed:
                bomb.position = random.randrange(field_size.x), random.randrange(field_size.y)
                if not arcade.check_for_collision_with_list(bomb, self.wall_list):
                    placed = True
            self.bomb_list.append(bomb)

        self.light_layer.add(lights.Light(*field_center, 1200, arcade.color.WHITE, 'soft'))
        
        
    def on_mouse_motion(self, x, y, dx, dy):
        self.mousex = x * self.render_ratio
        self.mousey = y * self.render_ratio
        # print(x, y)
    
    def on_key_press(self, key: int, modifiers: int):
        
        if key in (arcade.key.UP, arcade.key.W):
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        if key in (arcade.key.LEFT, arcade.key.A):
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
            
        if key == arcade.key.F1: CONFIG.fog_of_war = not CONFIG.fog_of_war
    
    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key in (arcade.key.UP, arcade.key.W) or key in (arcade.key.DOWN, arcade.key.S):
            self.player_sprite.change_y = 0
        elif key in (arcade.key.LEFT, arcade.key.A) or key in (arcade.key.RIGHT, arcade.key.D):
            self.player_sprite.change_x = 0
            
        if key == arcade.key.ESCAPE: arcade.exit()
    
    def on_draw(self):

        self.camera_sprites.use()
        # self.use()
        
        # self.channel_static.use()
        # self.channel_static.clear()
        self.channels[0].use()
        self.channels[0].clear()
        self.wall_list.draw()
        
        self.channels[1].use()
        self.channels[1].clear()
        self.field_list.draw()
        self.bomb_list.draw()
        self.wall_list.draw()
        
        
        # self.field_list.draw()
        # self.wall_list.draw()
        # self.bomb_list.draw()
        
        self.window.use()
        
        self.clear()
        
        p = ((self.player_sprite.position[0] - self.camera_sprites.position[0]) * self.render_ratio,
             (self.player_sprite.position[1] - self.camera_sprites.position[1]) * self.render_ratio)

        desired_heading_vector = Vector(self.mousex - p[0], self.mousey - p[1]).normalize()
        desired_heading_angle_rad = math.acos(Vector(0, 1) * desired_heading_vector)
        if desired_heading_vector[0] > 0: desired_heading_angle_rad *= -1
        desired_heading_angle_deg = math.degrees(desired_heading_angle_rad)
        
        # if desired_heading_angle_deg < 0: desired_heading_angle_deg += 360.0
        # self.player_sprite.angle += get_shortest_angle(self.player_sprite.angle, turn_to_angle) * CLOCK.delta_time * 1
        self.player_sprite.angle = rinterp_to(self.player_sprite.angle, desired_heading_angle_deg, CLOCK.delta_time, 5)
        # turn_to_angle = turn_to_angle // 45 * 45
        # self.player_sprite.angle = turn_to_angle
        current_heading_vector = Vector(0, 1).rotate(self.player_sprite.angle)
        # self.player_sprite.angle = math.degrees(pa_rad)
        
        self.shader.program['activated'] = CONFIG.fog_of_war
        self.shader.program['lightPosition'] = p
        self.shader.program['lightSize'] = 500 * self.render_ratio
        self.shader.program['lightAngle'] = 75.0
        self.shader.program['lightDirectionV'] = current_heading_vector
        # self.shader.program['lightDirectionV'] = self.player_sprite.angle
        
        with self.light_layer:
        
            self.shader.render()
            self.player_list.draw()
        
        self.light_layer.draw(ambient_color=(128,128,128))
        
        self.player_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
        
        self.camera_gui.use()
        self.scroll_to_player()
        
    def on_update(self, delta_time: float):
        self.physics_engine.update()
        CLOCK.tick()
        # self.render_ratio = self.window.get_framebuffer_size()[0] / self.window.get_size()[0]   # should be moved to os level hidpi change event
    
    def scroll_to_player(self, speed = 0.1):
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        position = Vector(self.player_sprite.center_x - self.window.width / 2,
                        self.player_sprite.center_y - self.window.height / 2)
        self.camera_sprites.move_to(position, speed)

    
class GameOverScreen(TitleScreen):
    pass

def main():
    CLOCK.use_engine_tick = True
    window = Window(*CONFIG.screen_size, PROJECT_NAME)
    title = TitleScreen()
    window.show_view(title)
    arcade.run()
    
if __name__ == '__main__':
    main()