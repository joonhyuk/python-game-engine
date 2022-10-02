from __future__ import annotations

from .object import *
from .action import *
from .common import *

class Controller(Handler):
    
    def __init__(
        self,
        movement : MovementHandler,
        action : ActionHandler,
        ) -> None:
        
        super().__init__()
        self.movement = movement
        self.action = action
    
    def spawn(self) -> GameObject:
        GAME.controllers.append(self)
        return super().spawn()
    
    def tick(self, delta_time:float) -> bool:
        if not self.spawnned : return False
        if not self.owner.alive : return False
        
    def destroy(self) -> None:
        GAME.controllers.remove(self)
        return super().destroy()


class PlayerController(Controller):
    
    def setup(self) -> None:
        self.local_player_id : int = None
        ''' for local multiplay '''
    
    def on_spawn(self) -> None:
        GAME.add_player(self)
        return super().on_spawn()
    
    def tick(self, delta_time: float) -> bool:
        if not super().tick(delta_time) : return False
        
        self.movement.turn_to_position(GAME.target_point)
        self.movement.move_direction = GAME.move_input
        GAME.debug_text['player_speed'] = round(self.body.speed, 1)
        
        return True
    
    def on_key_press(self, key: int, modifiers: int):
        pass
    
    def on_key_release(self, key: int, modifiers: int):
        pass
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        GAME.mouse_screen_position = Vector(x, y)
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        pass
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        pass
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        pass
    
    def on_joybutton_press(self, _joystick, button):
        print("TEST : Button {} down".format(button))
        GAME.remove_player(self)
    
    def on_joybutton_release(self, _joystick, button):
        pass
    
    
    @property
    def lstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not GAME.gamepads[self.local_player_id]: return None
        x = map_range_abs(GAME.gamepads[self.local_player_id].x, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True)
        y = map_range_abs(GAME.gamepads[self.local_player_id].y, CONFIG.gamepad_deadzone_lstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    
    @property
    def rstick(self) -> Vector:
        ''' returns raw info of left stick (-1, -1) ~ (1, 1) '''
        if not GAME.gamepads[self.local_player_id]: return None
        x = map_range_abs(GAME.gamepads[self.local_player_id].rx, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True)
        y = map_range_abs(GAME.gamepads[self.local_player_id].ry, CONFIG.gamepad_deadzone_rstick, 1, 0, 1, True) * -1
        return Vector(x, y)
    