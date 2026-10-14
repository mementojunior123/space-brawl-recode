import pygame
from typing import Generator, TypeAlias, Literal, cast
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, AnchorStr
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

from src.sprites.base_enemy import BaseEnemy, BaseNormalEnemy, BaseBossEnemy, EnemyType, BossType, ENEMY_WEIGHT_DICT
from src.sprites.base_enemy import enemy_killed_particle_effect, enemy_damaged_particle_effect, explosion_particle_effect, explosion_small_effect

from src.sprites.enemy import BasicEnemy, EliteEnemy, GunnerEnemy, RunnerEnemy

boss_killed_particle_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('boss_killed'))

core_object.asset_manager.load_surface("assets/graphics/enemy/alien.png", 'basic_boss', 'alpha_to_colorkey', base_scale=2, colorkey=(0, 255, 0))

class BasicBoss(BaseBossEnemy, sprite_count=5):
    KILL_SCORE_BOSS = 200
    KILL_SCORE_REGULAR = 60

    default_image = cast(pygame.Surface, core_object.asset_manager.get_surface('basic_boss'))

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def spawn(cls, position_anchor : AnchorStr = "midbottom", position : pygame.Vector2|None = None,
              max_health : float = 50, summoned_as_boss : bool = True):
        element = cls.inactive_elements[0]
        
        element.image = element.default_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position if position is not None else pygame.Vector2(480, 0))
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.type = 'basic_boss'
        element.max_hp = max_health
        element.health = element.max_hp

        element.health_bar = ProgressBar(BaseDrawableInfo(element.calc_health_bar_pos(), zindex=-10), (50, 5), "#555454", "Dark Green", 'right', 1)
        element.update_health_bar_surf()
        element.health_bar.visible = False
        core_object.main_ui.add(element.health_bar)

        element.invincible = False
        element.summoned_as_boss = summoned_as_boss
        element.real_kill_score = cls.KILL_SCORE_BOSS if summoned_as_boss else cls.KILL_SCORE_REGULAR

        element.control_script = BasicBossControlScript()
        element.control_script.initialize(core_object.game_tsource or Timer.base_time_source, element)

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        next_script = self.control_script.process_frame(delta)
        if isinstance(next_script, CoroutineScript):
            self.control_script = next_script
            self.control_script.initialize(core_object.game.game_timer.get_time, self)
        elif self.control_script.is_over:
            self.kill_instance_safe()
            return
        self.check_collisions()
        self.update_health_bar_pos()

    def take_damage(self, damage: float):
        super().take_damage(damage)
        self.update_health_bar_surf()

    def clean_instance(self):
        super().clean_instance()

class BasicBossControlScript(CoroutineScript[float, None|str|CoroutineScript]):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        entry_script : BasicBossEntryScript = BasicBossEntryScript()
        entry_script.initialize(time_source, unit)
        delta = yield
        if delta is None: delta = core_object.dt
        while not entry_script.is_over:
            entry_script.process_frame(delta)
            delta = yield
        
        main_script : BasicBossMovementScript = BasicBossMovementScript()
        main_script2 : BasicBossShootingScript = BasicBossShootingScript()
        main_script.initialize(time_source, unit)
        main_script2.initialize(time_source, unit)
        while unit.health > 0:
            main_script.process_frame(delta)
            main_script2.process_frame(delta)
            delta = yield
        unit.invincible = True
        death_script : BasicBossDeathSequence = BasicBossDeathSequence()
        death_script.initialize(time_source, unit)
        while not death_script.is_over:
            death_script.process_frame(delta)
            delta = yield
        unit.give_score(unit.real_kill_score)
        return

