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
from src.sprites.enemy import BaseEnemy

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
            case 'ShotgunShot':
                return ShotgunSecondaryFire(player, upgrade.rank, upgrade)
            case 'MissileShot':
                return MissileSecondaryFire(player, upgrade.rank, upgrade)
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

    def refresh_cooldown(self, active_now : bool = False):
        cooldown : float = self.player.upgrades.alt_fire_cooldown
        self.player.alt_fire_cooldown_timer.set_duration(cooldown)
        if active_now: self.player.alt_fire_cooldown_timer.start_time -= cooldown

core_object.asset_manager.load_sound("assets/audio/sfx/lazer.ogg", 'lazer_shot_sfx', 0.4)

class LazerSecondaryFire(SecondaryFire):
    BASE_COOLDOWN = 1 / 0.9
    BASE_DAMAGE = 4

    def __init__(self, player : 'Player', rank : int, original_upgrade: Upgrade) -> None:
        super().__init__(player, 'LazerShot', rank, LazerSecondaryFire.BASE_COOLDOWN, LazerSecondaryFire.BASE_DAMAGE, original_upgrade)

    def attempt_fire(self) -> BaseProjectile | None:
        super().attempt_fire()
        proj_scatter_reps : int
        proj_per_scatter : int
        damage_decay : float
        if self.rank >= 3:
            proj_scatter_reps = 2
            proj_per_scatter = 4
            damage_decay = 1.0
        elif self.rank >= 2:
            proj_scatter_reps = 2
            proj_per_scatter = 4
            damage_decay = 0.5
        elif self.rank >= 1:
            proj_scatter_reps = 1
            proj_per_scatter = 4
            damage_decay = 0.5
        else:      
            proj_scatter_reps : int = 0
            proj_per_scatter : int = 0
            damage_decay : float = 0.0

        core_object.bg_manager.play_sfx('lazer_shot_sfx', 1.0)
        return ScatterProjectile.spawn(self.player.position + pygame.Vector2(0, -30), pygame.Vector2(0, -16), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image3, "Purple"), team=Teams.ALLIED,
                                       damage=self.player.upgrades.alt_fire_damage, can_destroy=True, bounce_count=0, scatter_count=proj_scatter_reps,
                                       scatter_proj_num=proj_per_scatter, scatter_reflect=True, damage_decay=damage_decay,
                                        track_hits=True, track_misses=True)

core_object.asset_manager.load_sound("assets/audio/sfx/shotgun_shot.ogg", 'shotgun_shot_sfx', 0.4)

class ShotgunSecondaryFire(SecondaryFire):
    BASE_COOLDOWN = 1 / 0.5
    BASE_DAMAGE = 1.5

    def __init__(self, player : 'Player', rank : int, original_upgrade: Upgrade) -> None:
        super().__init__(player, 'ShotgunShot', rank, ShotgunSecondaryFire.BASE_COOLDOWN, ShotgunSecondaryFire.BASE_DAMAGE, original_upgrade)

    def attempt_fire(self) -> BaseProjectile | None:
        super().attempt_fire()
        proj_list : list[ScatterProjectile] = []
        proj_scatter_reps : int = 1 if self.rank >= 1 else 0
        proj_per_scatter : int = 3
        damage_decay : float = 0.0
        wall_bounce_count : int = 2 if self.rank >= 2 else 0
        core_object.bg_manager.play_sfx('shotgun_shot_sfx', 1.0)
        for angle in (-20, -10, 0, 10, 20):
            proj = ScatterProjectile.spawn(self.player.position + pygame.Vector2(0, -30), pygame.Vector2(0, -16).rotate(angle), None, None, 
                                        angle, recolor_image(BaseProjectile.normal_image4, "White"), team=Teams.ALLIED,
                                        damage=self.player.upgrades.alt_fire_damage, can_destroy=True, bounce_count=wall_bounce_count, 
                                        scatter_count=proj_scatter_reps, scatter_proj_num=proj_per_scatter, scatter_reflect=True, 
                                        damage_decay=damage_decay, track_hits=True, track_misses=(angle==0))
            proj_list.append(proj)
        return proj_list[2]

core_object.asset_manager.load_sound("assets/audio/sfx/rocket_shot.ogg", 'rocket_shot_sfx', 0.4)

class MissileSecondaryFire(SecondaryFire):
    BASE_COOLDOWN = 1 / 0.35
    BASE_DAMAGE = 4

    def __init__(self, player : 'Player', rank : int, original_upgrade: Upgrade) -> None:
        super().__init__(player, 'MissileShot', rank, MissileSecondaryFire.BASE_COOLDOWN, MissileSecondaryFire.BASE_DAMAGE, original_upgrade)

    def attempt_fire(self) -> BaseProjectile | None:
        super().attempt_fire()
        core_object.bg_manager.play_sfx('rocket_shot_sfx', 1.0)
        explosive_range : float = 300 if self.rank >= 1 else 250
        aoe_fraction : float = 0.75 if self.rank >= 1 else 0.50
        return HomingProjectile.spawn(self.player.position + pygame.Vector2(0, -30), 
                                      pygame.Vector2(0, -10), 
                                      None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=3,
        homing_targets=BaseEnemy, team=Teams.ALLIED, can_destroy=True, damage=self.player.upgrades.alt_fire_damage, die_after_destroying=False,
        explosion_damage=self.player.upgrades.alt_fire_damage * aoe_fraction, explosive_range=explosive_range,
        track_hits=True, track_misses=True)

def runtime_imports3():
    global Player
    import src.sprites.player
    from src.sprites.player import Player