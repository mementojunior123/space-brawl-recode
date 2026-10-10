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
    ENEMY_KILLED : int = pygame.event.custom_type()

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
        if projectile.track_hits and projectile.team == Teams.ALLIED:
            pygame.event.post(pygame.Event(BaseProjectile.PROJECTILE_HIT, {}))
        overlap_point : tuple[int, int]|None = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point) if overlap_point else self.position
        if self.health <= BaseEnemy.health_epsilon:
            self.kill_instance_safe()
            pygame.event.post(pygame.Event(self.ENEMY_KILLED, {'enemy_type' : self.type}))
            enemy_killed_particle_effect.play(self.position.copy(), core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
            self.give_score(self.KILL_SCORE)
        elif not self.invincible:
            enemy_damaged_particle_effect.play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx('enemy_hit_sfx', 1.0)
            self.give_score(1)


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
        
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")


class BasicEnemy(BaseNormalEnemy, sprite_count = 30):
    BASE_SPEED : float = 4.0
    APPROCH_RATE : int = 100
    KILL_SCORE : int = 5
    def __init__(self):
        super().__init__()
        self.control_script : BasicEnemyControlScript
        self.speed : float
        self.mask : pygame.Mask #type: ignore
    
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        element = cls.inactive_elements[0]

        element.image = BaseEnemy.default_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.invincible = False

        element.control_script = BasicEnemyControlScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element, target_anchor, target_pos)
        element.speed = BasicEnemy.BASE_SPEED

        element.type = 'basic'
        element.health = 3

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.control_script.process_frame(delta)
        self.check_collisions()
    
    def fire_homing_projectile(self) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, 5), None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=1,
        homing_targets=Player, team=Teams.ENEMY)
    
    def fire_normal_projectile(self) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, 5), None, None, 0,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)
    
    def clean_instance(self):
        super().clean_instance()
        del self.control_script
        del self.speed

class BasicEnemyControlScript(CoroutineScript[float, str|None]):
    def initialize(self, time_source : TimeSource, unit : BasicEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        return super().initialize(time_source, unit, target_anchor, target_pos)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        start_position : pygame.Vector2 = unit.position.copy()
        unit.move_rect(target_anchor, target_pos)
        target_position : pygame.Vector2 = unit.position.copy()
        unit.position = start_position
        
        
        transition_timer : Timer = Timer(0.8, time_source)
        delta = yield
        unit.invincible = True
        if delta is None: delta = core_object.dt
        while not transition_timer.isover():
            alpha : float = interpolation.smoothstep(transition_timer.get_time() / transition_timer.duration)
            if alpha > 1: alpha = 1
            unit.position = start_position.lerp(target_position, alpha)
            delta = yield
        unit.position = target_position
        unit.invincible = False

        move_timer : Timer = Timer(-1, time_source)
        shot_timer : Timer = Timer(1, time_source)
        direction : int = 1 if unit.position.x < centerx else -1
        base_speed = unit.speed
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, base_speed, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
                unit.position += pygame.Vector2(0, BasicEnemy.APPROCH_RATE)
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
                unit.position += pygame.Vector2(0, BasicEnemy.APPROCH_RATE)
            if shot_timer.isover():
                unit.fire_normal_projectile()
                shot_timer.set_duration(random.uniform(3, 5))
            delta = yield
            
class EnemyTypes(Enum):
    BASIC = 'basic'

EnemyType : TypeAlias = Literal['basic']
EnemyTypeList : list[EnemyType] = ['basic']

class BossTypes(Enum):
    BASIC_BOSS = 'basic_boss'

BossType : TypeAlias = Literal['basic_boss']
BossTypeList : list[BossType] = ['basic_boss']

def runtime_imports():
    global Player
    from src.sprites.player import Player