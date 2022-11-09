import copy
import hashlib

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, NamedTuple, Sequence, Union, cast

import pytiled_parser
import pytiled_parser.tiled_object
# from pytiled_parser.tiled_object import TiledObject

from pytiled_parser import Properties

from arcade import (
    AnimatedTimeBasedSprite,
    AnimationKeyframe,
    load_texture,
)       ### Should be deprecated

from config.engine import *
from lib.foundation.base import *
from lib.foundation.engine import *
from lib.foundation.component import CameraHandler

_FLIPPED_HORIZONTALLY_FLAG = 0x80000000
_FLIPPED_VERTICALLY_FLAG = 0x40000000
_FLIPPED_DIAGONALLY_FLAG = 0x20000000

PointList = Sequence[Point]
Rect = Union[Tuple[float, float, float, float], List[float]]  # x, y, width, height


def _get_image_info_from_tileset(tile: pytiled_parser.Tile):
    image_x = 0
    image_y = 0
    if tile.tileset.image is not None:
        margin = tile.tileset.margin or 0
        spacing = tile.tileset.spacing or 0
        row = tile.id // tile.tileset.columns
        image_y = margin + row * (tile.tileset.tile_height + spacing)
        col = tile.id % tile.tileset.columns
        image_x = margin + col * (tile.tileset.tile_width + spacing)

    if tile.tileset.image:
        width = tile.tileset.tile_width
        height = tile.tileset.tile_height
    else:
        width = tile.image_width
        height = tile.image_height

    return image_x, image_y, width, height


def _get_image_source(
    tile: pytiled_parser.Tile,
    map_directory: Optional[str],
) -> Optional[Path]:
    image_file = None
    if tile.image:
        image_file = tile.image
    elif tile.tileset.image:
        image_file = tile.tileset.image

    if not image_file:
        print(
            f"Warning for tile {tile.id}, no image source listed either for individual tile, or as a tileset."
        )
        return None

    if os.path.exists(image_file):
        return image_file

    if map_directory:
        try2 = Path(map_directory, image_file)
        if os.path.exists(try2):
            return try2

    print(f"Warning, can't find image {image_file} for tile {tile.id}")
    return None


class TiledObject(NamedTuple):
    shape: Union[Point, PointList, Rect]
    properties: Optional[Properties] = None
    name: Optional[str] = None
    class_: Optional[str] = None


