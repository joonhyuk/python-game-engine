from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.foundation import *
from config import *
import gc

# print(gc.get_stats())

class MyProperty:
    "Emulate PyProperty_Type() in Objects/descrobject.c"

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
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

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError(f"can't delete attribute {self._name}")
        self.fdel(obj)

    def getter(self, fget):
        prop = type(self)(fget, self.fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def setter(self, fset):
        prop = type(self)(self.fget, fset, self.fdel, self.__doc__)
        prop._name = self._name
        return prop

    def deleter(self, fdel):
        prop = type(self)(self.fget, self.fset, fdel, self.__doc__)
        prop._name = self._name
        return prop

class Foo(Actor):
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.movement = PhysicsMovement()
        self.action = ActionComponent()
        self.body = Body(SpriteCircle())
        

f = Foo()


class PropertySet:
    
    def __init__(self, proxied) -> None:
        self.proxied = proxied
        self.name = None
        
    def __set_name__(self, owner, name):
        print(owner, name)
        self.name = name
    
    def __get__(self, owner, objtype = None):
        return getattr(owner, self.name, None)


class CComponent(ActorComponent):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._aa = 0
    
    def _get_aa(self):
        print('get_aa')
        return self._aa
    
    def _set_aa(self, aa):
        print('set_aa')
        self._aa = aa
    
    aa = property(_get_aa, _set_aa)
    
    def on_register(self):
        setattr(self.owner, 'aa', self.aa)
        # setattr(self.owner, 'aa', PropertySet())
        


class AActor(Actor):
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cc = CComponent()
    
    aa = PropertyFrom('cc')


a = AActor()
a.spawn()
# print(a.aa)
# a.aa = 3

b = StaticBody(SpriteCircle())
d = DynamicBody(SpriteCircle())

print(b.is_movable_physics)
print(d.is_movable_physics)

'''
테스트용 뷰 클래스:

창 열고 기본 루프만 도는...

'''