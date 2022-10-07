from abc import abstractmethod
from functools import partial

from ..utils import *

from .object import *
from .body import *
from .movement import *

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
    
    '''
    
    def __init__(self, *args, **kwargs) -> None:
        # self.do = update_wrapper(self.do, self.do)
        self.owner = None
        self.setup(*args, **kwargs)
    
    def __set_name__(self, owner, name):
        # setattr(owner, 'act_'+name, self)
        self.name = name
    
    def __get__(self, owner:Union[GameObject, ActionHandler], objtype = None):
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
    def do(self, owner:Union[GameObject, ActionHandler], *args, **kwargs):
        return True
