import pygame
from framework.utils.my_timer import Timer, TimeSource
from framework.utils.base_animation import Animation
import src.animations
import framework.utils.interpolation as interpolation
from framework.utils.helpers import load_alpha_to_colorkey
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
spark_particle_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/fire_particle.png", (0, 255, 0))
# ParticleEffect currently does not have access to the asset manager...

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

enemy_damaged : EffectDataDict = {'offset_x' : [-8, 8], 'offset_y' : [0, 8], 'velocity_x' : [0,0], 'velocity_y' : [-6.0,-6.0], 'angle' : [210, 330], 'speed' : [8, 8],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 3, 'cooldown' : 0.20, 'target_spawn_count' : 3, 'lifetime' : [5,5], 'part_per_wave' : 3,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_hit_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

enemy_killed : EffectDataDict = {'offset_x' : [-8, 8], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-3.0,-3.0], 'angle' : [0, 360], 'speed' : [5, 5],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 8, 'cooldown' : 0.20, 'target_spawn_count' : 8, 'lifetime' : [5,5], 'part_per_wave' : 8,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_killed_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

boss_killed : EffectDataDict = {'offset_x' : [-8, 8], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-3.0,-3.0], 'angle' : [0, 360], 'speed' : [5, 5],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 35, 'cooldown' : 0.20, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 35,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_killed_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

dash_effect : EffectDataDict = {'offset_x' : [-16, 16], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-1.5,-1.5], 'angle' : [0, 0], 'speed' : [0, 0],
            'accel_x' : [0,0], 'accel_y' : [-0.11,-0.10], 'drag' : [0, 0],
            'init_spawn_count' : 5, 'cooldown' : 0.025, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 5,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('dash_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

explosion_effect : EffectDataDict = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [-2.0,-2.0], 'angle' : [0, 360], 'speed' : [3, 3],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 20, 'cooldown' : 0.20, 'target_spawn_count' : 20, 'lifetime' : [5,5], 'part_per_wave' : 20,
            'main_texture' : spark_particle_image, 'alt_textures' : None, "animation" : Animation.get_animation('explosion_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

explosion_small_effect : EffectDataDict = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [-2.0,-2.0], 'angle' : [0, 360], 'speed' : [3, 3],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 10, 'cooldown' : 0.20, 'target_spawn_count' : 10, 'lifetime' : [5,5], 'part_per_wave' : 10,
            'main_texture' : spark_particle_image, 'alt_textures' : None, "animation" : Animation.get_animation('explosion_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

effect_dict : dict[str, EffectDataDict] = {'test' : test_effect, 'test2' : test_effect2, 'enemy_damaged' : enemy_damaged,
                               'enemy_killed' : enemy_killed, 'boss_killed' : boss_killed, 'dash_effect' : dash_effect,
                               'explosion_effect' : explosion_effect, 'explosion_small_effect' : explosion_small_effect}

for name, data in effect_dict.items():
    ParticleEffect.add_effect(name, data)

