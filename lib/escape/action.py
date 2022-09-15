from lib.foundation import *


class Gaze(Action):
    
    def do(self, owner:ActionComponent, target_pos):
        # target_pos:Vector = get_from_dict(kwargs, 'target_pos')
        self.owner.movement.turn_toward(target_pos - self.owner.body.position)


class TestBoost(Action):
    
    def do(self, owner: Union[Actor, ActionComponent], direction:Vector, impulse:float):
        owner.body.apply_impulse(direction.unit * impulse)


class TestShootBall(Action):
    
    def do(self, owner: Union[Actor, ActionComponent], proj_type, impulse):
        
        return self.fire(0, owner, proj_type, impulse)

    def fire(self, dt, owner:ActionComponent, proj_type, impulse):
        proj:DynamicObject = proj_type()
        proj.body.damping = 1.0
        return proj.spawn(owner.body.layers[0], owner.body.position, initial_impulse=owner.body.forward_vector * impulse)
        ''' somewhat bad usage becaues action attached on ActionComponent '''


class ToggleFireAction(TestShootBall):
    
    def __init__(self) -> None:
        super().__init__()
        self.fire_counter = 0
        self.on = False
    
    def do(self, owner:Union[Actor, ActionComponent], proj_type:type, impulse):
        self.on = not self.on
        if self.on:
            schedule_interval(self.fire, 0.06, owner, proj_type, impulse)
        else: unschedule(self.fire)


class TestAction(Action):
    
    def __init__(self) -> None:
        self.counter = 0
        super().__init__()
    
    def do(self, owner):
        ''' hellow '''
        print('hello action from', owner)
        self.counter = 0
        tick_for(self.something, 1, 1/3, owner)
        
    def something(self, delta_time:float, owner):
        print('test-action-tick', self.counter)
        self.counter += 1
    
    def stupid(self, dt):
        print('yeah', self.counter)
        self.counter += 1


class TestAction2(TestAction):
    
    def do(self, owner):
        self.counter = 0
        tick_for(self.stupid, 1, 1/3)


class TestFullAction(Action):
    
    def end(self, dt):
        print('full action end------')
    
    def do(self, owner):
        print('full action start-----')
        schedule_once(self.act, 1, owner)
    
    def act(self, dt, owner):
        print('action!!!')
        schedule_once(self.cooldown, 1, owner)
    
    def cooldown(self, dt, owner):
        print('cooldown...')
        schedule_once(self.end, 1)
    
    def reserved_do(self, duration, next_func):
        schedule_once(next_func, duration)