class BasicBossEntryScript(CoroutineScript[float, None|str]):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        target_position : pygame.Vector2 = pygame.Vector2(centerx, 20) + pygame.Vector2(0, unit.rect.height // 2)
        start_position : pygame.Vector2 = unit.position.copy()
        move_in_timer : Timer = Timer(2, time_source)
        delta = yield
        unit.invincible = True
        if delta is None: delta = core_object.dt
        while not move_in_timer.isover():
            alpha : float = interpolation.smoothstep(move_in_timer.get_time() / move_in_timer.duration)
            if alpha > 1: alpha = 1
            new_pos : pygame.Vector2 = start_position.lerp(target_position, alpha)
            unit.position = new_pos
            delta = yield
        unit.position = target_position
        unit.invincible = False
        return "Done"

class BasicBossMovementScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def predict_projectile_contact(unit : BasicBoss, projectile : BaseProjectile, unit_velocity : pygame.Vector2,
                                   bounding_box : pygame.Rect) -> bool:
        if abs(unit.position.y - projectile.position.y) > 200.0:
            return False
        projected_unit_position : pygame.Vector2 = unit.position.copy()
        projected_projectile_position : pygame.Vector2 = projectile.position.copy()
        projected_unit_rect = unit.rect.copy()
        projected_projectile_rect = projectile.rect.copy()
        prev_distance : float = 999_999.0
        for _ in range(100):
            projected_unit_position += unit_velocity
            projected_projectile_position += projectile.velocity
            projected_projectile_rect.center = projected_projectile_position
            projected_unit_rect.center = projected_unit_position
            distance : float = (projected_projectile_position - projected_unit_position).magnitude()
            if projected_projectile_rect.colliderect(projected_unit_rect):
                return True
            prev_distance = distance
            if not (bounding_box.collidepoint(projected_unit_position) and bounding_box.collidepoint(projected_projectile_position)):
                break
        return False

    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        dodge_cooldown : Timer = Timer(0.5, time_source)
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)
        direction : int = 1
        SPEED : float = 6.0
        move_timer : Timer = Timer(-1, time_source)
    
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, SPEED, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            distance_to_margin : float = min(unit.rect.left, abs(screen_sizex - unit.rect.right))
            if distance_to_margin > 50:
                if dodge_cooldown.isover():
                    for proj in BaseProjectile.active_elements:
                        if proj.team not in (Teams.ALLIED, Teams.FFA):
                            continue
                        if BasicBossMovementScript.predict_projectile_contact(
                        unit, proj, pygame.Vector2(direction * SPEED, 0), bounding_box):
                            dodge_cooldown.set_duration(0.75 if distance_to_margin > 200 else 1.25 )
                            if distance_to_margin < 100:
                                luck = 4
                            else:
                                luck = 7
                            if random.randint(1, 10) <= luck:
                                direction *= -1
            delta = yield

class BasicBossShootingScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)

    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 4
        elif x_offset < 50:
            return 2
        elif x_offset < 100:
            return 1.5
        elif x_offset < 150:
            return 1
        else:
            return 0.5
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss):
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
            proximity_buff : float = BasicBossShootingScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required and player is not None:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position)) * 0
                unit.fire_normal_projectile(8, angle_offset)
                shotgun_odds : int = 1 if angle_offset < 10 else 2
                fired_shotgun : bool = random.randint(1, 4) <= shotgun_odds
                if fired_shotgun:
                    core_object.bg_manager.play_sfx('shotgun_shot_sfx', 1.0)
                    unit.fire_normal_projectile(8, angle_offset - 20)
                    unit.fire_normal_projectile(8, angle_offset + 20)
                else:
                    pass
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(60, 120) if not fired_shotgun else random.uniform(80, 160)
            delta = yield

