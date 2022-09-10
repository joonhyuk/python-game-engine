from lib.foundation import *

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
        # self.body.physics.shape.filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
        # self.body.physics.shape.filter = pymunk.ShapeFilter(mask=physics_types.allmask^collision.character)
        # print(self.body.physics.shape.filter)

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
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None, lifetime: float = None) -> None:
        super().spawn(spawn_to, position, angle, initial_impulse, lifetime)
        delay_run(self.shrinking_start, self.start_shrink)
        
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


class BigBox(DynamicObject):
    
    def __init__(self, body: DynamicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.shrinking_start = 5
        self.shrinking_delay = 3
        self.alpha = 1.0
        self._temp_multiplier = -1
        
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None, lifetime: float = None) -> None:
        super().spawn(spawn_to, position, angle, initial_impulse, lifetime)
        # delay_run(self.shrinking_start, self.start_shrink)
        schedule_once(self.start_shrink, self.shrinking_start)
    
    def start_shrink(self, dt):
        unschedule(self.start_shrink)
        schedule_interval(self._shrink, 1/60)
        print('box dancing start!')
    
    def _shrink(self, dt):
        if not CONFIG.debug_f_keys[4] :return False
        self.alpha = self.alpha + self._temp_multiplier * dt / self.shrinking_delay
        if self.alpha <= 0:
            self.alpha = 0
            # self.destroy()
            self._temp_multiplier = 1
            return
        if self.alpha > 1:
            self.alpha = 1
            self._temp_multiplier = -1
            return
        alpha = clamp(self.alpha, 0.3, 1)
        self.body.sprite.color = (255, 0, 255, 255 * alpha)
        self.body.scale = alpha


class EscapePlayer(Character):
    
    # __slots__ = ('_fire_counter', 'movement', 'camera')
    
    def __init__(self, hp: float = 100, body: DynamicBody = None, **kwargs) -> None:
        if not body:
            body = DynamicBody(sprite = Sprite(IMG_PATH + 'player_handgun_original.png'),
                               collision_type = collision.character,
                               physics_shape = physics_types.circle(None, 16))
        super().__init__(body, hp, **kwargs)
        self.body.physics.shape.filter = pymunk.ShapeFilter(categories=collision.character)
        self._fire_counter = 0
        self.max_energy = 100
        self.energy = self.max_energy
        self.controller = PlayerController()
        self.movement = MovementHandler()
        
        # self.hidden = TrasferProperty(self.body.hidden)
    
    # hidden = PropertyFrom('body')
    # position = PropertyFrom('body')
    # angle = PropertyFrom('body')
    # velocity = PropertyFrom('body')
    # visibility = PropertyFrom('body')
    
    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        if self._fire_counter % 5 == 0:
            if CONFIG.debug_f_keys[3]: self.test_projectile(1000)
            self._fire_counter = 0
        self._fire_counter += 1
        '''
        빠르게 쏘고 삭제하고를 반복할 경우,
        삭제를 threading.Timer 스레드락 없이 쓰면 아래와 같은 에러가 나온다.
        아마도 쿼리 도는 중에 바디를 삭제해버린게 아닐지.
        
        Aborting due to Chipmunk error: This operation cannot be done safely during a call to cpSpaceStep() or during a query. Put these calls into a post-step callback.
        Failed condition: !space->locked
        Source:Chipmunk2D/src/cpSpace.c:527
        '''
    def test_boost(self, power:float = 1000):
        self.apply_impulse(self.forward_vector * power)
    
    def test_projectile(self, impulse:float = 10000):
        proj = ShrinkingBall()
        # delay_run(2, proj.destroy)
        # proj2 = BallProjectile()
        proj.body.damping = 1.0
        proj.spawn(self.body.layers[0], self.position,
                   initial_impulse= self.forward_vector * impulse)
        
        # print(proj.destroy.__closure__)
        # print('proj.dest ', proj.dest)
        # print(threading.enumerate()
        return proj
    
    def test_directional_attack(self, 
                                target_direction:Vector = None, 
                                thickness = 1.0,
                                distance = 500,
                                muzzle_speed:float = 300,
                                ):
        origin = self.position
        if not target_direction: target_direction = Vector.directional(self.angle)
        end = target_direction * distance + origin
        # self.body.physics.shape.filter = pymunk.ShapeFilter(categories=0b1)
        shape_filter = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^collision.character)
        
        query = ENV.physics_engine.space.segment_query(origin, end, thickness / 2, shape_filter)
        
        if query:
            first_hit = query[0]
            sprite_first_hit:Sprite = ENV.physics_engine.get_object_from_shape(first_hit.shape)
            # sprite_first_hit.color = colors.RED
            print(sprite_first_hit.owner)


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
