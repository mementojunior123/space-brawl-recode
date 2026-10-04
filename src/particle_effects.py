import pygame
from framework.utils.my_timer import Timer, TimeSource
from framework.utils.base_animation import Animation
import framework.utils.interpolation as interpolation
from random import random
from math import sin, radians, cos, atan2
from framework.game.sprite import Sprite
from framework.utils.pivot_2d import Pivot2D
from typing import TypedDict, Literal, Union, TypeAlias, Sequence, cast, NotRequired

from dataclasses import dataclass

from framework.utils.base_particle_effects import EffectDataDict, Particle, ParticleEffect

TEMPLATE : EffectDataDict = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [0,0], 'angle' : [0,360], 'speed' : [0,0],
            'accel_x' : [0,0], 'accel_y' : [0,0], 'drag' : [0, 0],
            'init_spawn_count' : 0, 'cooldown' : 0.25, 'target_spawn_count' : 0, 'lifetime' : [0,0], 'part_per_wave' : 1,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : False, 'type' : None}

# To add a particle effect : ParticleEffect.add_effect(effect_name, effect_data)

test_effect : EffectDataDict = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [0,0], 'angle' : [80, 100], 'speed' : [5, 9],
            'accel_x' : [0,0], 'accel_y' : [0.15,0.12], 'drag' : [0, 0],
            'init_spawn_count' : 3, 'cooldown' : 0.20, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 3,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'simulated', 'destroy_offscreen' : False, 'copy_surface' : False, 'type' : None}

test_effect2 : EffectDataDict = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [1.5,1.6], 'velocity_y' : [0.8,0.82], 'angle' : [0, 20], 'speed' : [20, 22],
            'accel_x' : [0,0], 'accel_y' : [0.0,0.0], 'drag' : [0, 0],
            'init_spawn_count' : 1, 'cooldown' : 0.05, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 1,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'spiral', 'destroy_offscreen' : False, 'copy_surface' : False, 'type' : None}

ParticleEffect.add_effect('test', test_effect)
ParticleEffect.add_effect('test2', test_effect2)
