from lib.foundation import *

class Ball(Pawn):
    
    def __init__(self, 
                 radius = 16, 
                 color = colors.OUTRAGEOUS_ORANGE,
                 hp: float = 100, 
                 mass: float = 1.0,
                 elasticity: float = 0.75, 
                 **kwargs) -> None:
        body = DynamicBody(SpriteCircle(radius, color),
                           mass=mass,
                           collision_type=collision.projectile,
                           elasticity=elasticity,
                           physics_shape=physics_types.circle) 
        super().__init__(body, hp, **kwargs)


class BallProjectile(Ball):
    
    def __init__(self, radius=16, color=colors.OUTRAGEOUS_ORANGE, hp: float = 100, mass: float = 1, elasticity: float = 0.75, **kwargs) -> None:
        super().__init__(radius, color, hp, mass, elasticity, **kwargs)
        # self.body.physics.shape.filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
        # self.body.physics.shape.filter = pymunk.ShapeFilter(mask=physics_types.allmask^collision.character)
        # print(self.body.physics.shape.filter)

class ShrinkingBall(BallProjectile):
    
    def __init__(self, 
                 shrinking_start = 3.0,
                 shrinking_delay = 3.0,
                 ) -> None:
        super().__init__()
        self.shrinking_start = shrinking_start
        self.shrinking_delay = shrinking_delay
        self.alpha = 1.0
    
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None, lifetime: float = None) -> None:
        super().spawn(spawn_to, position, angle, initial_impulse, lifetime)
        delay_run(self.shrinking_start, self.start_shrink)
        
    def start_shrink(self):
        schedule(self._shrink)
    
    def _shrink(self, dt):
        self.alpha -= dt / self.shrinking_delay
        if self.alpha <= 0:
            self.destroy()
            return
        alpha = clamp(self.alpha, 0.1, 1)
        self.body.sprite.color = (255, 0, 255, 255 * alpha)
        self.body.scale = alpha

class BigBox(DynamicObject):
    
    def __init__(self, body: DynamicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)
        self.shrinking_start = 5
        self.shrinking_delay = 10
        self.alpha = 1.0
        
    def spawn(self, spawn_to: ObjectLayer, position: Vector, angle: float = None, initial_impulse: Vector = None, lifetime: float = None) -> None:
        super().spawn(spawn_to, position, angle, initial_impulse, lifetime)
        delay_run(self.shrinking_start, self.start_shrink)
    
    def start_shrink(self):
        schedule(self._shrink)
    
    def _shrink(self, dt):
        self.alpha -= dt / self.shrinking_delay
        if self.alpha <= 0:
            self.destroy()
            return
        alpha = clamp(self.alpha, 0.1, 1)
        self.body.sprite.color = (255, 0, 255, 255 * alpha)
        self.body.scale = alpha
    

class TrasferProperty:
    
    def __init__(self, target:property):
        print(target.__getattribute__())
        self.fget = target.fget
        self.fset = target.fset
        self._name = ''
        
    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(f'unreadable attribute {self._name}')
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError(f"can't set attribute {self._name}")
        self.fset(obj, value)

def find_name_in_mro(cls, name, default):
    "Emulate _PyType_Lookup() in Objects/typeobject.c"
    for base in cls.__mro__:
        if name in vars(base):
            return vars(base)[name]
    return default

class TrasferProperty:
    
    def __init__(self, target:property):
        print(target.__getattribute__())
        self.fget = target.fget
        self.fset = target.fset
        self._name = ''
        
    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError(f'unreadable attribute {self._name}')
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError(f"can't set attribute {self._name}")
        self.fset(obj, value)


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
        
        # self.hidden = TrasferProperty(self.body.hidden)
    
    hidden = PropertyFrom('body')
    position = PropertyFrom('body')
    angle = PropertyFrom('body')
    velocity = PropertyFrom('body')
    visibility = PropertyFrom('body')
    
    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        if self._fire_counter % 6 == 0:
            # self.test_projectile(1000)
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
            sprite_first_hit.color = colors.RED
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
