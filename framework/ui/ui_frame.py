import pygame
from .ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr
from .ui_sprite import UiSprite
from .ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect

from typing import Iterable, overload
from dataclasses import dataclass

@dataclass
class BaseUiFrameInfo:
    """Note : size arg is ignored if a base surf is passed in"""
    size : pygame.typing.IntPoint
    do_clip : bool = False

    def __post_init__(self):
        ...

class UiFrameCacheLine:
    def __init__(self, priority : int, result : pygame.Surface, local_override : TransformedRect|None = None,
                 scale : pygame.Vector2|None = None, angle : float = 0, opacity : float = 1) -> None:
        self.priority : int = priority
        self.result : pygame.Surface = result
        self.scale : pygame.Vector2 = scale if scale is not None else pygame.Vector2(1, 1)
        self.angle : float = angle
        self.opacity : float = opacity
        self.local_override : TransformedRect|None = None

class UiFrame(UiSpriteGroup):
    MAX_CACHE_SIZE : int = 12
    def __init__(self, base_drawable_info : BaseDrawableInfo, elements : list[UiDrawable], ui_frame_info : BaseUiFrameInfo):
        """Note : size arg is ignored if a base surf is passed in"""
        super().__init__(base_drawable_info, elements)
        self._base_size : pygame.Vector2 = pygame.Vector2(ui_frame_info.size)
        if base_drawable_info.final_anchor is not None: self.change_anchor(base_drawable_info.final_anchor)
        self.obstructs_clicks = False
        self.temp_local_tranfs_rect : TransformedRect|None = None
        self._do_clip = ui_frame_info.do_clip
        self._surf : pygame.Surface|None = None
        self._curr_cache_no : int = 0
        self._cache_line_count : int = 0
        self._cache : dict[tuple[float, float], list[UiFrameCacheLine]] = {}
        if self._do_clip:
            self._render()

    def _next_cache_no(self) -> int:
        self._curr_cache_no += 1
        return self._curr_cache_no - 1

    @property
    def do_clip(self) -> bool:
        return self._do_clip

    @do_clip.setter
    def do_clip(self, value : bool):
        self._do_clip = value
        if value:
            self.unpack = False

    @property
    def size(self) -> pygame.Vector2:
        return self._base_size

    @size.setter
    def size(self, value : pygame.Vector2):
        self._base_size = value
        self._cache.clear()
    
    def translate_local_to_world(self, point : pygame.typing.Point) -> pygame.Vector2:
        if self.temp_local_tranfs_rect is None:
            point_v2 : pygame.Vector2 = pygame.Vector2(point)

            point_v2.rotate_ip(-self._angle)
            point_v2 *= self._scale.elementwise()

            local_topleft = self.position.calculate_anchor(self.size * self._scale.elementwise(), 'topleft', -self._angle)
            point_v2 += local_topleft
            return point_v2
        else:
            actual_tranfs_rect : TransformedRect = self.get_local_rotoscaled_rect()
            old_x_axis : pygame.Vector2 = (actual_tranfs_rect['topright'] - actual_tranfs_rect['topleft'])
            old_y_axis : pygame.Vector2 = (actual_tranfs_rect['bottomleft'] - actual_tranfs_rect['topleft'])
            x_axis : pygame.Vector2 = (self.temp_local_tranfs_rect['topright'] - self.temp_local_tranfs_rect['topleft']) / old_x_axis.length()
            y_axis : pygame.Vector2 = (self.temp_local_tranfs_rect['bottomleft'] - self.temp_local_tranfs_rect['topleft']) / old_y_axis.length()
            return point[0] * x_axis + point[1] * y_axis + self.temp_local_tranfs_rect['topleft']

    def translate_local_rect_to_world(self, rect : TransformedRect|pygame.Rect) -> TransformedRect:
        if isinstance(rect, pygame.Rect):
            rect_t : TransformedRect = {'topleft' : pygame.Vector2(rect.topleft), 'topright' : pygame.Vector2(rect.topright), 
                                        'bottomright' : pygame.Vector2(rect.bottomright), 'bottomleft' : pygame.Vector2(rect.bottomleft)}
        else: rect_t = rect
        return {k : self.translate_local_to_world(rect_t[k]) for k in rect_t}

    def get_local_rotoscaled_rect(self, use_parent_layout : bool = False) -> TransformedRect:
        if use_parent_layout and isinstance((layout_parent := self.get_frame_parent()), BaseLayout) and self in layout_parent.curr_layout:
            return layout_parent.curr_layout[self]
        return {anchor : self.position.calculate_anchor(self.size * self._scale.elementwise(), anchor, -self._angle) 
                        for anchor in ('topleft', 'topright', 'bottomright', 'bottomleft')}

    def get_world_rotoscaled_rect(self, frame : "UiFrame|None" = None, override_local_rect : TransformedRect|None = None, 
                                  use_parent_layout : bool = False) -> TransformedRect|None:
        ancestors = self.get_frame_ancestors(frame)
        if ancestors is None:
            return None
        current_result : TransformedRect = override_local_rect or self.get_local_rotoscaled_rect(use_parent_layout=use_parent_layout)
        for ancestor in ancestors:
            current_result = ancestor.translate_local_rect_to_world(current_result)
        return current_result
        
    def get_local_draw_rect(self, use_parent_layout : bool = False) -> pygame.Rect:
        local_trs_rect = self.get_local_rotoscaled_rect(use_parent_layout)
        return UiDrawable.get_draw_rect_from_transformed(local_trs_rect)

    @overload
    def get_world_draw_rect(self, frame : None = None, use_parent_layout : bool = False) -> pygame.Rect: ...
    @overload
    def get_world_draw_rect(self, frame : "UiFrame", use_parent_layout : bool = False) -> pygame.Rect|None: ...
    def get_world_draw_rect(self, frame : "UiFrame|None" = None, use_parent_layout : bool = False) -> pygame.Rect|None:
        world_trs_rect : TransformedRect|None = self.get_world_rotoscaled_rect(frame, use_parent_layout=use_parent_layout)
        if world_trs_rect is None: return None
        return UiDrawable.get_draw_rect_from_transformed(world_trs_rect)
        

    @staticmethod
    def _does_cache_match(cache_line : UiFrameCacheLine, scale : pygame.Vector2, angle : float, opacity : float,
                          local_override : TransformedRect|None = None) -> bool:
        SCALE_MARGIN : float = 0
        ANGLE_MARGIN : float = 0
        OPACITY_MARGIN : float = 0
        if ((scale - cache_line.scale).magnitude() < SCALE_MARGIN 
            and abs(angle - cache_line.angle) < ANGLE_MARGIN  
            and abs(opacity - cache_line.opacity) < OPACITY_MARGIN
            and local_override == cache_line.local_override):
            return True
        return False

    def _get_cached(self, scale : pygame.Vector2|None = None, angle : float = 0, opacity : float = 1, target_size : pygame.Vector2|None = None,
                    local_override : TransformedRect|None = None) -> pygame.Surface|None:
        if target_size is None:
            target_size = self.size
        if scale is None:
            scale = pygame.Vector2(1, 1)
        for cache_line in self._cache.get((target_size[0], target_size[1]), []):
            if UiFrame._does_cache_match(cache_line, scale, angle, opacity, local_override):
                cache_line.priority = self._next_cache_no()
                return cache_line.result
        return None

    def _cache_surf(self, target_size : pygame.Vector2|None = None, scale : pygame.Vector2|None = None, angle : float = 0,
                    opacity : float = 1, local_override : TransformedRect|None = None) -> UiFrameCacheLine:
        if target_size is None:
            target_size = self.size
        if scale is None:
            scale = pygame.Vector2(1, 1)
        result : pygame.Surface = pygame.Surface(target_size, pygame.SRCALPHA)
        for element in self.elements:
            element.draw(result, None)
        result = pygame.transform.scale_by(result, scale)
        result = pygame.transform.rotate(result, angle)
        a : int|None = result.get_alpha()
        result.set_alpha(round((255 if a is None else a) * self.get_true_opacity()))
        
        cache_line : UiFrameCacheLine = UiFrameCacheLine(self._next_cache_no(), result, local_override, scale, angle, opacity)
        self._add_to_cache(target_size, cache_line)
        return cache_line

    def _add_to_cache(self, target_size : pygame.Vector2, cache_line : UiFrameCacheLine):
        self._cache_line_count += 1
        if (target_size[0], target_size[1]) not in self._cache:
            self._cache[(target_size[0], target_size[1])] = []
            
        self._cache[(target_size[0], target_size[1])].append(cache_line)
        if self._cache_line_count > self.MAX_CACHE_SIZE:
            self._remove_oldest_cache_line()

    def _remove_oldest_cache_line(self) -> UiFrameCacheLine|None:
        lowest_priority : int = -1
        lowest_target_size : tuple[float, float]|None = None
        lowest_cache_line : UiFrameCacheLine|None = None
        for target_size, cache_line_list in self._cache.items():
            for cache_line in cache_line_list:
                if cache_line.priority < lowest_priority or lowest_cache_line is None:
                    lowest_target_size = target_size
                    lowest_cache_line = cache_line
                    lowest_priority = cache_line.priority
        if lowest_cache_line and lowest_target_size:
            self._cache[lowest_target_size].remove(lowest_cache_line)
            if len(self._cache[lowest_target_size]) == 0:
                del self._cache[lowest_target_size]
            self._cache_line_count -= 1
        return lowest_cache_line

    def _render(self, local_override : TransformedRect|None = None):
        scale : pygame.Vector2 = self.get_true_scale(local_override)
        angle : float = self.get_true_angle(local_override)
        opacity : float = self.get_true_opacity()
        if (cached_surf := self._get_cached(scale, angle, opacity, self.size, local_override)):
            self._surf = cached_surf
        else:
            self._surf = self._cache_surf(self.size, scale, angle, opacity, local_override).result

    def on_child_update(self, do_update_layout : bool = True):
        self._cache.clear()

    def draw(self, display : pygame.Surface, frame : "UiFrame|None" = None, 
             override_pos_local: TransformedRect|None = None, override_pos_global : pygame.Rect|None = None):
        if not self.visible:
            return
        self.temp_local_tranfs_rect = override_pos_local
        self.elements.sort(key = lambda d : d.zindex)
        if self._do_clip:
            self._render(override_pos_local)
            if self._surf is None: return
            draw_rect : pygame.Rect|None = self.calculate_draw_rect(override_pos_global, override_pos_local, frame)
            if draw_rect is None:
                return
            display.blit(self._surf, draw_rect)
        else:
            for element in self.elements:
                element.draw(display, self if frame is None else frame)
        self.temp_local_tranfs_rect = None

    def add(self, new_element: UiDrawable):
        super().add(new_element)
        self.on_child_update()

    def remove(self, element: UiDrawable):
        super().remove(element)
        self.on_child_update()

def local_imports4():
    global BaseLayout
    from .layouts.base_layout import BaseLayout