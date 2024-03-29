import random, math
from typing import Tuple
import arcade
import time
from arcade.experimental import Shadertoy, lights
from pyglet.math import Vec2

# Do the math to figure out our screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Ray-casting Demo"

SPRITE_SCALING = 0.5

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.1

PLAYER_MOVEMENT_SPEED = 2
BOMB_COUNT = 30
PLAYING_FIELD_WIDTH = 2560
PLAYING_FIELD_HEIGHT = 1440

class MyGame(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # The shader toy and 'channels' we'll be using
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.render_ratio = 1.0
        self.light_layer = lights.LightLayer(*self.get_framebuffer_size())
        
        self.load_shader()
        
        self.perf_counter = time.perf_counter()
        
        # Sprites and sprite lists
        self.background_sprite_list = arcade.SpriteList()
        self.player_sprite = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList()
        self.physics_engine = None
        
        # Create cameras used for scrolling
        self.camera_sprites = arcade.Camera(width, height)
        self.camera_gui = arcade.Camera(width, height)
        
        self.mousex = 0
        self.mousey = 0
        self.fps = 0
        
        self.generate_sprites()
        
        # Our sample GUI text
        self.score_text = arcade.Text("Score: 0", 10, 10, arcade.color.WHITE, 24)
        self.fps_text = arcade.Text('FPS : 0', 10, 30, arcade.color.CYAN, 24)
        
        arcade.set_background_color(arcade.color.ARMY_GREEN)

    def load_shader(self):
        # Where is the shader file? Must be specified as a path.
        shader_file_path = "_scratch/shaders/rc_test.glsl"

        # Size of the window
        window_size = self.get_framebuffer_size()
        self.render_ratio = window_size[0] / self.get_size()[0]
        
        # Create the shader toy
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )

        # Assign the frame buffers to the channels
        self.shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.shadertoy.channel_1 = self.channel1.color_attachments[0]
    
    def generate_sprites(self):
        
        for x in range(0, PLAYING_FIELD_WIDTH, 128):
            for y in range(0, PLAYING_FIELD_HEIGHT, 128):
                sprite = arcade.Sprite(":resources:images/tiles/brickTextureWhite.png")
                sprite.position = x, y
                sprite.color = (30,30,30)
                self.background_sprite_list.append(sprite)
        
        # -- Set up several columns of walls
        for x in range(0, PLAYING_FIELD_WIDTH, 128):
            for y in range(0, PLAYING_FIELD_HEIGHT, int(128 * SPRITE_SCALING)):
                # Randomly skip a box so the player can find a way through
                if random.random() > 0.5:
                    wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING)
                    wall.center_x = x
                    wall.center_y = y
                    self.wall_list.append(wall)

        # -- Set some hidden bombs in the area
        for i in range(BOMB_COUNT):
            bomb = arcade.Sprite(":resources:images/tiles/bomb.png", 0.25)
            placed = False
            while not placed:
                bomb.center_x = random.randrange(PLAYING_FIELD_WIDTH)
                bomb.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
                if not arcade.check_for_collision_with_list(bomb, self.wall_list):
                    placed = True
            self.bomb_list.append(bomb)

        # Create the player
        # self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png",
        #                                    scale=SPRITE_SCALING)
        self.player_sprite = arcade.Sprite('resources/art/player_handgun.png', scale=1, center_x=30, center_y=66)
        # self.player_sprite.center_x = 256
        # self.player_sprite.center_y = 512
        self.player_list.append(self.player_sprite)

        self.light_layer.add(lights.Light(500,500,500,(255,0,0), 'soft'))
        
        # Physics engine, so we don't run into walls
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

    # def on_draw(self):
    #     self.clear()

    #     self.wall_list.draw()
    #     self.bomb_list.draw()
    #     self.player_list.draw()
    
    def on_draw(self):
        
        # Use our scrolled camera
        self.camera_sprites.use()
        
        # Select the channel 0 frame buffer to draw on
        self.channel0.use()
        self.channel0.clear()
        # Draw the walls
        self.wall_list.draw()

        self.channel1.use()
        self.channel1.clear()
        self.background_sprite_list.draw()
        self.bomb_list.draw()
        self.wall_list.draw()
        
        
        # Select this window to draw on
        self.use()
        # Clear to background color
        self.clear()
        
        # Calculate the light position. We have to subtract the camera position
        # from the player position to get screen-relative coordinates.
        p = ((self.player_sprite.position[0] - self.camera_sprites.position[0]) * self.render_ratio,
             (self.player_sprite.position[1] - self.camera_sprites.position[1]) * self.render_ratio)

        # Set the uniform data
        self.shadertoy.program['lightPosition'] = p
        
        # Run the shader and render to the window
        # self.shadertoy.program['lightPosition'] = self.player_sprite.position
        self.shadertoy.program['lightSize'] = 500
        # self.shadertoy.program['lightDirection'] = 0.0
        self.shadertoy.program['lightAngle'] = 120.0
        # self.shadertoy.program['lightDirection'] = 45
        player_heading_vec_norm = Vec2(self.mousex - p[0], self.mousey - p[1]).normalize()
        self.shadertoy.program['lightDirectionV'] = player_heading_vec_norm
        
        pa_rad = math.acos(Vec2(0, 1).dot(player_heading_vec_norm))
        if player_heading_vec_norm[0] > 0: pa_rad *= -1
        self.player_sprite.angle = math.degrees(pa_rad)
        
        
        with self.light_layer:
            self.shadertoy.render()
            self.player_list.draw()
        
        self.light_layer.draw(ambient_color=(255,255,255))
        self.player_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
                
        # Switch to the un-scrolled camera to draw the GUI with
        self.camera_gui.use()
        # Draw our sample GUI text
        # self.score_text.draw()
        self.fps_text.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mousex = x * self.render_ratio
        self.mousey = y * self.render_ratio
        # print(x, y)
        
    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key in (arcade.key.UP, arcade.key.W):
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        if key in (arcade.key.LEFT, arcade.key.A):
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key in (arcade.key.UP, arcade.key.W) or key in (arcade.key.DOWN, arcade.key.S):
            self.player_sprite.change_y = 0
        elif key in (arcade.key.LEFT, arcade.key.A) or key in (arcade.key.RIGHT, arcade.key.D):
            self.player_sprite.change_x = 0
            
        if key == arcade.key.ESCAPE: arcade.exit()

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.physics_engine.update()
        
        self.scroll_to_player()
        
        # self.fps = 1 / (time.perf_counter() - self.perf_counter)
        self.fps = 1 / delta_time
        
        self.fps_text.text = str(round(self.fps, 1))
        self.perf_counter = time.perf_counter()
        # print(fps)
        # if fps < 45: print('low fps :', fps)
        
    def scroll_to_player(self, speed=CAMERA_SPEED):
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        position = Vec2(self.player_sprite.center_x - self.width / 2,
                        self.player_sprite.center_y - self.height / 2)
        self.camera_sprites.move_to(position, speed)


if __name__ == "__main__":
    MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()