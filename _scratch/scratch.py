import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from config import *
from lib.foundation import *

class SampleActor(arcade.Sprite, MObject):
    def __init__(self, **kwargs) -> None:
        super(SampleActor, self).__init__(**kwargs)
        MObject.__init__(self)
    
    def samplefunc(self, a:int, b = None, c:str = 'tt'):
        print(f'{a}{b}{c}')

import functools
import inspect

def test_decorator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # name = kwargs.get('name')
        # """위와 같이 할 경우 args로 넘어간 인자는 가져올 수 없음"""
        name = inspect.getcallargs(f, *args, **kwargs).get('name')
        """inspect를 사용하면 알아서 wrapped의 인자 목록을 뒤져 가져옴"""
        if name != 'mash':
            # raise Exception('Only mash can do it')
            return False
        return f(*args, **kwargs)
    return wrapper

class TestDecorator:
    def __init__(self, f) -> None:
        @functools.wraps(f)
        def init_func(func):
            return func
        self.func = init_func(f)
        self.args = {}
    
    def __call__(self, *args, **kwargs):
        # self.args = inspect.getcallargs(self.func, *args, **kwargs)
        # name = inspect.getcallargs(self.f, *args, **kwargs).get('name')
        # name = self.args['name']
        name = kwargs.get('name')
        if name != 'mash':
            print('only mash can do it')
            return False
        print('wrapped - start')
        self.func(self, *args, **kwargs)
        print('wrapped - end')

class MashDecorator:
    def __init__(self, func) -> None:
        self.func = func
        self.args = {}
    
    def __call__(self, *args, **kwargs):
        # @functools.wraps(self.func)
        if not self.prefix() : return False
        self.args = inspect.getcallargs(self.func, *args, **kwargs)
        result = self.func(*args, **kwargs)
        return result

    def prefix(self) -> bool:
        return True
        
        

class TestCheckSuper(TestDecorator):
    def __call__(self, *args, **kwargs):
        self.args = inspect.getcallargs(self.func, *args, **kwargs)
        
        return super().__call__(*args, **kwargs)

def check_super_func(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # if not super().f: return False
        return f(*args, **kwargs)
    return wrapper

class AActor(MObject):
    
    def tick(self) -> bool:
        if not super().tick(): return False
        print('ticked!')
        return True
    
    @property
    def foo(self):
        pass
    
    @MashDecorator
    def do_something(self, name, thing):
        print(name, thing)

aa = AActor()
aa.do_something(name = 'mash', thing = 'directing')
print(aa.do_something.__name__)
aa._alive = False
aa.tick()