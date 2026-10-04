import pygame
from math import copysign
from typing import Callable, Any, Union, TypeAlias, Sequence, Literal
from random import random
from collections import OrderedDict

AnyJson : TypeAlias = Union[int, float, str, None, bool, list["AnyJson"], dict[str, "AnyJson"]]
EasingFunc : TypeAlias = Callable[[float], float]

AnchorStr : TypeAlias = Literal['topleft', 'midtop', 'topright', 'midleft', 'center', 'midright', 'bottomleft', 'midbottom', 'bottomright']
AnchorNameList : list[AnchorStr] = ['topleft', 'midtop', 'topright', 'midleft', 'center', 'midright', 'bottomleft', 'midbottom', 'bottomright']
ANCHOR_REL_POS_DICT : dict[AnchorStr, tuple[float, float]] = {
    'topleft' : (0, 0),
    'midtop' : (0.5, 0),
    'topright' : (1, 0),
    'midleft' : (0, 0.5),
    'center' : (0.5, 0.5),
    'midright' : (1.0, 0.5),
    'bottomleft' : (0, 1),
    'midbottom' : (0.5, 1),
    'bottomright' : (1, 1)
}

RectSideAnchorStr : TypeAlias = Literal['left', 'right', 'top', 'bottom', 'x', 'y', 'centerx', 'centery']
RectSideAnchorNameList : list[RectSideAnchorStr] = ['left', 'right', 'top', 'bottom', 'x', 'y', 'centerx', 'centery']

def is_rect_side(name : str) -> bool:
    return name in RectSideAnchorNameList

def is_rect_pos(name : str) -> bool:
    return name in AnchorNameList

def to_roman(num : int) -> str:

    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])

ColorType : TypeAlias = Union[list[int], tuple[int, int, int], pygame.Color, str]

class Task:
    def __init__(self, callback : Callable, *args, **kwargs) -> None:
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
    
    def execute(self):
        self.callback(*self.args, **self.kwargs)

def scale_surf(surf : pygame.Surface, scale : float|pygame.typing.Point):
    return pygame.transform.scale_by(surf, scale)

def rotate_around_center(image : pygame.Surface, pos : pygame.Vector2, angle : float) -> tuple[pygame.Surface, pygame.Rect]:
    new_image = pygame.transform.rotate(image, -angle)
    new_rect = new_image.get_rect(center = round(pos))
    return new_image, new_rect

def sign(x):
    return copysign(1, x) if x != 0 else 0

def is_sorted(iterable : list[object], key : Callable[[object], float|int]):
    current_val = key(iterable[0])
    for obj in iterable:
        val = key(obj)
        if val < current_val: return False
    return True

def average(values : list[float]):
    return sum(values) / len(values)

def random_float(a : float, b : float):
    return pygame.math.lerp(a, b, random())


def make_upgrade_bar(width : int = 100, length : int = 20, count = 5, border : int = 3, border_color : str|ColorType = 'Black', 
                     bg_color : str|ColorType = (90, 90, 90)):
    surf = pygame.surface.Surface((width + border * 2, (length + border) * count + border))
    surf.fill(border_color)
    pygame.draw.rect(surf, bg_color, (border, border, width, (length + border) * count - border))
    for i in range(count):
        pygame.draw.rect(surf, border_color, (0, (border + length) * i, width + border * 2, border))
    return surf

def paint_upgrade_bar(surf : pygame.Surface, index : int, width : int = 100, length : int = 20, border : int = 3, color : str|ColorType = 'Green'):
    pygame.draw.rect(surf, color, (border, (length + border) * index + border, width, length))

def reset_upgrade_bar(surf : pygame.Surface, count : int = 5, width : int = 100, length : int = 20, border : int = 3, bg_color : str|ColorType = (90, 90, 90)):
    for index in range(count):
        pygame.draw.rect(surf, bg_color, (border, (length + border) * index + border, width, length))

