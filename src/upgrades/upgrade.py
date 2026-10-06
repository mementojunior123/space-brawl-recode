import pygame
from typing import Literal, TypedDict, NotRequired, Required
from enum import Enum
from dataclasses import dataclass, field
from framework.utils.helpers import AnchorStr, ColorType, to_roman, RectSideAnchorStr
from framework.ui import TextStyle

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
    tags : list[str] = field(default_factory=lambda : [])

    def get_shop_description(self, already_present_upgrades : list['Upgrade']) -> list[tuple[str, ShopTextOptions]]:
        return[(f"{self.name} {to_roman(self.rank)} (type : {UpgradeType}), T{self.rarity_tier}", {'pos' : 30, 'anchor' : 'top'})]

    def get_shop_border_info(self) -> tuple[ColorType, int]:
        return ("Blue", 15)

def runtime_imports():
    pass