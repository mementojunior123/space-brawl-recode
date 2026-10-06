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

from src.sprites.projectiles import BaseProjectile, NormalProjectile, Teams
from src.sprites.enemy import BaseNormalEnemy, BaseEnemy

from src.upgrades import PlayerUpgrades

for i in range(8):
    core_object.asset_manager.load_surface(f"assets/graphics/player/player-{i}.png", f'player_cycle{i}', 'alpha_to_colorkey', 2, (0, 255, 0))

core_object.asset_manager.load_surface("assets/graphics/player/heart2.png", "full_heart", 'alpha_to_colorkey', colorkey=(0, 255, 0))
core_object.asset_manager.load_surface("assets/graphics/player/empty_heart4.png", "empty_heart", 'alpha_to_colorkey', colorkey=(0, 255, 0))

core_object.asset_manager.load_sound("assets/audio/sfx/player_hit2.ogg", 'hit_sfx', 0.5)
core_object.asset_manager.load_sound("assets/audio/sfx/normal_shot3.ogg", 'normal_shot_sfx', 0.5)
core_object.asset_manager.load_sound("assets/audio/sfx/lazer.ogg", 'lazer_shot_sfx', 0.4)
core_object.asset_manager.load_sound("assets/audio/sfx/shotgun_shot.ogg", 'shotgun_shot_sfx', 0.7)
core_object.asset_manager.load_sound("assets/audio/sfx/rocket_shot.ogg", 'rocket_shot_sfx', 0.18)
core_object.asset_manager.load_sound("assets/audio/sfx/dash.ogg", 'dash_sfx', 0.4)

enemy_killed_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('enemy_killed'))

class PlayerHealthbar(RowLayout):
    def __init__(self, heart_count : int, position : pygame.Vector2, anchor : AnchorStr):
        SPACING : int = 4
        HEART_WIDTH : int = max(Player.empty_heart.get_size()[0], Player.full_heart.get_size()[0])
        size : tuple[int, int] = ((SPACING + HEART_WIDTH) * max(heart_count, 1), 100)
        pos : UiPosition = UiPosition(UiPosition(position, anchor).calculate_anchor(size, 'midright'), 'midright')
        base_drawable_info : BaseDrawableInfo = BaseDrawableInfo(pos, name="player_healthbar")
        ui_frame_info : BaseUiFrameInfo = BaseUiFrameInfo((size))

        self._heart_count : int = heart_count
        self._health : int = heart_count

        super().__init__(base_drawable_info, [], ui_frame_info, SPACING)

        self.update_heart_amount()
        self.update_hearts()

    @property
    def heart_count(self) -> int:
        return self._heart_count

    @heart_count.setter
    def heart_count(self, value : int):
        self._heart_count = value
        self.update_heart_amount()

    @property
    def health(self) -> int:
        return self._health

    @health.setter
    def health(self, value : int):
        self._health = value
        self.update_hearts()
    
    def make_new_heart(self) -> UiSprite:
        return UiSprite(BaseDrawableInfo(UiPosition((0, 0), 'topright')), Player.full_heart)

    def update_heart_amount(self):
        curr_elem_count : int = len(self.elements)
        if curr_elem_count < self._heart_count:
            for _ in range(self._heart_count - curr_elem_count):
                self.add(self.make_new_heart())
        elif curr_elem_count > self._heart_count:
            for _ in range(curr_elem_count - self._heart_count):
                if self.elements: self.elements.pop()
        self.update_hearts()

    def update_hearts(self):
        for i, heart_sprite in enumerate(cast(Iterable[UiSprite], reversed(self.elements)), start=1):
            if i <= self._health:
                heart_sprite.base_surf = Player.full_heart
            else:
                heart_sprite.base_surf = Player.empty_heart

