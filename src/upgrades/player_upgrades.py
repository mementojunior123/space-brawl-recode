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

from .upgrade import AbilityName, Upgrade, UpgradeType

from .ability import Ability, DashAbility
from .perk import Perk
from .secondary_fire import SecondaryFire

class PlayerUpgrades:
    def __init__(self, player : 'Player'):
        self.player : Player = player
        self.upgrades : list[Upgrade] = [
            Upgrade(UpgradeType.ABILITY, 'Dash', 1, 1, tags= ['overrides_ability']),
            Upgrade(UpgradeType.SECONDARY_FIRE, 'Lazer', 0, 1, tags= ['overrides_weapon'])
        ]
        self.curr_ability : Ability = cast(Ability, Ability.get_ability_from_upgrade(self.player, self.upgrades[0]))
        self.curr_alt_fire : SecondaryFire = cast(SecondaryFire, SecondaryFire.get_secondary_fire_from_upgrade(self.upgrades[1]))
        self.curr_perks : list[Perk] = []

    @property
    def normal_firerate(self) -> float:
        return Player.BASE_SHOT_FIRERATE # How are we going to apply the modifiers?

    @property
    def max_hp(self) -> int:
        return Player.BASE_HEALTH

    @property
    def fixed_accel(self) -> pygame.Vector2|None:
        return None
    ...

    def apply_upgrade(self, upgrade : Upgrade):
        match upgrade.upgrade_type:
            case UpgradeType.ABILITY:
                pass
            case UpgradeType.SECONDARY_FIRE:
                pass
            case UpgradeType.PERK:
                pass
            case UpgradeType.MAJOR:
                pass
            case UpgradeType.MINOR:
                self.upgrades.append(upgrade)

    def update(self, delta : float):
        self.curr_ability.update(delta)
        self.curr_alt_fire.update(delta)
        for perk in self.curr_perks:
            perk.update(delta)

def runtime_imports2():
    global Player
    import src.sprites.player
    from src.sprites.player import Player