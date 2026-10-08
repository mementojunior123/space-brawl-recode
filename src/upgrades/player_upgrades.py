import pygame
from typing import Generator, TypeAlias, Literal, TypedDict, cast, Iterable, reveal_type
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, sign
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
from framework.utils.helpers import AnchorStr
from framework.ui import RowLayout, BaseDrawableInfo, BaseUiFrameInfo, UiSprite, UiPosition
from framework.utils.base_particle_effects import ParticleEffect
import src.particle_effects

from .upgrade import AbilityName, Upgrade, UpgradeType, PlayerStatsModifiers, PlayerStatsModifiersKey
from .upgrade import BaseInteractibleUpgrade

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
    def modifier_list(self) -> list[PlayerStatsModifiers]:
        return self.get_modifier_list()

    @property
    def normal_firerate(self) -> float:
        return Player.BASE_SHOT_FIRERATE * self.query_field('global_firerate_mult', float) * self.query_field('normal_firerate_mult', float)

    @property
    def normal_fire_cooldown(self) -> float:
        return 1 / self.normal_firerate

    @property
    def alt_fire_cooldown(self) -> float:
        return self.curr_alt_fire.base_cooldown / (self.query_field('global_firerate_mult', float) * self.query_field('alt_firerate_mult', float))

    @property
    def ability_cooldown(self) -> float:
        return self.curr_ability.base_cooldown / self.query_field('ability_recharge_rate', float)

    @property
    def normal_damage(self) -> float:
        return 1 * self.query_field('normal_damage_mult', float) * self.query_field('global_damage_mult', float)

    @property
    def alt_damage(self) -> float:
        return self.curr_alt_fire.base_damage * self.query_field('alt_damage_mult', float) * self.query_field('global_damage_mult', float)

    @property
    def max_hp(self) -> int:
        return Player.BASE_HEALTH + self.query_field('max_hp_bonus', int)

    @property
    def fixed_accel(self) -> bool:
        return self.query_field('lock_accel', bool) # done

    @property
    def accel_bonus(self) -> pygame.Vector2:
        return self.query_field('accel_bonus', pygame.Vector2) # done

    @property
    def invincible(self) -> bool:
        return self.query_field('invincible', bool) # done

    @property
    def projectile_intangible(self) -> bool:
        return self.query_field('projectile_intangible', bool) # done

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

    def get_modifier_list(self) -> list[PlayerStatsModifiers]:
        mod_list : list[PlayerStatsModifiers] = [upgrade.modifiers for upgrade in self.upgrades]
        mod_list.extend([perk.modifiers for perk in self.curr_perks])
        mod_list.extend([self.curr_ability.modifiers, self.curr_alt_fire.modifiers])
        return mod_list

    def query_field[T](self, field : PlayerStatsModifiersKey, _ : type[T]) -> T:
        return PlayerStatsModifiers.aggregate_field(self.modifier_list, field)

    def update(self, delta : float):
        self.curr_ability.update(delta)
        self.curr_alt_fire.update(delta)
        for perk in self.curr_perks:
            perk.update(delta)

    def on_event(self, event : pygame.Event):
        interactible_upgrade : BaseInteractibleUpgrade
        for interactible_upgrade in self.curr_perks:
            if event in interactible_upgrade.relevant_events:
                if interactible_upgrade.relevant_events[event.type]:
                    interactible_upgrade.event_queue.append(event)
                else:
                    interactible_upgrade.on_event(event)
        for interactible_upgrade in (self.curr_ability, self.curr_alt_fire):
            if event in interactible_upgrade.relevant_events:
                if interactible_upgrade.relevant_events[event.type]:
                    interactible_upgrade.event_queue.append(event)
                else:
                    interactible_upgrade.on_event(event)

def runtime_imports2():
    global Player
    import src.sprites.player
    from src.sprites.player import Player