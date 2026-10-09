import pygame
from typing import Literal, TypedDict, NotRequired, Required, cast, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from framework.utils.helpers import AnchorStr, ColorType, to_roman, RectSideAnchorStr
from framework.ui import TextStyle
from framework.core.core import core_object

type ModifierAggregationFunction = Callable[[str, list[PlayerStatsModifiers], list[Any]], Any]

class AggregatorMethods:
    @staticmethod
    def sum_aggregator(field_name : str, modifiers : list['PlayerStatsModifiers'], 
                       values : list[Any]) -> Any:
        return sum(values)

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
    'normal_firerate_mult' : AggregatorMethods.manual_product_aggregator,
    'alt_firerate_mult' : AggregatorMethods.manual_product_aggregator,
    'global_firerate_mult' : AggregatorMethods.manual_product_aggregator,
    'accel_bonus' : AggregatorMethods.manual_sum_aggregator,
    'lock_accel' : AggregatorMethods.any_aggregator,
    'invincible' : AggregatorMethods.any_aggregator,
    'projectile_intangible' : AggregatorMethods.any_aggregator,
    'normal_damage_mult' : AggregatorMethods.manual_product_aggregator,
    'alt_damage_mult' : AggregatorMethods.manual_product_aggregator,
    'global_damage_mult' : AggregatorMethods.manual_product_aggregator,
    'ability_recharge_rate' : AggregatorMethods.manual_product_aggregator
}


@dataclass
class PlayerStatsModifiers:
    max_hp_bonus : int = 0
    normal_firerate_mult : float = 1
    alt_firerate_mult : float = 1
    global_firerate_mult : float = 1
    normal_damage_mult : float = 1
    alt_damage_mult : float = 1
    global_damage_mult : float = 1
    accel_bonus : pygame.Vector2 = field(default_factory=lambda : pygame.Vector2(0, 0))
    lock_accel : bool = False
    invincible : bool = False
    projectile_intangible : bool = False
    ability_recharge_rate : float = 1
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


type AbilityName = Literal['Dash']
AbilityNameList : list[AbilityName] = ['Dash']
type PerkName = Literal['DamageChain']
PerkNameList : list[PerkName] = ['DamageChain']
type SecondaryFireName = Literal['LazerShot']
SecondaryFireNameList : list[SecondaryFireName] = ['LazerShot']
type UpgradeName = AbilityName|PerkName|SecondaryFireName

UpgradeNameList : list[UpgradeName] = []
UpgradeNameList.extend(AbilityNameList)
UpgradeNameList.extend(PerkNameList)
UpgradeNameList.extend(SecondaryFireNameList)

class ShopTextOptions(TypedDict, total=False):
    pos : Required[pygame.Vector2|int]
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
        match self.name:
            case _:
                return [(f"{self.name} {to_roman(self.rank)} (type : {UpgradeType}), T{self.rarity_tier}", {'pos' : 30, 'anchor' : 'top'})]

    def get_shop_border_info(self) -> tuple[ColorType, int]:
        return ("Blue", 15)

    @staticmethod
    def from_name_and_rank(name : UpgradeName, rank : int) -> 'Upgrade|None':
        match name:
            case 'Dash':
                return Upgrade(UpgradeType.ABILITY, name, rank, 1, stackable=False)
            case 'DamageChain':
                return Upgrade(UpgradeType.PERK, name, rank, 1, stackable=False)
            case 'LazerShot':
                return Upgrade(UpgradeType.SECONDARY_FIRE, name, rank, 1, stackable=False)
            case _:
                return None

def runtime_imports():
    pass

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