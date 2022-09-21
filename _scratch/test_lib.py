from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.escape import *
from config import *
import gc

'''
테스트용 뷰 클래스:

창 열고 기본 루프만 도는...

'''

class TACT(TAction):
    
    def do(self, *args, **kwargs):
        print(self.owner, 'do something like', args[0])
        return super().do(*args, **kwargs)


class PACT(Action):
    
    def do(self, owner, a, d):
        print(owner, 'is owner and I am', self, 'and args are', a, 'and kwargs are', d)
        

class MethodType:
    "Emulate PyMethod_Type in Objects/classobject.c"

    def __init__(self, func, obj):
        self.__func__ = func
        self.__self__ = obj

    def __call__(self, *args, **kwargs):
        func = self.__func__
        obj = self.__self__
        return func(obj, *args, **kwargs)
    
class FAction:
    
    def __get__(self, obj, objtype=None):
        "Simulate func_descr_get() in Objects/funcobject.c"
        if obj is None:
            return self
        return MethodType(self.do, obj)
    
    def do(self, *args, **kwargs):
        pass

class FACT(FAction):
    
    def do(self, a, b):
        print('FACT called', self, a,b )


def dummy(owner, c, d):
    pass

def action_func(owner, a, b):
    print(owner,'called me', a, b)

class Actio77:
    
    # func = None
    
    # def __new__(cls):
    #     cls.func = cls.func
    
    def __init__(self, func) -> None:
        self.func = func
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, owner, objtype = None):
        # return partial(self.__class__.func, owner)
        return partial(self.do, owner)
    
    def do(self, owner, *args, **kwargs):
        self.func(owner, *args, **kwargs)

class FACT(Action):
    ''' f-act test class '''
    # def __get__(self, owner, objtype=None):
    #     return partial(self.do, owner)

    def do(self, owner, a, b, c):
        """ DOC을 유지하려면??? """
        print(owner, a, b, c)


class NewAction:
    
    # def __init__(self, owner) -> None:
    #     self.owner = owner
    
    # def __set_name__(self, owner, name):
    #     print('set_name', owner, name)
    
    # def __call__(self, *args, **kwargs):
    #     return self.do(*args, **kwargs)
    
    # def do(self, a, b):
    #     print('new action!', a, b)
    def __get__(self, owner, objtype = None):
        return partial(self.do, owner)
    
    # def do(self, owner, *args, **kwargs):
    #     print(owner, args)

class NACT(NewAction):
    def do(self, owner, a, b):
        ''' new d ! '''
        print(owner, a, b)
    
class TACC(ActionHandler):
    
    pact = PACT()
    tact = TACT()
    fact = FACT()
    
    nact = NACT()

    
class Tactor(Pawn):
    
    action = PACT()
    faction = FACT()
    
    def __init__(self, body: DynamicBody, hp: float = 100, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        self.actions = TACC()
        # self.new_action = NewAction(self)

ta = Tactor(DynamicBody(SpriteCircle(16)))

ta.register_components()
# ta.actions.tact()
# ta.faction()

eah = EscapeCharacterActionHandler()
import inspect
# print(inspect.getmembers(eah))
for member_name, member_object in inspect.getmembers(eah):
    print(member_object)
    if isinstance(member_object, ActionFunction):
    # if inspect.isdatadescriptor(member_object):
        # print(member_object)
        print('weapons hot!')


ww = World()
ww.load_map('tiled/test_map2.json')