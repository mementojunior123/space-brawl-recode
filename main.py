import pygame
import asyncio
import traceback
pygame.init()

PROFILING : bool = False
GAME_ICON = pygame.image.load('assets/graphics/icon.png')
GAME_TITLE : str = "Test game title"
pygame.display.set_icon(GAME_ICON)

window_size = (960, 540)
window = pygame.display.set_mode(window_size)

pygame.mixer.set_num_channels(32)

from framework.core.asset_manager import asset_manager

for size in (40, 50, 60, 70, 150):
    asset_manager.load_font(r'assets/fonts/Pixeltype.ttf', f"font_{size}", size)

sound_list : list[tuple[str, str, float]] = [
    ('test_music', 'assets/audio/music/test_music.ogg', 1.0),
    ('test_sfx', 'assets/audio/sfx/test_sfx.ogg', 1.0),
    ('PLACEHOLDER_DO_NOT_TOUCH', 'assets/audio/NOTHING.ogg', 1.0)
]
for name, path, vol in sound_list:
    r = asset_manager.load_sound(path, name, vol)

from framework.core.core import Core, core_object

import src.settings as settings_module
core = core_object
core.init(window)
core.FPS = 120
if core.is_web(): core.setup_web(method=2)

pygame.display.set_caption(GAME_TITLE)

from framework.game.sprite import Sprite
Sprite._core_hint()

from framework.utils.base_animation import Animation, AnimationTrack, _sprite_hint
_sprite_hint()
import src.animations

from framework.ui import UiDrawable
from framework.utils.helpers import copysign
from framework.utils.base_particle_effects import ParticleEffect, Particle
import framework.utils.base_particle_effects
framework.utils.base_particle_effects.runtime_imports()
import src.particle_effects
from framework.utils.my_timer import Timer
import framework.utils.interpolation as interpolation
import framework.utils.tween_module as TweenModule



import src.game_states as game_states
from src.sprites.test_player import TestPlayer

core.storage.load(is_web=core.is_web())
core.settings.load(is_web=core.is_web())
settings_module.the_runtime_imports()
core.settings.apply()

core.menu.init()
core.game.init()
game_states.runtime_imports()

clock = pygame.Clock()

async def main():
    try:
        while 1:
            core.update_dt(60)
            for event in pygame.event.get():
                core.event_manager.process_event(event)

            if core.game.active == False:
                window.fill(core.menu.bg_color)
                core.menu.update(core.dt)
                core.menu.render(window)
            else:
                core.game.state.main_logic(core.dt)
                ParticleEffect.update_all()
                window.fill((94,129,162))    
                core.main_ui.update(core.dt)
                if core.MIX_UI_AND_SPRITES:
                    element_list : list[Sprite|UiDrawable] = Sprite.active_elements + core.main_ui.complete_list
                    element_list.sort(key = lambda sprite : sprite.zindex)
                    for element in element_list:
                        element.draw(window)
                else:
                    Sprite.draw_all_sprites(window)
                    core.main_ui.render(window)

            core.update()
            if core.settings.brightness != 0:
                window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
                
            pygame.display.update()
            core.frame_counter += 1
            clock.tick(core.FPS)
            await asyncio.sleep(0)
    except BaseException as e:
        if core_object.is_web():
            core_object.alert_js(f"Error in the pygame runtime : {str(e).capitalize()}")
            core_object.log_to_js_console(''.join(traceback.format_exception(e)))
        raise e

if PROFILING:
    import cProfile
    cProfile.run('asyncio.run(main())', sort=1)
else:
    asyncio.run(main())


