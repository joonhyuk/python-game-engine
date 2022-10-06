from .primitive import *
from .body import *


class ObjectLayer(arcade.SpriteList):
    """ extended spritelist with actor, body """
    def __init__(self, 
                 space:PhysicsSpace = None,
                 use_spatial_hash=None, spatial_hash_cell_size=128, is_static=False, atlas: arcade.TextureAtlas = None, capacity: int = 100, lazy: bool = False, visible: bool = True):
        super().__init__(use_spatial_hash, spatial_hash_cell_size, is_static, atlas, capacity, lazy, visible)
        self._space = space
    
    def _get_obj_tree(self, obj):
        actor:GameObject = None
        body:Body = None
        sprite:Sprite = None
        
        if isinstance(obj, (Sprite, SpriteCircle)):
            sprite = obj
        
        elif isinstance(obj, (Body, )):
            body = obj
            sprite = body.get_members(Sprite)[0]
        
        elif isinstance(obj, GameObject):
            actor = obj
            body = obj.get_members(Body)[0]
            sprite = body.get_members(Sprite)[0]
        
        else: raise Exception('ObjectLayer only accept Sprite, Body, Actor')
        
        return actor, body, sprite
        
    def add(self, obj:Union[GameObject, Body, Sprite, SpriteCircle]):
        
        actor, body, sprite = self._get_obj_tree(obj)
        
        if sprite:
            try:
                self.append(sprite)
            except ValueError:
                pass
        
        if self._space:
            if body:
                body:PhysicsBody
                if body.physics:
                    body.physics.spawn_in_space(self.space)
                    # self._add_to_physics(sprite, body.physics)
                    
                    # self._physics_instance.add_physics_object(sprite, body.physics)  ### add sprite-physics pair to engine for refering
                    # self._physics_instance.add_to_space(sprite)      ### add physics to space
    
    # def _add_to_physics(self, sprite:Sprite, physics:PhysicsObject):
    #     self.physics_instance.add_physics_object(sprite, physics)
    #     self.physics_instance.add_to_space(sprite)
    
    def remove(self, obj:Union[GameObject, Body, Sprite, SpriteCircle]):
        
        actor, body, sprite = self._get_obj_tree(obj)
        
        ''' 
        Because arcade spritelist remove method automatically remove body from physics,
        we don't need it
        
        if body:
           if body.physics:
               self.physics_instance.remove_sprite(sprite)
        '''
        return super().remove(sprite)
    
    def step(self, delta_time:float = 1/60, sync:bool = True):
        ''' Don't use it usually. For better performance, call directly from physics instance '''
        self._space.step(delta_time=delta_time, resync_objects=sync)
    
    def _get_physics(self):
        return self._space
    
    def _set_physics(self, physics_instance):
        #TODO : add feature of registreing sprites to another physics instance
        
        self._space = physics_instance
    
    space:PhysicsSpace = property(_get_physics, _set_physics)