class TiledMap:
    """ Tiled map based world class 
    
    Will be the biggest object handling all retroactive game objects like sprites, physics.
    
    - loading Tiled map(JSON)
    - tile layer support (name matching)
    - object layer or property (spawner, ...)
    - draw(), update()
    
    """
    def __init__(
        self,
        scale:float = 1.0,
        use_spatial_hash: Optional[bool] = None,
        hit_box_algorithm: str = "Simple",
        hit_box_detail: float = 4.5,
        offset: Vector = vectors.zero,
        space:PhysicsSpace = None,
        ) -> None:
        
        if space is None:
            try:
                space = getattr(self, 'space')
            except:
                self.default_space:PhysicsSpace = PhysicsSpace()
        else:
            self.default_space = space
        
        self.map:pytiled_parser.TiledMap= None
        ''' map data '''
        self.map_hash = None
        ''' hexdigest md5 of map json for cache comparison '''
        self.map_static_collision = []
        ''' static collision cache for map '''
        self.map_static_collision_cached = False
        ''' is collision cached '''
        self.size:Vector = None
        ''' size of map '''
        self.tile_size:Vector = None
        ''' size of tile '''
        self.bg_color = None
        ''' empty background color '''
        self.scale:float = scale
        ''' scale of tile '''
        self.use_spatial_hash:bool = use_spatial_hash
        ''' sprite spatial hash '''
        self.hit_box_algorithm:str = hit_box_algorithm
        ''' sprite hit box detail algorithm '''
        self.hit_box_detail:float = hit_box_detail
        ''' sprite hit box detail parameter '''
        self.offset:Vector = offset
        ''' map offset '''
        self.tile_layers:Dict[str, ObjectLayer] = OrderedDict()
        ''' field / static / dynamic layers '''
        self.object_layers:Dict[str, List[TiledObject]] = OrderedDict()
        ''' Tiled objects '''
        self.camera: Union[Camera, CameraHandler] = None
        ''' Viewport for world draw '''
    
    def load_map(
        self, 
        filepath:Union[str, Path] = None,
        # scale:float = 1.0,
        layer_options: Optional[Dict[str, Dict[str, Any]]] = None,
        # use_spatial_hash: Optional[bool] = None,
        # hit_box_algorithm: str = "Detailed",
        # hit_box_detail: float = 4.5,
        # offset: Vector = vectors.zero,
        tiled_map: Optional[pytiled_parser.TiledMap] = None,
        ) -> arcade.TileMap:
        
        # self.__init__(
        #     scale=scale,
        #     use_spatial_hash=use_spatial_hash,
        #     hit_box_algorithm=hit_box_algorithm,
        #     hit_box_detail=hit_box_detail,
        #     offset=offset,
        # )
        
        a = load_json(get_path(filepath))
        a = json.dumps(a, sort_keys=True).encode('utf-8')
        print(hashlib.md5(a).hexdigest())
        ### cd7ababb1ccdaa97c8004b127ed2c86d
        
        if not filepath: raise AttributeError('No map file path')
        self.map = tiled_map or pytiled_parser.parse_map(Path(get_path(filepath)))
        if self.map.infinite: raise AttributeError('Infinite map currently not supported')

        ### Try to get static collision data from cache
        self.map_hash = get_json_md5_hexdigest(str(self.map.map_file))
        collision_cache_filepath = ''.join(get_path(str(self.map.map_file)).split('.')[0:-1]) + '.cc'
        try:
            with open(collision_cache_filepath, 'rb') as f:
                map_cc = pickle.load(f)
        except:
            pass   
        else:
            if map_cc:
                if map_cc[0] == self.map_hash:
                    self.map_static_collision = map_cc[1]
                    self.map_static_collision_cached = True
        ### End of static collision cache process     
        
        print(self.map.map_file, collision_cache_filepath)
        
        self.size = Vector(*self.map.map_size)
        self.tile_size = Vector(*self.map.tile_size)
        self.bg_color = self.map.background_color
        self.properties = self.map.properties
        
        global_options = {  # type: ignore
            "scale": self.scale,
            "use_spatial_hash": self.use_spatial_hash,
            "hit_box_algorithm": self.hit_box_algorithm,
            "hit_box_detail": self.hit_box_detail,
            "offset": self.offset,
            "custom_class": None,
            "custom_class_args": {},
        }
        
        for layer in self.map.layers:
            if (layer.name in self.tile_layers) or (layer.name in self.object_layers):
                raise AttributeError(
                    f"You have a duplicate layer name '{layer.name}' in your Tiled map. "
                    "Please use unique names for all layers and tilesets in your map."
                )
            self._process_layer(layer, global_options, layer_options)
        
    def _process_layer(
        self,
        layer: pytiled_parser.Layer,
        global_options: Dict[str, Any],
        layer_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:

        processed: Union[
            ObjectLayer, Tuple[Optional[ObjectLayer], Optional[List[TiledObject]]]
        ]

        options = global_options

        if layer_options:
            if layer.name in layer_options:
                options = {
                    key: layer_options[layer.name].get(key, global_options[key])
                    for key in global_options
                }
                # options = new_options

        if isinstance(layer, pytiled_parser.TileLayer):
            processed = self._process_tile_layer(layer, **options)
            self.tile_layers[layer.name] = processed
            if processed.properties:
                if processed.properties.get('world_static', True):
                    if not self.map_static_collision_cached:
                        self.map_static_collision.extend(get_merged_convexes(processed))
                    
        elif isinstance(layer, pytiled_parser.ObjectLayer):
            processed = self._process_object_layer(layer, **options)
            if processed[0]:
                sprite_list = processed[0]
                if sprite_list:
                    self.tile_layers[layer.name] = sprite_list
            if processed[1]:
                object_list = processed[1]
                if object_list:
                    self.object_layers[layer.name] = object_list
        elif isinstance(layer, pytiled_parser.ImageLayer):
            pass
        #     processed = self._process_image_layer(layer, **options)
        #     self.tile_layers[layer.name] = processed
        elif isinstance(layer, pytiled_parser.LayerGroup):
            for sub_layer in layer.layers:
                self._process_layer(sub_layer, global_options, layer_options)
        
        if self.map_static_collision:
            self.default_space.add_static_collison(
                        shape_data = self.map_static_collision,
                        collision_type= collision.wall
                    )
            if not self.map_static_collision_cached:
                collision_cache_filepath = ''.join(get_path(str(self.map.map_file)).split('.')[0:-1]) + '.cc'
                
                with open(collision_cache_filepath, 'wb') as f:
                    pickle.dump((self.map_hash, self.map_static_collision), f)

    def _get_tile_by_gid(self, tile_gid: int) -> Optional[pytiled_parser.Tile]:
        flipped_diagonally = False
        flipped_horizontally = False
        flipped_vertically = False

        if tile_gid & _FLIPPED_HORIZONTALLY_FLAG:
            flipped_horizontally = True
            tile_gid -= _FLIPPED_HORIZONTALLY_FLAG

        if tile_gid & _FLIPPED_DIAGONALLY_FLAG:
            flipped_diagonally = True
            tile_gid -= _FLIPPED_DIAGONALLY_FLAG

        if tile_gid & _FLIPPED_VERTICALLY_FLAG:
            flipped_vertically = True
            tile_gid -= _FLIPPED_VERTICALLY_FLAG

        for tileset_key, tileset in self.map.tilesets.items():
            if tile_gid < tileset_key:
                continue

            # No specific tile info, but there is a tile sheet
            # print(f"data {tileset_key} {tileset.tiles} {tileset.image} {tileset_key} {tile_gid} {tileset.tile_count}")  # noqa
            if (
                tileset.image is not None
                and tileset_key <= tile_gid < tileset_key + tileset.tile_count
            ):
                # No specific tile info, but there is a tile sheet
                tile_ref = pytiled_parser.Tile(
                    id=(tile_gid - tileset_key), image=tileset.image
                )
                if tileset.tiles:
                    from_tileset = tileset.tiles.get(tile_gid)
                    if from_tileset:
                        tile_ref.properties = from_tileset.properties      ### Manually inject properties, by mash
            elif tileset.tiles is None and tileset.image is not None:
                # Not in this tileset, move to the next
                continue
            else:
                if tileset.tiles is None:
                    return None
                tile_ref = tileset.tiles.get(tile_gid - tileset_key)
                        
            if tile_ref:
                my_tile = copy.copy(tile_ref)
                my_tile.tileset = tileset
                my_tile.flipped_vertically = flipped_vertically
                my_tile.flipped_diagonally = flipped_diagonally
                my_tile.flipped_horizontally = flipped_horizontally
                return my_tile

        print(f"Returning NO tile for {tile_gid}.")
        return None

    def _get_tile_by_id(
        self, 
        tileset: pytiled_parser.Tileset, 
        tile_id: int
    ) -> Optional[pytiled_parser.Tile]:
        for tileset_key, cur_tileset in self.map.tilesets.items():
            if cur_tileset is tileset:
                for tile_key, tile in cur_tileset.tiles.items():
                    if tile_id == tile.id:
                        return tile

        return None

    def _create_sprite_from_tile(
        self,
        tile: pytiled_parser.Tile,
        scale: float = 1.0,
        hit_box_algorithm: str = "Detailed",
        hit_box_detail: float = 4.5,
        custom_class: Optional[type] = None,
        custom_class_args: Dict[str, Any] = {},
    ) -> Sprite:
        """Given a tile from the parser, try and create a Sprite from it."""

        if tile.properties:
            hit_box_algorithm = get_from_dict(tile.properties, 'hit_box_algorithm', hit_box_algorithm)
            hit_box_detail = get_from_dict(tile.properties, 'hit_box_detail', hit_box_detail)
            angle = get_from_dict(tile.properties, 'angle', 0.0)
            scale = get_from_dict(tile.properties, 'scale', scale)
        
        # --- Step 1, Find a reference to an image this is going to be based off of
        map_source = self.map.map_file
        map_directory = os.path.dirname(map_source)
        image_file = _get_image_source(tile, map_directory)

        if tile.animation:
            if not custom_class:
                custom_class = AnimatedTimeBasedSprite
            elif not issubclass(custom_class, AnimatedTimeBasedSprite):
                raise RuntimeError(
                    f"""
                    Tried to use a custom class {custom_class.__name__} for animated tiles
                    that doesn't subclass AnimatedTimeBasedSprite.
                    Custom classes for animated tiles must subclass AnimatedTimeBasedSprite.
                    """
                )
            args = {"filename": image_file, "scale": scale}
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore
        else:
            if not custom_class:
                custom_class = Sprite
            elif not issubclass(custom_class, Sprite):
                raise RuntimeError(
                    f"""
                    Tried to use a custom class {custom_class.__name__} for
                    a tile that doesn't subclass arcade.Sprite.
                    Custom classes for tiles must subclass arcade.Sprite.
                    """
                )
            image_x, image_y, width, height = _get_image_info_from_tileset(tile)
            args = {
                "filename": image_file,
                "scale": scale,
                "image_x": image_x,
                "image_y": image_y,
                "image_width": width,
                "image_height": height,
                "flipped_horizontally": tile.flipped_horizontally,
                "flipped_vertically": tile.flipped_vertically,
                "flipped_diagonally": tile.flipped_diagonally,
                "hit_box_algorithm": hit_box_algorithm,  # type: ignore
                "hit_box_detail": hit_box_detail,
            }
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore

        if tile.properties is not None and len(tile.properties) > 0:
            for key, value in tile.properties.items():
                my_sprite.properties[key] = value
        
        if tile.class_:
            print(tile.properties)
            my_sprite.properties["class"] = tile.class_

        # Add tile ID to sprite properties
        my_sprite.properties["tile_id"] = tile.id

        if tile.objects is not None:        ### set sprite.hit_box
            if not isinstance(tile.objects, pytiled_parser.ObjectLayer):
                print("Warning, tile.objects is not an ObjectLayer as expected.")
                return my_sprite

            if len(tile.objects.tiled_objects) > 1:
                if tile.image:
                    print(
                        f"Warning, only one hit box supported for tile with image {tile.image}."
                    )
                else:
                    print("Warning, only one hit box supported for tile.")

            for hitbox in tile.objects.tiled_objects:
                points: List[Point] = []
                if isinstance(hitbox, pytiled_parser.tiled_object.Rectangle):
                    if hitbox.size is None:
                        print(
                            "Warning: Rectangle hitbox created for without a "
                            "height or width Ignoring."
                        )
                        continue

                    sx = hitbox.coordinates.x - (my_sprite.width / (scale * 2))
                    sy = -(hitbox.coordinates.y - (my_sprite.height / (scale * 2)))
                    ex = (hitbox.coordinates.x + hitbox.size.width) - (
                        my_sprite.width / (scale * 2)
                    )
                    # issue #1068
                    # fixed size of rectangular hitbox
                    ey = -(hitbox.coordinates.y + hitbox.size.height) + (
                        my_sprite.height / (scale * 2)
                    )

                    points = [[sx, sy], [ex, sy], [ex, ey], [sx, ey]]
                elif isinstance(
                    hitbox, pytiled_parser.tiled_object.Polygon
                ) or isinstance(hitbox, pytiled_parser.tiled_object.Polyline):
                    for point in hitbox.points:
                        adj_x = (
                            point.x
                            + hitbox.coordinates.x
                            - my_sprite.width / (scale * 2)
                        )
                        adj_y = -(
                            point.y
                            + hitbox.coordinates.y
                            - my_sprite.height / (scale * 2)
                        )
                        adj_point = [adj_x, adj_y]
                        points.append(adj_point)

                    if points[0][0] == points[-1][0] and points[0][1] == points[-1][1]:
                        points.pop()
                elif isinstance(hitbox, pytiled_parser.tiled_object.Ellipse):
                    if not hitbox.size:
                        print(
                            f"Warning: Ellipse hitbox created without a height "
                            f" or width for {tile.image}. Ignoring."
                        )
                        continue

                    hw = hitbox.size.width / 2
                    hh = hitbox.size.height / 2
                    cx = hitbox.coordinates.x + hw
                    cy = hitbox.coordinates.y + hh

                    acx = cx - (my_sprite.width / (scale * 2))
                    acy = cy - (my_sprite.height / (scale * 2))

                    total_steps = 8
                    angles = [
                        step / total_steps * 2 * math.pi for step in range(total_steps)
                    ]
                    for angle in angles:
                        x = hw * math.cos(angle) + acx
                        y = -(hh * math.sin(angle) + acy)
                        points.append([x, y])
                else:
                    print(f"Warning: Hitbox type {type(hitbox)} not supported.")

                if tile.flipped_vertically:
                    for point in points:
                        point[1] *= -1

                if tile.flipped_horizontally:
                    for point in points:
                        point[0] *= -1

                if tile.flipped_diagonally:
                    for point in points:
                        point[0], point[1] = point[1], point[0]

                my_sprite.hit_box = points

        if tile.animation:
            key_frame_list = []
            for frame in tile.animation:
                frame_tile = self._get_tile_by_id(tile.tileset, frame.tile_id)
                if frame_tile:
                    image_file = _get_image_source(frame_tile, map_directory)

                    if frame_tile.image and image_file:
                        texture = load_texture(image_file)
                    elif not frame_tile.image and image_file:
                        # No image for tile, pull from tilesheet
                        (
                            image_x,
                            image_y,
                            width,
                            height,
                        ) = _get_image_info_from_tileset(frame_tile)

                        texture = load_texture(
                            image_file, image_x, image_y, width, height
                        )
                    else:
                        raise RuntimeError(
                            f"Warning: failed to load image for animation frame for "
                            f"tile '{frame_tile.id}', '{image_file}'."
                        )

                    key_frame = AnimationKeyframe(  # type: ignore
                        frame.tile_id, frame.duration, texture
                    )
                    key_frame_list.append(key_frame)

                    if len(key_frame_list) == 1:
                        my_sprite.texture = key_frame.texture

            cast(AnimatedTimeBasedSprite, my_sprite).frames = key_frame_list

        return my_sprite

    def _process_image_layer(
        self,
    ):
        pass
    
    def _process_tile_layer(
        self,
        layer: pytiled_parser.TileLayer,
        scale: float = 1.0,
        use_spatial_hash: Optional[bool] = None,
        hit_box_algorithm: str = "Detailed",
        hit_box_detail: float = 4.5,
        offset: Vector = vectors.zero,
        custom_class: Optional[type] = None,
        custom_class_args: Dict[str, Any] = {},
    ) -> ObjectLayer:

        try:    ### set_physics default True, unless set to False manually
            set_physics = layer.properties.get('physics', True)
        except:
            set_physics = True
        
        sprite_list: ObjectLayer = ObjectLayer(
            self.default_space if set_physics else None,
            use_spatial_hash=use_spatial_hash)
        
        map_array = layer.data
        # Loop through the layer and add in the list
        
        tqdmed = tqdm(total = len(map_array) * len(map_array[0]), desc = f'Loading {layer.name}')
        for row, rows in enumerate(map_array):
            for col, item in enumerate(rows):
                # Check for an empty tile
                if item == 0:
                    continue
                tile = self._get_tile_by_gid(item)
                if tile is None:
                    raise ValueError(
                        (
                            f"Couldn't find tile for item {item} in layer "
                            f"'{layer.name}' in file '{self.map.map_file}'"
                            f"at ({col}, {row})."
                        )
                    )
                
                my_sprite:Sprite
                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scale=scale,
                    hit_box_algorithm=hit_box_algorithm,
                    hit_box_detail=hit_box_detail,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )
                
                if my_sprite is None:
                    print(
                        f"Warning: Could not create sprite number {item} in layer '{layer.name}' {tile.image}"
                    )
                else:
                    my_sprite.center_x = (
                        col * (self.map.tile_size[0] * scale)
                        + my_sprite.width / 2
                    ) + offset[0]
                    my_sprite.center_y = (
                        (self.map.map_size.height - row - 1)
                        * (self.map.tile_size[1] * scale)
                        + my_sprite.height / 2
                    ) + offset[1]

                    # Tint
                    if layer.tint_color:
                        my_sprite.color = layer.tint_color

                    # Opacity
                    opacity = layer.opacity
                    if opacity:
                        my_sprite.alpha = int(opacity * 255)
                    
                    class_ = get_class_loaded(tile.class_)
                    if class_ is None:
                        sprite_list.append(my_sprite)
                    else:
                        sprite_list.add(
                            class_(sprite = my_sprite)
                        )
                tqdmed.update(1)

        sprite_list.visible = layer.visible
        if layer.properties:
            sprite_list.properties = layer.properties
        
        return sprite_list
    
    def _process_object_layer(
        self,
        layer: pytiled_parser.ObjectLayer,
        scale: float = 1.0,
        use_spatial_hash: Optional[bool] = None,
        hit_box_algorithm: str = "Detailed",
        hit_box_detail: float = 4.5,
        offset: Vector = vectors.zero,
        custom_class: Optional[type] = None,
        custom_class_args: Dict[str, Any] = {},
    ) -> Tuple[Optional[ObjectLayer], Optional[List[TiledObject]]]:

        if not scale:
            scale = self.scale

        try:    ### set_physics default True, unless set to False manually
            set_physics = layer.properties.get('physics', True)
        except:
            set_physics = True
        
        sprite_list: Optional[ObjectLayer] = None
        objects_list: Optional[List[TiledObject]] = []

        for cur_object in layer.tiled_objects:
            # shape: Optional[Union[Point, PointList, Rect]] = None
            if isinstance(cur_object, pytiled_parser.tiled_object.Tile):
                if not sprite_list:
                    sprite_list = ObjectLayer(
                        self.default_space if set_physics else None,
                        use_spatial_hash=use_spatial_hash)
                    sprite_list.visible = layer.visible

                tile = self._get_tile_by_gid(cur_object.gid)
                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scale=scale,
                    hit_box_algorithm=hit_box_algorithm,
                    hit_box_detail=hit_box_detail,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )

                x = (cur_object.coordinates.x * scale) + offset[0]
                y = (
                    (
                        self.map.map_size.height * self.map.tile_size[1]
                        - cur_object.coordinates.y
                    )
                    * scale
                ) + offset[1]

                my_sprite.width = width = cur_object.size[0] * scale
                my_sprite.height = height = cur_object.size[1] * scale
                center_x = width / 2
                center_y = height / 2
                x += center_x
                y += center_y
                if cur_object.rotation:
                    rotation = -math.radians(cur_object.rotation)
                else:
                    rotation = 0

                angle_degrees = math.degrees(rotation)
                rotated_center_x, rotated_center_y = rotate_point(
                    (0,0), angle_degrees, (width / 2, height / 2)
                )

                my_sprite.position = (x + rotated_center_x, y + rotated_center_y)
                my_sprite.angle = angle_degrees

                if layer.tint_color:
                    my_sprite.color = layer.tint_color

                opacity = layer.opacity
                if opacity:
                    my_sprite.alpha = int(opacity * 255)

                if cur_object.properties and "change_x" in cur_object.properties:
                    my_sprite.change_x = float(cur_object.properties["change_x"])

                if cur_object.properties and "change_y" in cur_object.properties:
                    my_sprite.change_y = float(cur_object.properties["change_y"])

                if cur_object.properties and "boundary_bottom" in cur_object.properties:
                    my_sprite.boundary_bottom = float(
                        cur_object.properties["boundary_bottom"]
                    )

                if cur_object.properties and "boundary_top" in cur_object.properties:
                    my_sprite.boundary_top = float(
                        cur_object.properties["boundary_top"]
                    )

                if cur_object.properties and "boundary_left" in cur_object.properties:
                    my_sprite.boundary_left = float(
                        cur_object.properties["boundary_left"]
                    )

                if cur_object.properties and "boundary_right" in cur_object.properties:
                    my_sprite.boundary_right = float(
                        cur_object.properties["boundary_right"]
                    )

                if cur_object.properties:
                    my_sprite.properties.update(cur_object.properties)
                
                class_ = get_class_loaded(tile.class_)
                if class_ is None:
                    sprite_list.append(my_sprite)
                else:
                    sprite_list.add(
                        class_(sprite = my_sprite)
                    )
                
                if cur_object.name:     ### What is this for?
                    my_sprite.properties["name"] = cur_object.name

                continue
            
            elif isinstance(cur_object, pytiled_parser.tiled_object.Point):
                x = cur_object.coordinates.x * scale
                y = (
                    self.map.map_size.height * self.map.tile_size[1]
                    - cur_object.coordinates.y
                ) * scale

                shape = [x + offset[0], y + offset[1]]
            elif isinstance(cur_object, pytiled_parser.tiled_object.Rectangle):
                if cur_object.size.width == 0 and cur_object.size.height == 0:
                    print(
                        f"WARNING: Tiled object with ID {cur_object.id} is a rectangle "
                        "with a width and height of 0. Loading it as a single point."
                    )
                    x = cur_object.coordinates.x * scale
                    y = (
                        self.map.map_size.height * self.map.tile_size[1]
                        - cur_object.coordinates.y
                    ) * scale

                    shape = [x + offset[0], y + offset[1]]
                else:
                    x = cur_object.coordinates.x + offset[0]
                    y = cur_object.coordinates.y + offset[1]
                    sx = x
                    sy = -y
                    ex = x + cur_object.size.width
                    ey = -(y + cur_object.size.height)

                    p1 = [sx, sy]
                    p2 = [ex, sy]
                    p3 = [ex, ey]
                    p4 = [sx, ey]

                    shape = [p1, p2, p3, p4]
            elif isinstance(
                cur_object, pytiled_parser.tiled_object.Polygon
            ) or isinstance(cur_object, pytiled_parser.tiled_object.Polyline):
                shape = []
                for point in cur_object.points:
                    x = point.x + cur_object.coordinates.x
                    y = (self.size.y * self.tile_size.y) - (
                        point.y + cur_object.coordinates.y
                    )
                    point = (x + offset[0], y + offset[1])
                    shape.append(point)

                # If shape is a polyline, and it is closed, we need to remove the duplicate end point
                if shape[0][0] == shape[-1][0] and shape[0][1] == shape[-1][1]:
                    shape.pop()
            elif isinstance(cur_object, pytiled_parser.tiled_object.Ellipse):
                hw = cur_object.size.width / 2
                hh = cur_object.size.height / 2
                cx = cur_object.coordinates.x + hw
                cy = cur_object.coordinates.y + hh

                total_steps = 8
                angles = [
                    step / total_steps * 2 * math.pi for step in range(total_steps)
                ]
                shape = []
                for angle in angles:
                    x = hw * math.cos(angle) + cx
                    y = -(hh * math.sin(angle) + cy)
                    point = [x + offset[0], y + offset[1]]
                    shape.append(point)
            else:
                continue

            if shape:
                tiled_object = TiledObject(
                    shape, cur_object.properties, cur_object.name, cur_object.class_
                )

                if not objects_list:
                    objects_list = []

                objects_list.append(tiled_object)

        return sprite_list or None, objects_list or None

    def setup(self):
        
        if not self.map: return False
        '''
        Object spawnning will be here
        '''
    
    def _create_actor_from_tile(self, class_name: str , *args, **kwds):
        #WIP
        
        # print('sys.modules',sys.modules[__name__])
        class_ = get_class_loaded(class_name)
        # return class_
        # return class_(*args, **kwds)
        
    def tick(self, delta_time:float):
        pass
    
    def draw(self):
        if self.camera:
            self.camera.use()
        for name, layer in self.tile_layers.items():
            layer.draw()


if __name__ != "__main__":
    print("include", __name__, ":", __file__)
