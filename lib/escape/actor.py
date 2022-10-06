from lib.foundation import *
from .component import *

class Ball(Pawn):
    
    __slots__ = ()
    recycling_bin = []
    
    def __init__(self, 
                 radius = 16, 
                 color = colors.OUTRAGEOUS_ORANGE,
                 hp: float = 100, 
                 mass: float = 1.0,
                 elasticity: float = 0.75, 
                 **kwargs) -> None:
        # if self.recycling_bin:
        #     print('body from',Ball.recycling_bin)
        #     body = Ball.recycling_bin.pop(0)
        #     body.hidden = False
        # else:
        body = DynamicBody(SpriteCircle(radius, color),
                            mass=mass,
                            collision_type=collision.projectile,
                            elasticity=elasticity,
                            physics_shape=physics_types.circle) 
        super().__init__(body, hp, **kwargs)
    
    # def destroy(self) -> bool:
    #     Ball.recycling_bin.append(self.body)
    #     print('body to',Ball.recycling_bin)
    #     self.body.hidden = True
    #     # return super().destroy()


class BallProjectile(Ball):
    
    __slots__ = ()

    def __init__(self, radius=16, color=colors.OUTRAGEOUS_ORANGE, hp: float = 100, mass: float = 1, elasticity: float = 0.75, **kwargs) -> None:
        super().__init__(radius, color, hp, mass, elasticity, **kwargs)
        # self.body.physics.filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
        # self.body.physics.filter = pymunk.ShapeFilter(mask=physics_types.allmask^collision.character)
        # print(self.body.physics.filter)

class ShrinkingBall(BallProjectile):
    
    __slots__ = ('shrinking_start', 'shrinking_delay', 'alpha')

    def __init__(self, 
                 shrinking_start = 3.0,
                 shrinking_delay = 1.0,
                 ) -> None:
        super().__init__()
        self.shrinking_start = shrinking_start
        self.shrinking_delay = shrinking_delay
        self.alpha = 1.0
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None) -> None:
        super().spawn(spawn_to, position, angle, initial_impulse)
        delay_run(self.shrinking_start, self.start_shrink)
        
    def destroy(self) -> None:
        return super().destroy()
    
    def start_shrink(self):
        delay_cancel(self.start_shrink)
        schedule_interval(self._shrink, 1/60)
    
    def _shrink(self, dt):
        self.alpha -= dt / self.shrinking_delay
        if self.alpha <= 0:
            unschedule(self._shrink)
            self.destroy()
            return
        alpha = clamp(self.alpha, 0.1, 1)
        self.body.sprite.color = (255, 0, 255, 255 * alpha)
        self.body.scale = alpha


class ShrinkingToy(DynamicObject):
    
    def __init__(self, body: DynamicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.shrinking_delay = 3
        
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None) -> None:
        # delay_run(self.shrinking_start, self.start_shrink)
        schedule_once(self.start_shrink, self.shrinking_delay)
        return super().spawn(spawn_to, position, angle, initial_impulse)
    
    scaling = TestScaleToggle()
    
    def start_shrink(self, dt):
        self.scaling()


class RollingRock(ShrinkingToy):
    
    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
        
    def tick(self, delta_time: float) -> bool:
        # if not super().tick(delta_time): return False
        if CONFIG.debug_f_keys[5]: self.body.physics.angular_velocity = 7
        return True


class KinematicRotatingFan(KinematicObject):
    
    def __init__(self, body: KinematicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)


class DynamicRotatingFan(DynamicObject):
    
    def tick(self, delta_time: float) -> bool:
        # if not super().tick(delta_time): return False
        if CONFIG.debug_f_keys[5]: 
            self.body.physics.apply_force_at_local_point((0, 10000), (self.body.size.x, 0))
        return True


