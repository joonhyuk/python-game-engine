import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lib.foundation import *
from config import *


class TestComponent(ActorComponent):
    
    p1:str = 'property 1'
    
    def _get_p2(self):
        return 'property 2'
    
    def _set_p2(self, content):
        self.p1 = content
    
    p2 = property(_get_p2, _set_p2)
    
    @property
    def p3(self):
        return 'property 3'
    
    def on_register(self):
        print('test component spawnned')
        self.owner.p1 = self.p1
    
import time
class TestActor(Actor):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.component = TestComponent()

### 컴포넌트의 프로퍼티를 옮겨오는 방법 테스트
# test = TestActor()
# test.spawn()
# test.component.p1 = 'aha'
# print(test.p1)

