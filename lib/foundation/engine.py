from __future__ import annotations
"""
framework wrapper for audio / video / control
might be coupled with base framwork(i.e. arcade, pygame, ...)
joonhyuk@me.com
"""

import os
import PIL.Image
import PIL.ImageOps
import PIL.ImageDraw

from dataclasses import dataclass
from typing import Union
from abc import *
from functools import partial, partialmethod, update_wrapper

import arcade
import arcade.key as keys
import arcade.color as colors

from lib.foundation.base import *
from lib.foundation.clock import *
from lib.foundation.physics import *
from lib.foundation.utils import *

from config.engine import *
try:
    from config.game import *
except:
    pass

import psutil
PROCESS = psutil.Process(os.getpid())

class DebugTextLayer(dict, metaclass=SingletonType):
    '''
    use text_obj property to access text attributes
    
    bgcolor not working now
    
    '''
    def __init__(self, 
                 font_name = 'Kenney Mini Square', 
                 font_size = 10, 
                 color = (255,255,255,192),
                 bgcolor = None, 
                 topleft_position:Vector = Vector.diagonal(10) 
                 ):
        self.content = ''
        self._position = topleft_position
    
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.bgcolor = bgcolor
        self.text:arcade.Text = None
        self.width = CONFIG.screen_size.x
        
        self.setup()
    
    def setup(self):
        self.width = CONFIG.screen_size.x
        position = Vector(self._position.x, CONFIG.screen_size.y - self._position.y)
        # position.y = CONFIG.screen_size.y - position.y
        self.text = arcade.Text('', *position, self.color, self.font_size, 
                                font_name=self.font_name, 
                                width = self.width, 
                                anchor_y = 'top', 
                                multiline=True)
    
    def draw(self):
        text = ''
        for k, v in self.items():
            text += ' : '.join((k, str(v)))
            text += '\n'
        self.text.value = text
        self.text.draw()
    
    def _set_topleft_position(self, position:Vector):
        self._position = position
        self.setup()
    
    def _get_topleft_position(self):
        return self._position
    
    def perf_start(self, name:str = 'foo'):
        self[name] = CLOCK.perf
    
    def perf_end(self, name:str = 'foo'):
        self[name] = f'{round((CLOCK.perf - self[name]) * 1000,2)} ms'
    
    def perf_check(self, name:str = 'foo'):
        ''' kinda toggle function '''
        if name in self:
            if isinstance(self[name], float): return self.perf_end(name)
        return self.perf_start(name)
    
    def timer_start(self, name:str = 'foo'):
        self[name] = round(CLOCK.timer_start(name),2)
    
    def timer_end(self, name:str = 'foo', remain_time:float = 1.0):
        self[name] = round(CLOCK.timer_remove(name),2)
        self.remove_item(name, remain_time)
    
    def show_timer(self, name:str = 'foo'):
        if name not in CLOCK.timers: return None
        self[name] = round(CLOCK.timer_get(name),2)
    
    def remove_item(self, name:str = 'foo', delay:float = 0.0):
        def _remove(name:str):
            if name in self: self.pop(name)
        
        if not delay: _remove(name)
        else:
            CLOCK.reserve_exec(delay, self.remove_item, name, 0.0)
    
    position = property(_get_topleft_position, _set_topleft_position)
    ''' topleft position of text box '''


class MObject(object):
    __slots__ = ('id', '_alive', '_lifetime', '_update_tick', '_spawned', 'movable')
    
    def __init__(self, **kwargs) -> None:
        self.id:str = self.get_id()     ### will be deprecated. use id(target) instead.
        """set id by id()"""
        self._alive:bool = True
        """ Object alive state. if not, should be destroyed. 
        Implementation varies by class """
        self._lifetime:float = None
        self._update_tick:bool = True
        """ 틱 활성화 여부 """
        self._spawned = False
        """ 스폰되었는지 여부. False시 tick을 실행하지 않는다. """
        self.movable = False
        ''' can move physically '''
        if kwargs:
            for k in kwargs:
                # setattr(self, k, kwargs[k])
                self.__setattr__(k, kwargs[k])
        self.on_init()
    
    def on_init(self) -> None:
        ''' override me if needed '''
        pass
        
    def get_id(self) -> str:
        return str(id(self))
    
    def spawn(self, lifetime:float = None):
        
        if lifetime is not None:
            self._lifetime = lifetime
        
        if self._lifetime:
            CLOCK.timer_start(self.id)
        
        self._spawned = True
        self.on_spawn()
        return self
    
    def on_spawn(self) -> None:
        ''' override me if needed '''
        pass
    
    def tick(self, delta_time:float) -> bool:
        """alive, ticking check\n
        if false, tick deactivated"""
        if not (self._spawned and self._update_tick and self._alive): return False
        if self._lifetime:
            if self._lifetime > CLOCK.timer_get(self.id):
                return True
            else:
                return self.destroy()
        else:
            '''additional lifecycle management could be here'''
            return True
    
    def set_update(self, switch = True):
        self._update_tick = switch
    
    def destroy(self) -> bool:
        self._spawned = False
        self._alive = False
        CLOCK.timer_remove(self.id)
        # self.on_destroy()
        # del self    # ????? do we need it?
        # SOUND.beep()
        return self.on_destroy()
    
    def delay_destroy(self, dt):
        # print(dt)
        return self.destroy()
    
    def on_destroy(self):
        pass
    
    # def __del__(self):
    #     print('good bye')
    
    def set_kwargs(self, kwargs:dict, keyword:str, default:... = None):
        self.__dict__[keyword] = get_from_dict(kwargs, keyword, default)
    
    @property
    def remain_lifetime(self) -> float:
        if self._lifetime:
            return 1 - CLOCK.timer_get(self.id) / self._lifetime
        else: return 1
    
    @property
    def is_alive(self) -> bool:
        return self._alive


