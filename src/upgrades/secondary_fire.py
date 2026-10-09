import pygame
from typing import Generator, TypeAlias, Literal, TypedDict, cast, Iterable
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, sign
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
from framework.utils.helpers import AnchorStr
from framework.ui import RowLayout, BaseDrawableInfo, BaseUiFrameInfo, UiSprite, UiPosition
from framework.utils.base_particle_effects import ParticleEffect
import src.particle_effects

from .upgrade import SecondaryFireName, Upgrade, UpgradeType, PlayerStatsModifiers, BaseInteractibleUpgrade

from src.sprites.projectiles import BaseProjectile, ScatterProjectile, NormalProjectile, HomingProjectile, Teams

class SecondaryFire(BaseInteractibleUpgrade):
    BASE_COOLDOWN : float = 1
    BASE_DAMAGE : float = 1
    @staticmethod
    def get_secondary_fire_from_upgrade(player : 'Player', upgrade : Upgrade) -> "SecondaryFire|None":
        if upgrade.upgrade_type != UpgradeType.SECONDARY_FIRE:
            return None
        alt_fire_name : SecondaryFireName = cast(SecondaryFireName, upgrade.name)
        match alt_fire_name:
            case 'LazerShot':
                return LazerSecondaryFire(player, upgrade.rank, upgrade)
            case _:
                return None

    def __init__(self, player : 'Player', name : SecondaryFireName, rank : int, base_cooldown : float,
                 base_damage : float,
                 original_upgrade : Upgrade) -> None:
        super().__init__()
        self.player : Player = player
        self.name : SecondaryFireName = name
        self.rank : int = rank
        self.base_cooldown : float = base_cooldown
        self.original_upgrade : Upgrade = original_upgrade
        self.modifiers : PlayerStatsModifiers = PlayerStatsModifiers()
        self.base_damage : float = base_damage

    def attempt_fire(self) -> BaseProjectile|None:
        self.player.alt_fire_cooldown_timer.set_duration(self.player.upgrades.alt_fire_cooldown)
        return None

    def update(self, delta : float):
        ...

    def refresh_cooldown(self):
        self.player.alt_fire_cooldown_timer.set_duration(self.player.upgrades.alt_fire_cooldown)

core_object.asset_manager.load_sound("assets/audio/sfx/lazer.ogg", 'lazer_shot_sfx', 0.4)

class LazerSecondaryFire(SecondaryFire):
    BASE_COOLDOWN = 1 / 0.9
    BASE_DAMAGE = 4

    def __init__(self, player : 'Player', rank : int, original_upgrade: Upgrade) -> None:
        super().__init__(player, 'LazerShot', rank, LazerSecondaryFire.BASE_COOLDOWN, LazerSecondaryFire.BASE_DAMAGE, original_upgrade)

    def attempt_fire(self) -> BaseProjectile | None:
        super().attempt_fire()
        proj_count : int = 0
        scatter_count : int = 0
        damage_decay : float = 0.0
        core_object.bg_manager.play_sfx('lazer_shot_sfx', 1.0)
        return ScatterProjectile.spawn(self.player.position + pygame.Vector2(0, -30), pygame.Vector2(0, -16), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image3, "Purple"), team=Teams.ALLIED,
                                       damage=self.player.upgrades.alt_fire_damage, can_destroy=True, bounce_count=0, scatter_count=scatter_count,
                                       scatter_proj_num=proj_count, scatter_reflect=True, damage_decay=damage_decay,
                                        track_hits=True, track_misses=True)

def runtime_imports3():
    global Player
    import src.sprites.player
    from src.sprites.player import Player