def make_right_arrow(height : int, width : int, color : ColorType|str = (255, 0, 0), colorkey : ColorType|str = (0, 255, 0)) -> pygame.Surface:
    surface = pygame.surface.Surface((width, height))
    surface.set_colorkey(colorkey)
    surface.fill(colorkey)
    pygame.draw.polygon(surface, color, [(0,0), (width, height // 2), (0, height)])
    return surface

def make_circle(radius : int, color : ColorType|str, colorkey : ColorType|str = (0, 255, 0)) -> pygame.Surface:
    d = radius * 2
    surface : pygame.Surface = pygame.Surface((d, d))
    surface.set_colorkey(colorkey)
    surface.fill(colorkey)
    pygame.draw.circle(surface, color, (radius, radius), radius)
    return surface


def load_alpha_to_colorkey(path : str, colorkey : ColorType|str):
    image = pygame.image.load(path).convert_alpha()
    new_surf = pygame.surface.Surface(image.get_size())
    new_surf.set_colorkey(colorkey)
    new_surf.fill(colorkey)
    new_surf.blit(image, (0,0))
    return new_surf

def tuple_vec_average(l : list[tuple[float, float]]) -> tuple[float, float]:
    x_sum : float = 0
    y_sum : float = 0
    count : int = 0
    for x, y in l:
        x_sum += x
        y_sum += y
        count += 1
    x_sum /= count
    y_sum /= count
    return (x_sum, y_sum)

def vector_sum(l : list[pygame.Vector2]) -> pygame.Vector2:
    total : pygame.Vector2 = pygame.Vector2(0, 0)
    for val in l:
        total += val
    return total

def vector_xmax_ysum(l : list[pygame.typing.Point]) -> pygame.Vector2:
    return pygame.Vector2(max([val[0] for val in l]), sum([val[1] for val in l]))

def recolor_image(img : pygame.Surface, new_color : ColorType) -> pygame.Surface:
    working_copy : pygame.Surface = img.copy()
    img_mask : pygame.Mask = pygame.mask.from_surface(working_copy)
    working_copy.blit(img_mask.to_surface(setcolor=new_color, unsetcolor=img.get_colorkey()), (0, 0))
    return working_copy

def recolor_image_ip(img : pygame.Surface, new_color : ColorType) -> None:
    img_mask : pygame.Mask = pygame.mask.from_surface(img)
    img.blit(img_mask.to_surface(setcolor=new_color, unsetcolor=img.get_colorkey()))

def remove_image_empty(img : pygame.Surface) -> pygame.Surface:
    bounding_box : pygame.Rect = img.get_bounding_rect()
    img_rect : pygame.Rect = img.get_rect()
    if bounding_box.size == img_rect.size:
        return img
    
    colorkey = img.get_colorkey()
    flags : int
    if not colorkey:
        flags = pygame.SRCALPHA
    else:
        flags = 0
    new_surf : pygame.Surface = pygame.Surface(bounding_box.size, flags)
    colorkey = img.get_colorkey()
    if colorkey:
        new_surf.set_colorkey(colorkey)
        new_surf.fill(colorkey)
    new_surf.blit(img, (0, 0), area = bounding_box)
    return new_surf

def rect_intersect(r1 : pygame.Rect, r2 : pygame.Rect) -> pygame.Rect|None:
    if not r1.colliderect(r2):
        return None
    x_start : int
    x_len : int
    if r1.left < r2.left and r1.right > r2.right:
        x_start = r2.left
        x_len = r2.width
    else:
        x_start = max(r1.left, r2.left)
        x_end : int = min(r1.right, r2.right)
        x_len = x_end - x_start

    y_start : int
    y_len : int
    if r1.top < r2.top and r1.bottom > r2.bottom:
        y_start = r2.top
        y_len = r2.width
    else:
        y_start = max(r1.top, r2.top)
        y_end : int = min(r1.bottom, r2.bottom)
        y_len = y_end - y_start

    return pygame.Rect((x_start, y_start), (x_len, y_len))