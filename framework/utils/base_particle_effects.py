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

def __random_float(a : float, b : float) -> float:
    return random() * (b-a) + a

def rand_float(iterable : float|Sequence[float]) -> float:
    if iterable is None: return iterable
    if isinstance(iterable, (float, int)): 
        return iterable
    return __random_float(iterable[0], iterable[1])


def vec_from_angle(angle : float, magnitude : float = 1) -> pygame.Vector2:
    x = cos(radians(angle))
    y = -sin(radians(angle))
    return pygame.Vector2(x, y) * magnitude

def get_vec_angle(vec : pygame.Vector2) -> float:
    return atan2(-vec.y, vec.x)

NumberRange : TypeAlias = Union[float, tuple[float, float], list[float]]
UpdateMethod : TypeAlias = Literal['simulated', 'animated', 'spiral']

class EffectDataDict(TypedDict):
    offset_x : NumberRange
    offset_y : NumberRange
    velocity_x : NumberRange|None
    velocity_y : NumberRange|None
    angle : NumberRange|None
    speed : NumberRange|None    
    accel_x : NumberRange|None
    accel_y : NumberRange|None
    drag : NumberRange|None
    init_spawn_count : int
    cooldown : float
    target_spawn_count : int 
    lifetime : NumberRange 
    part_per_wave : int
    main_texture : pygame.Surface
    alt_textures : None|list[pygame.Surface]
    animation : None|Animation
    update_method : UpdateMethod
    destroy_offscreen : NotRequired[bool]
    copy_surface : bool
    type : None|str

@dataclass
class EffectData:
    offset_x : NumberRange
    offset_y : NumberRange
    init_spawn_count : int
    cooldown : float
    target_spawn_count : int 
    lifetime : NumberRange 
    part_per_wave : int
    main_texture : pygame.Surface
    update_method : UpdateMethod
    copy_surface : bool
    destroy_offscreen : bool = True

    velocity_x : NumberRange|None = None
    velocity_y : NumberRange|None = None
    angle : NumberRange|None = None
    speed : NumberRange|None = None    
    accel_x : NumberRange|None = None
    accel_y : NumberRange|None = None
    drag : NumberRange|None = None

    alt_textures : None|list[pygame.Surface] = None
    animation : None|Animation = None
    type : None|str = None

    def get_rand_offset(self) -> pygame.Vector2:
        return pygame.Vector2(rand_float(self.offset_x), rand_float(self.offset_y))

    def get_rand_lifetime(self) -> float:
        return rand_float(self.lifetime)

    def get_rand_base_velocity(self) -> pygame.Vector2:
        if self.velocity_x is None or self.velocity_y is None:
            return pygame.Vector2(0, 0)
        return pygame.Vector2(rand_float(self.velocity_x), rand_float(self.velocity_y))

    def get_rand_drag(self) -> float:
        if self.drag is None:
            return 0
        return rand_float(self.drag)

    def get_rand_vel_angle(self) -> float:
        if self.angle is None:
            return 0
        return rand_float(self.angle)

    def get_rand_vel_mag(self) -> float:
        if self.speed is None:
            return 0
        return rand_float(self.speed)

    def get_rand_accel(self) -> pygame.Vector2:
        if self.accel_x is None or self.accel_y is None:
            return pygame.Vector2(0, 0)
        return pygame.Vector2(rand_float(self.accel_x), rand_float(self.accel_y))
    

    @classmethod
    def from_dict(cls, data : EffectDataDict):
        return cls(**data)

    def to_dict(self) -> EffectDataDict:
        return cast(EffectDataDict, self.__dict__)

    def validate(self) -> bool:
        return True


