from __future__ import annotations

from config.engine import *
from .engine import *


class StaticBody(PhysicsBody):
    
    __slots__ = ()



class Shadow(GameObject):
    
    def setup(self, **kwargs) -> None:
        self.body = self.owners(BodyHandler)
        return super().setup(**kwargs)
    
    
class Ticker(GameObject):
    
    #WIP
    '''
    Run every tick() of owner's members.
    
    GameObject 스폰에 그냥 기능을 넣어버리는 것은?
    Client에 커플링 시킬거면 컴포넌트로 가는게 맞다.
    '''
    
    __slots__ = 'tick_group', 
    
    def setup(self, **kwargs) -> None:
        self.tick_group: list[Callable] = None
        return super().setup(**kwargs)
    
    def on_spawn(self) -> None:
        self.set_tickers()
        return super().on_spawn()
    
    def on_destroy(self):
        self.tick_group.clear()
        return super().on_destroy()
    
    def set_tickers(self) -> None:
        self.tick_group = []
        for member in self.owner.members:
            if hasattr(member, 'tick') and not isinstance(member, (Ticker, Controller)):
                GAME.tick_group.append(member.tick)
                ''' Coupled with engine '''
    
    def tick(self, delta_time: float) -> bool:
        
        if not self.available: return False
        
        for tick in self.tick_group:
            tick(delta_time)
        
        return True


