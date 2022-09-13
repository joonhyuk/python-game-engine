from lib.foundation.component import *

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
        # if key == keys.LSHIFT: self.lshift_applied = True
        # if key == keys.LCTRL: self.lctrl_applied = True

        if key == keys.SPACE: self.actions.test_boost(ENV.input_move, 500)
        if key == keys.ENTER: self.actions.test_attack(self.body.forward_vector, 200)
        if key == keys.H: self.body.hidden = None
        
    def on_key_release(self, key: int, modifiers: int):
        if key in (keys.W, keys.UP): ENV.input_move -= vectors.up
        if key in (keys.S, keys.DOWN): ENV.input_move -= vectors.down
        if key in (keys.A, keys.LEFT): ENV.input_move -= vectors.left
        if key in (keys.D, keys.RIGHT): ENV.input_move -= vectors.right
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
        self.actions.test_attack()
        
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        ENV.last_mouse_lb_hold_time = CLOCK.perf - ENV.last_mouse_lb_hold_time
        APP.debug_text.timer_end('mouse_lb_hold', 3)
        self._tmp = self.owner.test_projectile(map_range(ENV.last_mouse_lb_hold_time, 0, 3, 800, 5000, True))
        # self._tmp = self.actions.test_shoot_ball()
        

class EscapePlayerMovement(MovementHandler):
    pass