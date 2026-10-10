import pygame
from typing import Literal, TypedDict, NotRequired, Required, cast, Callable, Any
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field
from framework.utils.helpers import AnchorStr, ColorType, to_roman, RectSideAnchorStr
from framework.ui import TextStyle
from framework.core.core import core_object

type ModifierAggregationFunction = Callable[[str, list[PlayerStatsModifiers], list[Any]], Any]

type PreUpgradeApplicationCallback = Callable[['PlayerUpgrades', 'Upgrade'], bool|None]
type PostUpgradeApplicationCallback = Callable[['PlayerUpgrades', 'Upgrade'], None]

class AggregatorMethods:
    @staticmethod
    def sum_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'], 
                       values : list[Any]) -> Any:
        return sum(values)

    @staticmethod
    def adjusted_sum_aggregator_creator(adjustment : float = 1) -> ModifierAggregationFunction:
        return lambda f, m, v : sum(v) + adjustment

    @staticmethod
    def manual_sum_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'], 
                              values : list[Any]) -> Any:
        if not values:
            return None
        result = values[0]
        skip_first : bool = True
        for value in values:
            if skip_first:
                skip_first = False
            else:
                result = result + value
        return result

    @staticmethod
    def manual_product_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'], 
                                  values : list[Any]) -> Any:
        if not values:
            return None
        result = values[0]
        skip_first : bool = True
        for value in values:
            if skip_first:
                skip_first = False
            else:
                result = result * value
        return result

    @staticmethod
    def any_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'],
                       values : list[Any] )-> Any:
        return any(values)

    @staticmethod
    def all_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'],
                        values : list[Any] )-> Any:
        return all(values)

    @staticmethod
    def min_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'],
                        values : list[Any] )-> Any:
        return min(values)

    @staticmethod
    def max_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'],
                        values : list[Any] )-> Any:
        return max(values)

    @staticmethod
    def warn_missing(field_name : str, *args, **kwargs):
        core_object.log(f'Missing field aggregation method for {field_name}!')
        return None

type PlayerStatsModifiersKey = Literal['max_hp_bonus', 'normal_firerate_mult', 'alt_firerate_mult',
                                       'global_firerate_mult', 'accel_bonus', 'lock_accel', 'invincible',
                                       'projectile_intangible',
                                       'normal_damage_mult', 'alt_damage_mult', 'global_damage_mult',
                                       'ability_recharge_rate']

MODIFIER_AGGREGATOR_DICT : dict[PlayerStatsModifiersKey, ModifierAggregationFunction] = {
    'max_hp_bonus' : AggregatorMethods.sum_aggregator,
    'normal_firerate_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'alt_firerate_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'global_firerate_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'accel_bonus' : AggregatorMethods.manual_sum_aggregator,
    'lock_accel' : AggregatorMethods.any_aggregator,
    'invincible' : AggregatorMethods.any_aggregator,
    'projectile_intangible' : AggregatorMethods.any_aggregator,
    'normal_damage_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'alt_damage_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'global_damage_mult' : AggregatorMethods.adjusted_sum_aggregator_creator(1),
    'ability_recharge_rate' : AggregatorMethods.adjusted_sum_aggregator_creator(1)
}


@dataclass
class PlayerStatsModifiers:
    max_hp_bonus : int = 0
    normal_firerate_mult : float = 0
    alt_firerate_mult : float = 0
    global_firerate_mult : float = 0
    normal_damage_mult : float = 0
    alt_damage_mult : float = 0
    global_damage_mult : float = 0
    accel_bonus : pygame.Vector2 = field(default_factory=lambda : pygame.Vector2(0, 0))
    lock_accel : bool = False
    invincible : bool = False
    projectile_intangible : bool = False
    ability_recharge_rate : float = 0
    ...

    def to_dict(self) -> 'PlayerStatsModifiersDict':
        return cast(PlayerStatsModifiersDict, self.__dict__)

    @classmethod
    def from_dict(cls, d : 'PlayerStatsModifiersDict') -> 'PlayerStatsModifiers':
        return cls(**d)

    @staticmethod
    def aggregate_field(modifiers : list['PlayerStatsModifiers'], field_name : PlayerStatsModifiersKey) -> Any:
        aggregation_method = MODIFIER_AGGREGATOR_DICT.get(field_name, AggregatorMethods.warn_missing)
        return aggregation_method(field_name, modifiers, [getattr(mod, field_name) for mod in modifiers])

    @staticmethod
    def aggregate(modifiers : list['PlayerStatsModifiers']) -> 'PlayerStatsModifiers':
        if not modifiers:
            return PlayerStatsModifiers()
        new_mod_dict : dict = {}
        for field_name in cast(dict[PlayerStatsModifiersKey, Any], DEFAULT_MODIFIERS.__dict__):
            new_mod_dict[field_name] = PlayerStatsModifiers.aggregate_field(modifiers, field_name)
        return PlayerStatsModifiers.from_dict(cast(PlayerStatsModifiersDict, new_mod_dict))

