import pygame
from .ui_drawable import BaseDrawableInfo, UiSpriteGroup
from .ui_sprite import UiSprite
from . import button_templates
from .ui_position import UiPosition
from framework.utils.helpers import AnchorStr
from .ui_frame import UiFrame

from framework.core.asset_manager import asset_manager
from typing import cast

class BaseUiElements:
    font_40 = cast(pygame.Font, asset_manager.get_font("font_40"))
    image_dict : dict[str, pygame.Surface] = button_templates.image_dict

    @classmethod
    def new_button(cls, button_type : str, text, tag, alignment, pos, scale : float|tuple = 1, text_settings : tuple|None = None, 
                   name : str|None = None, parent : UiSpriteGroup|None = None) -> UiSprite:
        if text_settings is None: text_settings = (cls.font_40, "Black", False)
        font : pygame.Font
        text_color : pygame.typing.ColorLike
        AA_enabled : bool
        font, text_color, AA_enabled = text_settings

        text_scale : float
        surf_scale : float
        if isinstance(scale, (int, float)):
            text_scale = surf_scale = scale
        else:
            surf_scale, text_scale = scale

        surface = cls.image_dict[button_type]
        surface = pygame.transform.scale_by(surface, surf_scale)
        
        surface_rect = surface.get_bounding_rect()
        
        text_surface = font.render(text, AA_enabled, text_color)
        text_surface = pygame.transform.scale_by(text_surface, text_scale)
        text_surface_rect = text_surface.get_bounding_rect()
        text_surface_rect.center = (surface_rect.centerx, surface_rect.centery) 
        
        surface_rect.__setattr__(alignment, pos)
        
        surface.blit(text_surface, text_surface_rect)
        return UiSprite(BaseDrawableInfo(UiPosition(pos, alignment), parent, name, tag), surface)
        
    @classmethod
    def new_textless_button(cls, button_type : str, tag, alignment, pos, scale : float|tuple = 1, name : str|None = None, 
                            parent : UiSpriteGroup|None = None) -> UiSprite:
        surface = pygame.transform.scale_by(cls.image_dict[button_type], scale)
        surface_rect = surface.get_bounding_rect()
        surface_rect.__setattr__(alignment, pos)
        
        
        
        return UiSprite(BaseDrawableInfo(UiPosition(pos, alignment), parent, name, tag), surface)


    @classmethod
    def new_text_sprite(cls, text : str, settings : tuple, tag : int, alignment : AnchorStr, pos : tuple, newline_settings = None,
                        name : str|None = None, scale : float|tuple = 1, parent : UiSpriteGroup|None = None) -> UiSprite:
        """
        Returns an UiSprite.
        Settings is a tuple of (font, color, AA).
        If the text has newlines, set newline_settings to a tuple of (newline_height(int), text_alignment(str)).
        """
        font : pygame.Font
        color_arg : pygame.typing.ColorLike
        AA_enabled : bool
        font, color_arg, AA_enabled = settings
        color : pygame.Color = pygame.color.Color(color_arg)
        if newline_settings is None:

            
            surf = font.render(text, AA_enabled, color).convert_alpha()
            surf = pygame.transform.scale_by(surf, scale)
            rect = surf.get_bounding_rect()
            rect.__setattr__(alignment, pos)
            return UiSprite(BaseDrawableInfo(UiPosition(pos, alignment), parent, name, tag), surf)
        else:
            newline_height, text_alignment = newline_settings
            if newline_height is None: newline_height = 5
            if text_alignment is None: text_alignment = 'center'

            lines = text.split('/n')
            line_count = len(lines)
            surfaces : list[pygame.Surface] = [font.render(line, AA_enabled, color).convert_alpha() for line in lines]

            line_heights = [surf.get_height() for surf in surfaces]
            line_widths = [surf.get_width() for surf in surfaces]

            total_height = sum(line_heights) + newline_height * (line_count - 1)
            total_width = max(line_widths)
            final_surf = pygame.surface.Surface((total_width, total_height), pygame.SRCALPHA)
            current_top = 0
            for surf in surfaces:
                rect = surf.get_rect()
                if text_alignment == 'left':
                    rect.topleft = (0, current_top)
                elif text_alignment == 'right':
                    rect.topright = (total_width, current_top)
                elif text_alignment == 'center':
                    rect.midtop = (int(total_width / 2), current_top)
                else:
                    rect.midtop = (int(total_width / 2), current_top)
                    
                final_surf.blit(surf, rect)
                current_top += surf.get_height()
                current_top += newline_height
            final_surf = pygame.transform.scale_by(final_surf, scale)
            final_rect = final_surf.get_bounding_rect()
            final_rect.__setattr__(alignment, pos)
            return UiSprite(BaseDrawableInfo(UiPosition(pos, alignment), parent, name, tag), final_surf)

            


    