import pygame
from typing import Literal, TypedDict, NotRequired, Required, cast
from enum import Enum
from dataclasses import dataclass, field
from framework.utils.helpers import AnchorStr, ColorType, to_roman, RectSideAnchorStr
from framework.ui import TextStyle

@dataclass
class PlayerStatsModifiers:
    max_hp : int = 0
    normal_firerate : float = 1
    alt_firerate : float = 1
    global_firerate : float = 1
    fixed_accel : pygame.Vector2|None = None
    ...

    def to_dict(self) -> 'PlayerStatsModifiersDict':
        return cast(PlayerStatsModifiersDict, self.__dict__)

    @classmethod
    def from_dict(cls, d : 'PlayerStatsModifiersDict') -> 'PlayerStatsModifiers':
        return cls(**d)

class PlayerStatsModifiersDict(TypedDict):
    max_hp : int
    normal_firerate : float
    alt_firerate : float
    global_firerate : float
    fixed_accel : pygame.Vector2|None
    ...
    

class UpgradeType(Enum):
    MINOR = 'Minor'
    MAJOR = 'Major'
    PERK = 'Perk'
    ABILITY = 'Ability'
    SECONDARY_FIRE = 'Secondary fire'


type AbilityName = Literal['Dash']
AbilityNameList : list[AbilityName] = ['Dash']
type PerkName = str
PerkNameList : list[PerkName] = []
type SecondaryFireName = Literal['Lazer']
SecondaryFireNameList : list[SecondaryFireName] = ['Lazer']
type UpgradeName = AbilityName|PerkName|SecondaryFireName|str

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

    def get_shop_description(self, already_present_upgrades : list['Upgrade']) -> list[tuple[str, ShopTextOptions]]:
        return[(f"{self.name} {to_roman(self.rank)} (type : {UpgradeType}), T{self.rarity_tier}", {'pos' : 30, 'anchor' : 'top'})]

    def get_shop_border_info(self) -> tuple[ColorType, int]:
        return ("Blue", 15)

def runtime_imports():
    pass