DEFAULT_MODIFIERS : PlayerStatsModifiers = PlayerStatsModifiers()
    
class PlayerStatsModifiersDict(TypedDict):
    max_hp_bonus : int
    normal_firerate_mult : float
    alt_firerate_mult : float
    global_firerate_mult : float
    normal_damage_mult : float
    alt_damage_mult : float
    global_damage_mult : float
    accel_bonus : pygame.Vector2
    lock_accel : bool
    invincible : bool
    projectile_intangible : bool
    ability_recharge_rate : float
    ...
    

class UpgradeType(Enum):
    MINOR = 'Minor'
    MAJOR = 'Major'
    PERK = 'Perk'
    ABILITY = 'Ability'
    SECONDARY_FIRE = 'Secondary fire'


type AbilityName = Literal['Dash', 'Overcharge']
AbilityNameList : list[AbilityName] = ['Dash', 'Overcharge']
type PerkName = Literal['DamageChain', 'AbilityLeech']
PerkNameList : list[PerkName] = ['DamageChain', 'AbilityLeech']
type SecondaryFireName = Literal['LazerShot', 'ShotgunShot', 'MissileShot']
SecondaryFireNameList : list[SecondaryFireName] = ['LazerShot', 'ShotgunShot', 'MissileShot']

type MinorUpgradeName = Literal['BonusNormalDamage', 'BonusAltDamage', 'BonusGlobalDamage',
                                'BonusNormalFirerate', 'BonusAltFirerate', 'BonusGlobalFirerate',
                                'BonusAbilityRechargeRate']
MinorUpgradeNameList : list[MinorUpgradeName] = ['BonusNormalDamage', 'BonusAltDamage', 'BonusGlobalDamage',
                                'BonusNormalFirerate', 'BonusAltFirerate', 'BonusGlobalFirerate',
                                'BonusAbilityRechargeRate']

type MajorUpgradeName = Literal['BonusMaxHealth']
MajorUpgradeNameList : list[MajorUpgradeName] = ['BonusMaxHealth']

type UpgradeName = AbilityName|PerkName|SecondaryFireName|MinorUpgradeName|MajorUpgradeName

UpgradeNameList : list[UpgradeName] = []
UpgradeNameList.extend(AbilityNameList)
UpgradeNameList.extend(PerkNameList)
UpgradeNameList.extend(SecondaryFireNameList)
UpgradeNameList.extend(MinorUpgradeNameList)
UpgradeNameList.extend(MajorUpgradeNameList)

class ShopTextOptions(TypedDict, total=False):
    pos : Required[pygame.Vector2|int|None]
    anchor : Required[AnchorStr|RectSideAnchorStr]
    font_size : int
    color : pygame.Color
    text_style : TextStyle