class Player(Sprite, sprite_count=1):
    animation_assets : dict[int, pygame.Surface] = {i : cast(pygame.Surface, core_object.asset_manager.get_surface(f"player_cycle{i}")) for i in range(8)}
    display_size = core_object.main_display.get_size()
    full_heart : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface("full_heart"))
    empty_heart : pygame.Surface = cast(pygame.Surface, core_object.asset_manager.get_surface("empty_heart"))

    normal_projectile_image : pygame.Surface = recolor_image(BaseProjectile.normal_image3, "White")

    INVULN_TIME : float = 1.5

    ACCEL_SPEED : float = 3.0
    FRICTION : float = 0.3
    MIN_VELOCITY : float = 0.1
    MAX_VELOCITY : float = 30
    BASE_SHOT_FIRERATE : float = 3
    BASE_HEALTH : int = 3

    PRIMARY_FIRE_BIND = pygame.K_SPACE
    ABILITY_BIND = pygame.K_LSHIFT

    def __init__(self) -> None:
        super().__init__()
        self.animation_images : dict[int, pygame.Surface]
        self.velocity : pygame.Vector2

        self.visible : bool
        self.max_hp : int
        self.current_hp : int
        self.healthbar : PlayerHealthbar

        self.invuln_timer : Timer
        self.animation_script : PlayerAnimationScript
        self.shot_cooldown_timer : Timer

        self.upgrades : PlayerUpgrades

        self.ability_cooldown_timer : Timer
        self.alt_fire_cooldown_timer : Timer

        self.mask : pygame.Mask #type: ignore

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        element = cls.inactive_elements[0]

        element.animation_images = cls.animation_assets
        element.image = element.animation_images[0]
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element._position = pygame.Vector2(0, 0)
        element.velocity = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.visible = True
        element.max_hp = Player.BASE_HEALTH
        element.current_hp = element.max_hp
        element.healthbar = PlayerHealthbar(element.max_hp, pygame.Vector2(950, 10), 'topright')

        element.invuln_timer = Timer(Player.INVULN_TIME, core_object.game_tsource)
        element.invuln_timer.start_time -= Player.INVULN_TIME
        element.animation_script = PlayerAnimationScript()
        element.animation_script.initialize(core_object.game_tsource or Timer.base_time_source, element, 0.25)
        
        element.shot_cooldown_timer = Timer(1 / Player.BASE_SHOT_FIRERATE, core_object.game_tsource)
        element.shot_cooldown_timer.start_time -= 1 / Player.BASE_SHOT_FIRERATE

        element.ability_cooldown_timer = Timer(-1, core_object.game_tsource)
        element.alt_fire_cooldown_timer = Timer(-1, core_object.game_tsource)

        element.upgrades = PlayerUpgrades(element)

        element.ability_cooldown_timer.set_duration(element.upgrades.curr_ability.base_cooldown)
        element.ability_cooldown_timer.start_time -= element.upgrades.curr_ability.base_cooldown
        element.alt_fire_cooldown_timer.set_duration(element.upgrades.curr_alt_fire.base_cooldown)
        element.alt_fire_cooldown_timer.start_time -= element.ability_cooldown_timer.start_time

        core_object.main_ui.add(element.healthbar)

        cls.unpool(element)
        return element

    def update(self, delta : float):
        self.update_movement(delta)
        self.check_collision()
        self.check_input()
        self.upgrades.update(delta)
        self.animation_script.process_frame()

    def update_movement(self, delta : float):
        accel = self.calculate_acceleration()
        self.velocity *=  ((1 - self.FRICTION) ** delta) ** 0.5

        self.velocity += accel * 0.5 * delta
        self.position += self.velocity * delta
        self.velocity += accel * 0.5 * delta

        self.velocity *=  ((1 - self.FRICTION) ** delta) ** 0.5
        curr_speed : float = self.velocity.magnitude()
        if curr_speed < Player.MIN_VELOCITY:
            self.velocity = pygame.Vector2(0, 0)
        elif curr_speed > Player.MAX_VELOCITY:
            self.velocity.scale_to_length(Player.MAX_VELOCITY)
        self.restrict_to_screen()

    def calculate_acceleration(self) -> pygame.Vector2:
        pressed_keys = pygame.key.get_pressed()
        accel_total : pygame.Vector2 = pygame.Vector2(0, 0)
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            accel_total += pygame.Vector2(-Player.ACCEL_SPEED, 0)
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            accel_total += pygame.Vector2(Player.ACCEL_SPEED, 0)
        return accel_total

    def restrict_to_screen(self):
        MARGIN : int = 25
        if self.rect.right > Player.display_size[0] - MARGIN:
            self.move_rect("right", Player.display_size[0] - MARGIN)
            if self.velocity.x > 0: self.velocity.x = 0
        if self.rect.bottom > Player.display_size[1]:
            self.move_rect("bottom", Player.display_size[1])
        if self.rect.left < MARGIN:
            self.move_rect('left', MARGIN)
            if self.velocity.x < 0: self.velocity.x = 0
        if self.rect.top < 0:
            self.move_rect('top', 0)

    def check_collision(self):
        colliding_projectiles : list[BaseProjectile] = [elem for elem in self.get_all_colliding(BaseProjectile)
                                                        if elem.team in (Teams.ENEMY, Teams.FFA)]
        colliding_enemies : list[BaseEnemy] = self.get_all_colliding(BaseEnemy)
        for enemy in colliding_enemies:
            took_damage : bool = self.take_damage(1)
            if isinstance(enemy, BaseNormalEnemy):
                if took_damage:
                    enemy.kill_instance()
                else:
                    enemy_killed_effect.play(enemy.position.copy(), core_object.game.game_timer.get_time)
                    core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
                    enemy.give_score(enemy.KILL_SCORE)
                    enemy.kill_instance()
        for proj in colliding_projectiles:
            self.take_damage(proj.damage)
            proj.kill_instance()

    def take_damage(self, damage : float) -> bool:
        if (not self.invuln_timer.isover()):
            return False
        core_object.log(f"Player took damage : {damage}")
        self.current_hp -= min(round(damage), 1)
        self.invuln_timer.restart()
        core_object.bg_manager.play_sfx('hit_sfx', 1.0)
        self.healthbar.health = self.current_hp
        return True

    def check_input(self):
        pressed = pygame.key.get_pressed()
        if pressed[Player.PRIMARY_FIRE_BIND]:
            self.attempt_primary_fire(ignore_cooldown=False)
        if pressed[Player.ABILITY_BIND] or pressed[pygame.K_RSHIFT]:
            self.attempt_ability_use(ignore_cooldown=False)
        

    def attempt_primary_fire(self, ignore_cooldown : bool = False) -> BaseProjectile|None:
        if not self.shot_cooldown_timer.isover() and not ignore_cooldown:
            return None
        return self.shoot()

    def attempt_ability_use(self, ignore_cooldown : bool = False) -> bool:
        if not self.ability_cooldown_timer.isover() and not ignore_cooldown:
            return False
        if self.upgrades.curr_ability.activate():
            self.ability_cooldown_timer.restart() # set it to the updated amount
            return True
        return False

    def shoot(self) -> BaseProjectile:
        self.shot_cooldown_timer.set_duration(1 / Player.BASE_SHOT_FIRERATE)
        core_object.bg_manager.play_sfx('normal_shot_sfx', 1.0)
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -10), None, None, 0,
            Player.normal_projectile_image, team=Teams.ALLIED,
            damage = 1, can_destroy=True)

    def draw(self, display : pygame.Surface):
        if not self.visible:
            return
        super().draw(display)

    def clean_instance(self):
        super().clean_instance()
        del self.animation_images
        del self.velocity

        del self.visible
        del self.healthbar
        del self.max_hp
        del self.current_hp

        del self.invuln_timer
        del self.animation_script
        del self.shot_cooldown_timer
        del self.upgrades

        del self.ability_cooldown_timer
        del self.alt_fire_cooldown_timer
        
class PlayerAnimationScript(CoroutineScript[None, None]):
    def initialize(self, time_source : TimeSource, player : Player, cycle_time : float):
        return super().initialize(time_source, player, cycle_time)
    
    @staticmethod
    def corou(time_source : TimeSource, player : Player, cycle_time : float):
        animation_timer : Timer = Timer(-1, time_source)
        prev_index : int = 0
        yield
        while True:
            image_index : int = int((animation_timer.get_time() * 8) // cycle_time) % 8
            if image_index != prev_index:
                player.image = player.animation_images[image_index]
                player.mask = pygame.mask.from_surface(player.image)
                prev_index = image_index
            if player.invuln_timer.isover():
                player.visible = True
            else:
                player.visible = (int(player.invuln_timer.get_time() / player.invuln_timer.duration * 5) % 2) != 0
            yield