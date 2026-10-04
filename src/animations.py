import json
import pygame
from framework.utils.helpers import Task, ColorType
from framework.utils.my_timer import Timer
import framework.utils.interpolation as interpolation
import framework.utils.tween_module as TweenModule
from typing import Any, Callable, Union, overload, Literal

from framework.utils.helpers import AnchorStr, AnchorNameList, ANCHOR_REL_POS_DICT
from framework.utils.helpers import RectSideAnchorStr, RectSideAnchorNameList, is_rect_pos, is_rect_side

from framework.utils.base_animation import Animation
# TODO : Add dataclasses

TEMPLATES = [
    {"type" : "move_by", "offset" : (0,0)},
    {"type" : "move_to", "target" : (0,0), "anchor" : "center"},

    {"type" : "slide_to", "target" : (0,0), "anchor" : "center", "time" : 0, "easing_style" : interpolation.linear}, #target is tuple|int
    {"type" : "slide_by", "offset" : (0,0), "time" : 0, "easing_style" : interpolation.linear}, #offset is always a tuple

    {"type" : "wait", "time" : 0},
    {"type" : "delay" , "index" : 0},
    {"type" : "delay_rel" , "index" : 0},

    {"type" : "switch_image", "source" : "source_name", "index" : None, 'dynamic_anchor' : 'rect_attribute or none', 'colorkey' : 'color or none'},
    {"type" : "rotate_by", "angle" : 0},
    {"type" : "rotate_to", "angle" : 0},

    {"type" : "rotate_by_over_time", "angle" : 0, "time" : 0, "easing_style" : interpolation.linear},
    {"type" : "rotate_to_over_time", "angle" : 0, "time" : 0, "easing_style" : interpolation.linear},

    {"type" : "image_gradient", "source" : "source_name", "target_index" : 0, "time" : 0, "easing_style" : interpolation.linear, 'dynamic_anchor' : 'rect_attr/none',
    'colorkey' : 'color or none'},
    {"type" : "tween_property", "property" : "", "goal" : 0, "time" : 0, "easing_style" : interpolation.linear},
    #{"type" : "set_alpha", "target" : 0}, set_alpha and alpha_gradient are currently unspported with no plan of being brought back
    #{"type" : "alpha_gradient", "target" : 0, "time" : 0, "easing_style" : interpolation.linear},
             ]

# To add an animation : Animation.add_animation(animation_name, animation_data)

test_anim = [
    {"type" : "wait", "time" : 1},
    {"type" : "move_to", "target" : [300, 300], "anchor" : None},
    {"type" : "wait", "time" : 1},
    {"type" : "move_by", "offset" : [-150, -150]},
    {"type" : "slide_by", "offset" : [200, 200], "time" : 1.5, "easing_style" : interpolation.smoothstep},
    {"type" : "delay_rel", "index" : -1},
    {"type" : "move_by", "offset" : [-200, -200]},
    {"type" : "slide_to", "target" : [800, 450], "anchor" : "topleft", "time" : 2, "easing_style" : interpolation.quad_ease_in},
    {"type" : "delay_rel", "index" : -1},
    {"type" : "switch_image", "source" : "color_images", "index" : "Green", 'dynamic_anchor' : None, 'colorkey' : [0,0, 255]},
    {"type" : "wait", "time" : 1},
    {"type" : "rotate_to", "angle" : 90},
    {"type" : "wait", "time" : 1},
    {"type" : "rotate_by_over_time", "angle" : 360, "time" : 1.5, "easing_style" : interpolation.smoothstep},
    {"type" : "image_gradient", "source" : "color_image_list", "target_index" : 7, "time" : 3, "easing_style" : interpolation.linear, 
    'dynamic_anchor' : 'topleft', 'colorkey' : [90, 90, 90]},
    {"type" : "delay_rel", "index" : -1},
    {"type" : "tween_property", "property" : "position", "goal" : [100, 100], "time" : 3, "easing_style" : interpolation.linear},
    ]

Animation.add_animation('test', test_anim)

def _sprite_hint():
    global Sprite
    from framework.game.sprite import Sprite