class SpriteMovement(MovementHandler):
    '''movement component for character'''
    
    # __slots__ = 'size', 'max_speed_run', 'max_speed_walk', 'max_rotation_speed', ''
    
    def __init__(self, 
                 capsule_radius = 16, 
                 max_speed_run = 250, 
                 max_speed_walk = 70, 
                 acceleration = 25, 
                 braking = 20, 
                 max_rotation_speed = 1080, 
                 rotation_interp_speed = 3, 
                 ) -> None:
        super().__init__()
        self.size = capsule_radius
        
        self.max_speed_run = max_speed_run
        ''' pixel per sec '''
        self.max_speed_walk = max_speed_walk
        ''' pixel per sec '''
        self.max_rotation_speed = max_rotation_speed
        ''' degree per sec '''
        self.rotation_interp_speed = rotation_interp_speed
        
        self.acceleration = acceleration
        ''' speed per sec^2 '''
        self._braking = braking if braking is not None else acceleration
        ''' default braking friction. if set to 0, no braking '''
        self._last_tick_speed = 0.0
        self.move_input:Vector = Vector()
        self.desired_rotation:float = 0.0
        
        self._speed_debug_val = avg_generator(0, 60)
        next(self._speed_debug_val)
        self._debug_speedq = []
        self._debug_braking_time = 0
        
    def tick(self, delta_time:float = None) -> bool:
        if not delta_time: return False
        if not super().tick(delta_time): return False
        
        self._set_movement(delta_time)
        self._set_heading(delta_time)
        
        GAME.debug_text['player_speed'] = self.speed_avg // delta_time
        # ENV.debug_text['player_heading'] = self.rotation
    
    def _set_movement(self, delta_time:float):
        ''' set movement of tick by user input '''
        # self._debug_check_speed(delta_time)
        # print(self.speed_avg)
        if self.move_input is None: return False
        if self.move_input.near_zero():
            ''' stop / braking '''
            if self.velocity.is_zero: return False
            # if not self._braking_start_speed:
            #     self._braking_start_speed = self.velocity.length
            
            # if not self.velocity.near_zero(0.01):
            if not math.isclose(self._last_tick_speed, 0, abs_tol=0.01):
                # self.velocity += -1 * self.velocity.unit * min(self.braking * delta_time, self.speed)
                braking_ratio = clamp((1 - self.braking * delta_time / self._last_tick_speed), 0.0, 1.0)
                # print(round(self._debug_braking_time,1) ,braking_ratio)
                self.velocity *= braking_ratio
                # self.velocity = self.velocity - self.velocity.unit * self.braking * delta_time
                self._debug_braking_time += delta_time
                # print(self.speed, round(self.sec_counter, 1))
                return True
            else:
                self.velocity = Vector()
                return False
        
        accel = self.acceleration
        
        max_speed = map_range_attenuation(self.move_input.length, 0.7, 1, 0, self.max_speed_walk, self.max_speed_run)
        max_speed *= self._get_directional_speed_multiplier()
        ''' apply directional speed limit '''
        self.velocity = (self.velocity + self.move_input.unit * accel * delta_time).clamp_length(max_speed * delta_time)
        self._last_tick_speed = self.velocity.length
        self._debug_braking_time = 0.0
        
        ### debug start
        # a = max_speed * delta_time
        # b = self.velocity.length
        # if abs(a - b) > 0.001:
        #     if b > 150:
        #         print('missing something')
        ### debug end
        
        return True
        
    def _debug_check_speed(self, delta_time):
        if len(self._debug_speedq) > 10: self._debug_speedq.pop(0)
        self._debug_speedq.append(self.velocity.length / delta_time)
        print(round(self._debug_braking_time, 1), sum(self._debug_speedq) // len(self._debug_speedq))
    
    @property
    def speed_avg(self):
        return self._speed_debug_val.send(self.velocity.length)
    
    def _set_heading(self, delta_time:float):
        ''' set player rotation per tick '''
        if self.rotation == self.desired_rotation: return False
        if math.isclose(self.rotation, self.desired_rotation):
            self.rotation = self.desired_rotation
            return False

        rot = rinterp_to(self.rotation, self.desired_rotation, delta_time, self.rotation_interp_speed)
        # rot = self.desired_rotation
        self.rotation = get_positive_angle(rot)
        return True
    
    def _get_directional_speed_multiplier(self):
        angle = abs(get_shortest_angle(self.rotation, self.velocity.angle))
        return get_curve_value(angle, CONFIG.directional_speed)
    
    def move(self, input:Vector = Vector()):
        self.move_input = input
        # if not self.desired_velocity.almost_there(input * self.max_speed):
        # if self.velocity.almost_there(self.desired_velocity): return False
        
        # if velocity.is_zero: accel = self.braking
        # else: accel = self.acceleration
    
    def turn_toward(self, abs_position:Vector = Vector()):
        ''' turn character to an absolute position '''
        # print(f'player position {self.owner.position}, mouse position {abs_position}')
        angle = (abs_position - self.owner.position).angle
        self.turn(angle)
    
    def turn_toward_rel(self, rel_position:Vector = Vector()):
        angle = ()
    
    def turn_angle(self, angle:float = 0.0):
        if not angle: return False
        self.desired_rotation += angle
    
    def turn_left(self, angle:float = 0.0):
        ''' turn counter clockwise '''
        return self.turn_angle(angle)
    
    def turn_right(self, angle:float = 0.0):
        ''' turn clockwise '''
        return self.turn_angle(-angle)
    
    def turn(self, rotation:float = 0.0):
        self.desired_rotation = rotation
    
    def stop(self):
        self.move()
    
    # def move_forward(self, speed):
    #     self.owner.body.forward(speed)
    
    def _get_velocity(self) -> Vector:
        return self.owner.velocity
    
    def _set_velocity(self, velocity:Vector = Vector()):
        self.owner.velocity = velocity
    
    velocity:Vector = property(_get_velocity, _set_velocity)
    
    def _get_rotation(self):
        return get_positive_angle(self.owner.angle)
    
    def _set_rotation(self, rotation:float):
        self.owner.angle = get_positive_angle(rotation)
    
    rotation:float = property(_get_rotation, _set_rotation)
    angle:float = property(_get_rotation, _set_rotation)
    
    @property
    def speed(self) -> float:
        ''' speed per sec '''
        return self.speed_tick / GAME.delta_time   # need to be removed
    
    @property
    def speed_tick(self) -> float:
        ''' speed per tick '''
        return self.owner.velocity.length
    
    @property
    def braking(self) -> float:
        if hasattr(self.owner, 'braking_friction'):
            return self._braking * self.owner.braking_friction
        else: return self._braking
    

class PhysicsMovement(MovementHandler):
    ''' movement handler for actor based on pymunk physics engine '''

    __slots__ = 'stopped', 
    
    def __init__(
        self, 
        body:PhysicsBody,
        **kwargs
        ) -> None:
        
        super().__init__(body = body, **kwargs)
        self.stopped = True
    
    # def tick(self, delta_time: float) -> bool:
    #     if not super().tick(delta_time): return False
    #     self._set_movement(delta_time)
    #     self._set_heading(delta_time)
    
    def _set_movement(self, delta_time:float):
        if not self.move_direction: return False
        if self.move_direction.near_zero():
            ''' stop '''
            if self.owner.velocity.is_zero: return False
            if self.owner.velocity.near_zero():
                self.stopped = True
                self.owner.velocity = vectors.zero
        else:
            # self.owner.velocity = self.move_direction * 250
            angle = abs(get_shortest_angle(self.owner.angle, self.owner.velocity.angle))
            # speed = 1000 * get_curve_value(angle, CONFIG.directional_speed)
            speed = 60 ### damping 0, force 10000 => max_spd 166.6 (1/60)
            '''
            위의 속도는 초당 픽셀. 프레임당 픽셀은 speed / fps
            1초간 감소하는 속도의 양은 1 - damping
            물리 계산하기 귀찮은데 선형 회귀를 써야하나;;;
            speed / (1 - damping)
            '''
            # desired_force = speed / (1- ENV.physics_engine.damping)
            # print(desired_force)
            
            if self.stopped:
                ''' 정지 상태에서 가속 '''
                # schedule_once(self._foo_print, 1)
                pass
            
            self.owner.body.apply_force_world(self._get_force(self.move_direction, 250))
            # self.owner.velocity = self.move_direction * 250
            self.stopped = False
    
    def _set_heading(self, delta_time:float):
        ''' set player rotation per tick '''
        if self.owner.angle == self.desired_angle: return False
        if math.isclose(self.owner.angle, self.desired_angle):
            self.owner.angle = self.desired_angle
            return False

        rot = rinterp_to(self.owner.angle, self.desired_angle, delta_time, self.rotation_interp_speed)
        # rot = self.desired_rotation
        self.owner.angle = get_positive_angle(rot)
        return True
    
    def _get_force(self, direction:Vector, speed:float):
        damping = pow(GAME.default_space.damping, 1/60)
        return direction * speed * (1 - damping) * 60 * self.owner.body.mass
    
    def move(self, direction:Vector = vectors.zero):
        self.move_direction = direction
    
    def turn(self, angle:float = 0.0):
        self.desired_angle = angle
    
    def turn_toward(self, abs_position:Vector = Vector()):
        ''' turn character to an absolute position '''
        # print(f'player position {self.owner.position}, mouse position {abs_position}')
        angle = (abs_position - self.owner.position).angle
        self.turn(angle)
    

class NewSpriteMovement(MovementHandler):
    
    pass


class TopDownPhysicsMovement(MovementHandler):
    
    walk = 0
    run = 1
    sprint = 2
    
    def __init__(self, 
                 body:PhysicsBody,
                 max_speeds:tuple = DEFAULT_PAWN_MOVE_SPEEDS,
                 rotation_interp_speed: float = 3,
                 acceleration: float = 4, 
                 **kwargs) -> None:
        super().__init__(body = body, rotation_interp_speed = rotation_interp_speed, **kwargs)
        self.max_speeds = max_speeds
        self.speed_level = self.run
        self.acceleration = acceleration

    @cache
    def _get_force_scalar(self, speed:float):
        damping = pow(self.body.damping, 1/60)
        return speed * (1 - damping) * 60 * self.body.mass
    
    def set_movement(self, delta_time: float):
        self.body.apply_force(self.move_direction * self._get_force_scalar(self.desired_move_speed))
        return True
    
    def set_heading(self, delta_time:float):
        ''' overridable or inheritable method for rotation setting '''
        self.body.angle = get_positive_angle(rinterp_to(self.body.angle,
                                                        self.desired_angle,
                                                        delta_time,
                                                        self.desired_rotation_speed,
                                                        precision = 1
                                                        ))
        return True
    
    @property
    def desired_move_speed(self):
        return self._move_modifier * self.max_speeds[self.speed_level]
    
    @property
    def desired_rotation_speed(self):
        return self._turn_modifier * self.rotation_interp_speed


class AIController(Controller):
    #WIP
    
    __slots__ = 'target', 
    
    def setup(self):
        self.target:Actor = None
        return super().setup()
    
    def on_spawn(self):
        GAME.ai_controllers.append(self)
        return super().on_spawn()
    
    def set_target(self, target):
        self.target = target
    
    def on_destroy(self):
        GAME.ai_controllers.remove(self)
        return super().on_destroy()


class LifeTime(Handler):
    pass


class InteractionHandler(Handler):
    '''
    handling interaction for actor
    그냥 언리얼처럼 컬리전에서 하는게 낫지 않을지?
    '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.others:list[Actor] = []
        
    def begin_overlap(self, other:Actor):
        self.others.append(other)
    
    def end_overlap(self, other:Actor):
        self.others.remove(other)
    

class CameraHandler(Handler):
    '''handling actor camera
    should be possesed by engine camera system'''
    
    # __slots__ = 
    
    def __init__(self,
                 body : BodyHandler,
                 offset:Vector = vectors.zero,
                 interp_speed:float = 0.05,
                 boom_length:float = 200,
                 dynamic_boom:bool = True,
                 max_lag_distance:float = 300,
                 ) -> None:
        super().__init__()
        # self._spawned = False
        self.body:DynamicBody = body
        self.offset:Vector = offset
        self.camera = Camera(*CONFIG.screen_size, max_lag_distance=max_lag_distance)
        self.camera_interp_speed = interp_speed
        self.boom_length = boom_length
        self.dynamic_boom = dynamic_boom
        self.max_lag_distance = max_lag_distance
        # self.owner_has_position = True
    
    # def on_spawn(self):
        # if not hasattr(self.owner, 'position'):
            # self.owner_has_position = False
            # self.set_update(False)  # failsafe, will be removed
    
    def tick(self, delta_time: float) -> bool:
        # if not super().tick(delta_time): return False
        if not self.spawnned: return False
        # ENV.debug_text.perf_check('update_camera')
        self.center = self.body.position
        
        GAME.abs_screen_center = self.center # not cool...
        self.spawnned = False
        # print('camera_tick')
        # ENV.debug_text.perf_check('update_camera')
        return True
        
    def use(self):
        self.spawnned = True
        self.camera.use()
        
    def on_resize(self, new_size:Vector):
        self.camera.resize(*new_size)
    
    def _get_center(self) -> Vector:
        return self.camera.position + CONFIG.screen_size / 2
    
    def _set_center(self, new_center:Vector = Vector()):
        # cam_accel = map_range(self.owner.speed, 500, 1000, 1, 3, True)
        self.camera.move_to(new_center - CONFIG.screen_size / 2 + self.offset + self._get_boom_vector(), self.camera_interp_speed)
    
    center:Vector = property(_get_center, _set_center)
    
    def _get_boom_vector(self) -> Vector:
        # if not self.owner_has_position: return vectors.zero
        if not self.dynamic_boom: return self.body.forward_vector.unit * self.boom_length
        # distv = ENV.cursor_position - ENV.scren_center
        distv = self.body.position - GAME.abs_cursor_position
        # print(self.owner.rel_position, ENV.cursor_position)
        # return Vector()
        alpha = map_range(self.body.speed, 500, 1000, 1, 0, clamped = True)
        
        in_min = GAME.screen_shortside // 5
        in_max = GAME.screen_shortside // 1.2
        ''' 최적화 필요 need optimization '''
        return self.body.forward_vector.unit * self.boom_length * map_range(distv.length, in_min, in_max, 0, 1, clamped=True) * alpha