class Particle(Sprite, sprite_count=250, do_link=False):
    test_image = pygame.surface.Surface((4,4))
    pygame.draw.rect(test_image, 'White', (0, 0, 4, 4))
    bounding_box = pygame.Rect(0, 0, 960, 540)

    def __init__(self) -> None:
        super().__init__()
        self.lifetime : float
        self.lifetime_timer : Timer

        self.velocity : pygame.Vector2
        self.acceleration : pygame.Vector2
        self.drag : float

        self.update_method : UpdateMethod = 'simulated'
        self.textures : list[pygame.Surface]
        self.kill_offscreen : bool = True
        self.pivot : Pivot2D

    
    def spawn(self, pos : pygame.Vector2, lifetime : float, update_method : UpdateMethod, main_texture : pygame.Surface, 
              velocity : pygame.Vector2|None = None, accel : pygame.Vector2|None = None, drag : float = 0, 
              alt_textures : list[pygame.Surface]|None = None, anim : Animation|None = None, destroy_offscreen : bool = False, angle : float = 0, mag : float = 0, 
              copy_surf = False, time_source : TimeSource|None = None):

        velocity = velocity if velocity is not None else pygame.Vector2(0, 0)
        accel = accel if accel is not None else pygame.Vector2(0, 0)
        alt_textures = alt_textures if alt_textures is not None else []

        self.zindex = 100
        self._position = pos
        self.update_method = update_method
        if copy_surf is False:
            self.image = main_texture
            self.textures = alt_textures
        else:
            self.image = main_texture.copy()
            self.textures = [surf.copy() for surf in alt_textures]

        self.rect = self.image.get_rect()
        self.rect.center = self.position

        self.lifetime = lifetime
        self.lifetime_timer = Timer(lifetime, time_source=time_source)

        self.velocity = velocity
        self.pivot = Pivot2D(self._position, self.image) # type: ignore
        if self.update_method == 'spiral':
            self.pivot.pivot_offset = pygame.Vector2(mag, 0).rotate(-angle)
        else:
            self.velocity += vec_from_angle(angle, mag)
        self.acceleration = accel
        self.drag = drag
        self.kill_offscreen= destroy_offscreen

        if anim:
            self.anim_track = anim.load(self, time_source)
            self.anim_track.play()
        else:
            self.anim_track = None
        
        Particle.unpool(self)
        self.rect.center = self.pivot.position
        self.current_camera = core_object.game.main_camera
    
    def update(self, delta : float):
        if self.lifetime_timer.isover():
            self.kill_instance_safe()
            return
        if self.kill_offscreen:
            if self.rect.colliderect(Particle.bounding_box) is False:
                self.kill_instance_safe()
                return
        if self.update_method == 'simulated':
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5

            self.velocity += self.acceleration * 0.5 * delta
            self.position += self.velocity * delta
            self.velocity += self.acceleration * 0.5 * delta

            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.rect.center = self.position
            if self.anim_track is not None:
                self.anim_track.update()
        elif self.update_method == 'spiral':
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.velocity += self.acceleration * 0.5 * delta
            current_distance_to_center : float = self.pivot.pivot_offset.magnitude()
            if current_distance_to_center:
                self.pivot.pivot_offset.rotate_ip(-self.velocity.x * delta)
                self.pivot.pivot_offset.scale_to_length(current_distance_to_center + self.velocity.y * delta)
            self.velocity += self.acceleration * 0.5 * delta
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.rect.center = self.pivot.position
            if self.anim_track is not None:
                self.anim_track.update()
        
        elif self.update_method == 'animated' and self.anim_track:
            self.anim_track.update()

    def clean_instance(self):
        super().clean_instance()
        del self.lifetime
        del self.lifetime_timer

        del self.velocity
        del self.acceleration
        del self.drag

        del self.update_method
        del self.textures
        del self.kill_offscreen
        del self.pivot

