import pygame

from ..ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr, ANCHOR_REL_POS_DICT
from ..ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect
from ..ui_sprite import UiSprite
from ..ui_frame import UiFrame
from math import floor

from typing import Literal

type FillDirection = Literal['up', 'down', 'left', 'right']

class ProgressBar(UiSprite):
    _base_surf_changeable = False
    def __init__(self, info : BaseDrawableInfo, base_size : pygame.typing.IntPoint, 
                 bg_color : pygame.typing.ColorLike, fill_color : pygame.typing.ColorLike,
                  fill_direction : FillDirection, progress : float = 0, use_alpha : bool = False):
        self._progress : float = progress
        self._base_size : pygame.typing.IntPoint = base_size
        self._bg_color : pygame.typing.ColorLike = bg_color
        self._fill_color : pygame.typing.ColorLike = fill_color
        self._fill_direction : FillDirection = fill_direction
        self._use_alpha : bool = use_alpha

        self._render_base(True)
        super().__init__(info, self._base_surf)

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value : float):
        if value != self._progress:
            self._progress = value
            self._render_base()

    @property
    def base_size(self) -> pygame.typing.IntPoint:
        return self._base_size

    @base_size.setter
    def base_size(self, value : pygame.typing.IntPoint):
        if value != self._base_size:
            self._base_size = value
            self._render_base()

    @property
    def bg_color(self) -> pygame.typing.ColorLike:
        return self._bg_color

    @bg_color.setter
    def bg_color(self, value : pygame.typing.ColorLike):
        if value != self._bg_color:
            self._bg_color = value
            self._render_base()

    @property
    def fill_color(self) -> pygame.typing.ColorLike:
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value : pygame.typing.ColorLike):
        if value != self._fill_color:
            self._fill_color = value
            self._render_base()

    @property
    def fill_direction(self) -> FillDirection:
        return self._fill_direction

    @fill_direction.setter
    def fill_direction(self, value : FillDirection):
        if value != self._fill_direction:
            self._fill_direction = value
            self._render_base()

    @property
    def use_alpha(self) -> bool:
        return self._use_alpha

    @use_alpha.setter
    def use_alpha(self, value : bool):
        if value != self._use_alpha:
            self._use_alpha = value
            self._render_base()

    def _render_base(self, init : bool = False):
        flags : int
        if self._use_alpha:
            flags = pygame.SRCALPHA
        else:
            flags = 0
        self._base_surf = pygame.Surface(self._base_size, flags)
        self._base_surf.fill(self._bg_color)
        size_x : int
        size_y : int
        size_x, size_y = self._base_size
        target_rect : pygame.Rect
        match self._fill_direction:
            case 'down':
                target_rect = pygame.Rect(0, 0, size_x, size_y * self.progress)
            case 'right':
                target_rect = pygame.Rect(0, 0, size_x * self._progress, size_y)
            case 'left':
                target_rect = pygame.Rect(round(size_x * (1 - self.progress)), 0, size_x * self.progress, size_y)
            case 'up':
                target_rect = pygame.Rect(0, round(size_y * (1 - self.progress)), size_x, size_y * self.progress)
            case _:
                target_rect = pygame.Rect(0, 0, 0, 0)
        pygame.draw.rect(self._base_surf, self._fill_color, target_rect)
        if not init:
            self._render()
            self._trigger_parent_frame_update(True)