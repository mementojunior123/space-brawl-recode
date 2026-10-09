import pygame
from typing import Generator, TypeAlias, Literal, TypedDict, cast, Iterable
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, sign
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
from framework.utils.helpers import AnchorStr
from framework.ui import RowLayout, BaseDrawableInfo, BaseUiFrameInfo, UiSprite, UiPosition, ProgressBar, UiFrame
from framework.utils.base_particle_effects import ParticleEffect
from src.sprites.projectiles import BaseProjectile
import src.particle_effects

from .upgrade import PerkName, Upgrade, UpgradeType, PlayerStatsModifiers, BaseInteractibleUpgrade

class Perk(BaseInteractibleUpgrade):
    @staticmethod
    def get_perk_from_upgrade(player : 'Player', upgrade : Upgrade) -> "Perk|None":
        perk_name : PerkName = cast(PerkName, upgrade.name)

        match perk_name:
            case 'DamageChain':
                return DamageChainPerk(player, upgrade.rank, upgrade)
            case _:
                return None

    def __init__(self, player : 'Player', name : PerkName, rank : int, original_upgrade : Upgrade|None = None) -> None:
        super().__init__()
        self.player : Player = player
        self.name : PerkName = name
        self.rank : int = rank
        self.original_upgrade : Upgrade|None = original_upgrade
        self.modifiers : PlayerStatsModifiers = PlayerStatsModifiers()

    def update(self, delta : float):
        ...

    def refresh_cooldown(self):
        pass

class DamageChainPerk(Perk):
    MULT_EPSILON : float = 0.01
    def __init__(self, player : 'Player', rank : int, original_upgrade : Upgrade|None = None) -> None:
        name : PerkName = 'DamageChain'
        super().__init__(player, name, rank, original_upgrade)
        self.relevant_events = {BaseProjectile.PROJECTILE_HIT : False, BaseProjectile.PROJECTILE_MISSED : False}
        self.accumulated_damage_bonus : float = 0
        self.frame_timer : Timer = Timer(-1, core_object.game_tsource)
        self.damage_bonus_cap : float = 0.5
        self.decay_per_sec : float = 0.07
        self.hit_bonus : float = 0.05
        self.mult_bar : ProgressBar = ProgressBar(BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.5), 'center', (7, 52))),
                                                  (5, 50), (0, 0, 0, 0), 'Orange', 'up', 0, True)
        bg_image : pygame.Surface = pygame.Surface((5 + 2, 50 + 2), pygame.SRCALPHA)
        bg_image.fill('Light Blue')
        pygame.draw.rect(bg_image, (0, 0, 0, 0), pygame.Rect((1, 1), (5, 50)))
        mult_bar_bg : UiSprite = UiSprite(BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.5), 'center', (7, 52)), zindex=-2), bg_image)
        self.mult_bar_frame : UiFrame = UiFrame(BaseDrawableInfo(UiPosition(self.player.rect.midleft + pygame.Vector2(-10, 0), 'midright')),
                                      [self.mult_bar, mult_bar_bg], BaseUiFrameInfo((7, 52)))
        core_object.main_ui.add(self.mult_bar_frame)

    def update(self, delta : float):
        frame_time : float = self.frame_timer.get_time()
        self.frame_timer.restart()
        if not isinstance(core_object.game.state, core_object.game.STATES.ShopGameState):
            self.accumulated_damage_bonus *= ((1 - self.decay_per_sec) ** frame_time)
            self.update_damage_mult()
        
        self.mult_bar_frame.position = UiPosition(self.player.rect.midleft + pygame.Vector2(-10, 0), 'midright')

    def on_event(self, event : pygame.Event):
        if isinstance(core_object.game.state, core_object.game.STATES.ShopGameState):
            return
        if event.type == BaseProjectile.PROJECTILE_MISSED:
            self.accumulated_damage_bonus = 0 # Make this a penalty
            self.update_damage_mult()
        elif event.type == BaseProjectile.PROJECTILE_HIT:
            self.accumulated_damage_bonus += self.hit_bonus
            self.update_damage_mult()

    def update_damage_mult(self):
        if self.accumulated_damage_bonus > self.damage_bonus_cap:
            self.accumulated_damage_bonus = self.damage_bonus_cap
        if self.accumulated_damage_bonus < self.MULT_EPSILON:
            self.accumulated_damage_bonus = 0
        self.modifiers.global_damage_mult = 1 + self.accumulated_damage_bonus
        self.mult_bar.progress = pygame.math.clamp(self.accumulated_damage_bonus / self.damage_bonus_cap, 0, 1)

    def cleanup(self):
        core_object.main_ui.remove(self.mult_bar_frame)

def runtime_imports4():
    global Player
    from src.sprites.player import Player