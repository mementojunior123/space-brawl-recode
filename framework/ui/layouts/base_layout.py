import pygame

from framework.ui.ui_frame import BaseUiFrameInfo
from ..ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr
from ..ui_sprite import UiSprite
from ..ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect
from ..ui_frame import UiFrame, UiFrameCacheLine

from typing import overload, Any
from dataclasses import dataclass

class BaseLayout(UiFrame):
    def __init__(self, base_drawable_info: BaseDrawableInfo, elements: list[UiDrawable], ui_frame_info: BaseUiFrameInfo):
        self._update_layout_next_draw : bool = True
        self.curr_layout : dict[UiDrawable, TransformedRect] = {}
        super().__init__(base_drawable_info, elements, ui_frame_info)

    def update_layout(self):
        self._cache.clear()
        self._update_layout_next_draw = False

    def _calculate_local_draw_pos(self, element : UiDrawable, element_position_data : Any = None, 
                                  other_data : dict|None = None) -> TransformedRect:
        raise NotImplementedError

    def _cache_surf(self, target_size : pygame.Vector2|None = None, scale : pygame.Vector2|None = None, angle : float = 0,
                        opacity : float = 1, local_override : TransformedRect|None = None) -> UiFrameCacheLine:
        if target_size is None:
            target_size = self.size
        if scale is None:
            scale = pygame.Vector2(1, 1)
        result : pygame.Surface = pygame.Surface(target_size, pygame.SRCALPHA)
        for element in self.elements:
            transformed_elem_rect : TransformedRect = self.curr_layout[element]
            element.draw(result, None, override_pos_local=transformed_elem_rect)
        result = pygame.transform.scale_by(result, scale)
        result = pygame.transform.rotate(result, angle)
        a : int|None = result.get_alpha()
        result.set_alpha(round((255 if a is None else a) * self.get_true_opacity()))
        
        cache_line : UiFrameCacheLine = UiFrameCacheLine(self._next_cache_no(), result, local_override, scale, angle, opacity)
        self._add_to_cache(target_size, cache_line)
        return cache_line

    def _render(self, local_override : TransformedRect|None = None):
        if self._update_layout_next_draw: self.update_layout()
        super()._render(local_override)

    def on_child_update(self, do_update_layout : bool = True):
        super().on_child_update(do_update_layout)
        if do_update_layout: self._update_layout_next_draw = True

    def draw(self, display: pygame.Surface, frame : UiFrame | None = None, 
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
            if self._update_layout_next_draw:
                self.update_layout()
            for element in self.elements:
                transformed_elem_rect : TransformedRect = self.curr_layout[element]
                element.draw(display, self if frame is None else frame, override_pos_local=transformed_elem_rect)
        self.temp_local_tranfs_rect = None