class ParticleEffect:
    elements : list['ParticleEffect'] = []
    effects_data : dict[str, EffectDataDict] = {}
    special_effect_name_dict : dict[str, type['ParticleEffect']] = {}
    def __init__(self, data : EffectDataDict, persistance : bool, dynamic_origin : bool = False) -> None:
        self.data : EffectDataDict = data
        ParticleEffect.elements.append(self)
        self.tracks : list[ParticleEffectTrack] = []
        self.plays_remaining = None
        self.started_playing_once : bool = False
        self.destroy_on_end : bool = True
        self.is_persistent : bool = persistance
        self.dynamic_origin : bool = dynamic_origin
        self.position : pygame.Vector2 = pygame.Vector2(0,0)
        self._zombie : bool = False

    @classmethod
    def add_effect(cls, name : str, data : EffectDataDict, override : bool = True):
        if name in cls.effects_data and not override:
            return
        cls.effects_data[name] = data

    @classmethod
    def add_special_effect_class(cls, name : str, effect_class : type['ParticleEffect'], override : bool = True):
        if name in cls.special_effect_name_dict and not override:
            return
        cls.special_effect_name_dict[name] = effect_class
    
    @classmethod
    def load_effect(cls, name : str, persistance : bool = False, dynamic_origin : bool = False):
        if name not in cls.effects_data: return None
        effect_data : EffectDataDict = cls.effects_data[name]
        effect_type : str|None = effect_data['type']
        if effect_type is None:
            return ParticleEffect(effect_data, persistance, dynamic_origin)
        special_effect_class = ParticleEffect.special_effect_name_dict.get(effect_type, SpecialParticleEffect)
        return special_effect_class(effect_data, persistance, dynamic_origin)
    
    def emit(self, track : 'ParticleEffectTrack'):
        if not Particle.inactive_elements:
            return
        new_particle : Particle = Particle.inactive_elements[0]

        effect_data_class = EffectData.from_dict(self.data)

        offset : pygame.Vector2 = effect_data_class.get_rand_offset()
        if not self.dynamic_origin:
            new_pos = track.origin + offset
        else:
            new_pos = self.position + offset

        life : float = effect_data_class.get_rand_lifetime()
        velocity : pygame.Vector2 = effect_data_class.get_rand_base_velocity()
        drag : float = effect_data_class.get_rand_drag()
        accel : pygame.Vector2 = effect_data_class.get_rand_accel()
        kill_offscreen = self.data.get('destroy_offscreen', True)
        angle : float = effect_data_class.get_rand_vel_angle()
        mag : float = effect_data_class.get_rand_vel_mag()
        new_particle.spawn(new_pos, life, self.data['update_method'], self.data['main_texture'], 
                           velocity=velocity, accel=accel, drag=drag, alt_textures=self.data['alt_textures'], anim=self.data['animation'], 
                           destroy_offscreen=kill_offscreen, angle=angle, mag=mag, copy_surf = self.data['copy_surface'],
                           time_source=track.time_source)
        
        track.active.append(new_particle)
        track.total_count += 1
    
    def play(self, pos : pygame.Vector2, time_source : TimeSource|None = None) -> 'ParticleEffectTrack':
        self.started_playing_once = True
        new_track = ParticleEffectTrack(pos, self.data['cooldown'], time_source=time_source)
        self.tracks.append(new_track)
        for _ in range(self.data['init_spawn_count']):
            self.emit(new_track)
        return new_track

    def update(self):
        if len(self.tracks) <= 0 and self.is_persistent == False and self.started_playing_once == True:
            self.kill_safe()
            return
        to_del = []
        for track in self.tracks:
            self.continue_track(track)
            if track.ended: 
                to_del.append(track)

        for track in to_del:
            self.tracks.remove(track)

    def continue_track(self, track : 'ParticleEffectTrack'):
        if track.timer.isover() and track.total_count < self.data['target_spawn_count']:
            count, remainder = divmod(track.timer.get_time() , track.timer.duration)
            track.timer.restart()
            if track.can_emit:
                for _ in range(round(count)):
                    for _ in range(self.data['part_per_wave']):
                        self.emit(track)
                        if track.total_count >= self.data['target_spawn_count']: break
            track.timer.start_time -= remainder

            

        if (len(track.active) == 0) and ((track.total_count >= self.data['target_spawn_count']) or (track.can_emit == False)):
            track.ended = True
        
        to_del = []
        for part in track.active:
            if part.is_active() == False:
                to_del.append(part)

        for part in to_del:
            track.active.remove(part)

    def stop(self):
        for track in self.tracks:
            track.stop_emission()
    
    def cancel_all(self):
        for track in self.tracks:
            track.cleanup()
        self.tracks.clear()

    def kill_safe(self):
        self._zombie = True
        self.stop()
    
    def destroy(self):
        ParticleEffect.elements.remove(self)
        self.stop()
    
    @classmethod
    def update_all(cls):
        to_del : list[ParticleEffect] = []
        for element in cls.elements:
            element.update()
            if element._zombie:
                to_del.append(element)
        for element in to_del:
            cls.elements.remove(element)
    
    def shedule_destruction(self):
        self.destroy_on_end = True

class SpecialParticleEffect(ParticleEffect):
    def __init__(self, data : EffectDataDict, persistance : bool, dynamic_origin : bool = False):
        super().__init__(data, persistance, dynamic_origin)
        self.type : str = data['type'] or 'NoNameSpecialEffect'

class TestParticleEffect(SpecialParticleEffect):
    pass

ParticleEffect.add_special_effect_class('test', TestParticleEffect)
class TestEffectData(EffectDataDict):
    pass


class ParticleEffectTrack:
    def __init__(self, origin, cooldown, time_source : TimeSource|None = None) -> None:
        self.total_count = 0
        self.active : list[Particle] = []
        self.timer : Timer = Timer(cooldown, time_source)
        self.origin = origin
        self.ended = False
        self.can_emit = True
        self.time_source : TimeSource|None = time_source
    
    def cleanup(self):
        for part in self.active:
            part.kill_instance_safe()
        self.active.clear()
    
    def stop_emission(self):
        self.can_emit = False

def runtime_imports():
    global core_object
    from framework.core.core import core_object
    Particle.bounding_box = pygame.Rect(0, 0, *core_object.main_display.get_size())
