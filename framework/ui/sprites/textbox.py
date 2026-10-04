import pygame

from ..ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr, ANCHOR_REL_POS_DICT
from ..ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect
from ..ui_sprite import UiSprite
from ..ui_frame import UiFrame
from ..textstyle import TextStyle, TextStyleProxy

from framework.utils.helpers import vector_xmax_ysum
from math import floor
from dataclasses import dataclass

from typing import Sequence

class Textbox(UiSprite):
    _base_surf_changeable = False
    def __init__(self, info : BaseDrawableInfo, background : pygame.Surface, text : str, text_style : TextStyle,
                 text_pos : AnchorStr|pygame.typing.Point = (0.5, 0.5), text_aligment : AnchorStr|pygame.typing.Point = (0.5, 0.5), 
                 text_percent : float = 1):
        if isinstance(text_pos, str):
            text_pos = ANCHOR_REL_POS_DICT[text_pos]
        if isinstance(text_aligment, str):
            text_aligment = ANCHOR_REL_POS_DICT[text_aligment]

        self._background : pygame.Surface = background
        self._text : str = text
        self._text_style : TextStyle = text_style
        self._text_percent : float = text_percent
        self._text_pos : pygame.Vector2 = pygame.Vector2(text_pos)
        self._text_alignment : pygame.Vector2 = pygame.Vector2(text_aligment)

        self._render_base(True)
        super().__init__(info, self._base_surf)

    def get_shown_text(self) -> str:
        text_index = floor(self._text_percent * len(self._text))
        return self._text[:text_index + 1]

    @property
    def background(self) -> pygame.Surface:
        return self._background

    @background.setter
    def background(self, new_value : pygame.Surface):
        if new_value != self._background:
            self._background = new_value
            self._render_base()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_value : str):
        prev_shown_text : str = self.get_shown_text()
        self._text = new_value
        new_shown_text : str = self.get_shown_text()
        if new_shown_text != prev_shown_text:
            self._render_base()

    @property
    def text_percent(self) -> float:
        return self._text_percent

    @text_percent.setter
    def text_percent(self, new_value : float):
        prev_shown_text : str = self.get_shown_text()
        self._text_percent = new_value
        new_shown_text : str = self.get_shown_text()
        if new_shown_text != prev_shown_text:
            self._render_base()

    @property
    def text_style(self) -> TextStyleProxy:
        return TextStyleProxy(self._text_style, self._on_style_change)

    @text_style.setter
    def text_style(self, new_value : TextStyle):
        self._text_style = new_value
        self._render_base()

    @property
    def text_pos(self) -> pygame.Vector2:
        return self._text_pos

    @text_pos.setter
    def text_pos(self, new_value : pygame.typing.Point|AnchorStr):
        prev_text_pos : pygame.Vector2 = self._text_pos
        if isinstance(new_value, str):
            self._text_pos = pygame.Vector2(ANCHOR_REL_POS_DICT[new_value])
        elif not isinstance(new_value, pygame.Vector2):
            self._text_pos = pygame.Vector2(new_value)
        else:
            self._text_pos = new_value
        if prev_text_pos != self._text_pos:
            self._render_base()

    @property
    def text_alignment(self) -> pygame.Vector2:
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, new_value : pygame.typing.Point|AnchorStr):
        prev_text_alignment : pygame.Vector2 = self._text_alignment
        if isinstance(new_value, str):
            self._text_alignment = pygame.Vector2(ANCHOR_REL_POS_DICT[new_value])
        elif not isinstance(new_value, pygame.Vector2):
            self._text_alignment = pygame.Vector2(new_value)
        else:
            self._text_alignment = new_value
        if prev_text_alignment != self._text_alignment:
            self._render_base()

    def _on_style_change(self, proxy : TextStyleProxy):
        if proxy._value == self._text_style:
            self._render_base()

    def _render_base(self, init : bool = False):
        self._base_surf = self.background.copy()
        text_surf : pygame.Surface = self._text_style.render_text(self.get_shown_text())
        text_size = text_surf.get_size()
        text_local_topleft : pygame.Vector2 = UiPosition.from_normal_coords(
            self._text_pos, self._text_alignment, self.background.get_size()).calculate_anchor(text_size, 'topleft')
        text_rect = pygame.Rect(text_local_topleft, text_size)
        self._base_surf.blit(text_surf, text_rect)
        if not init:
            self._render()
            self._trigger_parent_frame_update(True)