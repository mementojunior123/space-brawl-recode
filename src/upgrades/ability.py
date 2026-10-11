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
            case 'Overcharge':
                return OverchargeAbility(player, upgrade.rank, upgrade)
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
        self.refresh_cooldown()
        return True

    def update(self, delta : float):
        pass

    def refresh_cooldown(self, active_now : bool = False):
        cooldown : float = self.player.upgrades.ability_cooldown
        self.player.ability_cooldown_timer.set_duration(cooldown)
        if active_now: self.player.ability_cooldown_timer.start_time -= cooldown

    @property
    def active_ability_progress(self) -> float:
        return 0

class DashAbility(Ability):
    BASE_COOLDOWN : float = 3
    dash_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('dash_effect', persistance=True))

    BASE_INVULN_TIME : float = 0.125
    BASE_DURATION : float = 0.15

    def __init__(self, player : 'Player', rank : int, original_upgrade : Upgrade) -> None:
        super().__init__(player, 'Dash', rank, self.BASE_COOLDOWN, original_upgrade)
        self.dash_timer : Timer = Timer(-1, core_object.game_tsource)
        self.active : bool = False
        self.dash_track : ParticleEffectTrack|None = None
        self.duration : float
        self.invlun_time : float
        self.max_uses : int

        self.curr_uses : int = 0

        if self.rank <= 1:
            self.duration = self.BASE_DURATION
            self.invlun_time = self.BASE_INVULN_TIME
            self.max_uses = 1
        elif self.rank == 2:
            self.duration = 0.225
            self.invlun_time = 0.18
            self.max_uses = 1
        elif self.rank == 3:
            self.duration = 0.225
            self.invlun_time = 0.20
            self.max_uses = 2
        elif self.rank == 4:
            self.duration = 0.30
            self.invlun_time = 0.25
            self.max_uses = 2
        elif self.rank >= 5:
            self.duration = 0.30
            self.invlun_time = 0.25
            self.max_uses = 3


    def refresh_cooldown(self, active_now: bool = False):
        super().refresh_cooldown(active_now)
        self.curr_uses = 0
        

    @property
    def active_ability_progress(self) -> float:
        if not self.player.ability_cooldown_timer.isover():
            return 0
        uses_left : int = self.max_uses - self.curr_uses
        curr_dash_progress : float = 0 if not self.active else 1 - (pygame.math.clamp(self.dash_timer.get_time() / self.invlun_time, 0, 1))
        return (curr_dash_progress + uses_left) / self.max_uses

    def activate(self) -> bool:
        if self.curr_uses >= self.max_uses or self.active:
            return False
        
        active_keys = pygame.key.get_pressed()
        direction : int = -1 * (active_keys[pygame.K_a] or active_keys[pygame.K_LEFT]) + 1 * (active_keys[pygame.K_d] or active_keys[pygame.K_RIGHT])
        if direction == 0:
            if self.player.velocity.x == 0:
                return False
            direction = round(sign(self.player.velocity.x))

        self.player.ability_cooldown_timer.pause()
        self.dash_timer.set_duration(self.duration)
        self.dash_track = self.dash_effect.play(self.player.position, core_object.game_tsource)
        self.dash_track.origin = self.player.position
        core_object.bg_manager.play_sfx('dash_sfx', 1.0)
        self.curr_uses += 1
        
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

        if self.curr_uses >= self.max_uses:
            self.curr_uses = 0
            self.refresh_cooldown()

    def update(self, delta : float):
        if self.active:
            if self.dash_timer.isover():
                self.deactivate()
            elif self.dash_timer.get_time() > self.invlun_time:
                self.modifiers.invincible = False
                self.modifiers.projectile_intangible = False
        if self.dash_track:
            if self.dash_track.ended:
                self.dash_track = None
            else:
                self.dash_track.origin = self.player.position

class OverchargeAbility(Ability): # TODO : Add ability visual
    BASE_COOLDOWN : float = 20
    dash_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('dash_effect', persistance=True))

    BASE_DURATION : float = 3

    def __init__(self, player : 'Player', rank : int, original_upgrade : Upgrade) -> None:
        super().__init__(player, 'Overcharge', rank, self.BASE_COOLDOWN, original_upgrade)
        self.ability_timer : Timer = Timer(self.BASE_DURATION, core_object.game_tsource)
        self.active : bool = False

        self.damage_bonus : float
        self.firerate_bonus : float
        self.duration : float

        if self.rank <= 1:
            self.damage_bonus = 0
            self.firerate_bonus = 0.5
            self.duration = 3
        elif self.rank == 2:
            self.damage_bonus = 0
            self.firerate_bonus = 0.5
            self.duration = 5
        elif self.rank == 3:
            self.damage_bonus = 0.5
            self.firerate_bonus = 0.5
            self.duration = 5
        elif self.rank >= 4:
            self.damage_bonus = 1
            self.firerate_bonus = 1
            self.duration = 5

    @property
    def active_ability_progress(self) -> float:
        return 0 if not self.active else pygame.math.clamp(1 - self.ability_timer.get_time() / self.ability_timer.duration, 0, 1)
    
    def activate(self) -> bool:
        super().activate()
        self.player.ability_cooldown_timer.pause()
        self.ability_timer.set_duration(self.duration)

        self.modifiers.alt_firerate_mult = self.firerate_bonus
        self.modifiers.alt_damage_mult = self.damage_bonus
        self.active = True
        return True

    def deactivate(self):
        self.player.ability_cooldown_timer.unpause()
        self.active = False
        self.modifiers.alt_firerate_mult = 0
        self.modifiers.alt_damage_mult = 0

    def update(self, delta : float):
        if self.active:
            if self.ability_timer.isover():
                self.deactivate()

def runtime_imports1():
    global Player
    import src.sprites.player
    from src.sprites.player import Player