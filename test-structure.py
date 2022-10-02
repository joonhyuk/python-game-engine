from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.escape import *
from config import *

import json


class GameObject(object):
    '''
    Base class of everything 'in game'
    
    Defines lifecycle of objects.
    
    :Parameters:
        `id` : str
            returns id(self)
        `alive` : bool
            not destroyed
        `spawnned` : bool
            is in game space
    
    '''
    
    __slots__ = ['_alive', '_spawnned']
    
    def __init__(self) -> None:
        self._alive = True
        ''' Rockbottom switch of alive check '''
        self._spawnned = False
        self.setup()
    
    def setup(self) -> None:
        '''
        Initial setup and reset
        
        '''
        pass
    
    def spawn(self) -> GameObject:
        '''
        Put self into the game space and return self
        
        '''
        self._spawnned = True
        return self
    
    def destroy(self) -> None:
        '''
        Literally destroy this object. Note that it's not dead, dispawn, etc.
        
        For a living character, dead or on_dead method needed for some presentation process. 
        destroy() should be called as kinda callback after all process of death ends.
        '''
        self._spawnned = False
        self._alive = False
    
    def is_alive(self) -> bool:
        ''' Overridable but need retuning super().is_alive()'''
        return self._alive
    
    @property
    def id(self) -> str:
        return str(id(self))
    
    @property
    def alive(self) -> bool:
        return self.is_alive()


class GameComponent(GameObject):
    
    def __init__(self) -> None:
        super().__init__()
        self._owner : Union[_Actor, GameComponent] = None
    
    def get_owner(self, obj):
        if obj._owner is None: return obj
        return self.get_owner(obj._owner)
    
    def _get_owner(self) -> Union[Actor, ActorComponent]:
        return self.get_owner(self)
    
    def _set_owner(self, owner:Union[Actor, ActorComponent]):
        self._owner = owner
        # self._owner.movable = self.movable
    
    owner:Union[Actor, ActorComponent] = property(_get_owner, _set_owner)


class _Actor(GameObject):
    
    def spawn(self) -> GameObject:
        self.spawn_components()
        return super().spawn()
    
    def get_components(self, *types:GameComponent) -> Union[list[GameComponent], GameComponent]:
        if not types: types = GameComponent
        components:list[GameComponent] = []    ### type hinting
        if hasattr(self, '__dict__'):    ### for those have only __slots__
            components.extend([c for c in self.__dict__.values() if isinstance(c, types)])
        if hasattr(self, '__slots__'):
            components.extend([getattr(self, c) for c in self.__slots__ if isinstance(getattr(self, c), types)])
        if len(components) == 1: return components[0]
        return components
    
    def spawn_components(self, candidate = (GameComponent,)):
        components:list[candidate] = []    ### type hinting
        
        components = self.get_components(*candidate)
        
        if components:
            for component in components:
                if hasattr(component, 'owner'): component.owner = self  ### set owner
                # if hasattr(component, 'tick'): 
                    # if component.tick: self.tick_components.append(component)
                    # ''' to disable component tick, put `self.tick = None` into __init__() '''
                if hasattr(component, 'spawn'): component.spawn()
        
        # self.tick_components.sort(key = lambda tc:tc.priority, reverse = True)
    

g = GameObject()
print(g.id)
a = _Actor()
print(a.alive)


class C0:
    def __init__(self) -> None:
        self._owner = None
        
    def get_owner(self, obj):
        if obj._owner is None: return obj
        return self.get_owner(obj._owner)
    
    @property
    def owner(self):
        return self.get_owner(self)


class C1(C0):
    
    def __init__(self) -> None:
        super().__init__()
        self.c2 = C2()
        self.c2._owner = self

class C2(C0):
    
    def __init__(self) -> None:
        super().__init__()
        self.c3 = C0()
        self.c3._owner = self
        

cc = C1()
print(cc.c2.owner)
