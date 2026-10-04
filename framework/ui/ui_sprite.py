import pygame
from .ui_position import AnyUiPosition, UiPosition, AnchorStr
from .ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect

from typing import overload, TypeAlias

class UiSpriteCacheLine:
    def __init__(self, priority : int, result : pygame.Surface, 
                 scale : pygame.Vector2|None = None, angle : float = 0, opacity : float = 1) -> None:
        self.priority : int = priority
        self.result : pygame.Surface = result
        self.scale : pygame.Vector2 = scale if scale is not None else pygame.Vector2(1, 1)
        self.angle : float = angle
        self.opacity : float = opacity

class UiSprite(UiDrawable):
    _base_surf_changeable = True
    MAX_CACHE_SIZE : int = 12
    def __init__(self, info : BaseDrawableInfo, base_surf : pygame.Surface):
        super().__init__(info)
        self._base_surf : pygame.Surface = base_surf
        self._surf : pygame.Surface
        self._cache : dict[pygame.Surface, list[UiSpriteCacheLine]] = {}
        self._curr_cache_no : int = 0
        self._cache_line_count : int = 0
        self._render()
        if info.final_anchor is not None: self.change_anchor(info.final_anchor)

    def _next_cache_no(self) -> int:
        self._curr_cache_no += 1
        return self._curr_cache_no - 1

    @property
    def base_surf(self) -> pygame.Surface:
        return self._base_surf

    @base_surf.setter
    def base_surf(self, new_value : pygame.Surface):
        if not self._base_surf_changeable:
            raise AttributeError(f"Base surf of {self} is not changeable.")
        if self._base_surf == new_value:
            return
        old_size = self._base_surf.get_size()
        new_size = new_value.get_size()
        self._base_surf = new_value
        self._render()
        self._trigger_parent_frame_update(old_size != new_size)

    @property
    def surf(self) -> pygame.Surface:
        return self._surf

    @property
    def size(self) -> pygame.Vector2:
        return pygame.Vector2(self._base_surf.get_size())
    
    def get_local_rotoscaled_rect(self, use_parent_layout : bool = False) -> TransformedRect:
        if use_parent_layout and isinstance((layout_parent := self.get_frame_parent()), BaseLayout) and self in layout_parent.curr_layout:
            return layout_parent.curr_layout[self]
        return {anchor : self.position.calculate_anchor(self.size.elementwise() * self._scale, anchor, self._angle) 
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
        local_trs_rect = self.get_local_rotoscaled_rect(use_parent_layout=use_parent_layout)
        return UiDrawable.get_draw_rect_from_transformed(local_trs_rect)
    
    @overload
    def get_world_draw_rect(self, frame : None = None,
                                  use_parent_layout : bool = False) -> pygame.Rect: ...
    @overload
    def get_world_draw_rect(self, frame : "UiFrame",
                                  use_parent_layout : bool = False) -> pygame.Rect|None: ...
    def get_world_draw_rect(self, frame : "UiFrame|None" = None,
                                  use_parent_layout : bool = False) -> pygame.Rect|None:
        world_trs_rect : TransformedRect|None = self.get_world_rotoscaled_rect(frame, use_parent_layout=use_parent_layout)
        if world_trs_rect is None: return None
        return UiDrawable.get_draw_rect_from_transformed(world_trs_rect)

    def _get_cached(self, scale : pygame.Vector2|None = None, angle : float = 0, opacity : float = 1, target_surf : pygame.Surface|None = None) -> pygame.Surface|None:
        if target_surf is None:
            target_surf = self._base_surf
        if scale is None:
            scale = pygame.Vector2(1, 1)
        for cache_line in self._cache.get(target_surf, []):
            if UiSprite._does_cache_match(cache_line, scale, angle, opacity):
                cache_line.priority = self._next_cache_no()
                return cache_line.result
        return None

    def _cache_surf(self, target_surf : pygame.Surface|None = None, scale : pygame.Vector2|None = None, angle : float = 0, opacity : float = 1) -> UiSpriteCacheLine:
        if target_surf is None:
            target_surf = self._base_surf
        if scale is None:
            scale = pygame.Vector2(1, 1)

        if angle != 0 or scale != pygame.Vector2(1, 1):
            int_surf = pygame.transform.scale_by(target_surf.convert_alpha(), scale)
            if angle == 0:
                result = int_surf
            else:
                new_surf : pygame.Surface = pygame.transform.rotozoom(int_surf.convert_alpha(), angle, 1)
                result = pygame.Surface(new_surf.get_size(), pygame.SRCALPHA)
                result.blit(new_surf.convert_alpha(), (0, 0))

        else:
            result = target_surf.copy()
        if opacity < 1:
            base_alpha : int|None = result.get_alpha()
            if base_alpha is None:
                base_alpha = 255

            result.set_alpha(round(base_alpha * opacity))

        cache_line : UiSpriteCacheLine = UiSpriteCacheLine(self._next_cache_no(), result, scale, angle, opacity)
        self._add_to_cache(target_surf, cache_line)
        return cache_line

    @staticmethod
    def _does_cache_match(cache_line : UiSpriteCacheLine, scale : pygame.Vector2, angle : float, opacity : float) -> bool:
        SCALE_MARGIN : float = 0
        ANGLE_MARGIN : float = 0
        OPACITY_MARGIN : float = 0
        if ((scale - cache_line.scale).magnitude() < SCALE_MARGIN 
            and abs(angle - cache_line.angle) < ANGLE_MARGIN and 
            abs(opacity - cache_line.opacity) < OPACITY_MARGIN):
            return True
        return False

    def _add_to_cache(self, target_surf : pygame.Surface, cache_line : UiSpriteCacheLine):
        self._cache_line_count += 1
        if target_surf not in self._cache:
            self._cache[target_surf] = []
            
        self._cache[target_surf].append(cache_line)
        if self._cache_line_count > self.MAX_CACHE_SIZE:
            self._remove_oldest_cache_line()

    def _remove_oldest_cache_line(self) -> UiSpriteCacheLine|None:
        lowest_priority : int = -1
        lowest_target_surf : pygame.Surface|None = None
        lowest_cache_line : UiSpriteCacheLine|None = None
        for target_surf, cache_line_list in self._cache.items():
            for cache_line in cache_line_list:
                if cache_line.priority < lowest_priority or lowest_cache_line is None:
                    lowest_target_surf = target_surf
                    lowest_cache_line = cache_line
                    lowest_priority = cache_line.priority
        if lowest_cache_line and lowest_target_surf:
            self._cache[lowest_target_surf].remove(lowest_cache_line)
            if len(self._cache[lowest_target_surf]) == 0:
                del self._cache[lowest_target_surf]
            self._cache_line_count -= 1
        return lowest_cache_line
            

    def _render(self):
        true_angle : float = self.get_true_angle()
        true_scale : pygame.Vector2 = self.get_true_scale()
        true_opacity : float = self.get_true_opacity()
        if (cached_result := self._get_cached(true_scale, true_angle, true_opacity)):
            self._surf = cached_result
        else:
            self._surf = self._cache_surf(self._base_surf, true_scale, true_angle, true_opacity).result
        self._trigger_parent_frame_update(False)
        return
        
    def calculate_overriden_draw_source(self, local_override : TransformedRect|None = None, frame : "UiFrame|None" = None) -> pygame.Surface|None:
        tranfs_rect : TransformedRect|None = local_override if frame is None else self.get_world_rotoscaled_rect(frame, local_override)
        if tranfs_rect is None:
            return None
        target_scale : pygame.Vector2 = self.get_true_scale(local_override)
        target_rotation : float = self.get_true_angle(local_override)
        if True:
            target_opacity : float = self.get_true_opacity()
            source : pygame.Surface
            if (cached_result := self._get_cached(target_scale, target_rotation, target_opacity)):
                source = cached_result
            else:
                source = self._cache_surf(self._base_surf, target_scale, target_rotation, target_opacity).result
            return source

    def draw(self, display : pygame.Surface, frame : "UiFrame|None" = None, 
             override_pos_local: TransformedRect|None = None, override_pos_global : pygame.Rect|None = None):
        if not self.visible:
            return
        source : pygame.Surface = self._surf
        draw_rect : pygame.Rect|None = self.calculate_draw_rect(override_pos_global, override_pos_local, frame)
        if draw_rect is None:
            return
        if not override_pos_global and override_pos_local:
            if (new_source := self.calculate_overriden_draw_source(override_pos_local, frame)) is None:
                return
            else:
                source = new_source
        else:
            self._render()
        display.blit(source, draw_rect)


def local_imports():
    global UiFrame
    from .ui_frame import UiFrame
    global BaseLayout
    from .layouts.base_layout import BaseLayout