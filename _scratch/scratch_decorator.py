import functools
import inspect
import time

from datetime import datetime

def say_hello(name):
    return f"Hello {name}"

def be_awesome(name):
    return f"Yo {name}, together we are the awesomest!"

def greet_bob(greeter_func):
    return greeter_func("mash")

def parent(num):
    def first_child():
        return "Hi, I am Emma"

    def second_child():
        return "Call me Liam"

    if num == 1:
        return first_child
    else:
        return second_child

print(parent(1)())

def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

def not_during_the_night(func):
    @functools.wraps(func)
    def wrapper():
        if 7 <= datetime.now().hour < 22:
            func()
        else:
            pass  # Hush, the neighbors are asleep
    return wrapper

def say_whee():
    print("Whee!")

# say_whee = my_decorator(say_whee)
say_whee = not_during_the_night(say_whee)

say_whee()
print(say_whee)

"""
데코레이터 핵심 내용
"""

def default_decorator(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        print('wrap-start')
        result = function(*args, **kwargs)
        print('wrap-end')
        return result
    return wrapper

def add_test(x, y):
    return x + y

@default_decorator
def add_test_decorated(x, y):
    return x + y

print(default_decorator(add_test)(2,3))

print(add_test_decorated(1, 2))

"""
@ 기호는 이후에 정의되는 함수를 래핑해주는 것.
"""

"""
아래는 테스트용 데코레이터 함수들
"""
def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()    # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()      # 2
        run_time = end_time - start_time    # 3
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return value
    return wrapper_timer

def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]                      # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)           # 3
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")           # 4
        return value
    return wrapper_debug

def slow_down(_func = None, delay_sec = 1.0):
    """Sleep delay_sec second before calling the function"""
    def slow_down_sec(func):
        @functools.wraps(func)
        def wrapper_slow_down(*args, **kwargs):
            time.sleep(delay_sec)
            return func(*args, **kwargs)
        return wrapper_slow_down
    
    if _func is None:
        return slow_down_sec
    return slow_down_sec(_func)

def countdown(from_number):
    if from_number < 1:
        print("Liftoff!")
    else:
        print(from_number)
        countdown(from_number - 1)

@slow_down(delay_sec = 0.75)
def countdown_decorated(from_number):
    if from_number < 1:
        print("Liftoff!")
    else:
        print(from_number)
        countdown_decorated(from_number - 1)

# slow_down(countdown(4), delay_sec = 0.75)(4) # 또다른 데코레이터 해석
# timer(countdown)(10)
# countdown_decorated(3)
# countdown(3)

def singleton(cls):
    """Make a class a Singleton class (only one instance)"""
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance:
            wrapper_singleton.instance = cls(*args, **kwargs)
        return wrapper_singleton.instance
    wrapper_singleton.instance = None
    return wrapper_singleton

@singleton
class TheOne:
    pass

first_one = TheOne()
another_one = TheOne()
print(id(first_one))
print(id(another_one))