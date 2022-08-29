import functools
from typing import Callable

scheduled_functions = []
''' simple replacement of pyglet.clock module '''

def schedule_once(func, delay, *args, **kwargs):
    ''' simple replacement of pyglet.clock.schedule_once '''
    print('scheduled func :',func)
    scheduled_functions.append(func)

def unschedule(func):
    ''' simple replacement of pyglet.clock.unschedule '''
    print('try to unschedule ', func)
    if func in scheduled_functions:
        scheduled_functions.remove(func)
    else:
        print(func, 'not found')

delayed_stuffs = {}

def delay_run(delay:float, func:Callable, *args, **kwargs):
    ''' my wrapper for add an argument(dt) to func '''
    if not isinstance(delay, (float, int)): return False
    if delay <= 0: return func(*args, **kwargs)
    
    @functools.wraps(func)
    def _wrapper(dt, func, *args, **kwargs):
        return func(*args, **kwargs)
    
    delayed_stuffs[func] = _wrapper
    
    return schedule_once(_wrapper, delay, *args, **kwargs)

def delay_cancel(func:Callable):
    
    unschedule(delayed_stuffs[func])
    delayed_stuffs.pop(func)
    

def add_dt(func):
    @functools.wraps(func)
    def _wrap(dt, *args, **kwargs):
        return func(*args, **kwargs)
    return _wrap



class Foo:
    @add_dt
    def destroy(self):
        print('destroy ', self)


import sys

f = Foo()
delay_run(1, f.destroy)
# unschedule(f.destroy)
print(delayed_stuffs, sys.getsizeof(delayed_stuffs))
delay_cancel(f.destroy)
print(delayed_stuffs, sys.getsizeof(delayed_stuffs))
