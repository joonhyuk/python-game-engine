from __future__ import annotations

from lib.foundation.new_engine import *

class TestBodyHandler(Handler):
    
    def setup(self) -> None:
        self.position = 'pos'
        # self.handler = Handler()

class TestMovementHandler(Handler):
    
    def __init__(self, body : TestBodyHandler) -> None:
        super().__init__()
        self.body = body
    
    def setup(self) -> None:
        self.max_speed = 100
    
    def __del__(self):
        print('SHHIT', self)
    # def on_spawn(self) -> None:
    #     self.body = self.register_owner_member(TestBodyHandler)
    #     return super().on_spawn()

class ATestMovementHandler(TestMovementHandler):
    pass


class TestController(Handler):
    
    def __init__(self, movement:TestMovementHandler) -> None:
        super().__init__()
        self.movement = movement
        
class TestActor(GameObject):
    
    def setup(self) -> None:
        self.body = TestBodyHandler()
        self.movement = ATestMovementHandler(self.body)
        self.controller = TestController(self.movement)
    
a = TestActor()
print('first', a.controller.movement)
a.spawn()
print('second', a.controller.movement.body)
print('hahaha')
