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

from .upgrade import AbilityName, Upgrade, UpgradeType, PlayerStatsModifiers

class Ability:
    BASE_COOLDWON : float = -1
    @staticmethod
    def get_ability_from_upgrade(player : 'Player', upgrade : Upgrade) -> 'Ability|None':
        if upgrade.upgrade_type != UpgradeType.ABILITY:
            return None
        ability_name : AbilityName = cast(AbilityName, upgrade.name)
        match ability_name:
            case 'Dash':
                return DashAbility(player, upgrade.rank, upgrade)
            case _:
                return None
        
    def __init__(self, player : 'Player', name : AbilityName, rank : int, base_cooldown : float,
                 original_upgrade : Upgrade|None = None) -> None:
        self.player : Player = player
        self.name : AbilityName = name
        self.rank : int = rank
        self.base_cooldown : float = base_cooldown
        self.original_upgrade : Upgrade|None = original_upgrade
        self.modifiers : PlayerStatsModifiers = PlayerStatsModifiers()

    def activate(self) -> bool: # Does activate need to return anything?
        return True

    def update(self, delta : float):
        pass

class DashAbility(Ability):
    BASE_COOLDOWN : float = 3
    def __init__(self, player : 'Player', rank : int, original_upgrade : Upgrade|None = None) -> None:
        super().__init__(player, 'Dash', rank, self.BASE_COOLDOWN, original_upgrade)
        self.dash_timer : Timer = Timer(-1, core_object.game_tsource)

    def activate(self) -> bool:
        active_keys = pygame.key.get_pressed()
        direction : int = -1 * (active_keys[pygame.K_a] or active_keys[pygame.K_LEFT]) + 1 * (active_keys[pygame.K_d] or active_keys[pygame.K_RIGHT])
        if direction == 0:
            if self.player.velocity.x == 0:
                return False
            direction = round(sign(self.player.velocity.x))
        self.player.velocity += pygame.Vector2(direction, 0) * 50
        return True

def runtime_imports1():
    global Player
    import src.sprites.player
    from src.sprites.player import Player