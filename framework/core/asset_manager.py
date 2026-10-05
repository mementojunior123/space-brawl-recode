import pygame
from pygame.typing import _PathLike, ColorLike, Point
from framework.utils.helpers import remove_image_empty
from typing import Literal, Sequence

class AssetManager:
    def __init__(self):
        self.core : "Core"

        self.surfaces : dict[str, tuple[pygame.Surface, bool]] = {}
        self.fonts : dict[str, tuple[pygame.Font, int]] = {}
        self.sounds : dict[str, tuple[pygame.Sound, str, float]] = {}

    def inject_core_reference(self, core_refrence : "Core"):
        self.core = core_refrence
        global core_object
        core_object = core_refrence
        self.sync_bg_manager()

    def sync_bg_manager(self):
        self.core.bg_manager.SOUNDS = {name : (self.sounds[name][0], self.sounds[name][1]) for name in self.sounds}
        
    def load_surface(self, path : _PathLike, name : str,
                     alpha_config : Literal['none', 'colorkey', 'alpha', 'alpha_to_colorkey'], 
                     base_scale : float|Point = 1, colorkey : ColorLike = (0, 255, 0), 
                     copy_on_request : bool = False, trim_edges : bool = False) -> bool:
        """
        Note : loading an asset with the same name as an already loaded asset overrides the new asset
        Note 2 : If assets of two different types have the same name, any generic function 
        (get_asset and unload_asset) will target assets in this order:
            surface --> sound --> font
        """
        if isinstance(base_scale, (float, int)):
            base_scale = (base_scale, base_scale)
        try:
            unconverted_image = pygame.image.load(path)
        except (FileNotFoundError, pygame.error, TypeError):
            return False
        new_surf : pygame.Surface
        if alpha_config == "alpha":
            new_surf = unconverted_image.convert_alpha()
        elif alpha_config == "alpha_to_colorkey":
            image : pygame.Surface = unconverted_image.convert_alpha()
            new_surf = pygame.surface.Surface(image.get_size())
            new_surf.set_colorkey(colorkey)
            new_surf.fill(colorkey)
            new_surf.blit(image.convert_alpha(), (0,0))
        elif alpha_config == "colorkey":
            new_surf = unconverted_image.convert()
            new_surf.set_colorkey(colorkey)
        elif alpha_config == "none":
            new_surf = unconverted_image.convert()

        if trim_edges:
            new_surf : pygame.Surface = remove_image_empty(new_surf)
        if base_scale != (1, 1):
            new_surf = pygame.transform.scale_by(new_surf, base_scale)

        self.surfaces[name] = (new_surf, copy_on_request)
        return True

    def load_font(self, path : _PathLike, name : str, font_size : int) -> bool:
        try:
            font : pygame.Font = pygame.Font(path, font_size)
        except (FileNotFoundError, pygame.error, TypeError):
            return False
        self.fonts[name] = (font, font_size)
        return True

    def load_sound(self, path : _PathLike, name : str, base_vol : float) -> bool:
        try:
            sound : pygame.Sound = pygame.Sound(path)
        except (FileNotFoundError, pygame.error, TypeError):
            return False
        sound.set_volume(base_vol)
        path_str : str = str(path)
        self.sounds[name] = (sound, path_str, base_vol)
        if hasattr(self, 'core'):
            self.core.bg_manager.SOUNDS[name] = (sound, path_str)
        return True

    def unload_asset(self, asset_name : str) -> bool:
        if asset_name in self.surfaces:
            self.surfaces.pop(asset_name)
            return True
        if asset_name in self.fonts:
            self.fonts.pop(asset_name)
            return True
        if asset_name in self.sounds:
            self.sounds.pop(asset_name)
            if hasattr(self, 'core'):
                self.core.bg_manager._unload_sound(asset_name)
            return True
        return False

    def get_asset(self, asset_name : str) -> pygame.Surface|pygame.Sound|pygame.Font|None:
        if asset_name in self.surfaces:
            surf : pygame.Surface = self.surfaces[asset_name][0]
            if self.surfaces[asset_name][1]:
                return surf.copy()
            else:
                return surf
        elif asset_name in self.fonts:
            return self.fonts[asset_name][0]
        elif asset_manager in self.sounds:
            return self.sounds[asset_name][0]
        else:
            return None

    def get_surface(self, asset_name : str) -> pygame.Surface|None:
        if asset_name in self.surfaces:
            surf : pygame.Surface = self.surfaces[asset_name][0]
            if self.surfaces[asset_name][1]:
                return surf.copy()
            else:
                return surf
        return None

    def get_font(self, asset_name : str) -> pygame.Font|None:
        if asset_name in self.fonts:
            return self.fonts[asset_name][0]
        return None

    def get_sound(self, asset_name : str) -> pygame.Sound|None:
        if asset_name in self.sounds:
            return self.sounds[asset_name][0]
        return None

asset_manager : AssetManager = AssetManager()

def _runtime_hints():
    global Core
    from framework.core.core import Core