class EscapePlayer(Character):
    
    # __slots__ = ('_fire_counter', 'movement', 'camera')
    
    def __init__(self, hp: float = 100, body: DynamicBody = None, **kwargs) -> None:
        if not body:
            body = DynamicBody(sprite = Sprite(get_path(IMG_PATH + 'player_handgun_original.png')),
                               collision_type = collision.character,
                               shape_type = pymunk.Circle,
                               shape_edge_radius = -16)
        super().__init__(body, hp, **kwargs)
        self.body.physics.filter = pymunk.ShapeFilter(categories=collision.character)
        self.max_energy = 100
        self.energy = self.max_energy
        self.camera = CameraHandler(body = self.body)
        self.movement = EscapePlayerMovement(body=self.body)
        self.actions = EscapeCharacterActionHandler(body=self.body, movement=self.movement)
        self.controller = EscapePlayerController(movement=self.movement, action=self.actions)
        self.projectile = ShrinkingBall
        
    
    # def tick(self, delta_time: float = None) -> bool:
    #     if not super().tick(delta_time): return False
    #     if self._fire_counter % 5 == 0:
    #         if CONFIG.debug_f_keys[3]: self.test_projectile(1000)
    #         self._fire_counter = 0
    #     self._fire_counter += 1
    #     '''
    #     빠르게 쏘고 삭제하고를 반복할 경우,
    #     삭제를 threading.Timer 스레드락 없이 쓰면 아래와 같은 에러가 나온다.
    #     아마도 쿼리 도는 중에 바디를 삭제해버린게 아닐지.
        
    #     Aborting due to Chipmunk error: This operation cannot be done safely during a call to cpSpaceStep() or during a query. Put these calls into a post-step callback.
    #     Failed condition: !space->locked
    #     Source:Chipmunk2D/src/cpSpace.c:527
    #     '''
    
    def test_directional_attack(self, 
                                target_direction:Vector = None, 
                                thickness = 1.0,
                                distance = 500,
                                muzzle_speed:float = 300,
                                ):
        origin = self.position
        if not target_direction: target_direction = Vector.directional(self.angle)
        end = target_direction * distance + origin
        # self.body.physics.filter = pymunk.ShapeFilter(categories=0b1)
        shape_filter = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^collision.character)
        
        query = self.body.physics.space.segment_query(origin, end, thickness / 2, shape_filter)
        # query = ENV.physics_engine.space.segment_query(origin, end, thickness / 2, shape_filter)
        if query:
            first_hit = query[0]
            sprite_first_hit:Sprite = GAME.default_space.get_object_from_shape(first_hit.shape)
            # sprite_first_hit.color = colors.RED
            # print(sprite_first_hit.owner)


class PlatformerPlayer(EscapePlayer):
    
    def __init__(self, body: DynamicBody = None, hp: float = 100, **kwargs) -> None:
        if not body:
            body = DynamicBody(SpriteCircle(64, colors.AFRICAN_VIOLET),
                               )
        super().__init__(body, hp, **kwargs)
    
    def on_init(self) -> None:
        self.controller = 'WASTED!'
        return super().on_init()


class SimpleAIObject(DynamicObject):
    
    def __init__(self, body: DynamicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.movement = EscapeAIMovement(body=self.body)
        self.actions = TestAIActionComponent(body=self.body, movement=self.movement)
        self.controller = TestAIController(movement=self.movement, action=self.actions)
    
    # def get_components(self, *types: ActorComponent):
        # return super().get_components(*types)
    
    # def tick(self, delta_time: float) -> bool:
    #     print(self, 'ticking')
    #     return super().tick(delta_time)

class Door(Pawn):
    
    def __init__(self, body: DynamicBody, hp: float = 1000, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        self.hp = hp
        self._open = False
        self._locked = False
        self._sealed = False
    
    def _set_open(self):
        if self._open: return False
        if self._locked or self._sealed: return False
        
        self._open = True
        return self._open
    
    def _get_open(self):
        return self._open
    
    open = property(_get_open, _set_open)
