import pygame
from typing import Generator, TypeAlias, Literal, cast
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
import src.sprites.projectiles
from src.game_states import SCORE_EVENT
from src.sprites.projectiles import NormalProjectile, BaseProjectile, HomingProjectile, Teams, ScatterProjectile
import random
from enum import Enum
from framework.utils.base_particle_effects import ParticleEffect
import framework.utils.interpolation as interpolation

from framework.ui import BaseDrawableInfo, UiPosition, ProgressBar

core_object.asset_manager.load_sound("assets/audio/sfx/enemy_hit.ogg", 'enemy_hit_sfx', 0.41)
core_object.asset_manager.load_sound("assets/audio/sfx/enemy_killed2.ogg", 'enemy_killed_sfx', 0.5)

core_object.asset_manager.load_surface("assets/graphics/enemy/alien.png", 'basic_enemy', 'alpha_to_colorkey', colorkey=(0, 255, 0))

enemy_killed_particle_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('enemy_killed'))
enemy_damaged_particle_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('enemy_damaged'))
explosion_particle_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('explosion_effect'))
explosion_small_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('explosion_small_effect'))

class BaseEnemy(Sprite):
    default_image : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface('basic_enemy'))
    display_size : tuple[int, int] = core_object.main_display.get_size()
    KILL_SCORE : int = 5

    health_epsilon : float = 0.01
    ENEMY_KILLED : int = pygame.event.custom_type()

    def __init__(self) -> None:
        super().__init__()
        self.type : EnemyType|BossType
        self.health : float
        self.invincible : bool
        self.mask : pygame.Mask #type: ignore

    @classmethod
    def spawn(cls, *args, **kwargs):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")
        element = cls.inactive_elements[0]

        element.image = element.default_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        pass

    def give_score(self, score : int):
        pygame.event.post(pygame.Event(SCORE_EVENT, {'score' : score}))
    
    def take_damage(self, damage : float):
        if self.invincible: return
        self.health -= damage
        core_object.log(f"{self.type.capitalize()} enemy took {damage} damage")

    def when_hit(self, projectile : BaseProjectile):
        self.take_damage(projectile.damage)
        if projectile.track_hits and projectile.team == Teams.ALLIED:
            pygame.event.post(pygame.Event(BaseProjectile.PROJECTILE_HIT, {}))
        overlap_point : tuple[int, int]|None = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point) if overlap_point else self.position
        if self.health <= BaseEnemy.health_epsilon:
            self.when_killed()
        elif not self.invincible:
            enemy_damaged_particle_effect.play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx('enemy_hit_sfx', 1.0)
            self.give_score(1)

    def when_killed(self):
        self.kill_instance_safe()
        pygame.event.post(pygame.Event(self.ENEMY_KILLED, {'enemy_type' : self.type}))
        enemy_killed_particle_effect.play(self.position.copy(), core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
        self.give_score(self.KILL_SCORE)

    def check_collisions(self):
        colliding_projectiles : list[BaseProjectile] = [elem for elem in self.get_all_colliding(BaseProjectile)
                                                        if elem.team in (Teams.ALLIED, Teams.FFA)]
        if colliding_projectiles:
            for elem in colliding_projectiles:
                if isinstance(elem, ScatterProjectile):
                    if self in elem.ignore:
                        continue
                self.when_hit(elem)
                if isinstance(elem, HomingProjectile):
                    if elem.explosive_range:
                        elem.explode(self)
                elif isinstance(elem, ScatterProjectile):
                    elem.scatter(self)
                elem.kill_instance()
                if self._zombie:
                    break

    def clean_instance(self):
        super().clean_instance()
        del self.type
        del self.health
        del self.invincible

class BaseNormalEnemy(BaseEnemy):
    def __init__(self) -> None:
        super().__init__()
        self.type : EnemyType # type: ignore
        
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")

    def fire_homing_projectile(self, proj_speed : float = 5) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed), None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=1,
        homing_targets=Player, team=Teams.ENEMY, destructible=True)
    
    def fire_normal_projectile(self, proj_speed : float = 5) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed), None, None, 0,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)


class BaseBossEnemy(BaseEnemy):
    def __init__(self) -> None:
        super().__init__()
        self.type : BossType # type: ignore
        self.max_hp : float
        self.health_bar : ProgressBar
        self.control_script : CoroutineScript
        self.summoned_as_boss : bool
        self.real_kill_score : int

    def when_killed(self):
        pass # has to be overriden by subclass (or not)

    def update(self, delta : float):
        ...

    def update_health_bar_surf(self):
        color_breakpoints : dict[float, pygame.typing.ColorLike] = {
            0.8 : 'Dark green',
            0.6 : "#0ED80E",
            0.4 : "#FFFF41",
            0.2 : "#CE900A",
        }
        chosen_color : pygame.typing.ColorLike = 'Red'
        health_percent : float = self.health / self.max_hp
        for breakpoint, color in sorted(color_breakpoints.items(), key=lambda cb : cb[0], reverse=True):
            if health_percent >= breakpoint:
                chosen_color = color
                break

        self.health_bar._fill_color = chosen_color
        self.health_bar.progress = health_percent
        self.health_bar.visible = health_percent > 0

    def update_health_bar_pos(self):
        self.health_bar.position = self.calc_health_bar_pos()

    def calc_health_bar_pos(self) -> UiPosition:
        return UiPosition(self.rect.midtop + pygame.Vector2(0, 0), 'midbottom')

    def fire_homing_projectile(self, proj_speed : float = 4.5, angle : float = 0) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed).rotate(angle), None, None,
        0, BaseProjectile.rocket_image, homing_range=300, homing_rate=0.8,
        homing_targets=Player, team=Teams.ENEMY, destructible=True)
    
    def fire_normal_projectile(self, proj_speed : float = 8, angle : float = 0) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed).rotate(angle), 
                                      None, None, angle, recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)

    def clean_instance(self):
        super().clean_instance()
        del self.max_hp
        core_object.main_ui.remove(self.health_bar)
        del self.health_bar
        del self.control_script
        del self.summoned_as_boss
        del self.real_kill_score

class EnemyTypes(Enum):
    BASIC = 'basic'
    ELITE = 'elite'
    GUNNER = 'gunner'
    RUNNER = 'runner'

EnemyType : TypeAlias = Literal['basic', 'elite', 'gunner', 'runner']
EnemyTypeList : list[EnemyType] = ['basic', 'elite', 'gunner', 'runner']

class BossTypes(Enum):
    BASIC_BOSS = 'basic_boss'
    ELITE_BOSS = 'elite_boss'

BossType : TypeAlias = Literal['basic_boss', 'elite_boss']
BossTypeList : list[BossType] = ['basic_boss', 'elite_boss']

ENEMY_WEIGHT_DICT : dict[EnemyType|BossType, float] = {
    'basic' : 1,
    'elite' : 2,
    'gunner' : 2,
    'runner' : 2,
    'basic_boss' : 15,
    'elite_boss' : 25
}

def runtime_imports():
    global Player
    from src.sprites.player import Player