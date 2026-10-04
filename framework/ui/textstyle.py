from typing import Any, Callable

import pygame
from dataclasses import dataclass

from framework.utils.helpers import vector_xmax_ysum

@dataclass
class TextStyle:
    font : pygame.Font
    text_color : pygame.typing.ColorLike
    anti_aliasing : bool
    text_stroke_color : pygame.typing.ColorLike|None = None
    text_stroke_size : int|None = None
    max_line_length : int = 0
    newline_height : int = 5 # does not currently function
    colorkey : pygame.typing.ColorLike|None = None
    text_scale : float = 1

    def __copy__(self) -> "TextStyle":
        return self.copy()

    def copy(self) -> "TextStyle":
        return TextStyle(self.font, self.text_color, self.anti_aliasing,
                         self.text_stroke_color, self.text_stroke_size, self.max_line_length,
                         self.newline_height, self.colorkey, self.text_scale)

    def __post_init__(self):
        ...

    def render_text(self, text : str) -> pygame.Surface:
        result : pygame.Surface
        if self.text_stroke_color and self.text_stroke_size:
            stroke_x : int = self.text_stroke_size * 2
            stroke_y : int = self.text_stroke_size * 2 * (text.count("\n") + 1)
            final_surf_size = (
            pygame.Vector2(stroke_x, stroke_y) 
            + vector_xmax_ysum([self.font.size(chunk) for chunk in text.split("\n")])
            + (1,1)
            )
            if self.colorkey:
                final_surf = pygame.Surface(final_surf_size)
                final_surf.fill(self.colorkey)
            else:
                final_surf = pygame.Surface(final_surf_size, pygame.SRCALPHA)

            first_text_sprite = self.font.render(text, self.anti_aliasing, self.text_color, wraplength=self.max_line_length)
            outline = self.font.render(text, self.anti_aliasing, self.text_stroke_color, wraplength=self.max_line_length)
            

            
            for ox in range(-1, 2):
                for oy in range(-1, 2):
                    if ox or oy or 1:
                        dx, dy = (ox + 1) * self.text_stroke_size, (oy + 1) * self.text_stroke_size
                        final_surf.blit(outline, (dx, dy))


            final_surf.blit(first_text_sprite, (self.text_stroke_size, self.text_stroke_size))            
            result = final_surf
            if self.colorkey:
                result.set_colorkey(self.colorkey)
        else:
            result = self.font.render(text, self.anti_aliasing, self.text_color, wraplength=self.max_line_length, bgcolor=self.colorkey)
            if self.colorkey:
                result.set_colorkey(self.colorkey)
        if self.text_scale != 1:
            result = pygame.transform.rotozoom(result, 0, self.text_scale)
        return result


class TextStyleProxy:
    def __init__(self, value : TextStyle, on_change : Callable[["TextStyleProxy"], None]) -> None:
        self._value : TextStyle = value
        self._on_change : Callable[["TextStyleProxy"], None] = on_change

    def type_hints(self):
        self.font : pygame.Font
        self.text_color : pygame.typing.ColorLike
        self.anti_aliasing : bool
        self.text_stroke_color : pygame.typing.ColorLike|None
        self.text_stroke_size : int|None
        self.max_line_length : int
        self.newline_height : int
        self.colorkey : pygame.typing.ColorLike|None
        self.text_scale : float

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in ("_value", "_on_change"):
            old_value = getattr(self._value, name)
            if old_value != value:
                setattr(self._value, name, value)
                self._on_change(self)
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name : str):
        return getattr(self._value, name)