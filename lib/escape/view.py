from lib.foundation import *
from lib.escape.actor import *


class TitleScreen(View):
    def on_show_view(self):
        """run once when switched to"""
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
        # reset viewport
        arcade.set_viewport(0, self.window.width, 0, self.window.height)
        self.shadertoy = Shadertoy(size = self.window.get_framebuffer_size(), main_source = open(get_path('data/shader/title_planet.glsl')).read())
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
    def __init__(self, window: Client = None):
        super().__init__(window)
        # self.window.set_mouse_visible(True)
        # Sprites and sprite lists
        self.field_list = ObjectLayer()
        self.wall_list = ObjectLayer(ENV.physics_engine)
        self.player_list = ObjectLayer(ENV.physics_engine)
        self.npc_list = ObjectLayer(ENV.physics_engine)
        self.bomb_list = ObjectLayer(ENV.physics_engine)
        self.movable_list = ObjectLayer()
        self.physics_simple = None
        
        self.test_layers:list[ObjectLayer] = []
        
        self.barrier_list = None

        # Create cameras used for scrolling
        self.camera_sprites = Camera(*CONFIG.screen_size)
        self.camera_gui = Camera(*CONFIG.screen_size)
        self.camera:CameraHandler = None
        
        self.channel_static = None
        self.channel_dynamic = None
        self.channels:list[GLTexture] = [self.channel_static, self.channel_dynamic]
        self.shader = None
        self.light_layer = None
        
        self.emitter = None
    
    def on_show_view(self):
        # print('view_show')
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
        return super().on_show_view()
    
    def setup(self):
        
        self.physics_complex = PhysicsEngine()
        
        self.player = EscapePlayer()
        self.player.spawn(self.player_list, Vector(100,100))
        self.camera = self.player.camera
        
        self.enemy = Pawn(DynamicBody(Sprite(":resources:images/tiles/boxCrate_double.png", 1),
                                      mass=10,
                                      elasticity=0.8,
                                      collision_type=collision.enemy,
                                      ),
                          
                          )
        self.enemy.spawn(self.npc_list, Vector(-200, -200), 90)
        
        self.light_layer = lights.LightLayer(*self.window.get_framebuffer_size())
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.shader = load_shader(get_path('data/shader/rtshadow.glsl'), self.window, self.channels)
        
        self._set_random_level()
        
        # self._setup_pathfinding()
        
        ENV.physics_engine.add_sprite_list(self.bomb_list, 
                                     friction = 1.0, 
                                     body_type = PhysicsEngine.DYNAMIC, 
                                     collision_type = collision.enemy)

        def player_hit_wall(player, wall, arbiter, space, data):
            print(wall)
            return True
        
        ENV.physics_engine.add_collision_handler(collision.character, collision.enemy, player_hit_wall)
        
    def _set_random_level(self, wall_prob = 0.2):
        field_size = CONFIG.screen_size * 2
        field_center = field_size * 0.5
        
        for _ in range(1):
            layer = ObjectLayer()
            for x in range(-6400, 6400, 64):
                for y in range(-6400, 6400, 64):
                    ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                    ground.position = x, y
                    ground.color = (30, 30, 30)
                    layer.append(ground)
            # layer.append(self.player.body)
            self.test_layers.append(layer)
        
        for x in range(0, field_size.x, 64):
            for y in range(0, field_size.y, 64):
                ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                
                ground.position = x, y
                ground.color = (30, 30, 30)
                self.field_list.append(ground)
                
                if flip_coin(wall_prob):
                    wall = StaticBody(Sprite(':resources:images/tiles/boxCrate_double.png', 0.5),
                                      (x, y),
                                      elasticity=0.75,
                                      spawn_to=self.wall_list)
        
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
                               get_path(IMG_PATH + "smoke.png"), 
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
        
        APP.debug_text.perf_check('draw_layer')
        
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
        # self.emitter.draw()
        
        self.window.use()
        
        self.clear()
        APP.debug_text.perf_check('draw_layer')
        
        
        APP.debug_text.perf_check('draw_shader')
        self.shader.program['activated'] = CONFIG.fog_of_war
        self.shader.program['lightPosition'] = self.player.screen_position * ENV.render_scale
        self.shader.program['lightSize'] = 500 * ENV.render_scale
        self.shader.program['lightAngle'] = 75.0
        self.shader.program['lightDirectionV'] = self.player.body.forward_vector
        
        # with self.light_layer:
        self.shader.render()
        APP.debug_text.perf_check('draw_shader')
        
        self.player_list.draw()
        
        # self.light_layer.draw(ambient_color=(128,128,128))
        
        
        APP.debug_text.perf_check('draw_debug')
        if CONFIG.debug_draw:
            self.player_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
            self.npc_list.draw_hit_boxes(color=(255,255,255,255), line_thickness=1)
        # self.wall_list.draw_hit_boxes(color=(128,128,255,128), line_thickness=1)
            debug_draw_circle(ENV.abs_cursor_position, line_thickness=1, line_color = (0, 255, 0, 128), fill_color= (255, 0, 0, 128))
        # ''' put debug marker to absolute position of mouse cursor '''
        # debug_draw_marker(self.player.rel_position, 16, arcade.color.YELLOW)
            debug_draw_segment(self.player.position, (self.player.position + self.player.body.forward_vector * 500), (512, 0, 0, 128))
        # debug_draw_marker(self.player.position)
        # path = arcade.astar_calculate_path(self.enemy.position, self.player.position, self.barrier_list)
        # if path:
            # arcade.draw_line_strip(path, arcade.color.BLUE, 2)
            # self.enemy.controller.move_path = path
        
        # print(ENV.abs_cursor_position)
        APP.debug_text.perf_check('draw_debug')
        
        self.camera_gui.use()
        
    def on_update(self, delta_time: float):
        # print('view_update')
        if not self.player.is_alive:
            view = GameOverScreen()
            self.window.show_view(view)
        
        # APP.debug_text.perf_start('update_physics')
        # self.physics_simple.update()
        # APP.debug_text.perf_end('update_physics')
        
        # direction = ENV.direction_input
        # if direction: self.player.movement.turn_toward(ENV.direction_input)
        # self.player.movement.move(ENV.move_input)
        # APP.debug_text['player_pos'] = self.player.position
        
        # if self.emitter:
        #     self.emitter.update()
        APP.debug_text.perf_check('update_player')
        
        self.player.tick(delta_time)
        # self.physics_complex.set_velocity(self.player.body, self.player.velocity * 100)
        # self.physics_complex.set_ang
        # self.physics_complex.apply_force(self.player.body, self.player.velocity * 200)
        # print('game tick update', CLOCK.delta_time)
        
        # obj = self.physics_complex.get_physics_object(self.player.body)
        # obj.body._set_angular_velocity(-10)
        # obj.rotation = math.radians(self.player.rotation)
        APP.debug_text.perf_check('update_player')
        
        APP.debug_text.perf_check('update_physics')
        self.physics_complex.step(1/60)
        APP.debug_text.perf_check('update_physics')
        # print(self.player.position, self.enemy.position, self.physics_complex.objects[self.enemy.body].position)
    
    def raycast_fire_check(self, start:Vector = Vector(), target:Vector = Vector()):
        target = ENV.abs_cursor_position
        # bullet = arcade.SpriteSolidColor(500, 2, arcade.color.ORANGE)
        # bullet:arcade.PointList = [Vector(-2,0).rotate(self.player.rotation), 
        #                             Vector(2,0).rotate(self.player.rotation), 
        #                             Vector(2, 500).rotate(self.player.rotation), 
        #                             Vector(-2,500).rotate(self.player.rotation)]
        
        # # print(arcade.has_line_of_sight(start, target.unit * 1000, self.wall_list))
        # print(arcade.get_sprites_at_point(target, self.wall_list))
    
    
class GameOverScreen(TitleScreen):
    pass

