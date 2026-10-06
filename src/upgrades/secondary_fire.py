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

from src.sprites.projectiles import BaseProjectile

class SecondaryFire:
    @staticmethod
    def get_secondary_fire_from_upgrade(upgrade : Upgrade) -> "SecondaryFire|None":
        return SecondaryFire()

    def __init__(self, *args, **kwargs) -> None:
        self.base_cooldown : float = 1
        self.modifiers : PlayerStatsModifiers = PlayerStatsModifiers()

    def attempt_fire(self) -> BaseProjectile|None:
        ...

    def update(self, delta : float):
        ...