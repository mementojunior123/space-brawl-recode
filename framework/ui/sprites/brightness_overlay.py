import pygame
from ..ui_position import AnyUiPosition, UiPosition
from framework.utils.helpers import AnchorStr
from ..ui_drawable import UiDrawable, UiSpriteGroup, BaseDrawableInfo, TransformedRect
from ..ui_sprite import UiSprite
from ..ui_frame import UiFrame

class BrightnessOverlay(UiSprite):
    _base_surf_changeable = False
    def __init__(self, info : BaseDrawableInfo, size : pygame.typing.IntPoint, brightness : int, experimental_blend : bool = True):
        self._experimental_blend : bool = experimental_blend
        self._size : pygame.Vector2 = pygame.Vector2(size)
        self._brightness : int = brightness
        self._blend_mode : int
        self._render_base(init=True)

        super().__init__(info, self._base_surf)

    @property
    def size(self) -> pygame.Vector2:
        return self._size

    @size.setter
    def size(self, new_value : pygame.typing.IntPoint):
        converted = pygame.Vector2(new_value)
        if converted == self._size:
            return
        self._size = converted
        self._render_base()

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, new_value : int):
        if new_value == self._brightness:
            return
        self._brightness = new_value
        self._render_base()

    @property
    def experimental_blend(self) -> bool:
        return self._experimental_blend

    @experimental_blend.setter
    def experimental_blend(self, new_value : bool):
        if new_value == self._experimental_blend:
            return
        self._experimental_blend = new_value
        self._render_base()

    @property
    def current_blend_mode(self) -> int:
        return self._blend_mode
    

    def _render_base(self, init : bool = False):
        if self._experimental_blend:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_MULT
            abs_brightness = abs(self._brightness) if self._brightness >= 0 else 255 - abs(self._brightness)
        else:
            self._blend_mode = pygame.BLEND_RGB_ADD if self._brightness >= 0 else pygame.BLEND_RGB_SUB
            abs_brightness = abs(self._brightness)

        self._base_surf = pygame.surface.Surface(self.size)
        self._base_surf.fill((abs_brightness, abs_brightness, abs_brightness))
        if not init:
            self._render()
            self._trigger_parent_frame_update(True)

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
        display.blit(source, draw_rect, special_flags=self._blend_mode)
    