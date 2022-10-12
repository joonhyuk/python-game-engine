from __future__ import annotations

from .object import *
from .action import *
from .movement import *
from .app import *


class Controller(GameObject):
    
    def setup(self, **kwargs) -> None:
        self.body : BodyHandler = self.owners(BodyHandler)
        self.movement : MovementHandler = self.owners(MovementHandler)
        self.action : ActionHandler = self.owners(ActionHandler)
        return super().setup(**kwargs)
    
    def spawn(self) -> GameObject:
        super().spawn()
        GAME.controllers.append(self)
        return self
    
    def tick(self, delta_time:float) -> bool:
        if not self.available: return False
        return True
        
    def destroy(self) -> None:
        GAME.controllers.remove(self)
        return super().destroy()
    

class PlayerController(Controller):
    
    def setup(self, **kwargs) -> None:
        self.local_player_id : int = None
        ''' for local multiplay '''
        return super().setup(**kwargs)
    
    def on_spawn(self) -> None:
        GAME.add_player(self)       ### push handlers to self
    
    def tick(self, delta_time: float) -> bool:
        # print(GAME.target_point)
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
        pass
    
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
        # GAME.remove_player(self)
    
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


