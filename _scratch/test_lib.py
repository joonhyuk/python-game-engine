from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.foundation import *
from config import *
import gc

'''
테스트용 뷰 클래스:

창 열고 기본 루프만 도는...

'''

class Comp:
    def __init__(self) -> None:
        self.position = None

class Act:
    def __init__(self) -> None:
        self.comp = Comp()
    
    def hello(self):
        return 
    
    position = PropertyFrom('comp')

class Act2(Act):
    
    def __init__(self) -> None:
        super().__init__()
        self.hello = None
        # self.__dict__.pop('hello')
        print(getattr(self,'hello', None))
    
    def _get_pos(self):
        return 'pos'
    
    # def hello(self):
    #     return super().hello()
    
    def _set_pos(self):
        print('set pos')
    
    position = property(_get_pos, _set_pos)
    """ overrided """

aa = Act2()
# print(aa.__dict__.items)