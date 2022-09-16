from lib.foundation.component import *
from .action import *

from config.game import * 

class EscapePlayerController(PlayerController):
    
    def on_key_press(self, key: int, modifiers: int):
        #TODO
        '''
        todo::
        - input config support (key, mouse, gamepad)
        - action manager component (movement, character action, system action)
        '''
        if key in (keys.W, keys.UP): ENV.input_move += vectors.up
        if key in (keys.S, keys.DOWN): ENV.input_move += vectors.down
        if key in (keys.A, keys.LEFT): ENV.input_move += vectors.left
        if key in (keys.D, keys.RIGHT): ENV.input_move += vectors.right
        
        if key == keys.LSHIFT: self.movement.speed_level = 2
        # if key == keys.LSHIFT: self.lshift_applied = True
        # if key == keys.LCTRL: self.lctrl_applied = True

        if key == keys.SPACE: self.actions.test_boost(ENV.input_move, 500)
        if key == keys.ENTER: self.actions.test_attack(self.body.forward_vector, 200)
        if key == keys.H: self.body.hidden = None
        
        if key == keys.Z:
            APP.debug_text.perf_check('DELEGATED_ACTION_DELAY') 
            self.actions.test_action()
            APP.debug_text.perf_check('DELEGATED_ACTION_DELAY') 
        
        if key == keys.X:
            self.actions.test_action_2()
            
        if key == keys.B:
            self.actions.toggle_ball(self.owner.projectile, 1000)
        
    def on_key_release(self, key: int, modifiers: int):
        if key in (keys.W, keys.UP): ENV.input_move -= vectors.up
        if key in (keys.S, keys.DOWN): ENV.input_move -= vectors.down
        if key in (keys.A, keys.LEFT): ENV.input_move -= vectors.left
        if key in (keys.D, keys.RIGHT): ENV.input_move -= vectors.right
        if key == keys.LSHIFT: self.movement.speed_level = 1
        # if key == keys.LSHIFT: self.lshift_applied = False
        # if key == keys.LCTRL: self.lctrl_applied = False

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        #TODO
        '''
        todo::
        - hold support by default (with Client or PlayerController base classes)
        - operate action via action manager component
        '''
        ENV.last_mouse_lb_hold_time = CLOCK.perf
        APP.debug_text.timer_start('mouse_lb_hold')
        # self.owner.test_directional_attack(distance=500)
        # APP.debug_text.perf_check('DELEGATED_ATTACK_DELAY') 
        # self.actions.test_attack()
        # APP.debug_text.perf_check('DELEGATED_ATTACK_DELAY') 
        
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        ENV.last_mouse_lb_hold_time = CLOCK.perf - ENV.last_mouse_lb_hold_time
        APP.debug_text.timer_end('mouse_lb_hold', 3)
        
        self._tmp = self.actions.test_projectile(self.owner.projectile, map_range(ENV.last_mouse_lb_hold_time, 0, 3, 800, 5000, True))
        # self._tmp = self.actions.test_shoot_ball()


class TestAIActionComponent(ActionHandler):
    
    gaze = Gaze()  


class EscapeCharacterActionHandler(ActionHandler):
    
    test_action = TestAction()
    test_action_2 = TestAction2()
    toggle_ball = ToggleFireAction2()
    test_boost = TestBoost()
    test_projectile = TestShootBall()
    
    body:DynamicBody = None
    
    def setup(self):
        pass
    
    def test_attack(self, direction:Vector = None, range:float = 500):
        self.movement._move_modifier = 0.2
        self.movement._turn_modifier = 0.1
        
        if direction is None: direction = self.body.forward_vector
        
        def delayed_action(dt, direction, range):
            print(self.body.physics.segment_query(self.body.position + direction * range, radius=5))
            self.movement._move_modifier = 1.0
            self.movement._turn_modifier = 1.0
        
        unschedule(delayed_action)
        schedule_once(delayed_action, 1, direction, range)
            

class EscapePlayerMovement(TopDownPhysicsMovement):
    pass


class EscapeAIMovement(TopDownPhysicsMovement):
    
    def tick(self, delta_time: float) -> bool:
        # if self.desired_angle != 0.0:
        #     print(self.owner, 'moving!')
        return super().tick(delta_time)


class TestAIController(AIController):
    
    target:DynamicObject = None
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        if CONFIG.debug_f_keys[7]:
            self.actions.gaze(target_pos = self.target.position)
        if CONFIG.debug_f_keys[6]:
            dist = get_distance(*self.body.position, *self.target.position)
            if dist > 100:
                self.movement.move(self.body.forward_vector * dist)
