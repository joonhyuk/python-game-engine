from lib.foundation import *

class TestAction(Action):
    
    def do(self):
        print('hello action')
        tick_for(self.something, 1, 1/10)
        
    def something(self, delta_time:float):
        print('test-action-tick', delta_time)
    