@dataclass
class Upgrade:
    upgrade_type : UpgradeType
    name : UpgradeName
    rank : int
    rarity_tier : int
    modifiers : PlayerStatsModifiers = field(default_factory=lambda : PlayerStatsModifiers())
    tags : list[str] = field(default_factory=lambda : [])
    stackable : bool = True

    def get_shop_description(self, already_present_upgrades : list['Upgrade']) -> list[tuple[str, ShopTextOptions]]:
        result : list[tuple[str, ShopTextOptions]] = []
        title_text : str
        if self.upgrade_type in (UpgradeType.ABILITY, UpgradeType.PERK):
            title_text = (f"{self.get_clean_name()} {to_roman(self.rank)}" if self.rank >= 1 
                          else f"New {'ability' if self.upgrade_type == UpgradeType.ABILITY else 'perk'} {self.get_clean_name()}")
        elif self.upgrade_type == UpgradeType.SECONDARY_FIRE:
            title_text = f"New weapon : {self.get_clean_name()}" if self.rank == 0 else f"{self.get_clean_name()} {to_roman(self.rank)}"
        else:
            title_text = f"{self.get_clean_name()}"
        result.append((title_text, {'pos' : None, 'anchor' : 'top'}))
        match self.name:
            case 'BonusNormalDamage':
                result.append((f"Increase regular shot damage by {self.modifiers.normal_damage_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusAltDamage':
                result.append((f"Increase regular alternate fire damage by {self.modifiers.alt_damage_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusGlobalDamage':
                result.append((f"Increase all damage by {self.modifiers.global_damage_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusNormalFirerate':
                result.append((f"Increase regular shot firerate by {self.modifiers.normal_firerate_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusAltFirerate':
                result.append((f"Increase alternate shot firerate by {self.modifiers.alt_firerate_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusGlobalFirerate':
                result.append((f"Increase all firerate by {self.modifiers.global_firerate_mult:.0%}", {'pos' : None, 'anchor' : 'top'}))
            case 'BonusAbilityRechargeRate':
                result.append((f"Increase ability recharge rate by {self.modifiers.ability_recharge_rate:.0%}", {'pos' : None, 'anchor' : 'top'}))

            case 'BonusMaxHealth':
                result.append((f"Increase max hp by {self.modifiers.max_hp_bonus}", {'pos' : None, 'anchor' : 'top'}))

            case 'LazerShot':
                match self.rank:
                    case 0:
                        result.append((f"A lazer that deals high damage...", {'pos' : None, 'anchor' : 'top'}))
                    case 1:
                        result.append((f"On hit, the lazer splits into 4 parts that deal half-damage", {'pos' : None, 'anchor' : 'top'}))
                    case 2:
                        result.append((f"The lazer splits one more time, dealing more damage", {'pos' : None, 'anchor' : 'top'}))
                    case 3:
                        result.append((f"The lazer no longer loses damage each split", {'pos' : None, 'anchor' : 'top'}))                    
            case 'ShotgunShot':
                match self.rank:
                    case 0:
                        result.append((f"A shotgun that fires 5 shells...", {'pos' : None, 'anchor' : 'top'}))
                    case 1:
                        result.append((f"The shells scatter on hit, creating more projectiles and dealing more damage", 
                                       {'pos' : None, 'anchor' : 'top'}))
                    case 2:
                        result.append((f"The shells bounce of the walls of the screen dealing even more damage", 
                                        {'pos' : None, 'anchor' : 'top'}))
            case 'MissileShot':
                match self.rank:
                    case 0:
                        result.append((f"A heat-seeking missile that deals half of its damage as AOE damage on hit", {'pos' : None, 'anchor' : 'top'}))
                    case 1:
                        result.append((f"The missile deals more AOE damage and has a bigger range", {'pos' : None, 'anchor' : 'top'}))

            case 'Dash':
                match self.rank:
                    case 1:
                        result.append((f"A dash that gives you i-frames...", {'pos' : None, 'anchor' : 'top'}))
            case 'Overcharge':
                match self.rank:
                    case 1:
                        result.append((f"Your secondary fire becomes much more dangerous...\n(+50% firerate)", {'pos' : None, 'anchor' : 'top'}))

            case 'DamageChain':
                match self.rank:
                    case 1:
                        result.append((f"Every hit, your chain goes up... Every miss, chain gets reset... Higher chain, higher damage...", 
                                       {'pos' : None, 'anchor' : 'top'}))
            case 'AbilityLeech':
                match self.rank:
                    case 1:
                        result.append((f"Every time you kill an enemy, progress your ability cooldown by 5%",
                                       {'pos' : None, 'anchor' : 'top'}))
            case _:
                result = [(f"{self.name} {to_roman(self.rank)} (type : {self.upgrade_type}), T{self.rarity_tier}", {'pos' : None, 'anchor' : 'top'})]

        if self.rank == 0 and self.upgrade_type == UpgradeType.SECONDARY_FIRE:
            prev_alt_fire : Upgrade|None = None
            for upgrade in already_present_upgrades:
                if upgrade.upgrade_type == UpgradeType.SECONDARY_FIRE and upgrade.name != self.name:
                    prev_alt_fire = upgrade
                    break
            if prev_alt_fire is not None:
                transfer_rank : int = self.get_specialisation_transfer_rank(prev_alt_fire.rank,
                    cast(SecondaryFireName, prev_alt_fire.name), cast(SecondaryFireName, self.name))
                if transfer_rank != 0:
                    result.append((f"Automatically upgraded to rank {transfer_rank}", {'pos' : None, 'anchor' : 'top', 'color' : pygame.Color('Cyan')}))

        match self.upgrade_type:
            case UpgradeType.ABILITY|UpgradeType.SECONDARY_FIRE:
                if self.rank != 0 and self.upgrade_type == UpgradeType.SECONDARY_FIRE:
                    pass
                elif self.rank != 1 and self.upgrade_type == UpgradeType.ABILITY:
                    pass
                else:
                    conflicting_upgrade : Upgrade|None = None
                    for upgrade in already_present_upgrades:
                        if upgrade.upgrade_type == self.upgrade_type and upgrade.name != self.name:
                            conflicting_upgrade = upgrade
                            break
                    if conflicting_upgrade is not None:
                        upgrade_type_text : str = 'ability' if self.upgrade_type == UpgradeType.ABILITY else 'secondary fire'
                        result.append((f"Overrides {conflicting_upgrade.get_clean_name()} {upgrade_type_text}", 
                                    {'pos' : None, 'anchor' : 'top', 'color' : pygame.Color('Red')}))
        return result
    
    def get_shop_border_info(self) -> tuple[pygame.typing.ColorLike, int]:
        color : pygame.typing.ColorLike
        match self.upgrade_type:
            case _:
                color = (130,160,210)
        return (color, 10)

    def get_clean_name(self) -> str:
        return CLEAN_NAME_DICT.get(self.name, self.name)


    @staticmethod
    def from_name_and_rank(name : UpgradeName, rank : int) -> 'Upgrade|None':
        match name:          
            case 'BonusNormalDamage':
                return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                               modifiers=PlayerStatsModifiers(normal_damage_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusAltDamage':
                return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                               modifiers=PlayerStatsModifiers(alt_damage_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusGlobalDamage':
                    return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                                   modifiers=PlayerStatsModifiers(global_damage_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusNormalFirerate':
                return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                               modifiers=PlayerStatsModifiers(normal_firerate_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusAltFirerate':
                return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                               modifiers=PlayerStatsModifiers(alt_firerate_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusGlobalFirerate':
                    return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                                   modifiers=PlayerStatsModifiers(global_firerate_mult=0.1 + ((rank - 1) * 0.05)))
            case 'BonusAbilityRechargeRate':
                return Upgrade(UpgradeType.MINOR, name, rank, rarity_tier=rank, 
                               modifiers=PlayerStatsModifiers(ability_recharge_rate=0.25 + ((rank - 1) * 0.025)))
            
            case 'BonusMaxHealth':
                return Upgrade(UpgradeType.MAJOR, name, rank, rarity_tier=rank, modifiers=(PlayerStatsModifiers(max_hp_bonus=rank)))

            case 'Dash':
                return Upgrade(UpgradeType.ABILITY, name, rank, rarity_tier=rank, stackable=False)
            case 'Overcharge':
                return Upgrade(UpgradeType.ABILITY, name, rank, rarity_tier=rank, stackable=False)
            
            case 'DamageChain':
                return Upgrade(UpgradeType.PERK, name, rank, rarity_tier=rank, stackable=False)
            case 'AbilityLeech':
                return Upgrade(UpgradeType.PERK, name, rank, rarity_tier=rank, stackable=False)
            
            case 'LazerShot':
                return Upgrade(UpgradeType.SECONDARY_FIRE, name, rank, rarity_tier=rank, stackable=False)
            case 'ShotgunShot':
                return Upgrade(UpgradeType.SECONDARY_FIRE, name, rank, rarity_tier=rank, stackable=False)
            case 'MissileShot':
                return Upgrade(UpgradeType.SECONDARY_FIRE, name, rank, rarity_tier=rank, stackable=False)
            
            case _:
                core_object.log(f"Could not create upgrade '{name}'!")
                return None

    @staticmethod
    def get_upgrade_type(name : UpgradeName) -> UpgradeType|None:
        if name in AbilityNameList:
            return UpgradeType.ABILITY
        elif name in PerkNameList:
            return UpgradeType.PERK
        elif name in SecondaryFireNameList:
            return UpgradeType.SECONDARY_FIRE
        elif name in MajorUpgradeNameList:
            return UpgradeType.MAJOR
        elif name in MinorUpgradeNameList:
            return UpgradeType.MINOR
        else:
            return None

    @staticmethod
    def get_list_of_all(upgrade_type : UpgradeType|None) -> list[UpgradeName]:
        if upgrade_type is None:
            return list(UpgradeNameList)
        return [x for x in (filter(lambda name : Upgrade.get_upgrade_type(name) == upgrade_type, UpgradeNameList))]

    @staticmethod
    def get_specialisation_transfer_rank(prev_rank : int, prev_weapon : SecondaryFireName, new_weapon : SecondaryFireName) -> int:
        if prev_weapon not in BASE_WEIGHTS or new_weapon not in BASE_WEIGHTS or prev_weapon == new_weapon:
            return 0

        prev_rarity_tier : int = BASE_WEIGHTS[prev_weapon][0].get(prev_rank, {0 : 0})[0]
        target_rank : int = 0

        for rank, rarity_info in sorted(BASE_WEIGHTS[prev_weapon][0].items(), key = lambda w_info : w_info[0], reverse=True):
            if prev_rarity_tier > rarity_info[0]:
                target_rank = rank
                break

        return int(pygame.math.clamp(target_rank, 0, MAX_RANK[new_weapon]))


    def __str__(self) -> str:
        return f"{self.name} {to_roman(self.rank)} (type : {self.upgrade_type}), T{self.rarity_tier}"

CLEAN_NAME_DICT : dict[UpgradeName, str] = {
    'BonusNormalDamage' : 'Normal damage bonus',
    'BonusAltDamage' :  'Alternate fire damage bonus',
    'BonusGlobalDamage' : 'Global damage bonus',

    'BonusNormalFirerate' : 'Normal firerate bonus',
    'BonusAltFirerate' : 'Alternate firerate bonus',
    'BonusGlobalFirerate' : 'Global firerate bonus',

    'BonusAbilityRechargeRate' : 'Ability recharge rate bonus',


    'BonusMaxHealth' : 'Max health bonus',


    'Dash' : 'Dash',
    'Overcharge' : 'Overcharge',


    'LazerShot' : 'Lazer',
    'ShotgunShot' : 'Shotgun',
    'MissileShot' : 'Homing Missile',


    'DamageChain' : 'Damage Chain',
    'AbilityLeech' : 'Ability Leech'
}

                                    #(rank --> (rarity tier, weight), ignore_rarity_tier)
BASE_WEIGHTS : dict[UpgradeName, tuple[dict[int, tuple[int, float]], bool]] = {
    'BonusNormalDamage' : ({1 : (1, 1.0), 
                            2 : (2, 1.0),
                            3 : (3, 1.0),
                            4 : (4, 1.0),
                            5 : (5, 1.0)},
                            False),

    'BonusAltDamage' : ({1 : (1, 1.0), 
                         2 : (2, 1.0),
                         3 : (3, 1.0),
                         4 : (4, 1.0),
                         5 : (5, 1.0)}, 
                         False),

    'BonusGlobalDamage' : ({1 : (1, 1.0), 
                            2 : (2, 1.0),
                            3 : (3, 1.0),
                            4 : (4, 1.0),
                            5 : (5, 1.0)}, 
                            False),

    'BonusNormalFirerate' : ({1 : (1, 1.0), 
                            2 : (2, 1.0),
                            3 : (3, 1.0),
                            4 : (4, 1.0),
                            5 : (5, 1.0)}, 
                            False),

    'BonusAltFirerate' : ({1 : (1, 1.0), 
                        2 : (2, 1.0),
                        3 : (3, 1.0),
                        4 : (4, 1.0),
                        5 : (5, 1.0)}, 
                        False),

    'BonusGlobalFirerate' : ({1 : (1, 1.0), 
                            2 : (2, 1.0),
                            3 : (3, 1.0),
                            4 : (4, 1.0),
                            5 : (5, 1.0)}, 
                            False),

    'BonusAbilityRechargeRate' : ({1 : (1, 1.0), 
                                    2 : (2, 1.0),
                                    3 : (3, 1.0),
                                    4 : (4, 1.0),
                                    5 : (5, 1.0)}, 
                                    False),


    'BonusMaxHealth' : ({1 : (1, 0.15), 
                         2 : (2, 0.01)},
                            True),
                            

    'Dash' : ({1 : (1, 1.0), 
               2 : (2, 1.0)},
               False),

    'Overcharge' : ({1 : (1, 1.0)},
                   False),

    'AbilityLeech' : ({1 : (1, 1.0)},
                   False),


    'DamageChain' : ({1 : (1, 1.0), 
                    2 : (2, 1.0)},
                    False),


    'LazerShot' :  ({0 : (1, 1.0),
                    1 : (1, 1.0), 
                    2 : (2, 1.0),
                    3 : (2, 1.0)},
                    True),

    'ShotgunShot' : ({0 : (1, 1.0),
                    1 : (1, 1.0), 
                    2 : (2, 1.0)},
                    True),

    'MissileShot' : ({0 : (1, 1.0),
                    1 : (1, 1.0)},
                    True),
}

MAX_RANK : dict[PerkName|AbilityName|SecondaryFireName, int] = {
    'Dash' : 2,
    'Overcharge' : 1,


    'DamageChain' : 2,
    'AbilityLeech' : 1,


    'LazerShot' : 3,
    'ShotgunShot' : 2,
    'MissileShot' : 1,
}

class PlayerUpgradeHooks:
    @staticmethod
    def update_max_health(player_upgrades : 'PlayerUpgrades', upgrade : Upgrade):
        new_max_hp : int = player_upgrades.max_hp
        old_max_hp : int = player_upgrades.player.max_hp
        hp_diff : int = new_max_hp - old_max_hp

        player_upgrades.player.max_hp = new_max_hp
        player_upgrades.player.current_hp += hp_diff

        player_upgrades.player.healthbar.heart_count = new_max_hp
        player_upgrades.player.healthbar.health = player_upgrades.player.current_hp
        

PRE_UPGRADE_HOOKS : dict[UpgradeName, PreUpgradeApplicationCallback] = defaultdict(lambda : (lambda p, u : None))
POST_UPGRADE_HOOKS : dict[UpgradeName, PostUpgradeApplicationCallback] = defaultdict(lambda : (lambda p, u : None))

pre_hooks_dict : dict[UpgradeName, PreUpgradeApplicationCallback] = {}
post_hooks_dict : dict[UpgradeName, PostUpgradeApplicationCallback] = {
    'BonusMaxHealth' : PlayerUpgradeHooks.update_max_health
}

PRE_UPGRADE_HOOKS.update(pre_hooks_dict)
POST_UPGRADE_HOOKS.update(post_hooks_dict)

class BaseInteractibleUpgrade:
    def __init__(self) -> None:
        self.relevant_events : dict[int, bool] = {} # bool : do_defer (add to queue instead of calling the callback)
        self.event_queue : list[pygame.Event] = []

    def on_event(self, event : pygame.Event):
        pass

    def cleanup(self):
        pass

    def update(self, delta : float):
        pass

    def refresh_cooldown(self):
        pass


def runtime_imports():
    global src, Player
    from src.sprites.player import Player
    import src.sprites.player

def local_imports1():
    global PlayerUpgrades
    from .player_upgrades import PlayerUpgrades