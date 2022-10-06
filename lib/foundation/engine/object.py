from __future__ import annotations

from typing import Union
from ..base import get_slots


class GameObject(object):
    '''
    Base class of everything 'in game'
    
    Defines the lifecycle of an object.
    
    If kwargs set, they'll pass to `setup(**kwargs)`
    
    i.e.
    ```
        class Foo(GameObject):
            def setup(self, **kwargs) -> None:
                self.hello = get_from_dict(kwargs, 'messsage')
                
        f = Foo(message = 'world')
        print(f.hello) --> world
    ```
    :Parameters:
        `id : str`
            returns id(self)
        `alive : bool`
            not destroyed
        `spawnned : bool`
            is in game space
        `owner : GameObject`
            get top owner
        `members : list[GameObject]`
            get child GameObjects, read only.
    
    '''
    
    # __slots__ = '_alive', 'spawnned', '_owner', '_members'
    
    def __init__(self, **kwargs) -> None:
        self._alive = True
        ''' Rockbottom switch of alive check '''
        self.spawnned = False
        ''' Is in game space '''
        self._owner : GameObject = None
        ''' Owner right above '''
        self._members : list[GameObject] = None
        ''' Child members of GameObject type, Don't access it directly. Use `_obj.members` instead '''
        self.setup(**kwargs)
    
    def setup(self, **kwargs) -> None:
        '''
        Initial setup, and reset
        
        Will have additional member variables.
        So, it's safe to run `super().setup(**kwargs)` for most cases.
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
        #TODO add 'remove_from_all_list' to Client for proper GC
        self.on_destroy()
        members = self.get_members()
        if members:
            for member in members:
                if member.owner == self : member.destroy()      ### for handlers
        del self._members
        self.spawnned = False
        self._alive = False
    
    def on_destroy(self):
        '''
        Method that runs right before destruction
        '''
        pass
    
    def get_members(
        self, 
        types_include : Union[type, tuple[type]] = None, 
        types_exclude : Union[type, tuple[type]] = None
        ) -> list[GameObject] :
        '''
        Get members with including types(type or tuple[type])
        '''
        if self._members is None:
            self._members : list[GameObject] = []
            if hasattr(self, '__dict__'):
                self._members.extend([c for c in self.__dict__.values() if isinstance(c, GameObject) and c != self._owner])
            if hasattr(self, '__slots__'):
                self._members.extend([getattr(self, c) for c in get_slots(self) if isinstance(getattr(self, c), GameObject) and getattr(self, c) != self._owner])
                ''' 
                if __slots__ exists, get all slots for member check. 
                slightly bad for spawn performance, but good for memory, performance
                '''
        
        if not types_include and not types_exclude : return self._members
        
        inc, exc = lambda _obj : True, lambda _obj : True
        if types_include is not None:
            inc = lambda _obj : isinstance(_obj, types_include) 
        if types_exclude is not None:
            exc = lambda _obj : not isinstance(_obj, types_exclude) 
        
        return [m for m in self._members if inc(m) and exc(m)]
    
    def owners(self, type_ : type) -> GameObject:
        try:
            return self.owner.get_members(type_)[0]
        except:
            raise AttributeError(f'{self.owner} doesn\'t have {type_} member')
    
    def is_alive(self) -> bool:
        ''' Overridable but need retuning super().is_alive()'''
        return self._alive
    
    def get_owner(self, _obj : GameObject) -> GameObject:
        if _obj._owner is None: return _obj
        return self.get_owner(_obj._owner)
    
    def _get_owner(self) -> GameObject:
        return self.get_owner(self)
    
    def _set_owner(self, owner : GameObject):
        self._owner = owner
    
    owner : GameObject = property(_get_owner, _set_owner)
    
    # @property
    # def id(self) -> str:
    #     return str(id(self))
    
    @property
    def alive(self) -> bool:
        return self.is_alive()
    
    @property
    def members(self) -> list[GameObject]:
        return self._members

    # def __getstate__(self):
    #     return dict([(k, getattr(self,k,None)) for k in self.__slots__])

    # def __setstate__(self,data):
    #     for k,v in data.items():
    #         setattr(self,k,v)


class Handler(GameObject):
    '''
    GameObjects that should yuji owner's handlers as theirs.
    
    '''
    __slots__ = ()
    
    def get_owner_member(self, type) -> None:
        owner_members = self.owner.get_members(type)
        if owner_members : return owner_members[0]
        return None


class Actor(GameObject):
    
    __slots__ = ()