class ActorComponent(MObject):
    '''component base class'''
    __slots__ = ('_owner', 'priority')
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._owner:Union[Actor, ActorComponent] = self
        # spawn = getattr(self, 'spawn', None)
        # if callable(spawn):
        #     print('spawn existence check ', spawn)
        self._spawned = True
        self.priority:int = 0
        ''' tick priority : the higher the earlier  '''
    
    def on_register(self):
        pass
    
    def _get_owner(self) -> Union[Actor, ActorComponent]:
        return self._owner or self
    
    def _set_owner(self, owner:Union[Actor, ActorComponent]):
        self._owner = owner
        self._owner.movable = self.movable
    
    owner:Union[Actor, ActorComponent] = property(_get_owner, _set_owner)


class Actor(MObject):
    ''' can have actor components '''
    __slots__ = ('tick_components', )
    
    # def __init__(self, **kwargs) -> None:
    #     super().__init__(**kwargs)
    #     self.tick_components:list[ActorComponent] = []

    def on_init(self):
        self.tick_components:list[ActorComponent] = []
    
    def spawn(self, lifetime: float = None):
        self.register_components()
        return super().spawn(lifetime)
    
    def get_components(self, *types:ActorComponent):
        if not types: types = ActorComponent
        components:list[ActorComponent] = []    ### type hinting
        if hasattr(self, '__dict__'):    ### for those have only __slots__
            components.extend([c for c in self.__dict__.values() if isinstance(c, types)])
        if hasattr(self, '__slots__'):
            components.extend([getattr(self, c) for c in self.__slots__ if isinstance(getattr(self, c), types)])
        return components
    
    def register_components(self, candidate = (ActorComponent,)):
        components:list[candidate] = []    ### type hinting
        
        components = self.get_components(*candidate)
        
        if components:
            for component in components:
                if hasattr(component, 'owner'): component.owner = self  ### set owner
                if hasattr(component, 'tick'): 
                    if component.tick: self.tick_components.append(component)
                    ''' to disable component tick, put `self.tick = None` into __init__() '''
                if hasattr(component, 'on_register'): component.on_register()
        
        self.tick_components.sort(key = lambda tc:tc.priority, reverse = True)
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        if self.tick_components:
            for ticker in self.tick_components:
                ticker.tick(delta_time)
                # print('character_tick', delta_time)
        return True
    
    def destroy(self) -> bool:
        for component in self.tick_components:
            component.destroy()
        
        self.tick_components = []
        return super().destroy()
    

