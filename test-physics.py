'''
DISCLAIMER:

It's dirty nasty testbed.
Never blame anything for the codes below.

Code review for the classes themselves used here is always welcome.

'''

# from lib.foundation import *
from lib.escape import *
# from config.game import *
import config

# from tqdm import tqdm
import gc

VERSION = Version()

SPRITE_SCALING_TILES = 0.5
PLAYER_MOVE_FORCE = 4000
PLAYER_ATTACK_RANGE = 500
PHYSICS_TEST_DEBRIS_NUM = 100
PHYSICS_TEST_DEBRIS_RADIUS = 9


class PhysicsTestView(View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        
        self.space = PhysicsSpace()
        
        self.field_layer = ObjectLayer()
        self.wall_layer = ObjectLayer(self.space)
        
        self.debris_layer = ObjectLayer(self.space)
        self.character_layer = ObjectLayer(self.space)
        self.fx_layer = ObjectLayer(self.space)
        
        self.test_layer = ObjectLayer(self.space)
        
        self.player:EscapePlayer = None
        self.test_npc:RollingRock = None
        self.test_box = None
        
        self.wall_collision_debug_shape = []
        
        self.camera:CameraHandler = None
        GAME.viewport = Camera(*CONFIG.screen_size)
        
        self._tmp = None
        
    def on_show(self):
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)
        
    def setup(self):
        start_loading_time = CLOCK.get_perf()
        self._tmp_actor = None
        
        self.channel_static = None
        self.channel_dynamic = None
        
        self.channels:list[GLTexture] = [self.channel_static, self.channel_dynamic]
        self.shader = load_shader(get_path('data/shader/rtshadow.glsl'), self.window, self.channels)
        
        self.space.damping = 0.01
        
        self.player = EscapePlayer()
        self.player.spawn(self.character_layer, Vector(100, 100))
        self.player.body.sprite.pymunk.max_velocity = CONFIG.terminal_speed
        # self.player.body.physics.friction = 1.0
        # self.player.body.sprite.pymunk.gravity = (0,980)
        # self.player.body.sprite.pymunk.damping = 0.01
        self.camera = self.player.camera
        
        field_start = CLOCK.perf
        self._setup_field(self.field_layer)
        print('FIELD LOADING TIME :',CLOCK.perf - field_start)
        
        wall_start = CLOCK.perf
        self._setup_walls_onecue(self.wall_layer)
        print('WALLS LOADING TIME :',CLOCK.perf - wall_start)
        
        # self._setup_debris_onecue(self.debris_layer)
        
        ### test new method!
        test_simplebody = StaticBody(SpriteCircle(32, colors.YELLOW_GREEN), 
                                     collision_type=collision.none,
                                     elasticity=1.0
                                     )
        test_simplebody2 = StaticBody(SpriteCircle(32, colors.YELLOW_GREEN), 
                                     collision_type=collision.none,
                                     elasticity=1.0
                                     )
        # test_simplebody.position = vectors.zero
        test_simpleactor = StaticObject(test_simplebody).spawn(self.wall_layer, position=Vector(200,200))
        test_simpleactor2 = StaticObject(test_simplebody2).spawn(self.wall_layer, position=Vector(200,568))
        # self._tmp_actor = test_simpleactor
        # test_simpleactor.position = vectors.zero
        # test_simpleactor.spawn(self.test_layer, Vector(300,300))
        # test_simpleactor.body.sprite.remove_from_sprite_lists()
        
        ### DynamicObject.spawn test
        box_body = DynamicBody(Sprite(":resources:images/tiles/grassCenter.png", 1.5),
                               mass = 10, friction=1.0,
                               collision_type=collision.debris,
                               )
        # box = DynamicObject(box_body)
        self.test_box = ShrinkingToy(box_body)
        self.test_box.spawn(self.wall_layer, CONFIG.screen_size / 2)
        # box.body.physics.add_pivot(self.player.body.physics.body, self.player.position, box.position)
        dynamic_fan_blade_body = DynamicBody(
            Sprite(get_path(IMG_PATH + 'test_fan_blade4.png'), scale=2, hit_box_algorithm='Detailed'),
            collision_type=collision.wall,
            shape_type=physics_types.poly, 
            mass=20,
            shape_edge_radius=2)
        
        self.test_rotating_dynamic = DynamicRotatingFan(dynamic_fan_blade_body).spawn(self.wall_layer, Vector(800,200))
        dynamic_fan_blade_body.physics.add_world_pivot(dynamic_fan_blade_body.position)
        dynamic_fan_blade_body.damping = 0.1
        
        kinematic_fan_blade_body = KinematicBody(Sprite(get_path(IMG_PATH + 'test_fan_blade2.png'), scale=2, hit_box_algorithm='Detailed'),
                                                 shape_type=physics_types.poly,
                                                 shape_edge_radius=1)
        self.test_rotating_kinematic:KinematicRotatingFan = KinematicRotatingFan(kinematic_fan_blade_body).spawn(self.wall_layer, Vector(800, 550))
        kinematic_fan_blade_body.physics.angular_velocity = 5
        
        circle_body = DynamicBody(
            # SpriteCircle(48),
            Sprite(':resources:images/animated_characters/female_person/femalePerson_idle.png'),
                                            mass = 7,
                                            friction = 1.2,
                                            collision_type=collision.debris,
                                            shape_type=physics_types.poly,
                                            )
        # print(fan_blade_body.physics.shape)
        
        
        self.test_npc = RollingRock(circle_body,
                                ).spawn(self.debris_layer, Vector(300,550))
        ### DynamicObject.spawn test
        
        def begin_player_hit_wall(player, wall, arbiter, space, data):
            print(get_owner(player), 'begin_hit', get_owner(wall))
            return True
        def pre_player_hit_wall(player, wall, arbiter, space, data):
            print(player, 'pre_hit', wall)
            return True
        def post_player_hit_wall(player, wall, arbiter, space, data):
            print(player, 'post_hit', wall)
        def seperate_player_hit_wall(player, wall, arbiter, space, data):
            print(player, 'seperate_hit', wall)
        
        collision_handler = partial(
            self.space.add_collision_handler, 
            begin_handler=begin_player_hit_wall, 
            pre_handler=pre_player_hit_wall,
            separate_handler=seperate_player_hit_wall,
            post_handler=post_player_hit_wall)
        
        ### Pretty case for dealing with collision handler
        # collision_handler(collision.character, collision.debris)
        
        # self.space.add_collision_handler(collision.character, collision.wall, 
        #                                           begin_handler=begin_player_hit_wall, 
        #                                           pre_handler=pre_player_hit_wall,
        #                                           separate_handler=seperate_player_hit_wall,
        #                                           post_handler=post_player_hit_wall)

        print(f'INITIAL LOADING TIME : {round(CLOCK.perf - start_loading_time, 2)} sec')
        
    def _setup_debris_onecue(self, layer:ObjectLayer):
        '''
        example of actor spawn setting
        '''
        print('setup debris')
        def spawn_rand_pos(actor:DynamicObject):
            placed = False
            while not placed:
                actor.position = random.randrange(CONFIG.screen_size.x), random.randrange(CONFIG.screen_size.y)
                if not arcade.check_for_collision_with_lists(actor.body.sprite, [self.wall_layer, layer]):
                    actor.spawn(layer)
                    placed = True
        
        for _ in tqdm(range(PHYSICS_TEST_DEBRIS_NUM)):
            debri_body = DynamicBody(SpriteCircle(PHYSICS_TEST_DEBRIS_RADIUS, (255,255,0,128)),
                                             mass = 0.5, elasticity = 0.2, friction=1.0,
                                             collision_type = collision.debris)
            debri = SimpleAIObject(debri_body)
            spawn_rand_pos(debri)
    
    def _setup_walls_onecue_master(self, layer:ObjectLayer):
        '''
        example of body spawn setting
        
        '''
        
        for x in range(0, CONFIG.screen_size.x + 1, 64):
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES),
                              Vector(x, 0), 
                              elasticity=0.75,
                              spawn_to = layer)
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES),
                              Vector(x, CONFIG.screen_size.y), 
                              elasticity=0.75,
                              spawn_to = layer)
        
        for y in range(64, CONFIG.screen_size.y, 64):
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES),
                              Vector(0, y), 
                              elasticity=0.75,
                              spawn_to = layer)
            wall = StaticBody(Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES),
                              Vector(CONFIG.screen_size.x, y), 
                              elasticity=0.75,
                              spawn_to = layer)
        
    def _setup_walls_onecue(self, layer:ObjectLayer):
        '''
        make walls without actor or physics body.
        
        '''
        sprite_list:list[Sprite] = []
        for x in range(0, CONFIG.screen_size.x + 1, 64):
            
            sprite = Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES)
            sprite.position = Vector(x, 0)
            sprite_list.append(sprite)
            
            sprite = Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES)
            sprite.position = Vector(x, CONFIG.screen_size.y)
            sprite_list.append(sprite)
        
        for y in range(64, CONFIG.screen_size.y, 64):
            sprite = Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES)
            sprite.position = Vector(0, y)
            sprite_list.append(sprite)
            
            sprite = Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES)
            sprite.position = Vector(x, y)
            sprite_list.append(sprite)
        
        sprite_list.append(
            Sprite(":resources:images/tiles/grassCenter.png", SPRITE_SCALING_TILES, position = Vector(64,256))
        )
        
        layer.extend(sprite_list)
        
        self.wall_collision_debug_shape = self.space.add_static_collison(
            layer, 
            collision_type = collision.wall,
            elasticity=1.0)
        ### for presentation, leaving old one below
        # walls_points:list = []
        # for sprite in sprite_list:
        #     hit_box = sprite.get_hit_box()
        #     pos = sprite.position
        #     scaled_poly = [[int(x * sprite.scale + p) for x, p in zip(z, pos)] for z in hit_box]
        #     walls_points.append(scaled_poly)

        # self.wall_collision_debug_shape = build_convex_shape(self.physics_main.space.static_body, walls_points)
        
    def _setup_field(self, layer:ObjectLayer):
        '''
        example of sprite only setting
        
        '''
        print('setup field floor')
        field_size = 6400
        for x in tqdm(range(-field_size, field_size, 64)):
            for y in range(-field_size, field_size, 64):
                ground = Sprite(':resources:images/tiles/brickTextureWhite.png', 0.5)
                ground.position = x, y
                ground.color = (30, 30, 30)
                layer.add(ground)
    
    def on_key_press(self, key: int, modifiers: int):
        print('key, mod', key, modifiers, keys.DOWN, keys.MOD_OPTION)
        if key == keys.G: 
            self.change_gravity(vectors.zero)
            gc.collect()    ### garbage collect manually
        
        mod_alt = modifiers & keys.MOD_COMMAND or modifiers & keys.MOD_ALT
        
        if key == keys.UP:
            self.change_gravity(vectors.up)
        if key == keys.DOWN:
            self.change_gravity(vectors.down)
        if key == keys.LEFT:
            self.change_gravity(vectors.left)
        if key == keys.RIGHT:
            self.change_gravity(vectors.right)
        
        # if key == keys.SPACE: self.player.test_boost(500)
        
        # if key == keys.H:
        #     self.player.body.physics.hidden = None
        
        if key == keys.I: self._setup_debris_onecue(self.debris_layer)
        
        if key == keys.K:
            self.test_npc.destroy()
            self.test_npc = None
        
        return super().on_key_press(key, modifiers)
    
    def on_key_release(self, key: int, modifiers: int):
        
        return super().on_key_release(key, modifiers)
    
    # def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
    #     ENV.last_mouse_lb_hold_time = CLOCK.perf
    #     ENV.debug_text.timer_start('mouse_lb_hold')
        
    #     self.player.test_directional_attack(distance=PLAYER_ATTACK_RANGE)

    #     # if self._tmp: self._tmp.destroy() # works well
    
    # def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
    #     ENV.last_mouse_lb_hold_time = CLOCK.perf - ENV.last_mouse_lb_hold_time
    #     ENV.debug_text.timer_end('mouse_lb_hold', 3)
        
    #     self._tmp = self.player.test_projectile(map_range(ENV.last_mouse_lb_hold_time, 0, 3, 800, 5000, True))
    #     # delay_run(2, self._tmp.destroy)
    #     # CLOCK.reserve_exec(2, self._tmp.destroy)
        
    #     # self.player.test_directional_attack(distance=PLAYER_ATTACK_RANGE)
    #     # self.line_of_fire_check(self.player.position, self.player.position + self.player.forward_vector * 1000, 5)
    
    def change_gravity(self, direction:Vector) -> None:
        
        if direction == vectors.zero:
            self.space.damping = 0.01
            self.space.gravity = vectors.zero
            return
        
        self.space.gravity = direction * DEFAULT_GRAVITY
        self.space.damping = 1.0
        self.space.activate_objects()
        return
        
    def change_gravity_body(self, body:DynamicBody, direction:Vector) -> None:
        
        if direction == vectors.zero:
            body.damping = 0.01
            body.gravity = vectors.zero
            return
        
        body.gravity = direction * DEFAULT_GRAVITY
        body.damping = 1.0
        body.physics.activate()
        return
        
    def line_of_fire_check(self, origin:Vector, end:Vector, thickness:float = 1, muzzle_speed:float = 500):
        ''' 초고속 발사체(광학병기, 레일건) 체크용. 화학병기 발사체는 발사체를 직접 날려서 충돌체크.
        '''
        self.player.body.physics.filter = pymunk.ShapeFilter(categories=0b1)
        sf = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^0b1)
        query = self.space.space.segment_query(origin, end, thickness / 2, sf)
        query_first = self.space.space.segment_query_first(origin, end, thickness / 2, sf)
        # if query:
        #     for sq in query:
        #         shape = sq.shape
        #         location = sq.point
        #         normal = sq.normal
        #         c1 = SpriteCircle(5, color=(255, 96, 0, 192))
        #         c1.position = location
        #         self.debris_layer.add(c1)
        #         schedule_once(c1.remove_from_sprite_lists, 3)
        
        if query_first:
            qb:pymunk.Body = query_first.shape.body
            iv = (end - origin).unit * muzzle_speed / 2
            iv -= query_first.normal * muzzle_speed / 2
            qb.apply_impulse_at_world_point(iv, query_first.point)
            add_sprite_timeout(SpriteCircle(5, (255, 64, 0, 128)), query_first.point, self.debris_layer, 3)
    
    def on_draw(self):
        GAME.debug_text.perf_check('on_draw')
        super().on_draw()
        
        self.camera.use()
        self.field_layer.draw()
        
        self.channels[0].use()
        self.channels[0].clear()
        self.wall_layer.draw()
        
        self.channels[1].use()
        self.channels[1].clear()
        self.field_layer.draw()
        self.wall_layer.draw()
        self.debris_layer.draw()
        self.character_layer.draw()
        self.fx_layer.draw()
        
        self.test_layer.draw()
        debug_draw_segment(self.player.position, self.player.position + self.player.body.velocity, color = colors.AERO_BLUE)
        debug_draw_segment(self.player.position, self.player.position + self.player.forward_vector * PLAYER_ATTACK_RANGE, colors.RED)
        
        self.shader.program['activated'] = CONFIG.debug_f_keys[0]
        self.shader.program['lightPosition'] = self.player.screen_position * GAME.render_scale
        self.shader.program['lightSize'] = 500 * GAME.render_scale
        self.shader.program['lightAngle'] = 75.0
        self.shader.program['lightDirectionV'] = self.player.body.forward_vector
        
        self.window.use()
        self.clear()
        self.shader.render()

        self.player.draw()
        
        if CONFIG.debug_f_keys[2]:
            self.space.debug_draw_movable_collision()
            self.space.debug_draw_static_collision()
        # self.test_npc.body.physics.draw()
        # self.test_box.body.physics.draw()
        # self.test_rotating_dynamic.body.physics.draw()
        # self.test_rotating_kinematic.body.physics.draw()
        
        # for shape in self.wall_collision_debug_shape:
            # debug_draw_shape(shape, line_color = (255, 0, 0, 255))
        
        GAME.viewport.use()
        # GAME.debug_text['PLAYER_POS'] = self.player.position
        # GAME.debug_text['CAMERA_POS'] = self.camera.center
        GAME.debug_text.perf_check('on_draw')
    
    def on_update(self, delta_time: float):
        # print('-------------->UPDATE',self)
        GAME.debug_text.perf_check('update_game')
        super().on_update(delta_time)
        GAME.debug_text.perf_check('PLAYER_TICK')
        self.player.controller.tick(delta_time)
        self.player.camera.tick(delta_time)
        self.player.movement.tick(delta_time)
        GAME.debug_text.perf_check('PLAYER_TICK')
        
        if self.test_npc: self.test_npc.tick(delta_time)
        self.test_rotating_dynamic.tick(delta_time)
        
        GAME.debug_text.perf_check('AI_TICK')
        for ai_pawn in GAME.ai_controllers:
            ai_pawn.target = self.player
            ai_pawn.tick(delta_time)
            ai_pawn.movement.tick(delta_time)
        GAME.debug_text.perf_check('AI_TICK')
        
        GAME.debug_text.perf_check('update_physics')
        self.space.step(1/60)
        if CONFIG.debug_f_keys[3]:
            grounding = self.player.body.physics.get_grounding()
            # print(self.player.body.physics.get_grounding())
        GAME.debug_text.perf_check('update_physics')
        
        GAME.debug_text.perf_check('resync_objects')
        # self.physics_main.resync_objects()
        # print(self.player.body.physics.segment_query((0,0), CONFIG.screen_size))
        
        # ENV.debug_text['distance'] = rowund(self.player.position.length, 1)
        non_static_objects = self.space._movable_objs
        if non_static_objects:
            for o in non_static_objects:
                o.owner.body.tick(delta_time)
            total = len(non_static_objects)
            # sleeps = list(map(lambda a:a.is_sleeping, self.physics_main.space.bodies)).count(True)
            sleeps = 0
            for a in self.space.bodies:
                if a.is_sleeping: sleeps += 1
            GAME.debug_text['MOVABLE TOTAL/SLEEP'] = f'{total}/{sleeps}'
        GAME.debug_text.perf_check('resync_objects')
        
        # ENV.debug_text.perf_check('update_empty_physics')
        # for pe in self.test_physics_layers:
        #     pe.physics_instance.step(delta_time)
        # ENV.debug_text.perf_check('update_empty_physics')
        GAME.debug_text.show_timer('mouse_lb_hold')
        
        GAME.debug_text['GAMEOBJECT SPAWN/DESTROYED/GC'] = f'{GameObject.spawn_counter - GameObject.destroy_counter}/{GameObject.destroy_counter - GameObject.gc_counter}/{GameObject.gc_counter}'
        
        GAME.debug_text['BODY ALIVE/REMOVED/TRASHED'] = f'{BodyHandler.counter_created - BodyHandler.counter_removed}/{BodyHandler.counter_removed - BodyHandler.counter_gced}/{BodyHandler.counter_gced}'
    
    # def on_resize(self, width: int, height: int):
    #     super().on_resize(width, height)
    #     scale = width / 1024
    #     self.field_layer.rescale(scale)
        GAME.debug_text.perf_check('update_game')