class BasicBossDeathSequence(CoroutineScript[float, str|None]):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        delta = yield
        if delta is None: delta = core_object.dt
        #Insert death sequence
        boss_killed_particle_effect.play(unit.position.copy(), core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
        core_object.main_ui.remove(unit.health_bar)
        return "Done"

core_object.asset_manager.load_surface(f"assets/graphics/enemy/elite_enemy.png", 'elite_boss', 'alpha_to_colorkey', base_scale=2, colorkey=(0, 255, 0))

class EliteBoss(BaseBossEnemy, sprite_count=5):
    KILL_SCORE_BOSS = 300
    KILL_SCORE_REGULAR = 100

    default_image = cast(pygame.Surface, core_object.asset_manager.get_surface('elite_boss'))

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def spawn(cls, position_anchor : AnchorStr = "midbottom", position : pygame.Vector2|None = None,
              max_health : float = 100, summoned_as_boss : bool = True):
        element = cls.inactive_elements[0]
        
        element.image = element.default_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position if position is not None else pygame.Vector2(480, 0))
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.type = 'elite_boss'
        element.max_hp = max_health
        element.health = element.max_hp

        element.health_bar = ProgressBar(BaseDrawableInfo(element.calc_health_bar_pos(), zindex=-10), (50, 5), "#555454", "Dark Green", 'right', 1)
        element.update_health_bar_surf()
        element.health_bar.visible = False
        core_object.main_ui.add(element.health_bar)

        element.invincible = False
        element.summoned_as_boss = summoned_as_boss
        element.real_kill_score = cls.KILL_SCORE_BOSS if summoned_as_boss else cls.KILL_SCORE_REGULAR

        element.control_script = EliteBossControlScript()
        element.control_script.initialize(core_object.game_tsource or Timer.base_time_source, element)

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        next_script = self.control_script.process_frame(delta)
        if isinstance(next_script, CoroutineScript):
            self.control_script = next_script
            self.control_script.initialize(core_object.game.game_timer.get_time, self)
        elif self.control_script.is_over:
            self.kill_instance_safe()
            return
        self.check_collisions()
        self.update_health_bar_pos()

    def take_damage(self, damage: float):
        super().take_damage(damage)
        self.update_health_bar_surf()

    def clean_instance(self):
        super().clean_instance()

