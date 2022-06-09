from scratch_decorator import singleton

@singleton
class SingletonDecorated:
    
    @classmethod
    def is_okay(cls):
        """
        classmethod will be not callable with decorated singleton class
        """
        print(cls)

class SingletonMethodType:
    __instance = None
    
    @classmethod
    def __getInstance(cls):
        return cls.__instance
    
    @classmethod
    def instance(cls, *args, **kwargs):
        cls.__instance = cls(*args, **kwargs)
        cls.instance = cls.__getInstance
        return cls.__instance
    
    @classmethod
    def is_okay(cls):
        print(cls.__instance)

class SingletonClass(object):
    __instance = None
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls.__instance, cls):
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

    @classmethod
    def is_okay(cls):
        print(cls.__instance)

class MyGameManager(SingletonClass):
    pass

a = SingletonDecorated()
b = SingletonDecorated()

c = MyGameManager()
d = MyGameManager()

e = SingletonClass()
f = SingletonClass()

print(a, b, c, d, e, f)
print(SingletonDecorated.is_okay())