class PlatformerTestView(View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        
        self.physics_engine = PhysicsSpace((0, -980), 1.0)
        self.wall_layer:ObjectLayer = ObjectLayer(self.physics_engine)
        self.debris_layer:ObjectLayer = ObjectLayer(self.physics_engine)
        self.character_layer:ObjectLayer = ObjectLayer(self.physics_engine)
        self.kinematic_layer:ObjectLayer = ObjectLayer(self.physics_engine)
        self.ladder_layer:ObjectLayer = ObjectLayer(self.physics_engine)
        
        # self.player:PlatformerPlayer = None
        
        arcade.set_background_color(arcade.color.AMAZON)
    
    def setup(self):
        map_name = ":resources:/tiled_maps/pymunk_test_map.json"
        tile_map = arcade.load_tilemap(map_name, SPRITE_SCALING_TILES)
        
        # self.wall_layer = tile_map.
        

class WorldTestView(View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        
        self.player:EscapePlayer = None
        ''' will be substitute with spawn object in map '''
        self.world:World = None
        ''' 
        contains everything for game : layers of objects, physics, update() or tick(), draw()
        '''
    def setup(self):
        
        self.player = EscapePlayer()
        self.world = World()
        
    def on_update(self, delta_time: float):
        
        # self.player.tick(delta_time)
        self.world.tick(delta_time)     ### includes player, physics update
        
    def on_draw(self):
        
        self.world.draw()       ### includes player draw(in proper layer)


def main():
    CLOCK.use_engine_tick = True
    
    GAME.set_window(CONFIG.screen_size, CONFIG.screen_title + ' ' + Version().full)
    GAME.set_scene(PhysicsTestView)
    GAME.run()

if __name__ == '__main__':
    main()
    