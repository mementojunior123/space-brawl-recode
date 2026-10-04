import pygame

from framework.ui.ui_frame import BaseUiFrameInfo
from ..ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr
from ..ui_sprite import UiSprite
from ..ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect
from ..ui_frame import UiFrame
from .base_layout import BaseLayout

from typing import overload, Any, Literal
from dataclasses import dataclass

class ColumnLayout(BaseLayout):
    def __init__(self, base_drawable_info: BaseDrawableInfo, elements: list[UiDrawable], ui_frame_info: BaseUiFrameInfo):
        super().__init__(base_drawable_info, elements, ui_frame_info)

    def update_layout(self):
        super().update_layout()
        self.curr_layout = {}
        prev_rect_drawn : pygame.Rect|None = None
        for element in self.elements:
            transformed_elem_rect : TransformedRect = self._calculate_local_draw_pos(element, prev_rect_drawn)
            self.curr_layout[element] = transformed_elem_rect
            prev_rect_drawn = UiDrawable.get_draw_rect_from_transformed(transformed_elem_rect)

    def _calculate_local_draw_pos(self, element : UiDrawable, element_position_data : pygame.Rect|None = None, 
                                  other_data : dict|None = None) -> TransformedRect:
        if element_position_data is None:
            ...
            target_left : float = 0
            target_top : float = 0
        else:
            target_left : float = 0
            target_top : float = element_position_data.bottom
        old_tranfs_rect = element.get_local_rotoscaled_rect()
        topleft, topright, bottomleft, bottomright = (old_tranfs_rect['topleft'], old_tranfs_rect['topright'], 
                                                      old_tranfs_rect['bottomleft'], old_tranfs_rect['bottomright'])
        curr_left : float = min(bottomleft.x, bottomright.x, topleft.x, topright.x)
        curr_top : float = min(bottomleft.y, topleft.y, topright.y, bottomright.y)
        offset : pygame.Vector2 = pygame.Vector2(target_left - curr_left, target_top - curr_top)
        new_transf_rect : TransformedRect = {
            'topleft' : topleft + offset,
            'topright' : topright + offset,
            'bottomleft' : bottomleft + offset,
            'bottomright' : bottomright + offset
        }
        return new_transf_rect