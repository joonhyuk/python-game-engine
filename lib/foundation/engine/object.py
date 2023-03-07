from __future__ import annotations

from functools import cache, cached_property
from typing import Union

from ..base import get_slots


class GameObject(object):
    '''
    Base class of everything 'in game'
    
    Defines the lifecycle of an object.
    
    ## Setup with **kwargs
    
    If kwargs set, they'll pass to `setup(**kwargs)`
    
    i.e.
    ```
        class Foo(GameObject):
            def setup(self, **kwargs) -> None:
                self.hello = get_from_dict(kwargs, 'messsage')
                
        f = Foo(message = 'world')
        print(f.hello) --> world
    ```
    
    ## Get owner's member
    
    For handlers that should yuji top(highest) owner's members as theirs, 
    use `self.owner[TYPE_OF_GAMEOBJECT]`.
    
    i.e.
    ```
        self.body = self.owner(BodyHandler)
    ```
    
    ## Parameters
        `id : str`
            returns id(self)
        `alive : bool`
            not destroyed
        `spawnned : bool`
            is in game space
        `owner : GameObject`
            get top owner, read only.
        `members : list[GameObject]`
            get child GameObjects, read only.
        `available : bool`
            for validity check, read only.
    
    '''
    
    spawn_counter:int = 0
    destroy_counter:int = 0
    gc_counter:int = 0
    
    __slots__ = '_alive', 'spawnned', '_owner', '_members'
    
    def __init__(self, **kwargs) -> None:
        self._alive = True
        ''' Rockbottom switch of alive check. Only set to false when destroyed. '''
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
                member._owner = self
                if not member.spawnned : member.spawn()
        self._set_owners_member()
        self.on_spawn()
        GameObject.spawn_counter += 1
        ''' For only debugging '''
        return self
    
    def on_spawn(self) -> None:
        '''
        Method that runs right after spawn.
        
        If needed, register this to processor.
        '''
        pass
    
    def destroy(self) -> bool:
        '''
        Literally destroy this object. Note that it's not dead, dispawn, etc.
        
        For a living character, dead or on_dead method needed for some presentation process. 
        destroy() should be called as kinda callback after all process of death ends.
        '''
        #TODO add 'remove_from_all_list' to Client for proper GC
        if not self._alive: return False
        self.on_destroy()
        members = self.get_members()[:]
        if members:
            for member in members:
                if member._owner == self :
                    '''
                    Destroy only my own members, not my superior (for handlers)
                    '''
                    member.destroy()
                    
        self.spawnned = False
        self._alive = False
        # self._owner = None    ### Uncomment this line for immediate GC
        self._members.clear()
        self.get_top_owner.cache_clear()
        self.get_members.cache_clear()
        GameObject.destroy_counter += 1
        ''' For only debugging '''
        return True
    
    def on_destroy(self):
        '''
        Method that runs right before destruction
        '''
        pass
    
    def __del__(self):
        ''' For only debugging '''
        if not self.alive: GameObject.gc_counter += 1
    
    @cache
    def get_members(
        self, 
        types_include : Union[type, tuple[type]] = None, 
        types_exclude : Union[type, tuple[type]] = None,
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
    
    def _set_owners_member(self) -> None:
        ''' Should be called after spawnned '''
        members:list[str] = []
        if hasattr(self, '__dict__'):
            members.extend([k for k, v in self.__dict__.items() if isinstance(v, ReservedMember) and v != self._owner])
        if hasattr(self, '__slots__'):
            members.extend([c for c in get_slots(self) if isinstance(getattr(self, c), ReservedMember) and getattr(self, c) != self._owner])
            ''' 
            if __slots__ exists, get all slots for member check. 
            slightly bad for spawn performance, but good for memory, performance
            '''
        if members:
            for name in members:
                setattr(self, name, self.owners(getattr(self, name).type_))
    
    def owners(self, type_ : type) -> GameObject:
        '''
        Try to fetch top owner's member of type : `type_`
        '''
        if not self.spawnned:
            ''' Before spawnned, postpone fetching for later '''
            return ReservedMember(type_)
        
        try:
            member = self.owner.get_members(type_)[0]
        except:
            raise AttributeError(f'{self.owner} doesn\'t have {type_} member')
        else:
            return member
    
    def _is_alive(self) -> bool:
        ''' Overridable but need retuning super()._is_alive()'''
        return self._alive
    
    @cache        ### Should clear cache when destroyed for GC
    def get_top_owner(self, _obj : GameObject = None) -> GameObject:
        ''' retrieve owner recursively '''
        if _obj is None: _obj = self
        if _obj._owner is None: return _obj
        return self.get_top_owner(_obj._owner)
    
    owner : GameObject = property(get_top_owner)
    ''' Returns top owner found recursively. 
    
    Use `self._owner` to get the owner directly above '''
    
    @cached_property
    def id(self) -> str:
        return str(id(self))
    
    @property
    def alive(self) -> bool:
        '''
        Returns validity
        '''
        return self._is_alive()
    
    @property
    def members(self) -> list[GameObject]:
        return self._members or self.get_members()

    @property
    def available(self) -> bool:
        '''
        Returns alive and spawnned
        '''
        if not self._owner:
            return self.alive and self.spawnned
        
        return all((
            self._owner.alive,
            self._owner.spawnned,
            self.alive,
            self.spawnned
        ))
    # def __getstate__(self):
    #     return dict([(k, getattr(self,k,None)) for k in self.__slots__])

    # def __setstate__(self,data):
    #     for k,v in data.items():
    #         setattr(self,k,v)


class ReservedMember:
    
    def __init__(self, type_ : type) -> None:
        self.type_ = type_


class Handler(GameObject):
    '''
    GameObjects that should yuji owner's members as theirs.
    
    Use `self.owner(GAMEOBJECT_TYPE_TO_RETRIEVE)`
    '''
    pass
    

class Actor(GameObject):
    
    __slots__ = ()

