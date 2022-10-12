from lib.foundation.component import *
from .action import *

import gc

from config.game import * 

class EscapePlayerController(PlayerController):
    
    
    def setup(self, **kwargs) -> None:
        self.action:EscapeCharacterActionHandler
        self._last_projectile = None
        
        return super().setup(**kwargs)
    
    def on_key_press(self, key: int, modifiers: int):
        #TODO
        '''
        todo::
        - input config support (key, mouse, gamepad)
        - action manager component (movement, character action, system action)
        '''
        if key in (keys.W, keys.UP): GAME.input_move += vectors.up
        if key in (keys.S, keys.DOWN): GAME.input_move += vectors.down
        if key in (keys.A, keys.LEFT): GAME.input_move += vectors.left
        if key in (keys.D, keys.RIGHT): GAME.input_move += vectors.right
        
        if key == keys.LSHIFT: self.movement.speed_level = 2
        # if key == keys.LSHIFT: self.lshift_applied = True
        # if key == keys.LCTRL: self.lctrl_applied = True

        if key == keys.SPACE: self.action.test_boost(GAME.input_move, 500)
        if key == keys.ENTER: self.action.test_attack(self.body.forward_vector, 200)
        if key == keys.H: self.body.hidden = None
        
        if key == keys.Z:
            GAME.debug_text.perf_check('DELEGATED_ACTION_DELAY') 
            self.action.test_action()
            GAME.debug_text.perf_check('DELEGATED_ACTION_DELAY') 
        
        if key == keys.X:
            self.action.test_action_2()
            
        if key == keys.B:
            self.action.toggle_ball(self.owner.projectile, 1000)
        
    def on_key_release(self, key: int, modifiers: int):
        if key in (keys.W, keys.UP): GAME.input_move -= vectors.up
        if key in (keys.S, keys.DOWN): GAME.input_move -= vectors.down
        if key in (keys.A, keys.LEFT): GAME.input_move -= vectors.left
        if key in (keys.D, keys.RIGHT): GAME.input_move -= vectors.right
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
        GAME.last_mouse_lb_hold_time = CLOCK.perf
        GAME.debug_text.timer_start('mouse_lb_hold')
        self.action.test_directional_attack(distance=500)
        # ENV.debug_text.perf_check('DELEGATED_ATTACK_DELAY') 
        # ENV.debug_text.perf_check('DELEGATED_ATTACK_DELAY') 
        
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        GAME.last_mouse_lb_hold_time = CLOCK.perf - GAME.last_mouse_lb_hold_time
        GAME.debug_text.timer_end('mouse_lb_hold', 3)
        
        self.action.test_projectile(self.owner.projectile, map_range(GAME.last_mouse_lb_hold_time, 0.2, 2, 500, 2000, True))
        # print(self._last_projectile)

class TestAIActionComponent(ActionHandler):
    
    gaze = Gaze()  


class EscapeCharacterActionHandler(ActionHandler):
    
    test_action = TestAction()
    test_action_2 = TestAction2()
    toggle_ball = ToggleFireAction2()
    test_boost = TestBoost()
    test_projectile = TestShootBall()
    jump = Jump()
    
    body:DynamicBody = None
    
    def test_attack(self, direction:Vector = None, range:float = 500):
        self.movement._move_modifier = 0.2
        # self.movement._turn_modifier = 1.0
        
        if direction is None: direction = self.body.forward_vector
        
        def delayed_action(dt, direction, range):
            print(self.body.physics.segment_query(self.body.position + direction * range, radius=5))
            self.movement._move_modifier = 1.0
            self.movement._turn_modifier = 1.0
        
        unschedule(delayed_action)
        schedule_once(delayed_action, 1, direction, range)
    
    def test_directional_attack(self, 
                                target_direction:Vector = None, 
                                thickness = 1.0,
                                distance = 500,
                                muzzle_speed:float = 300,
                                ):
        origin = self.body.position
        if not target_direction: target_direction = Vector.directional(self.body.angle)
        end = target_direction * distance + origin
        # self.body.physics.filter = pymunk.ShapeFilter(categories=0b1)
        shape_filter = pymunk.ShapeFilter(mask = pymunk.ShapeFilter.ALL_MASKS()^collision.character)
        
        query = self.body.physics.space.segment_query(end, origin, thickness / 2, shape_filter)
        # query = ENV.physics_engine.space.segment_query(origin, end, thickness / 2, shape_filter)
        if query:
            first_hit = query[0]
            
            ### BUGS below for now.
            try:
                victim:PhysicsObject = first_hit.shape.body.owner
            except:
                print('HIT_QUERY', first_hit.shape.body)
                pass
            else:
                print(victim, ' HIT!')
                victim.body.sprite.color = colors.RED
                # victim.destroy()
    

class EscapePlayerMovement(TopDownPhysicsMovement):
    
    def __del__(self):
        print('WHY??', self)
        return super().__del__()
    


class EscapeAIMovement(TopDownPhysicsMovement):
    #WIP
    def tick(self, delta_time: float) -> bool:
        # if self.desired_angle != 0.0:
        #     print(self.owner, 'moving!')
        return super().tick(delta_time)


class TestAIController(AIController):
    #WIP #test
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time): return False
        if CONFIG.debug_f_keys[7]:
            self.action.gaze(target_pos = self.target.position)
        if CONFIG.debug_f_keys[6]:
            dist = get_distance(*self.body.position, *self.target.position)
            if dist > 100:
                self.movement.move(self.body.forward_vector * dist)


class TestKinematicObject(StaticObject):
    
    def __init__(self, body: KinematicBody, **kwargs) -> None:
        super().__init__(body, **kwargs)