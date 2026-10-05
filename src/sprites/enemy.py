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

    def __init__(self) -> None:
        super().__init__()
        self.type : EnemyType|BossType
        self.health : float
        self.invincible : bool
        self.mask : pygame.Mask #type: ignore

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
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
        overlap_point : tuple[int, int]|None = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point) if overlap_point else self.position
        if self.health <= BaseEnemy.health_epsilon:
            self.kill_instance_safe()
            enemy_killed_particle_effect.play(self.position.copy(), core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
            self.give_score(self.KILL_SCORE)
        elif not self.invincible:
            enemy_damaged_particle_effect.play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx('enemy_hit_sfx', 1.0)
            self.give_score(1)


    def check_collisions(self):
        colliding_projectiles : list[BaseProjectile] = [elem for elem in cast(list[BaseProjectile], self.get_all_colliding(BaseProjectile)) 
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
        
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")


class EnemyTypes(Enum):
    BASIC = 'basic'

EnemyType : TypeAlias = Literal['basic']
EnemyTypeList : list[EnemyType] = ['basic']

class BossTypes(Enum):
    BASIC_BOSS = 'basic_boss'

BossType : TypeAlias = Literal['basic_boss']
BossTypeList : list[BossType] = ['basic_boss']