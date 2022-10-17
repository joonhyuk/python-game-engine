from abc import abstractmethod
from functools import partial
from typing import Any

from ..utils import *

from .object import *
from .body import *
from .movement import *
from .app import GAME

class ActionHandler(GameObject):
    '''
    Action : custom functions for owner
    
    attack, evade, open(이건 인터렉션이잖아...)
    
    SHOULD BE REVISED AFTER VERSION 0.10
    
    '''
    
    __slots__ = '_locked', 'locked_actions', 
    
    def setup(self, **kwargs) -> None:
        self._locked = False
        self.locked_actions:list[type] = []
        return super().setup(**kwargs)
    
    def on_spawn(self) -> None:
        self.body = self.owners(BodyHandler)
        self.movement = self.owners(MovementHandler)
        return super().on_spawn()
    
    def tick(self, delta_time: float):
        ''' For actions need tick '''
        
        pass
    
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
    
    :self.setup(): setting 'local' variable after `__init__()`
    :self.do(): action function
    
    호출될 때 스타트 액션(없으면 바로 본론으로)
    스타트 액션 종료 콜백으로 본론, 본론 콜백으로 마무리.
    딜레이 혹은 애니메이션 플레이가 가능해야 한다.
    콜 되면 틱마다 실행??? 타이머??? 액션 핸들러가 틱마다 실행해줌???
    
    '''
    
    def __init__(self, *args, **kwargs) -> None:
        # self.do = update_wrapper(self.do, self.do)
        self.owner = None
        self.setup(*args, **kwargs)
    
    def __set_name__(self, owner, name):
        # setattr(owner, 'act_'+name, self)
        self.name = name
    
    def __get__(self, owner:Union[GameObject, ActionHandler], objtype = None):
        if GAME.global_pause: return self.void
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
    
    def lock_global(self, owner:Union[GameObject, ActionHandler]):
        if isinstance(owner, GameObject):
            raise Exception('actor could not be locked')
        owner.global_lock = True
        
    def unlock_global(self, dt, owner:Union[GameObject, ActionHandler]):
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
    def do(self, owner:Union[GameObject, ActionHandler], *args, **kwargs) -> Any:
        return True


class SequentialAction(Callable):
    ''' 
    - pre, do, post
    - register self to handler ticker
    
    Callable처럼 그냥 call 해서 사용할 수 있어야 함.
    '''
    #TODO pre, post 더 쉽게 비활성화 시키는 방법, 지속 및 종료 훅 만드는 방법.
    
    def __init__(self, *args, **kwds) -> None:
        self.owner:Actor = None
        
        # self._post = partial(self._sequencial_do, self.post, None)
        self._do_post = partial(self._sequencial_do, self.do, self.post)
        self._pre_post = partial(self._sequencial_do, self.pre, self._do_post)
        self._pre = partial(self._sequencial_do, self.pre, self.do)
        
        self.setup(*args, **kwds)
    
    def __set_name__(self, owner, name):
        self.owner:ActionHandler = owner
        self.name = name
    
    def __call__(self, *args, **kwds) -> None:
        if self.pre:
            if self.post:
                return self._pre_post(*args, **kwds)
            return self._pre(*args, **kwds)
        elif self.post:
            return self._do_post(*args, **kwds)
        else:
            return self.do(*args, **kwds)
        # return self.do(*args, *kwds)
    
    def setup(self, *args, **kwds) -> None:
        pass
    
    def _sequencial_do(self, do:Callable, next: Callable = None, *args, **kwds):
        done = do(*args, **kwds)
        if next: return next(*args, **kwds)
        return done
    
    @cache
    def pre(self, *args, **kwds):
        pass
    
    @abstractmethod
    @cache
    def do(self, *args, **kwds):
        pass
    
    @cache
    def post(self, *args, **kwds):
        pass