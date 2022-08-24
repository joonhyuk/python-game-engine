from lib.foundation import *


class Player(Actor):
    
    def __init__(self, physics_engine: PhysicsEngine = None, **kwargs) -> None:
        super().__init__(sprite = Sprite(IMG_PATH + 'player_handgun_original.png'), 
                         size = Vector(32, 32), 
                         physics_engine = physics_engine, 
                         mass = 1, 
                         body_type = physics_types.dynamic, 
                         collision_type = collision.character, 
                         physics_shape = physics_types.circle, 
                         **kwargs)
        self.hp = 100
        self.camera = CameraHandler()
        self.movement = PhysicsMovement()

    def tick(self, delta_time: float = None) -> bool:
        if not super().tick(delta_time): return False
        direction = ENV.direction_input
        if direction: self.movement.turn_toward(direction)
        self.movement.move(ENV.move_input)
        ENV.debug_text['player_speed'] = round(self.speed, 1)
        
    def apply_damage(self, damage:float):
        self.hp -= damage
    
    @property
    def is_alive(self) -> bool:
        if self.hp <= 0: return False
        return super().is_alive


class Door(Actor2D):
    def __init__(self, body: Sprite = None, hp:float = 1000, **kwargs) -> None:
        super().__init__(body, **kwargs)
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
