import pygame
from typing import Generator, TypeAlias, Literal, TypedDict, cast, Iterable
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, sign
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
from framework.utils.helpers import AnchorStr
from framework.ui import RowLayout, BaseDrawableInfo, BaseUiFrameInfo, UiSprite, UiPosition
from framework.utils.base_particle_effects import ParticleEffect, ParticleEffectTrack
import src.particle_effects

from .upgrade import AbilityName, Upgrade, UpgradeType, PlayerStatsModifiers, BaseInteractibleUpgrade

class Ability(BaseInteractibleUpgrade):
    BASE_COOLDWON : float = -1
    @staticmethod
    def get_ability_from_upgrade(player : 'Player', upgrade : Upgrade) -> 'Ability|None':
        if upgrade.upgrade_type != UpgradeType.ABILITY:
            return None
        ability_name : AbilityName = cast(AbilityName, upgrade.name)
        match ability_name:
            case 'Dash':
                return DashAbility(player, upgrade.rank, upgrade)
            case _:
                return None
        
    def __init__(self, player : 'Player', name : AbilityName, rank : int, base_cooldown : float,
                 original_upgrade : Upgrade) -> None:
        super().__init__()
        self.player : Player = player
        self.name : AbilityName = name
        self.rank : int = rank
        self.base_cooldown : float = base_cooldown
        self.original_upgrade : Upgrade = original_upgrade
        self.modifiers : PlayerStatsModifiers = PlayerStatsModifiers()

    def activate(self) -> bool: # Does activate need to return anything?
        self.player.ability_cooldown_timer.set_duration(self.player.upgrades.ability_cooldown)
        return True

    def update(self, delta : float):
        pass

    def refresh_cooldown(self):
        self.player.ability_cooldown_timer.set_duration(self.player.upgrades.ability_cooldown)

class DashAbility(Ability):
    BASE_COOLDOWN : float = 3
    dash_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('dash_effect', persistance=True))

    BASE_INVULN_TIME : float = 0.26
    BASE_DURATION : float = 0.3

    def __init__(self, player : 'Player', rank : int, original_upgrade : Upgrade) -> None:
        super().__init__(player, 'Dash', rank, self.BASE_COOLDOWN, original_upgrade)
        self.dash_timer : Timer = Timer(-1, core_object.game_tsource)
        self.active : bool = False
        self.dash_track : ParticleEffectTrack|None = None

    def activate(self) -> bool:
        active_keys = pygame.key.get_pressed()
        direction : int = -1 * (active_keys[pygame.K_a] or active_keys[pygame.K_LEFT]) + 1 * (active_keys[pygame.K_d] or active_keys[pygame.K_RIGHT])
        if direction == 0:
            if self.player.velocity.x == 0:
                return False
            direction = round(sign(self.player.velocity.x))

        super().activate() # This code should only run if the activation is sucessful

        self.player.ability_cooldown_timer.pause()
        self.dash_timer.set_duration(self.BASE_DURATION)
        self.dash_track = self.dash_effect.play(self.player.position, core_object.game_tsource)
        self.dash_track.origin = self.player.position
        core_object.bg_manager.play_sfx('dash_sfx', 1.0)
        
        self.modifiers.lock_accel = True
        self.modifiers.accel_bonus = pygame.Vector2(direction * 7, 0)
        self.active = True
        self.modifiers.invincible = True
        self.modifiers.projectile_intangible = True
        return True

    def deactivate(self):
        self.player.ability_cooldown_timer.unpause()
        self.modifiers.lock_accel = False
        self.modifiers.accel_bonus = pygame.Vector2(0, 0)
        self.modifiers.invincible = False
        self.modifiers.projectile_intangible = False
        self.active = False

    def update(self, delta : float):
        if self.active:
            if self.dash_timer.isover():
                self.deactivate()
            elif self.dash_timer.get_time() > self.BASE_INVULN_TIME:
                self.modifiers.invincible = False
                self.modifiers.projectile_intangible = False
        if self.dash_track:
            if self.dash_track.ended:
                self.dash_track = None
            else:
                self.dash_track.origin = self.player.position

def runtime_imports1():
    global Player
    import src.sprites.player
    from src.sprites.player import Player