class Body(ActorComponent):
    
    """
    Base class of 'body'. Combined with transform component/
    """
    
    counter_created = 0 ### for debug. total created
    counter_removed = 0 ### for debug. total destroyed
    counter_gced = 0 ### for debug. total garbage collected
    __slots__ = ('sprite', '_hidden', )
    
    def __init__(self, 
                 sprite:Sprite,
                 position:Vector = None,
                 angle:float = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        Body.counter_created += 1 ### for debug
        
        self.sprite:Sprite = sprite
        self._hidden:bool = False
        
        if position: self.position = position
        if angle: self.angle = angle
    
    def get_ref(self):
        return self.sprite
    
    def __del__(self):
        Body.counter_gced += 1
    
    def spawn(self, spawn_to:ObjectLayer, position:Vector = None, angle:float = None):
        self.sprite.owner = self.owner
        if position is not None: 
            self.position = position
        if angle is not None:
            self.angle = angle
        
        spawn_to.add(self)
        return super().spawn()
    
    def draw(self, *args, **kwargs):
        self.sprite.draw(*args, **kwargs)
    
    def _hide(self, switch:bool = None) -> bool:
        ''' hide sprite and physics if exist and return switch '''
        if switch is None: switch = not self.hidden
        self.visibility = not switch
        return switch
    
    def _get_hidden(self) -> bool:
        return self._hidden
    
    def _set_hidden(self, switch:bool = None):
        ''' hide sprite and physics body '''
        self._hidden = self._hide(switch)
    
    hidden:bool = property(_get_hidden, _set_hidden)
    
    def destroy(self) -> bool:
        Body.counter_removed += 1
        self.sprite.remove_from_sprite_lists()
        return super().destroy()
    
    def _set_owner(self, owner):
        super()._set_owner(owner)
        self.sprite.owner = self.owner
    
    owner = property(ActorComponent._get_owner, _set_owner)
    
    def _get_visibility(self) -> bool:
        return self.sprite.visible
    
    def _set_visibility(self, switch:bool = None):
        if switch is None: switch = not self.sprite.visible
        self.sprite.visible = switch
    
    visibility:bool = property(_get_visibility, _set_visibility)
    ''' set None to toggle visibility '''
    
    def _get_position(self):
        return self.get_ref().position
    
    def _set_position(self, position):
        self.get_ref().position = position
    
    position:Vector = property(_get_position, _set_position)
    
    def _get_angle(self) -> float:
        return self.get_ref().angle
    
    def _set_angle(self, angle:float = 0.0):
        self.get_ref().angle = angle
    
    angle:float = property(_get_angle, _set_angle)
    
    def _get_veloticy(self) -> Vector:
        return self.get_ref().velocity
    
    def _set_velocity(self, velocity):
        self.get_ref().velocity = velocity
    
    velocity:Vector = property(_get_veloticy, _set_velocity)
    
    def _get_scale(self) -> float:
        return self.sprite.relative_scale
    
    def _set_scale(self, scale:float):
        self.sprite.relative_scale = scale
    
    scale = property(_get_scale, _set_scale)
    
    @property
    def speed(self) -> float :
        ''' different according to physics or sprite 
        
        :physics = per sec
        :sprite = per tick
        '''
        return self.velocity.length
    
    @property
    def forward_vector(self) -> Vector:
        return Vector.directional(self.angle)
    
    @property
    def size(self) -> Vector:
        return Vector(self.sprite.width, self.sprite.height)
    
    @property
    def layers(self) -> list[ObjectLayer]:
        ''' Layers(ObjectLayer list) where this body is '''
        return self.sprite.sprite_lists


class MovementHandler(ActorComponent):
    #WIP
    ''' need body component to move 
    
    Move:
    - with direction and speed
    - with force
    - toward a position
    
    Turn:
    - by some degrees
    - to a certain degrees
    - by rotational force
    - toward a position
    
    Warp:
    - to a position
    
    '''
    def __init__(self, 
                 rotation_interp_speed:float = 3.0,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Body = None

        self.move_direction:Vector = None
        ''' direction unit vector for movement '''
        self.desired_angle:float = None
        self.rotation_interp_speed = rotation_interp_speed
        
        self._move_modifier:float = 1.0
        self._turn_modifier:float = 1.0
        self.priority = 8
        
    @property
    def move_lock(self):
        return math.isclose(self._move_modifier, 0.0, abs_tol=0.001)
    
    @property
    def turn_lock(self):
        return math.isclose(self._turn_modifier, 0.0, abs_tol=0.001)
    
    def on_register(self):
        body:list[Body] = self.owner.get_components(Body)
        if not body or len(body) > 1:
            raise Exception('MovementHandler needs only one Body')
        elif not body[0].movable:
            raise Exception('Body should be movable')
        self.body = body[0]
        self.desired_angle = self.body.angle
        # self.owner.move = self.move
        """
        이동에 필요한 것이 없으면 비활성화 시켜야 함.
        """
    
    def tick(self, delta_time:float) -> bool:
        if not super().tick(delta_time): return False
        self._set_heading(delta_time)
        self._set_movement(delta_time)
        return True
    
    def _set_movement(self, delta_time:float):
        if not self.move_direction: return False
        if self.move_direction.near_zero():
            ''' stop '''
            if self.body.velocity.is_zero: return False
            if self.body.velocity.near_zero():
                self.body.velocity = vectors.zero
                return False
        if self.move_lock: return False
        
        return self.set_movement(delta_time)
    
    def _set_heading(self, delta_time:float):
        if self.body.angle == self.desired_angle: return False
        if math.isclose(self.body.angle, self.desired_angle):
            self.body.angle = self.desired_angle
            return False
        if self.turn_lock: return False
        
        return self.set_heading(delta_time)
    
    @abstractmethod
    def set_movement(self, delta_time:float):
        ''' overridable method for movement setting '''
        return True
    
    @abstractmethod
    def set_heading(self, delta_time:float):
        ''' overridable or inheritable method for rotation setting '''
        return True
    
    def move_to_position(self, destination:Vector):
        #WIP
        ''' move to position '''
        cur_move_vec = destination - self.body.position
        self.move(cur_move_vec)
    
    def move_toward(self, direction:Vector, speed:float):
        force = direction 
        pass
    
    def move(self, force:Vector):
        self.owner.apply_force(force)
        pass
    
    def move_forward(self):
        # self.move_towa
        pass
    
    def turn(self, angle:float = 0.0):
        self.desired_angle = angle
    
    def turn_by(self, angle_diff:float = 0.0):
        self.desired_angle += angle_diff
    
    def turn_toward(self, direction:Vector = None):
        if not direction: return False
        self.desired_angle = direction.angle
    
    def turn_to_position(self, destination:Vector = None):
        if not destination: return False
        angle = (destination - self.body.position).angle
        self.turn(angle)
        
    def move_toward(self, destination:Vector):
        self.move_to_position(destination)
        self.turn_to_position(destination)
    
    def warp(self, position:Vector, angle:float):
        pass
    

class PawnController(ActorComponent):
    #WIP
    """
    액터 컴포넌트로 만들지 않아도 되지 않을까.
    어차피 컨트롤러니까 앱 혹은 ENV에 등록해두고... 즉, 액터의 owner가 되는거지.
    액션을 수행할 body와 움직임을 제어할 movement는 있어야 하므로 pawn부터 붙을 수 있음.
    즉, 게임에서 ai를 가질 수 있는 것은 pawn부터.
    pawn에 controller를 붙이면 character가 된다.
    
    입력(조작) 혹은 명령(조건에 따른)에 의해 액터의 의지인양 움직이는 것.
    (리액션은 컨트롤러가 책임지지 않음.)
    
    PlayerController(조작에 의한 직접 행동제어)
    AIController(조건에 의한 자동 행동제어)
    ObjectController(조작에 의한 간접 행동제어)
    
    행동의 주체가 되는 Actor는 '행동'을 가져야 한다.
    '행동'은 이동과 액션, 인터렉션으로 구분된다.
    이동은 MovementHandler를 통하거나 직접 스프라이트를 setpos하는 것.
    액션은 다양.
    
    view의 on_input에 app의 player_controller의 on_input이 함께 실행되어 필요한 것 들을 한다.
    매 업데이트 틱(캐릭터 틱)에 tick이 실행되어 부가적인 작업들을 한다?
    
    
    """
    ''' actor component which control actor.
    get env.inputs, set movement, action
    movement <- body
    action <- actor, body
    
    - handles inputs maybe.
    '''
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Body = None
        self.movement:MovementHandler = None
        self.priority = 9
        ''' for reactivity '''
    
    def on_register(self):
        
        self.actions = self.owner.get_components(ActionHandler)[0]
        self.body = self.owner.get_components(Body)[0]
        self.movement = self.owner.get_components(MovementHandler)[0]
        
        if not self.body or not self.movement:
            raise Exception('Controller needs Body and Movement')
    
    def possess(self, actor:Actor):
        # if actor is not valid: return False
        if self.owner == actor: return False
        else:
            # self.owner.get_components(PawnController) = None
            self.owner = actor
    

class ActionHandler(ActorComponent):
    '''
    Action : custom functions for owner
    기본 액션을 미리 정의해 놓는게 나을지?
    attack, evade, open(이건 인터렉션이잖아...)
    컨트롤러에서 실행시키는 방식. 이름 커맨드로 할지 아니면 미리 정의해놓은 키워드로 하는게 나을지?
    
    '''
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.body:Body = None
        self.movement:MovementHandler = None
        self._locked = False
        self.locked_actions:list[type] = []
    
    def on_register(self):
        self.body:Body = self.owner.get_components(Body)[0]
        self.movement:MovementHandler = self.owner.get_components(MovementHandler)[0]
    
    def _get_global_lock(self):
        return self._locked
    
    def _set_global_lock(self, switch:bool = None):
        if switch is None: switch = not self._locked
        self._locked = switch
    
    global_lock:bool = property(_get_global_lock, _set_global_lock)


class ActionFunction(partial):
    ''' Wrapper for partial. Just in case of needed later. '''
    pass


class Action:
    ''' Base class of action.
    
    (WIP: support type hint on do function.)
    
    :self.setup(): setting 'local' variable
    :self.do(): action function
    
    '''
    
    def __init__(self, *args, **kwargs) -> None:
        # self.do = update_wrapper(self.do, self.do)
        self.owner = None
        self.setup(*args, **kwargs)
    
    def __set_name__(self, owner, name):
        # setattr(owner, 'act_'+name, self)
        self.name = name
    
    def __get__(self, owner:Union[Actor, ActionHandler], objtype = None):
        if isinstance(owner, ActionHandler):
            if owner.global_lock or self.__class__ in owner.locked_actions:
                return self.void
                # return lambda x, *args, **kwargs:x    ### return empty function. not good for performance
        
        func = ActionFunction(self.do, owner)
        return func
    
    def setup(self, *args, **kwargs):
        ''' set up additional vars '''
        pass
    
    def void(self, *args, **kwargs):
        ''' empty function for locked situation '''
        pass
    
    def lock_global(self, owner:Union[Actor, ActionHandler]):
        if isinstance(owner, Actor):
            raise Exception('actor could not be locked')
        owner.global_lock = True
        
    def unlock_global(self, dt, owner:Union[Actor, ActionHandler]):
        if isinstance(owner,ActionHandler):
            owner.global_lock = False
    
    def lock(self, owner:ActionHandler, *action_types):
        if not action_types: action_types = (self.__class__, )
        owner.locked_actions.extend(action_types)
    
    def unlock(self, owner:ActionHandler, *action_types):
        if not action_types: action_types = (self.__class__, )
        for at in action_types:
            owner.locked_actions.remove(at)
    
    def delayed_unlock(self, dt, owner:ActionHandler, *action_types):
        return self.unlock(owner, *action_types)
        if not action_types: action_types = (self.__class__, )
        for at in action_types:
            owner.locked_actions.remove(at)
    
    def lock_for(self, owner:ActionHandler, duration:float, *action_types):
        self.lock(owner, *action_types)
        schedule_once(self.delayed_unlock, duration, owner, *action_types)
    
    
    @abstractmethod
    def do(self, owner:Union[Actor, ActionHandler], *args, **kwargs):
        return True
    

class TAction(Callable):
    ''' NOT USED. just for reference '''
    timeline = (0.3, 0.25, 0.5)
    
    def __init__(self) -> None:
        self.owner:Actor = None
        pass
    
    def __set_name__(self, owner, name):
        self.owner:ActionHandler = owner
        self.name = name
    
    def __call__(self, *args, **kwds) -> None:
        self.do(*args, **kwds)
    
    @abstractmethod
    def do(self, *args, **kwargs):
        pass


class Window(arcade.Window):
    
    def on_show(self):
        if GAME.gamepad: self.set_mouse_visible(False)
        GAME.debug_text['FPS'] = 0
        GAME.debug_text['MEMORY_USAGE'] = ""
        GAME.debug_text['UPTIME'] = ""
        
    def on_update(self, delta_time: float):
        
        GAME.delta_time = delta_time
        
        scheduler_count = pyglet_clock._schedule_interval_items.__len__()
        
        CLOCK.fps_current = 1 / delta_time
        GAME.debug_text['FPS'] = CLOCK.fps_average
        GAME.debug_text['MEMORY_USAGE'] = str(round(PROCESS.memory_info()[0]/(1024*1024),2))+" MB"
        GAME.debug_text['UPTIME'] = CLOCK.uptime
        GAME.debug_text['SCHEDULER'] = scheduler_count
        
    def on_draw(self):
        
        GAME.debug_text.draw()
    
    def on_resize(self, width: float, height: float):
        ### broken now. maybe arcade bug
        super().on_resize(width, height)
        resizing = Vector(width, height)
        tmp_scale = width / 1024
        print(self._ctx.projection_2d)
        GAME.set_screen()
        GAME.player_controller.owner.camera.camera.scale = 1 / tmp_scale
        
        # CLIENT.viewport.resize(*resizing * tmp_scale)
        GAME.player_controller.owner.camera.on_resize(resizing / tmp_scale)


class View(arcade.View):
    
    def __init__(self, window: Window = None):
        super().__init__(window)
        self.fade_out = 0.0
        self.fade_in = 0.0
        self.fade_alpha = 1

    def setup(self):
        pass
        
    def draw_tint(self, alpha = 0.0, color = (0, 0, 0)):
        arcade.draw_rectangle_filled(self.window.width / 2, self.window.height / 2,
                                     self.window.width, self.window.height,
                                     (*color, alpha * 255))
    
    def draw_contents(self):
        pass
    
    def on_draw(self):
        self.clear()
        self.draw_contents()
        if self.fade_in > 0 or self.fade_out > 0:
            # self.fade_alpha = finterp_to(self.fade_alpha, )
            self.draw_tint()
    
    def go_next(self, next_screen:arcade.View):
        if self.fade_out:
            pass
        
    def go_after_fade_out(self, next_screen:arcade.View):
        pass
    
    def on_update(self, delta_time: float):
        GAME.delta_time = delta_time


class Sprite(arcade.Sprite):
    
    __slots__ = ('owner', 'collide_with_radius', '_initial_scale', '_relative_scale')
    
    def __init__(self, 
                 filename: str = None, 
                 scale: float = 1, 
                 image_x: float = 0, image_y: float = 0, image_width: float = 0, image_height: float = 0, 
                 center_x: float = 0, center_y: float = 0, 
                 repeat_count_x: int = 1, repeat_count_y: int = 1, 
                 flipped_horizontally: bool = False, flipped_vertically: bool = False, flipped_diagonally: bool = False, 
                 hit_box_algorithm: str = "Detailed", hit_box_detail: float = 4.5, 
                 texture: arcade.Texture = None, 
                 angle: float = 0,
                 ):
        super().__init__(filename, scale, image_x, image_y, image_width, image_height, center_x, center_y, repeat_count_x, repeat_count_y, flipped_horizontally, flipped_vertically, flipped_diagonally, hit_box_algorithm, hit_box_detail, texture, angle)
        self.owner = None
        self._initial_scale = scale
        self._relative_scale = 1.0
        self.collides_with_radius = False   ### will be deprecated

    def scheduled_remove_from_sprite_lists(self, dt):
        # print('REMOVING!')
        return super().remove_from_sprite_lists()
    
    def _get_relative_scale(self) -> float:
        return self._relative_scale
    
    def _set_relative_scale(self, scale:float):
        self._relative_scale = scale
        self.scale = self._initial_scale * self._relative_scale
        # print(self, 'SCALE :::', self.scale)
    
    relative_scale = property(_get_relative_scale, _set_relative_scale)
    
    def _get_hidden(self):
        return not self.visible
    
    def _set_hidden(self, switch:bool = None):
        if switch is None: switch = self.visible
        self.visible = not switch
    
    hidden:bool = property(_get_hidden, _set_hidden)
    

class Old_SpriteCircle(arcade.SpriteCircle, Sprite):
    
    __slots__ = ('owner', )
    
    def __init__(self, 
                 radius: int = 16, 
                 color: tuple = colors.ALLOY_ORANGE, 
                 soft: bool = False):
        self.owner = None
        super().__init__(radius, color, soft)


class SpriteCircle(Sprite):
    ''' If ellipse, make sure to set physics_shape as poly '''
    # __slots__ = ['owner', 'texture', '_points']   ### sprite not works if set with slots.
    
    def __init__(self, 
                 radius: Union[int, Vector], 
                 color: arcade.Color = colors.ALIZARIN_CRIMSON, 
                 nose: bool = True):
        super().__init__()
        self.owner = None
        if isinstance(radius, int):
            radius = Vector.diagonal(radius)
        diameter = radius * 2

        # determine the texture's cache name
        # if soft:
            # cache_name = arcade.texture._build_cache_name("circle_texture_soft", diameter, color[0], color[1], color[2])
        # else:
        cache_name = arcade.texture._build_cache_name("circle_texture", diameter, color[0], color[1], color[2], 255, 0)

        # use the named texture if it was already made
        if cache_name in arcade.texture.load_texture.texture_cache:  # type: ignore
            texture = arcade.texture.load_texture.texture_cache[cache_name]  # type: ignore

        # generate the texture if it's not in the cache
        else:
            img = PIL.Image.new('RGBA', diameter, (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(img)
            
            point_b:Vector = diameter - Vector(1, 1)
            
            draw.ellipse((0, 0, *point_b), fill = color)
            if nose: draw.line((*radius, point_b.x, radius.y), width = 1, fill = (0, 0, 0, 255))
            texture = GLTexture(cache_name, img)
            # if soft:
            #     texture = arcade.texture.make_soft_circle_texture(diameter, color, name=cache_name)
            # else:
            #     texture = arcade.texture.make_circle_texture(diameter, color, name=cache_name)

            arcade.texture.load_texture.texture_cache[cache_name] = texture  # type: ignore

        # apply results to the new sprite
        self.texture = texture
        self._points = self.texture.hit_box_points


class SpriteCross(Sprite):
    
    def __init__(self, size:Vector, color:tuple):
        cache_name = arcade.texture._build_cache_name("cross_texture", size, color[0], color[1], color[2], 255, 0)
        
        if cache_name in arcade.texture.load_texture.texture_cache:  # type: ignore
            texture = arcade.texture.load_texture.texture_cache[cache_name]  # type: ignore
        else:
            img = PIL.Image.new('RGBA', size, (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(img)
            
            center = size / 2
            
            draw.rounded_rectangle((0,center.y + 10,size.x, center.y - 10), radius=5, fill=color)
            draw.rounded_rectangle((center.x - 10,0,center.x + 10, size.y), radius=5, fill=color)
            texture = GLTexture(cache_name, img)
            arcade.texture.load_texture.texture_cache[cache_name] = texture  # type: ignore
        main_path = ":resources:images/animated_characters/female_person/femalePerson_idle.png"
        texture = arcade.load_texture(main_path, hit_box_algorithm="Detailed")
        super().__init__(texture=texture, hit_box_algorithm="Detailed")
        # self.texture = texture
        # self._points = self.texture.hit_box_points


class Capsule(Sprite):
    """ LEGACY : DEPRECATED """
    
    def __init__(self, radius: int):
        super().__init__()
        
        diameter = radius * 2
        cache_name = arcade.sprite._build_cache_name("circle_texture", diameter, 255, 255, 255, 64, 0)
        texture = None
        
        # texture = make_circle_texture(diameter, color, name=cache_name)
        
        img = PIL.Image.new('RGBA', (diameter, diameter), (0,0,0,0))
        draw = PIL.ImageDraw.Draw(img)
        draw.ellipse((0, 0, diameter - 1, diameter - 1), fill=(255,255,255,64))
        texture = arcade.Texture(cache_name, img, 'Detailed', 1.0)
        
        arcade.texture.load_texture.texture_cache[cache_name] = texture
        
        self.texture = texture
        self._points = self.texture.hit_box_points
        self.collision_radius = radius
        self.collides_with_radius = True
        
    def draw_hit_box(self, color: colors = ..., line_thickness: float = 1):
        return debug_draw_circle(self.position, self.collision_radius, color, line_thickness)


class ObjectLayer(arcade.SpriteList):
    """ extended spritelist with actor, body """
    def __init__(self, 
                 physics_instance:PhysicsEngine = None,
                 use_spatial_hash=None, spatial_hash_cell_size=128, is_static=False, atlas: arcade.TextureAtlas = None, capacity: int = 100, lazy: bool = False, visible: bool = True):
        super().__init__(use_spatial_hash, spatial_hash_cell_size, is_static, atlas, capacity, lazy, visible)
        self._physics_instance = physics_instance
        
    def add(self, obj:Union[Actor, Body, Sprite, SpriteCircle]):
        sprite:Sprite = None
        body:Body = None
        if isinstance(obj, Actor):
            sprite = obj.body.sprite
            body = obj.body
        elif isinstance(obj, (Body, )):
            sprite = obj.sprite
            body = obj
        elif isinstance(obj, (Sprite, SpriteCircle)):
            sprite = obj
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        if sprite:
            try:
                self.append(sprite)
            except ValueError:
                pass
        
        if self._physics_instance:
            if body:
                if body.physics:
                    self._add_to_physics(sprite, body.physics)
                    # self._physics_instance.add_physics_object(sprite, body.physics)  ### add sprite-physics pair to engine for refering
                    # self._physics_instance.add_to_space(sprite)      ### add physics to space
    
    def _add_to_physics(self, sprite:Sprite, physics:PhysicsObject):
        self.physics_instance.add_physics_object(sprite, physics)
        self.physics_instance.add_to_space(sprite)
    
    def remove(self, obj:Union[Actor, Body, Sprite, SpriteCircle]):
        sprite:Sprite = None
        # body:SimpleBody = None
        if isinstance(obj, Actor):
            sprite = obj.body.sprite
            # body = obj.body
        elif isinstance(obj, Body):
            sprite = obj.sprite
            # body = obj
        elif isinstance(obj, (Sprite, SpriteCircle)):
            sprite = obj
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        ''' 
        Because arcade spritelist remove method automatically remove body from physics,
        we don't need it
        
        if body:
           if body.physics:
               self.physics_instance.remove_sprite(sprite)
        '''
        return super().remove(sprite)
    
    def step(self, delta_time:float = 1/60, sync:bool = True):
        ''' Don't use it usually. For better performance, call directly from physics instance '''
        self._physics_instance.step(delta_time=delta_time, resync_objects=sync)
    
    def _get_physics(self):
        return self._physics_instance
    
    def _set_physics(self, physics_instance):
        #TODO : add feature of registreing sprites to another physics instance
        
        self._physics_instance = physics_instance
    
    physics_instance:PhysicsEngine = property(_get_physics, _set_physics)


class Camera(arcade.Camera):
    
    def __init__(self, viewport_width: int = 0, viewport_height: int = 0, window: Optional["arcade.Window"] = None, 
                 max_lag_distance:float = None,
                 ):
        if not viewport_width or not viewport_height:
            viewport_width, viewport_height = CONFIG.screen_size.x, CONFIG.screen_size.y
        super().__init__(viewport_width, viewport_height, window)
        self.max_lag_distance:float = max_lag_distance
    
    def update(self):
        # last_tick_pos = self.position
        super().update()
        
        if self.max_lag_distance:
            distv = self.position - self.goal_position
            if distv.mag > self.max_lag_distance:
                # print(distv.mag)
                self.position = self.goal_position + distv.limit(self.max_lag_distance)
                # self.position.lerp(self.goal_position + distv.limit(self.max_lag_distance * 0.75), 0.9)


class GLTexture(arcade.Texture):
    pass


class SoundBank:
    def __init__(self, path:str) -> None:
        self.path:str = path
        self.filenames:list = []
        self.sounds:dict[str, arcade.Sound] = {}
        self.mute:bool = False
        self.volume_master:float = 0.5
        print('SOUND initialized')
        self.load()
        
    def load(self, path:str = None):
        sfxpath = path or self.path
        try:
            self.filenames = os.listdir(get_path(sfxpath))
        except FileNotFoundError:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        if not self.filenames:
            print(f'no sound file found on "{sfxpath}"')
            return None
        
        for filename in self.filenames:
            namespaces = filename.split('.')
            if namespaces[1] in ('wav', 'ogg', 'mp3'):
                self.sounds[namespaces[0]] = arcade.Sound(get_path(sfxpath + filename))
        return self.sounds
    
    def play(self, name:str, volume:float = 0.2, repeat:int = 1) -> float:
        if self.mute: return None
        if name not in self.sounds:
            print(f'no sound file "{name}"')
            return None
        
        sound = self.sounds[name]
        # self.sounds[name].set_volume(volume)
        sound.play(volume)
        return sound.get_length()
    
    def set_mute(self, switch:bool = None):
        if switch is None: switch = not self.mute
        self.mute = switch
        return self.mute
    
    def set_volume_master(self, amount:float):
        self.volume_master = amount
        
    def beep(self):
        self.play('beep', 1.0)


@dataclass
class Client(metaclass = SingletonType):
    ''' I/O for game
    
    - 디스플레이 정보
        - 렌더링 배율
    - 현재 뷰포트 중앙의 절대 좌표
    - 이동 조작, 카메라 조작
    - 게임패드 입력 raw
    - 마우스 입력 raw
        - 뷰포트 내 상대좌표
        - 월드상의 절대 좌표
    
    (나중에 Window 클래스에 통합시켜버릴 수도 있음)
    '''
    
    delta_time:float = 0.0
    physics_engine:PhysicsEngine = None
    window:Window = None
    
    abs_screen_center:Vector = Vector()
    render_scale:float = 1.0
    screen_shortside = None
    screen_longside = None

    debug_text:DebugTextLayer = None
    viewport:Camera = None
    _player_controller:PawnController = None
    local_players = []
    
    gamepads : list[pyglet.input.Joystick] = None
    keyboard : pyglet.window.key.KeyStateHandler = None            ### for later implementation
    mouse : pyglet.window.mouse.MouseStateHandler = None     ### for later implementation
    
    mouse_screen_position:Vector = Vector()
    gamepad:arcade.joysticks.Joystick = None
    input_move:Vector = Vector()
    
    key = arcade.key
    key_inputs = []
    
    last_abs_pos_mouse_lb_pressed:Vector = vectors.zero
    last_abs_pos_mouse_lb_released:Vector = vectors.zero
    last_mouse_lb_hold_time = 0.0
    
    walk_key_engaged = False
    
    ai_controllers = []
    
    def __init__(
        self,
        max_local_players : int = 1,
        ) -> None:
        super().__init__()
        self.max_local_players = max_local_players
        self.local_players:list[PawnController] = []
        self.gamepads = self.get_gamepads()
        self.gamepad = self.get_gamepads(0)
        self.physics_engine = PhysicsEngine()
    
    def add_player(self, player_controller : PawnController):
        
        if len(self.local_players) >= self.max_local_players:
            return self.show_alert('Local player max error')
        
        self.local_players.append(player_controller)
        idx = self.local_players.index(player_controller)
        player_controller.local_player_id = idx
        
        self.window.push_handlers(player_controller)
        
        if self.gamepads:       ### need to revise logic for kb + gamepad pair.
            if len(self.local_players) >= len(self.gamepads):
                return self.show_alert('No more gamepads')
            self.gamepads[idx].push_handlers(player_controller)

    def remove_player(self, player_controller : PawnController):
        
        idx = player_controller.local_player_id
        self.local_players.remove(player_controller)
        self.gamepads[idx].remove_handlers(player_controller)
        self.window.remove_handlers(player_controller)
        
    def show_alert(self, message : str = 'ALERT'):
        #TODO
        ''' will be implemented later '''
        print(message)
    
    def _get_player_controller(self):
        return self.local_players[0]
    
    # def _set_player_controller(self, player_controller : PawnController):
    #     self._player_controller = player_controller
    #     if self.gamepad:
    #         self.gamepad.push_handlers(self._player_controller)
    #     self.window.push_handlers(self._player_controller)
        
    player_controller = property(_get_player_controller)
    
    def get_gamepads(self, id : int = None):
        if not self.gamepads:
            gamepads : list[pyglet.input.Joystick] = pyglet.input.get_joysticks()
            if not gamepads:
                return None
            for i, gamepad in enumerate(gamepads):
                gamepad.open()
                # gamepad.push_handlers(self)
                print(f'Gamepad[{i}] attached')
            # self.gamepads = gamepads
            return gamepads
        if id is None:
            return self.gamepads
        return self.gamepads[id]
        
    def set_window(
        self,
        size: Vector = CONFIG.screen_size,
        title: Optional[str] = 'mash arcade framework',
        fullscreen: bool = False,
        resizable: bool = True,
        update_rate: Optional[float] = 1 / 60,
        antialiasing: bool = True, 
        gl_version: Tuple[int, int] = (3, 3), 
        screen: pyglet.canvas.Screen = None,
        style: Optional[str] = pyglet.window.Window.WINDOW_STYLE_DEFAULT,
        visible: bool = True,
        vsync: bool = False,
        gc_mode: str = "context_gc",
        center_window: bool = False,
        samples: int = 4,
        enable_polling: bool = False,
        ):
        
        self.window = Window(
            *size, 
            title = title,
            fullscreen = fullscreen,
            resizable = resizable,
            update_rate = update_rate,
            antialiasing = antialiasing,
            gl_version = gl_version,
            screen = screen,
            style = style,
            visible = visible,
            vsync = vsync,
            gc_mode = gc_mode,
            center_window = center_window,
            samples = samples,
            enable_polling = enable_polling,
            )
        
        self.set_screen()
        self.window.push_handlers(self)
    
    def set_screen(self):
        ''' should be called after resizing, fullscreen, etc. '''
        size = self.window.get_size()
        self.screen_shortside = min(*size)
        self.screen_longside = max(*size)
        CONFIG.screen_size = Vector(size)
        self.render_scale = self.window.get_framebuffer_size()[0] / size[0]  
        self.debug_text = DebugTextLayer()
          
    def set_scene(self, view_class:View, *args, **kwargs):
        scene = view_class(*args, **kwargs)
        scene.setup()
        self.window.show_view(scene)
    
    def run(self):
        arcade.run()
    
    def on_key_press(self, key:int, modifiers:int):
        print(f'on key press from CLIENT {key, modifiers}')
        self.key_inputs.append(key)
        if key == keys.GRAVE and not modifiers: 
            CONFIG.debug_f_keys[0] = not CONFIG.debug_f_keys[0]
        for i in range(13):
            if key == keys.__dict__[f'F{i+1}'] and not modifiers: 
                CONFIG.debug_f_keys[i+1] = not CONFIG.debug_f_keys[i+1]
    
    def on_key_release(self, key:int, modifiers:int):
        self.key_inputs.remove(key)
        if key == arcade.key.ESCAPE: arcade.exit()  ### for convenience

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_screen_position = Vector(x, y)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        pass
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pass
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        print('mouse press from window')
        if button == arcade.MOUSE_BUTTON_LEFT:
            GAME.last_abs_pos_mouse_lb_pressed = GAME.abs_cursor_position
        # if GAME.player_controller: 
            # GAME.player_controller.on_mouse_press(x=x, y=y, button=button, modifiers=modifiers)
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            GAME.last_abs_pos_mouse_lb_released = GAME.abs_cursor_position
        # if GAME.player_controller: 
            # GAME.player_controller.on_mouse_release(x=x, y=y, button=button, modifiers=modifiers)

    
    @property
    def lstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.x, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.y, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    @property
    def rstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not self.gamepad: return None
        x = map_range_abs(self.gamepad.rx, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True)
        y = map_range_abs(self.gamepad.ry, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    def _get_move_input(self):
        if self.gamepad:
            return self.lstick
        else:
            return self.input_move.clamp_length(1) * (0.5 if self.walk_key_engaged else 1)

    move_input:Vector = property(_get_move_input)
    ''' returns movement direction vector (-1, -1) ~ (1, 1) '''
    
    def _get_target_point(self):
        if self.gamepad:
            if self.rstick.length > 0.5:
                return (self.rstick.unit * CONFIG.screen_size.y / 2 + self.abs_screen_center) * self.render_scale
        else:
            return self.abs_cursor_position
    
    target_point:Vector = property(_get_target_point)
    ''' returns relative target point '''
    
    def _get_cursor_position(self) -> Vector:
        # if not self.mouse_input: return Vector()
        return self.mouse_screen_position * self.render_scale
    
    cursor_position:Vector = property(_get_cursor_position)
    ''' returns relative mouse cursor point '''
    
    def _get_abs_cursor_position(self) -> Vector:
        return self.mouse_screen_position + self.abs_screen_center - CONFIG.screen_size / 2
        # return self.mouse_input + self.window.current_camera.position
    
    abs_cursor_position:Vector = property(_get_abs_cursor_position)
    ''' get absolute position in world, pointed by mouse cursor '''


if __name__ != "__main__":
    print("include", __name__, ":", __file__)
    SOUND = SoundBank(SFX_PATH)
    GAME = Client()
    # APP = Window(*CONFIG.screen_size, CONFIG.screen_title + ' ' + Version().full)
