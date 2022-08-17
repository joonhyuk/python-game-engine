from arcade import PymunkPhysicsEngine
from lib.foundation import *
from config import *
import random, math, time

VERSION = Version()

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
        self.field_list = ObjectLayer()
        self.wall_list = ObjectLayer()
        self.player_list = ObjectLayer()
        self.npc_list = ObjectLayer()
        self.bomb_list = ObjectLayer()
        self.movable_list = ObjectLayer()
        self.physics_simple = None
        
        self.test_layers:list[ObjectLayer] = []
        
        self.barrier_list = None

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
        self.emitter = None
    
    def on_show_view(self):
        # print('view_show')
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
        return super().on_show_view()
    
    def setup(self):
        
        self.player = Character2D(Sprite(IMG_PATH + 'player_handgun_original.png'), size = 32)
        # self.player = Character2D(Capsule(24))
        self.player.spawn(Vector(-100, -100), 0, self.player_list, self.movable_list)
        self.camera = self.player.camera
        
        self.enemy = NPC(Sprite(":resources:images/tiles/boxCrate_double.png", 1))
        # self.enemy = NPC(Capsule(64))
        self.enemy.spawn(Vector(-200, -200), 90, self.npc_list, self.movable_list)
        
        self.light_layer = lights.LightLayer(*self.window.get_framebuffer_size())
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.shader = load_shader(RESOURCE_PATH + '/shader/rtshadow.glsl', self.window, self.channels)
        
        self._set_random_level()
        
        # self._setup_pathfinding()
        
        # self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        body =  self.player.body_movement if self.player.body_movement else self.player.body
        self.physics_simple = arcade.PhysicsEngineSimple(body, [self.wall_list, self.npc_list])
        
        self.physics_complex = PhysicsEngine()
        self.physics_complex.add_sprite(self.player.body, 
                                       friction=0.6,
                                       body_type = PhysicsEngine.KINEMATIC, 
                                       moment_of_inertia=PhysicsEngine.MOMENT_INF,
                                       damping=0.01,
                                collision_type=collision.character, 
                                max_velocity=1000)
                                
        self.physics_complex.add_sprite_list(self.wall_list,
                                     friction=0.2, 
                                     collision_type = collision.wall, 
                                     body_type = PhysicsEngine.STATIC)
        
        self.physics_complex.add_sprite_list(self.bomb_list, 
                                     friction = 1.0, 
                                     collision_type = collision.enemy)

        def player_hit_wall(player, wall, arbiter, space, data):
            print(wall)
        
        self.physics_complex.add_collision_handler(collision.character, collision.wall, player_hit_wall)
        
    def _set_random_level(self, wall_prob = 0.2):
        field_size = CONFIG.screen_size * 2
        field_center = field_size * 0.5
        
        # for _ in range(1):
        #     layer = ObjectLayer()
        #     for x in range(-6400, 6400, 64):
        #         for y in range(-6400, 6400, 64):
        #             ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
        #             ground.position = x, y
        #             ground.color = (30, 30, 30)
        #             layer.append(ground)
        #     # layer.append(self.player.body)
        #     self.test_layers.append(layer)
        
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
        
        self.emitter = arcade.Emitter(center_xy=(100, 100), 
                           emit_controller=arcade.EmitBurst(500), 
                           particle_factory=lambda emitter: arcade.LifetimeParticle(
                               IMG_PATH + "smoke.png", 
                               change_xy=arcade.rand_in_circle((0,0), 1.0), 
                               lifetime = 100, 
                               scale = 1, 
                               alpha=128
                           ))
    
    def _setup_pathfinding(self):
        self.barrier_list = arcade.AStarBarrierList(self.enemy.body, 
                                                    self.wall_list, 
                                                    32, -500, 1000, -500, 1000)
        
    
    def on_key_press(self, key: int, modifiers: int):
        # print('[game]key input')
        if key == arcade.key.F1: CONFIG.fog_of_war = not CONFIG.fog_of_war
        
        if key == arcade.key.C:
            self.camera = self.enemy.camera
            self.enemy.camera.camera.position = self.window.current_camera.position
        
        if key == arcade.key.K:
            self.player.hp = 0

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.ESCAPE: arcade.exit()
        if key == arcade.key.KEY_1: schedule_once(self.test_schedule_func, 1, '1 sec delayed schedule')
        if key == arcade.key.KEY_2: schedule_interval(self.test_schedule_func, 1, '1 sec repeating schedule')
        if key == arcade.key.KEY_3: unschedule(self.test_schedule_func)
        if key == arcade.key.C: 
            self.camera = self.player.camera
            self.player.camera.camera.position = self.window.current_camera.position
        if key == arcade.key.F:
            # self.player.body.change_x = -100
            self.physics_complex.apply_force(self.player.body, (10000,0)) 
    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.raycast_fire_check(self.player.position, Vector(x, y))
        
    def test_schedule_func(self, dt, text:str = 'testing schedule'):
        return print(text)
    
    def on_draw(self):
        # print('view_draw')
        self.camera.use()
        
        self.channels[0].use()
        self.channels[0].clear()
        self.wall_list.draw()
        
        self.channels[1].use()
        self.channels[1].clear()
        self.field_list.draw()
        # for layer in self.test_layers:
            # layer.draw()
        self.test_layers[0].draw()
        self.bomb_list.draw()
        self.wall_list.draw()
        self.npc_list.draw()
        self.emitter.draw()
        
        self.window.use()
        
        self.clear()
        
        
        
        self.shader.program['activated'] = CONFIG.fog_of_war
        self.shader.program['lightPosition'] = self.player.rel_position * ENV.render_scale
        self.shader.program['lightSize'] = 500 * ENV.render_scale
        self.shader.program['lightAngle'] = 75.0
        self.shader.program['lightDirectionV'] = self.player.forward_vector
        
        # with self.light_layer:
        
        self.shader.render()
        self.player_list.draw()
        
        # self.light_layer.draw(ambient_color=(128,128,128))
        
        
        if CONFIG.debug_draw:
            self.player_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
            self.npc_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
        # self.wall_list.draw_hit_boxes(color=(128,128,255,128), line_thickness=1)
        debug_draw_circle(ENV.abs_cursor_position, line_thickness=1, line_color = (0, 255, 0, 128), fill_color= (255, 0, 0, 128))
        ''' put debug marker to absolute position of mouse cursor '''
        # debug_draw_marker(self.player.rel_position, 16, arcade.color.YELLOW)
        debug_draw_line(self.player.position, (self.player.position + self.player.forward_vector * 500), (512, 0, 0, 128))
        # debug_draw_marker(self.player.position)
        # path = arcade.astar_calculate_path(self.enemy.position, self.player.position, self.barrier_list)
        # if path:
            # arcade.draw_line_strip(path, arcade.color.BLUE, 2)
            # self.enemy.controller.move_path = path
        
        # print(ENV.abs_cursor_position)
        
        self.camera_gui.use()
        
    def on_update(self, delta_time: float):
        # print('view_update')
        if not self.player.is_alive:
            view = GameOverScreen()
            self.window.show_view(view)
        
        # self.physics_simple.update()
        
        # direction = ENV.direction_input
        # if direction: self.player.movement.turn_toward(ENV.direction_input)
        # self.player.movement.move(ENV.move_input)
        # ENV.debug_text['player_pos'] = self.player.position
        
        if self.emitter:
            self.emitter.update()
        
        self.player.tick(delta_time)
        self.physics_complex.set_velocity(self.player.body, self.player.velocity * 100)
        # self.physics_complex.set_ang
        # self.physics_complex.apply_force(self.player.body, self.player.velocity * 200)
        # print('game tick update', CLOCK.delta_time)
        
        obj = self.physics_complex.get_physics_object(self.player.body)
        # obj.body._set_angular_velocity(-10)
        obj.rotation = math.radians(self.player.rotation)
        
        self.physics_complex.step(1/60)
    
    def raycast_fire_check(self, start:Vector = Vector(), target:Vector = Vector()):
        target = ENV.abs_cursor_position
        # bullet = arcade.SpriteSolidColor(500, 2, arcade.color.ORANGE)
        bullet:arcade.PointList = [Vector(-2,0).rotate(self.player.rotation), 
                                    Vector(2,0).rotate(self.player.rotation), 
                                    Vector(2, 500).rotate(self.player.rotation), 
                                    Vector(-2,500).rotate(self.player.rotation)]
        
        # print(arcade.has_line_of_sight(start, target.unit * 1000, self.wall_list))
        print(arcade.get_sprites_at_point(target, self.wall_list))
    
    
class GameOverScreen(TitleScreen):
    pass


def main():
    CLOCK.use_engine_tick = True
    window = Window(*CONFIG.screen_size, PROJECT_NAME + ' ' + str(VERSION.full))
    title = TitleScreen()
    window.show_view(title)
    arcade.run()


if __name__ == '__main__':
    main()