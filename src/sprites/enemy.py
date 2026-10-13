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

    def fire_homing_projectile(self, proj_speed : float = 5) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed), None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=1,
        homing_targets=Player, team=Teams.ENEMY)
    
    def fire_normal_projectile(self, proj_speed : float = 5) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, proj_speed), None, None, 0,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)


class BasicEnemy(BaseNormalEnemy, sprite_count = 30):
    BASE_SPEED : float = 4.0
    APPROCH_RATE : int = 100
    KILL_SCORE : int = 5

    SHOT_SPEED : float = 5
    BASE_HEALTH : float = 3

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
        element.health = BasicEnemy.BASE_HEALTH

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.control_script.process_frame(delta)
        self.check_collisions()
    
    def clean_instance(self):
        super().clean_instance()
        del self.control_script
        del self.speed

class BasicEnemyControlScript(CoroutineScript[float, None]):
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
                unit.fire_normal_projectile(BasicEnemy.SHOT_SPEED)
                shot_timer.set_duration(random.uniform(3, 5))
            delta = yield

core_object.asset_manager.load_surface(f"assets/graphics/enemy/elite_enemy.png", 'elite_enemy', 'alpha_to_colorkey', colorkey=(0, 255, 0))

class EliteEnemy(BaseNormalEnemy, sprite_count = 30):
    BASE_SPEED : float = 6.0
    APPROCH_RATE : int = 100
    KILL_SCORE : int = 10

    SHOT_SPEED : float = 8.0
    BASE_HEALTH : float = 6.0

    BASE_IMAGE : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface('elite_enemy'))
    NORMAL_SHOT_RESISTANCE : float = 0.0 # disabled for balance reasons

    def __init__(self):
        super().__init__()
        self.control_script : EliteEnemyControlScript
        self.speed : float
        self.mask : pygame.Mask #type: ignore
    
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        element = cls.inactive_elements[0]

        element.image = cls.BASE_IMAGE
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.invincible = False

        element.control_script = EliteEnemyControlScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element, target_anchor, target_pos)
        element.speed = EliteEnemy.BASE_SPEED

        element.type = 'elite'
        element.health = EliteEnemy.BASE_HEALTH

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.control_script.process_frame(delta)
        self.check_collisions()

    def when_hit(self, projectile: BaseProjectile): # TODO : Make this better
        prev_damage : float = projectile.damage
        if projectile.is_player_regular_fire:
            projectile.damage = prev_damage * (1 - self.NORMAL_SHOT_RESISTANCE)
        super().when_hit(projectile)
        if projectile.is_player_regular_fire:
            projectile.damage = prev_damage
    
    def clean_instance(self):
        super().clean_instance()
        del self.control_script
        del self.speed

class EliteEnemyControlScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : EliteEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        return super().initialize(time_source, unit, target_anchor, target_pos)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
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
                unit.position += pygame.Vector2(0, EliteEnemy.APPROCH_RATE)
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
                unit.position += pygame.Vector2(0, EliteEnemy.APPROCH_RATE)
            if shot_timer.isover():
                unit.fire_normal_projectile(EliteEnemy.SHOT_SPEED)
                shot_timer.set_duration(random.uniform(1.0, 2.5))
            delta = yield


core_object.asset_manager.load_surface(f"assets/graphics/enemy/gunner_enemy.png", 'gunner_enemy', 'alpha_to_colorkey', colorkey=(0, 255, 0))

class GunnerEnemy(BaseNormalEnemy, sprite_count = 30):
    BASE_SPEED : float = 3.0
    KILL_SCORE : int = 10

    SHOT_SPEED : float = 7.0
    BASE_HEALTH : float = 4

    BASE_IMAGE : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface('gunner_enemy'))

    def __init__(self):
        super().__init__()
        self.control_script : GunnerEnemyControlScript
        self.speed : float
        self.mask : pygame.Mask #type: ignore
    
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        element = cls.inactive_elements[0]

        element.image = cls.BASE_IMAGE
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.invincible = False

        element.control_script = GunnerEnemyControlScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element, target_anchor, target_pos)
        element.speed = GunnerEnemy.BASE_SPEED

        element.type = 'gunner'
        element.health = GunnerEnemy.BASE_HEALTH

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.control_script.process_frame(delta)
        self.check_collisions()
    
    def clean_instance(self):
        super().clean_instance()
        del self.control_script
        del self.speed


class GunnerEnemyControlScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : GunnerEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        return super().initialize(time_source, unit, target_anchor, target_pos)
    
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GunnerEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        
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

        shooting_script : GunnerEnemyShootingScript = GunnerEnemyShootingScript()
        shooting_script.initialize(time_source, unit)
        moving_script : GunnerEnemyMoveScript = GunnerEnemyMoveScript()
        moving_script.initialize(time_source, unit)
    
        while True:
            shooting_script.process_frame(delta)
            moving_script.process_frame(delta)
            delta = yield

class GunnerEnemyMoveScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : GunnerEnemy):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def predict_projectile_contact(unit : GunnerEnemy, projectile : BaseProjectile, unit_velocity : pygame.Vector2,
                                   bounding_box : pygame.Rect) -> bool:
        if abs(unit.position.y - projectile.position.y) > 200.0:
            return False
        projected_unit_position : pygame.Vector2 = unit.position.copy()
        projected_projectile_position : pygame.Vector2 = projectile.position.copy()
        prev_distance : float = 999_999.0
        for _ in range(100):
            projected_unit_position += unit_velocity
            projected_projectile_position += projectile.velocity
            distance : float = (projected_projectile_position - projected_unit_position).magnitude_squared()
            if distance < 1200.0:
                return True
            if distance > prev_distance:
                return False
            prev_distance = distance
            if not (bounding_box.collidepoint(projected_unit_position) and bounding_box.collidepoint(projected_projectile_position)):
                break
        return False

    @staticmethod
    def corou(time_source : TimeSource, unit : GunnerEnemy):
        
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        move_timer : Timer = Timer(-1, time_source)
        direction : int = 1 if unit.position.x < centerx else -1
        dodge_cooldown : Timer = Timer(0.6, time_source)
    
        delta = yield
        if delta is None: delta = core_object.dt
        base_speed = unit.speed
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, base_speed, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            
            if 50 <= unit.position.x <= screen_sizex - 50:
                if dodge_cooldown.isover():
                    for proj in BaseProjectile.active_elements:
                        if proj.team not in (Teams.ALLIED, Teams.FFA):
                            continue
                        if GunnerEnemyMoveScript.predict_projectile_contact(
                        unit, proj, pygame.Vector2(direction * base_speed, 0), bounding_box):
                            dodge_cooldown.restart()
                            if random.randint(1, 10) <= 6:
                                direction *= -1
            delta = yield

class GunnerEnemyShootingScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : GunnerEnemy):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 8
        elif x_offset < 50:
            return 4
        elif x_offset < 100:
            return 2
        elif x_offset < 150:
            return 1
        else:
            return 0.5
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GunnerEnemy):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        min_shot_cooldown : Timer = Timer(0.25, time_source)
        aggro_required : float = 90.0
        current_aggro : float = 0
        player : Player|None
        if not Player.active_elements:
            player = None
        else:
            player = Player.active_elements[0]
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            proximity_buff : float = GunnerEnemyShootingScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required:
                unit.fire_normal_projectile(unit.SHOT_SPEED)
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(60, 120)
            delta = yield

core_object.asset_manager.load_surface(f"assets/graphics/enemy/runner_enemy.png", 'runner_enemy', 'alpha_to_colorkey', colorkey=(0, 255, 0))

class RunnerEnemy(BaseNormalEnemy, sprite_count = 30):
    BASE_SPEED : float = 5.0
    KILL_SCORE : int = 10
    BASE_HEALTH : float = 2

    BASE_IMAGE : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface('runner_enemy'))

    def __init__(self):
        super().__init__()
        self.control_script : RunnerEnemyControlScript
        self.speed : float
        self.mask : pygame.Mask #type: ignore
    
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        element = cls.inactive_elements[0]

        element.image = cls.BASE_IMAGE
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.invincible = False

        element.control_script = RunnerEnemyControlScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element, target_anchor, target_pos)
        element.speed = RunnerEnemy.BASE_SPEED

        element.type = 'runner'
        element.health = RunnerEnemy.BASE_HEALTH

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        if not self.control_script.is_over: self.control_script.process_frame(delta)
        self.check_collisions()
    
    def clean_instance(self):
        super().clean_instance()
        del self.control_script
        del self.speed

class RunnerEnemyControlScript(CoroutineScript[float, None|str]):
    def initialize(self, time_source : TimeSource, unit : RunnerEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        return super().initialize(time_source, unit, target_anchor, target_pos)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : RunnerEnemy, target_anchor : str = "top", target_pos : pygame.Vector2|int = 20):
        
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
        direction : int = 1 if unit.position.x < centerx else -1
        base_speed = unit.speed
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, base_speed, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                break
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                break
            delta = yield
        while unit.rect.bottom < (screen_sizey - 10):
            unit.position += pygame.Vector2(0, unit.speed * delta)
            if unit.rect.bottom > (screen_sizey - 10):
                unit.move_rect('bottom', screen_sizey - 10)
            delta = yield

        direction : int = 1 if unit.position.x < centerx else -1
        while True:
            unit.position += pygame.Vector2(direction * unit.speed * delta, 0)
            if not unit.rect.colliderect(pygame.Rect(0, 0, *core_object.main_display.get_size())):
                break
            delta = yield
        unit.kill_instance_safe()
        return "Done"
    

class EnemyTypes(Enum):
    BASIC = 'basic'
    ELITE = 'elite'
    GUNNER = 'gunner'
    RUNNER = 'runner'

EnemyType : TypeAlias = Literal['basic', 'elite', 'gunner', 'runner']
EnemyTypeList : list[EnemyType] = ['basic', 'elite', 'gunner', 'runner']

class BossTypes(Enum):
    BASIC_BOSS = 'basic_boss'

BossType : TypeAlias = Literal['basic_boss']
BossTypeList : list[BossType] = ['basic_boss']

ENEMY_WEIGHT_DICT : dict[EnemyType|BossType, float] = {
    'basic' : 1,
    'elite' : 2,
    'gunner' : 2,
    'runner' : 2,
    'basic_boss' : 24
}

def runtime_imports():
    global Player
    from src.sprites.player import Player