from __future__ import annotations

# from ..base import *


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
        `owner` : GameObject
            get top owner
    
    '''
    
    __slots__ = ['_alive', 'spawnned', '_owner']
    
    def __init__(self) -> None:
        self._alive = True
        ''' Rockbottom switch of alive check '''
        self.spawnned = False
        self._owner : GameObject = None
        
        self.setup()
    
    def setup(self) -> None:
        '''
        Initial setup, and reset
        
        '''
        pass
    
    def spawn(self) -> GameObject:
        '''
        Put self into the game space and return self
        
        '''
        self.spawnned = True
        members = self.get_members()
        if members:
            for member in members:
                member.owner = self
                if not member.spawnned : member.spawn()
        self.on_spawn()
        # print(f'{self} spawned by {self._owner}')
        return self
    
    def on_spawn(self) -> None:
        '''
        Method that runs right after spawn.
        
        If needed, register this to processor.
        '''
        pass
    
    def destroy(self) -> None:
        '''
        Literally destroy this object. Note that it's not dead, dispawn, etc.
        
        For a living character, dead or on_dead method needed for some presentation process. 
        destroy() should be called as kinda callback after all process of death ends.
        '''
        self.on_destroy()
        members = self.get_members()
        if members:
            for member in members:
                if member.owner == self : member.destroy()      ### for handlers
        self.spawnned = False
        self._alive = False
    
    def on_destroy(self):
        '''
        Method that runs right before destruction
        '''
        pass
    
    def get_members(self, types_include = None, types_exclude = None):
        if not types_include: types_include = GameObject
        members : list[GameObject] = []
        if hasattr(self, '__dict__'):    ### for those have only __slots__
            members.extend([c for c in self.__dict__.values() if isinstance(c, types_include) and c != self._owner])
        if hasattr(self, '__slots__'):
            members.extend([getattr(self, c) for c in self.__slots__ if isinstance(getattr(self, c), types_include) and getattr(self, c) != self._owner])
        # if len(members) == 1: return members[0]
        return members
    
    def is_alive(self) -> bool:
        ''' Overridable but need retuning super().is_alive()'''
        return self._alive
    
    def get_owner(self, obj : GameObject) -> GameObject:
        if obj._owner is None: return obj
        return self.get_owner(obj._owner)
    
    def _get_owner(self) -> GameObject:
        return self.get_owner(self)
    
    def _set_owner(self, owner : GameObject):
        self._owner = owner
    
    owner : GameObject = property(_get_owner, _set_owner)
    
    @property
    def id(self) -> str:
        return str(id(self))
    
    @property
    def alive(self) -> bool:
        return self.is_alive()


class Handler(GameObject):
    '''
    GameObjects that should yuji owner's handlers as theirs.
    
    '''
    
    def get_owner_member(self, type) -> None:
        owner_members = self.owner.get_members(type)
        if owner_members : return owner_members[0]
        return None


class Actor(GameObject):
    pass
