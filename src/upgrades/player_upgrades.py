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

from .upgrade import Upgrade, UpgradeType, PlayerStatsModifiers, PlayerStatsModifiersKey
from .upgrade import BaseInteractibleUpgrade, PRE_UPGRADE_HOOKS, POST_UPGRADE_HOOKS
from .upgrade import SecondaryFireName

from .ability import Ability, DashAbility
from .perk import Perk
from .secondary_fire import SecondaryFire

from src.sprites.projectiles import BaseProjectile
from src.sprites.enemy import BaseEnemy

class PlayerUpgrades:
    def __init__(self, player : 'Player'):
        default_alt_fire : Upgrade = cast(Upgrade, Upgrade.from_name_and_rank('LazerShot', 0))
        default_ability : Upgrade = cast(Upgrade, Upgrade.from_name_and_rank('Dash', 1))

        self.player : Player = player
        self.upgrades : list[Upgrade] = []
        self.curr_ability : Ability = cast(Ability, Ability.get_ability_from_upgrade(self.player, default_ability))
        self.curr_alt_fire : SecondaryFire = cast(SecondaryFire, SecondaryFire.get_secondary_fire_from_upgrade(self.player, default_alt_fire))
        self.curr_perks : list[Perk] = []

        self.apply_upgrade(default_alt_fire)
        self.apply_upgrade(default_ability)

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
    def alt_fire_damage(self) -> float:
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

    def apply_upgrade(self, upgrade : Upgrade|None) -> bool:
        if upgrade is None:
            return False
        if upgrade.name in PRE_UPGRADE_HOOKS:
            hook_exec_result : bool|None = PRE_UPGRADE_HOOKS[upgrade.name](self, upgrade)
            if hook_exec_result is not None:
                return hook_exec_result
            
        remove_all_of_type : bool = upgrade.upgrade_type in (UpgradeType.ABILITY, UpgradeType.SECONDARY_FIRE)
        match upgrade.upgrade_type:
            case UpgradeType.ABILITY:
                new_ability : Ability|None = Ability.get_ability_from_upgrade(self.player, upgrade)
                if new_ability is None:
                    core_object.log(f"Could not create ability '{upgrade.name}'!")  # TODO : Remember to delete old Upgrades
                    return False
                
                self.curr_ability.cleanup()
                self.curr_ability = new_ability

            case UpgradeType.SECONDARY_FIRE:
                new_rank : int
                if upgrade.rank == 0:
                    new_rank = self.get_rank_transfer(cast(SecondaryFireName, upgrade.name))
                else:
                    new_rank = upgrade.rank
                upgrade.rank = new_rank

                new_alt_fire : SecondaryFire|None = SecondaryFire.get_secondary_fire_from_upgrade(self.player, upgrade)
                if new_alt_fire is None:
                    core_object.log(f"Could not create alternate fire '{upgrade.name}'!")
                    return False
                
                self.curr_alt_fire.cleanup()
                self.curr_alt_fire = new_alt_fire

            case UpgradeType.PERK:
                new_perk : Perk|None = Perk.get_perk_from_upgrade(self.player, upgrade)
                if new_perk is None:
                    core_object.log(f"Could not create perk '{upgrade.name}'!")
                    return False
                    
                if not upgrade.stackable:
                    overriden_interactible_perks : list[Perk] = list(filter(lambda p : p.name == upgrade.name and p is not upgrade, self.curr_perks))
                    for p in overriden_interactible_perks:
                        self.curr_perks.remove(p)
                        p.cleanup() 
                self.curr_perks.append(new_perk)
            case UpgradeType.MAJOR:
                pass
            case UpgradeType.MINOR:
                pass

        self.upgrades.append(upgrade)
        if not upgrade.stackable or remove_all_of_type:
            overriden_perk_upgrades : list[Upgrade] = list(filter(
                lambda p : (p.name == upgrade.name and not upgrade.stackable) or (remove_all_of_type and p.upgrade_type == upgrade.upgrade_type),
                self.upgrades))
            for to_del_upgrade in overriden_perk_upgrades:
                if to_del_upgrade == upgrade:
                    continue
                self.upgrades.remove(to_del_upgrade)

        if upgrade.name in POST_UPGRADE_HOOKS:
            POST_UPGRADE_HOOKS[upgrade.name](self, upgrade)
        return True

    def get_rank_transfer(self, new_weapon : SecondaryFireName) -> int:
        return Upgrade.get_specialisation_transfer_rank(self.curr_alt_fire.rank, self.curr_alt_fire.name, 
                                                                        cast(SecondaryFireName, new_weapon))

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
            if event.type in interactible_upgrade.relevant_events:
                if interactible_upgrade.relevant_events[event.type]:
                    interactible_upgrade.event_queue.append(event)
                else:
                    interactible_upgrade.on_event(event)
        for interactible_upgrade in (self.curr_ability, self.curr_alt_fire):
            if event.type in interactible_upgrade.relevant_events:
                if interactible_upgrade.relevant_events[event.type]:
                    interactible_upgrade.event_queue.append(event)
                else:
                    interactible_upgrade.on_event(event)

def runtime_imports2():
    global Player
    import src.sprites.player
    from src.sprites.player import Player