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
    fact = FACT()
    
    nact = NACT()

    
class Tactor(Pawn):
    
    action = PACT()
    faction = FACT()
    
    def __init__(self, body: DynamicBody, hp: float = 100, **kwargs) -> None:
        super().__init__(body, hp, **kwargs)
        self.action = TACC()
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
        

class GameEntity(object):
    '''
    base class of everything 'in game'
    
    define lifecycle of objects.
    '''
    
    def __init__(self) -> None:
        self._alive = True
        self.setup()
        pass
    
    def setup(self) -> None:
        '''
        Initial setup
        '''
        pass
    
    def spawn(self) -> GameEntity:
        '''
        Put self into the game space
        '''
        return self
    
    def tick(self, delta_time:float) -> bool:
        '''
        Returns true if valid state
        이게 필요할까? tick도 범용 컴포넌트로 만들어버리면? 
        어차피 tick을 가지고 있는 컴포넌트들만 프로세서에서 돌려주면 되는 일.
        ECS 모델로 완전히 가게 되면 컴포넌트로 만들어야 한다. 
        단, 기존에는 액터 단위로 업데이트가 일어났다면 새 방식에서는 개별 프로세서들이 돌아가는 격.
        필요시 각 컴포넌트에서 생존 체크를 해야 한다.
        '''
        if not self.is_alive: return False
        return True
    
    def destroy(self, delay:float = None) -> None:
        '''
        Literally destroy this object. Note that it's not dead, dispawn, etc.
        
        For a living character, dead or on_dead method needed for some presentation process. 
        destroy() should be called as kinda callback after all process of death ends.
        '''
        if not delay:
            self._destroy(0)
        else:
            schedule_once(self._destroy, delay)
    
    def on_destroy(self):
        pass
    
    def _destroy(self, delta_time:float, *args, **kwargs):
        self._alive = False
        self.on_destroy(*args, **kwargs)
    
    def is_alive(self) -> bool:
        return self._alive
    
    @property
    def id(self) -> str:
        return str(id(self))
    
    @property
    def alive(self) -> bool:
        return self.is_alive()



class WorldStatic(GameEntity):
    
    def setup(self) -> None:
        
        return super().setup()


