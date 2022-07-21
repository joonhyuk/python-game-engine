from lib.foundation import *
from config import *
import random, math, time


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
        print('[title]key input')
        self.start_game()
    
    def on_key_press(self, symbol: int, modifiers: int):
        print('[title]key input')
        self.start_game()
    
    def on_update(self, delta_time: float):
        self.time += delta_time
        # print('titleview.onupdate')
        # print(CLOCK.delta_time)
        
    def start_game(self):
        game = EscapeGameView()
        game.setup()
        self.window.show_view(game)
        
    
class EscapeGameView(View):
    def __init__(self, window: Window = None):
        super().__init__(window)
        # self.window.set_mouse_visible(True)
        # Sprites and sprite lists
        self.field_list = Layer()
        self.wall_list = Layer()
        self.player_list = Layer()
        self.npc_list = Layer()
        self.bomb_list = Layer()
        self.physics_engine = None

        # Create cameras used for scrolling
        self.camera_sprites = Camera(*CONFIG.screen_size)
        self.camera_gui = Camera(*CONFIG.screen_size)
        self.camera:CameraHandler = None
        
        self.mousex = 64
        self.mousey = 64
        self.fps = 0
        self.render_ratio = self.window.render_ratio
        self.character_heading = None
        
        self.channel_static = None
        self.channel_dynamic = None
        self.channels:list[GLTexture] = [self.channel_static, self.channel_dynamic]
        self.shader = None
        self.light_layer = None
        
        self.debug_timer:float = time.perf_counter()
        
    def setup(self):
        
        self.player = Character2D(Sprite(IMG_PATH + 'player_handgun_original.png'))
        self.player.spawn(Vector(-100, -100), 0, self.player_list)
        self.camera = self.player.camera
        
        self.enemy = Character2D(Sprite(":resources:images/tiles/bomb.png", 1))
        self.enemy.spawn(Vector(500, 500), 90, self.npc_list)
        
        self.light_layer = lights.LightLayer(*self.window.get_framebuffer_size())
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.shader = load_shader(RESOURCE_PATH + '/shader/rtshadow.glsl', self.window, self.channels)
        
        self._set_random_level()
        
        # self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.physics_engine = arcade.PhysicsEngineSimple(self.player.body, (self.wall_list, self.npc_list))

    def _set_random_level(self, wall_prob = 0.2):
        field_size = CONFIG.screen_size * 2
        field_center = field_size * 0.5
        
        for x in range(0, field_size.x, 64):
            for y in range(0, field_size.y, 64):
                ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                
                ground.position = x, y
                ground.color = (30, 30, 30)
                self.field_list.append(ground)
                
                if flip_coin(wall_prob):
                    wall = Sprite(':resources:images/tiles/boxCrate_double.png', 0.5)
                    
                    wall.position = x, y
                    self.wall_list.append(wall)
        
        for _ in range(30):
            bomb = Sprite(":resources:images/tiles/bomb.png", 0.125)
            
            placed = False
            while not placed:
                bomb.position = random.randrange(field_size.x), random.randrange(field_size.y)
                if not arcade.check_for_collision_with_list(bomb, self.wall_list):
                    placed = True
            self.bomb_list.append(bomb)

        self.light_layer.add(lights.Light(*field_center, 1200, arcade.color.WHITE, 'soft'))
    
    def on_key_press(self, key: int, modifiers: int):
        print('[game]key input')
        if key == arcade.key.F1: CONFIG.fog_of_war = not CONFIG.fog_of_war
        
        if key == arcade.key.C:
            self.camera = self.enemy.camera
            self.enemy.camera.camera.position = self.window.current_camera.position

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.ESCAPE: arcade.exit()
        if key == arcade.key.KEY_1: schedule_once(self.test_schedule_func, 1, '1 sec delayed schedule')
        if key == arcade.key.KEY_2: schedule_interval(self.test_schedule_func, 1, '1 sec repeating schedule')
        if key == arcade.key.KEY_3: unschedule(self.test_schedule_func)
        if key == arcade.key.C: 
            self.camera = self.player.camera
            self.player.camera.camera.position = self.window.current_camera.position
    
    def test_schedule_func(self, dt, text:str = 'testing schedule'):
        return print(text)
    
    def on_draw(self):
        self.scroll_to_player()

        # self.camera_sprites.use()
        self.camera.use()
        
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
        self.npc_list.draw()
        
        debug_draw_line(self.player.position, (self.player.position + self.player.forward_vector * 500), (512, 0, 0, 128))
        
        
        # self.field_list.draw()
        # self.wall_list.draw()
        # self.bomb_list.draw()
        
        self.window.use()
        
        self.clear()
        
        # p = ((self.player_sprite.position[0] - self.camera_sprites.position[0]) * self.render_ratio,
        #      (self.player_sprite.position[1] - self.camera_sprites.position[1]) * self.render_ratio)
        # desired_heading_vector = (appio.mouse_input * appio.render_scale - Vector(p)).normalize()
        # print(self.window.direction_input)
        
        
        # self.player_sprite.angle = get_positive_angle(rinterp_to(self.player_sprite.angle, desired_heading_angle_deg, CLOCK.delta_time, 5))
        # self.player.rotation = get_positive_angle(rinterp_to(self.player.rotation, desired_heading_angle_deg, CLOCK.delta_time, 5))

        # current_heading_vector = Vector(0, 1).rotate(self.player_sprite.angle)
        # self.character_heading = current_heading_vector
        # p = (self.player.position - Vector(self.camera.camera.position)) * ENV.render_scale
        
        self.shader.program['activated'] = CONFIG.fog_of_war
        self.shader.program['lightPosition'] = self.player.rel_position * ENV.render_scale
        self.shader.program['lightSize'] = 500 * ENV.render_scale
        self.shader.program['lightAngle'] = 75.0
        self.shader.program['lightDirectionV'] = self.player.forward_vector
        
        with self.light_layer:
        
            self.shader.render()
            self.player_list.draw()
        
        self.light_layer.draw(ambient_color=(128,128,128))
        
        if CONFIG.debug_draw:
            self.player_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
            self.npc_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
        # self.wall_list.draw_hit_boxes(color=(128,128,255,128), line_thickness=1)
        debug_draw_circle(ENV.abs_cursor_position, line_thickness=1, line_color = (0, 255, 0, 128), fill_color= (255, 0, 0, 128))
        ''' put debug marker to absolute position of mouse cursor '''
        # debug_draw_marker(ENV.abs_cursor_position)
        # debug_draw_marker(p, 16, arcade.color.ORANGE)
        debug_draw_marker(self.player.rel_position, 16, arcade.color.YELLOW)
        
        # print(ENV.abs_cursor_position)
        
        self.camera_gui.use()
        
        
    def on_update(self, delta_time: float):
        
        self.physics_engine.update()
        
        p = (self.player.position - Vector(self.camera_sprites.position)) * ENV.render_scale
        desired_heading_vector = (ENV.direction_input - p).normalize()
        # desired_heading_vector = (self.window.direction_input - p).normalize()
        self.desired_heading = desired_heading_vector
        desired_heading_angle_rad = desired_heading_vector.argument(Vector(1,0))
        if desired_heading_vector[1] < 0: desired_heading_angle_rad *= -1
        desired_heading_angle_deg = math.degrees(desired_heading_angle_rad)
        
        cursor_pos = ENV.direction_input + Vector(self.camera_sprites.position)
        # cursor_pos = self.window.direction_input + Vector(self.camera_sprites.position)
        # print(f'cam{self.camera_sprites.position}, mouse{self.window.direction_input}')
        
        
        
        # self.player.movement.turn_angle(desired_heading_angle_deg)
        self.player.movement.turn_toward(ENV.abs_cursor_position)
        self.player.movement.move(ENV.move_input)
        # self.player.movement.move(self.window.move_input)
        
        self.player.tick(delta_time)
        # print('game tick update', CLOCK.delta_time)
        if not self.player.is_alive:
            view = GameOverScreen()
            self.window.show_view(view)
        
    
    def scroll_to_player(self, speed = 0.1):
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """
        # character_position = Vector(self.player_sprite.center_x - self.window.width / 2,
        #                 self.player_sprite.center_y - self.window.height / 2)
        
        character_position = self.player.position - CONFIG.screen_size / 2
        
        # position = character_position
        position = character_position + self.player.forward_vector * 100

        # self.camera_sprites.move_to(position, speed)
        # self.player.camera.camera.move_to(position, speed)

    
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