class EliteBossControlScript(CoroutineScript[float, None|str|CoroutineScript]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        entry_script : EliteBossEntryScript = EliteBossEntryScript()
        entry_script.initialize(time_source, unit)
        delta = yield
        if delta is None: delta = core_object.dt
        while not entry_script.is_over:
            entry_script.process_frame(delta)
            delta = yield
        
        main_script : EliteBossMovementScript = EliteBossMovementScript()
        main_script2 : EliteBossShootingNormalScript = EliteBossShootingNormalScript()
        main_script3 : EliteBossHomingShotScript = EliteBossHomingShotScript()
        main_script.initialize(time_source, unit)
        main_script2.initialize(time_source, unit)
        main_script3.initialize(time_source, unit)
        while unit.health > 0:
            main_script.process_frame(delta)
            main_script2.process_frame(delta)
            main_script3.process_frame(delta)
            delta = yield
        unit.invincible = True
        death_script : EliteBossDeathSequence = EliteBossDeathSequence()
        death_script.initialize(time_source, unit)
        while not death_script.is_over:
            death_script.process_frame(delta)
            delta = yield
        unit.give_score(unit.real_kill_score)
        return

class EliteBossEntryScript(CoroutineScript[float, None|str]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        target_position : pygame.Vector2 = pygame.Vector2(centerx, 20) + pygame.Vector2(0, unit.rect.height // 2)
        start_position : pygame.Vector2 = unit.position.copy()
        move_in_timer : Timer = Timer(2, time_source)
        delta = yield
        unit.invincible = True
        if delta is None: delta = core_object.dt
        while not move_in_timer.isover():
            alpha : float = interpolation.smoothstep(move_in_timer.get_time() / move_in_timer.duration)
            if alpha > 1: alpha = 1
            new_pos : pygame.Vector2 = start_position.lerp(target_position, alpha)
            unit.position = new_pos
            delta = yield
        unit.position = target_position
        unit.invincible = False
        return "Done"

class EliteBossMovementScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def predict_projectile_contact(unit : EliteBoss, projectile : BaseProjectile, unit_velocity : pygame.Vector2,
                                   bounding_box : pygame.Rect) -> bool:
        if abs(unit.position.y - projectile.position.y) > 200.0:
            return False
        projected_unit_position : pygame.Vector2 = unit.position.copy()
        projected_projectile_position : pygame.Vector2 = projectile.position.copy()
        projected_unit_rect = unit.rect.copy()
        projected_projectile_rect = projectile.rect.copy()
        prev_distance : float = 999_999.0
        for _ in range(100):
            projected_unit_position += unit_velocity
            projected_projectile_position += projectile.velocity
            projected_projectile_rect.center = projected_projectile_position
            projected_unit_rect.center = projected_unit_position
            distance : float = (projected_projectile_position - projected_unit_position).magnitude()
            if projected_projectile_rect.colliderect(projected_unit_rect):
                return True
            prev_distance = distance
            if not (bounding_box.collidepoint(projected_unit_position) and bounding_box.collidepoint(projected_projectile_position)):
                break
        return False

    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        dodge_cooldown : Timer = Timer(0.5, time_source)
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)
        direction : int = 1
        SPEED : float = 6.0
        move_timer : Timer = Timer(-1, time_source)
    
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, SPEED, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            distance_to_margin : float = min(unit.rect.left, abs(screen_sizex - unit.rect.right))
            if distance_to_margin > 50:
                if dodge_cooldown.isover():
                    for proj in BaseProjectile.active_elements:
                        if proj.team not in (Teams.ALLIED, Teams.FFA):
                            continue
                        if EliteBossMovementScript.predict_projectile_contact(
                        unit, proj, pygame.Vector2(direction * SPEED, 0), bounding_box):
                            dodge_cooldown.set_duration(0.6 if distance_to_margin > 200 else 0.9 )
                            if distance_to_margin < 100:
                                luck = 5
                            else:
                                luck = 7
                            if random.randint(1, 10) <= luck:
                                direction *= -1
            delta = yield

class EliteBossShootingNormalScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)

    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 4
        elif x_offset < 50:
            return 2
        elif x_offset < 100:
            return 1.5
        elif x_offset < 150:
            return 1
        else:
            return 0.5
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
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
            proximity_buff : float = EliteBossShootingNormalScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required and player is not None:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position))
                unit.fire_normal_projectile()
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(40, 70)
            delta = yield

class EliteBossHomingShotScript(CoroutineScript[float, None]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 2
        elif x_offset < 50:
            return 1.5
        elif x_offset < 100:
            return 1
        elif x_offset < 150:
            return 0.8
        else:
            return 0.8
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        min_shot_cooldown : Timer = Timer(0.25, time_source)
        aggro_required : float = 200.0
        current_aggro : float = 0
        player : Player|None
        if not Player.active_elements:
            player = None
        else:
            player = Player.active_elements[0]
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            proximity_buff : float = EliteBossHomingShotScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required and player is not None:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position))

                unit.fire_homing_projectile(angle=angle_offset - 30)
                unit.fire_homing_projectile(angle=angle_offset + 30)
                core_object.bg_manager.play_sfx('rocket_shot_sfx', 1.0)
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(180, 360)
            delta = yield

class EliteBossDeathSequence(CoroutineScript[float, str|None]):
    def initialize(self, time_source : TimeSource, unit : EliteBoss):
        return super().initialize(time_source, unit)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : EliteBoss):
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        delta = yield
        if delta is None: delta = core_object.dt
        #Insert death sequence
        boss_killed_particle_effect.play(unit.position.copy(), core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
        core_object.main_ui.remove(unit.health_bar)
        return "Done"

def runtime_imports():
    from src.sprites.enemy import runtime_imports as rt2
    rt2()
    global Player
    from src.sprites.player import Player