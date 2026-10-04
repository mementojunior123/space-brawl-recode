import json
import pygame
from framework.utils.helpers import Task, ColorType
from framework.utils.my_timer import Timer
import framework.utils.interpolation as interpolation
import framework.utils.tween_module as TweenModule
from typing import Any, Callable, Union, overload, Literal

from framework.utils.helpers import AnchorStr, AnchorNameList, ANCHOR_REL_POS_DICT
from framework.utils.helpers import RectSideAnchorStr, RectSideAnchorNameList, is_rect_pos, is_rect_side

class AnimationTrack:
    elements : list['AnimationTrack'] = []
    def __init__(self, owner : 'Sprite', data : list[dict], name : str|None = None, time_source : Callable[[], float]|None = None, timer_factor : float = 1):
        self.target : 'Sprite' = owner
        
        new_data = [AnimationInstruction.new(value) for value in data]
        for i, instruction in enumerate(new_data):
            instruction.animation_index = i

        self.data : list[AnimationInstruction] = new_data
        self.blocking_tasks : list[AnimationInstruction] = []
        self.tasks : list[AnimationInstruction] = []
        self.progress = 0
        self.count = len(self.data)

        self.has_started = False
        self.has_ended= False
        self.time_scale = 1
        self.name : str|None = name

        self.time_source : Callable[[], float]|None = time_source
        self.timer_factor : float = timer_factor
        self.callback : Task|None = None
    
    def reset(self):
        instruction : AnimationInstruction
        for instruction in self.data:
            instruction.reset()
        
        self.blocking_tasks = []
        self.tasks = []
        self.progress = 0
        self.count = len(self.data)

        self.has_started = False
        self.has_ended= False
    
    def set_time_scale(self, value):
        self.time_scale = value
        
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __delitem__(self, index):
        del self.data[index]
    
    def do_instruction(self, instruction : 'AnimationInstruction', index : int|None = None):
        instruction.execute(self)
                
    
    def play(self, update_manually : bool = False, callback : Task|None = None):
        self.has_started= True
        self.has_ended = False
        self.callback = callback
        instruction: AnimationInstruction
        for i, instruction in enumerate(self.data):
            if self.blocking_tasks: break
            self.do_instruction(instruction, i)
            if instruction.has_ended: self.progress += 1
        if not update_manually:
            self.register()
    
    def register(self):
        AnimationTrack.elements.append(self)
    
    def stop(self):
        self.has_ended = True
            

    def update(self):
        if not self.target.active: self.stop()
        if self.has_ended: return

        to_delete = []
        instruction: AnimationInstruction
        for i, instruction in enumerate(self.data): #this loop starting new tasks
            if self.blocking_tasks: 
                break #cant start new tasks when there's a blocking task
            if instruction.has_started: continue #Already being handled by self.tasks
            if instruction.has_ended: continue #Already finished
            self.do_instruction(instruction, i)
            if instruction.has_ended: 
                self.progress += 1
                #print(f'Progress made : {self.progress}/{self.count} (type = {instruction.type})')
                
        to_delete = []

        for instruction in self.blocking_tasks: #this loop is for blocking tasks
            if instruction.has_ended: 
                to_delete.append(instruction) #Uncessary guard clause
                continue

            self.do_instruction(instruction)
            if instruction.has_ended: 
                to_delete.append(instruction)
                self.progress += 1
                #print(f'Progress made : {self.progress}/{self.count} (type = {instruction.type})')
                
        
        for instruction in to_delete:
            self.blocking_tasks.remove(instruction)
        
        to_delete = []
        for i, instruction in enumerate(self.tasks): #this loop is for already running tasks
            if instruction.has_ended: 
                to_delete.append(instruction) #Uncessary guard clause
                continue

            self.do_instruction(instruction, i)
            if instruction.has_ended:
                to_delete.append(instruction)
                self.progress += 1
                #print(f'Progress made : {self.progress}/{self.count} (type = {instruction.type})')

        for instruction in to_delete:
            self.tasks.remove(instruction)

        if self.progress >= self.count: 
            self.has_ended = True
            if self.callback: self.callback.execute()
    
    @classmethod
    def update_all_elements(cls):
        to_del : list[AnimationTrack] = []
        for element in cls.elements:
            element.update()
            if element.has_ended:
                to_del.append(element)
        for element in to_del:
            cls.elements.remove(element)
        to_del.clear()
        



class AnimationInstruction:
    def __init__(self, data):
        self.type : str = data["type"]
        self.data : dict = data

        self.has_started : bool = False
        self.has_ended : bool = False

        self.start_value : Any|None = None
        self.last_update : Any|None = None
        self.last_value : Any|None = None
        self.timer : Timer
        self.animation_index : int
    
    
    def get_anchor(self, sprite : 'Sprite', anchor : AnchorStr) -> pygame.Vector2:
        if anchor is None:
            return sprite.position
        elif anchor == 'true':
            return sprite.true_position
        else:
            return pygame.Vector2(sprite.rect.__getattribute__(anchor))
    
    def set_anchor(self, sprite : 'Sprite', anchor : AnchorStr, position : pygame.Vector2):
        if anchor is None:
            sprite.position = position
        elif anchor == 'true':
            sprite.true_position = position
        else:
            sprite.move_rect(anchor, position)
    
    def get_rect_side(self, sprite : 'Sprite', anchor : RectSideAnchorStr) -> int:
        return sprite.rect.__getattribute__(anchor)
    
    def set_rect_side(self, sprite : 'Sprite', anchor : RectSideAnchorStr, position : int):
        sprite.move_rect(anchor, position)

    def get_any_anchor(self, sprite : 'Sprite', anchor : RectSideAnchorStr|AnchorStr) -> int|pygame.Vector2:
        if anchor in AnchorNameList:
            return self.get_anchor(sprite, anchor)
        elif anchor in RectSideAnchorNameList:
            return self.get_rect_side(sprite, anchor)
        else:
            raise ValueError(f"{anchor} is not a valid anchor target!")
    
    def set_any_anchor(self, sprite : 'Sprite', anchor : RectSideAnchorStr|AnchorStr, position : pygame.Vector2|int):
        if anchor in AnchorNameList:
            if not isinstance(position, pygame.Vector2):
                try:
                    position = pygame.Vector2(position)
                except ValueError:
                    raise ValueError(f"-->{position}<-- is not a valid value for a rect anchor")
            self.set_anchor(sprite, anchor, position)
        elif anchor in RectSideAnchorNameList:
            if not isinstance(position, int):
                raise ValueError(f"-->{position}<-- is not a valid position for the side of a rect!")
            self.set_rect_side(sprite, anchor, position)
        else:
            raise ValueError(f"{anchor} is not a valid anchor target!")
          
    @staticmethod
    def new(data : dict) -> 'AnimationInstruction':
        anim_conversion_dict : dict[str, type[AnimationInstruction]] = {
            "wait" : WaitInstruction,
            "delay" : DelayInstruction,
            'delay_rel' : DelayRelInstruction,
            "move_to" : MoveToInstruction,
            "move_by" : MoveByInstruction,
            "slide_by" : SlideByInstruction,
            "slide_to" : SlideToInstruction,
            "switch_image" : SwitchImageInstruction,
            "rotate_by" : RotateByInstruction,
            "rotate_to" : RotateToInstruction,
            "rotate_by_over_time" : RotateByOverTimeInstruction,
            "rotate_to_over_time" : RotateToOverTimeInstruction,
            "image_gradient" : ImageGradientInstruction,
            "tween_property" : TweenPropertyInstruction,
        }
        instruction_type : str = data['type']
        if instruction_type in anim_conversion_dict:
            return (anim_conversion_dict[instruction_type])(data)
        else:
            return AnimationInstruction(data)
    
    def execute(self, track : AnimationTrack):
        pass
        
    def reset(self):
        self.has_started = False
        self.has_ended = False

        self.start_value = None
        self.last_update = None
        self.last_value = None
        del self.timer

    def __str__(self) -> str:
        return f"Animation instruction of type {self.__class__.__name__} with {self.data =}"


class WaitInstruction(AnimationInstruction):

    def __init__(self, data):
        super().__init__(data)
        self.time : float = data['time']

    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            track.blocking_tasks.append(self)

        if self.timer.isover():
            self.has_ended = True
        return

class DelayInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        indexes : int|list[int] = data["index"]
        self.indexes : list[int] = [indexes] if isinstance(indexes, int) else indexes
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.blocking_tasks.append(self)
        
        for index in self.indexes:
            if not track.data[index].has_ended: return     
        self.has_ended = True

class DelayRelInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        indexes : int|list[int] = data["index"]
        self.indexes : list[int] = [indexes] if isinstance(indexes, int) else indexes
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.blocking_tasks.append(self)
        
        for index in self.indexes:
            target_index = self.animation_index + index
            if target_index < 0:
                print(f"@ {self}: Target index went below 0 ({target_index})")
                return
            if not track.data[target_index].has_ended: return     
        self.has_ended = True

class MoveByInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.offset : pygame.Vector2 = pygame.Vector2(data['offset'])
        self.last_value : None|pygame.Vector2 = None
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        self.has_started = True
        track.target.position += self.offset
        self.has_ended = True
        return

class MoveToInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.anchor : AnchorStr|RectSideAnchorStr = data['anchor'] if data['anchor'] is not None else 'center'
        target : int|list[int] = data['target']
        self.target : pygame.Vector2|int

        if isinstance(target, int) or isinstance(target, float):
            self.target = round(target)
        else:
            self.target = pygame.Vector2(target)
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        self.has_started = True
        self.set_any_anchor(track.target, self.anchor, self.target)
        self.has_ended = True
        return

class SlideByInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.offset : pygame.Vector2 = pygame.Vector2(data['offset'])
        self.time : float = data['time']
        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style

        self.last_value : pygame.Vector2
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if self.has_ended: return
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            self.start_value = pygame.Vector2(track.target.position)
            self.last_value = pygame.Vector2(0,0)    
            return
        
        
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_ended = True
        
        new_offset : pygame.Vector2 = interpolation.compatibilty_lerp(pygame.Vector2(0, 0), self.offset, self.easing_style(alpha))
        prev_offset : pygame.Vector2 = self.last_value
        result : pygame.Vector2 = new_offset - prev_offset

        
        track.target.position += result
        self.last_value = new_offset

        return

class SlideToInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.anchor : AnchorStr|RectSideAnchorStr = data['anchor'] if data['anchor'] is not None else 'center'

        target : int|list[int] = data['target']
        self.target : pygame.Vector2|int

        if isinstance(target, int) or isinstance(target, float):
            self.target = round(target)
        else:
            self.target = pygame.Vector2(target)
        
        self.time : float = data['time']
        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style

        self.start_value : pygame.Vector2|int
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            self.start_value = self.get_any_anchor(track.target, self.anchor)
        
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_ended = True

        new_pos : pygame.Vector2|int = interpolation.lerp(self.start_value, self.target, self.easing_style(alpha))
        self.set_any_anchor(track.target, self.anchor, new_pos)
        return

class SwitchImageInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.source_name : str = data['source']
        self.index : str = data['index']
        self.anchor : RectSideAnchorStr|AnchorStr|None = data['dynamic_anchor']
        self.colorkey : str|ColorType|None = data['colorkey']
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        self.has_started = True
        old_pos = None if self.anchor is None else self.get_any_anchor(track.target, self.anchor)

        source : dict[Any, pygame.Surface] = track.target.__getattribute__(self.source_name)
        new_image : pygame.Surface = source[self.index]
        if self.colorkey: new_image.set_colorkey(self.colorkey)
        elif self.colorkey == 0: new_image.set_colorkey(None)

        track.target.image = new_image
        if track.target.pivot:
            track.target.pivot.original_image = new_image
            if self.colorkey is None:
                pass
            elif self.colorkey == 0:
                track.target.pivot.img_colorkey = None
            else:
                track.target.pivot.img_colorkey = self.colorkey

        track.target.rect = new_image.get_rect()
        if self.anchor is None or old_pos is None:
            track.target.align_rect()
        else:
            track.target.move_rect(self.anchor, old_pos)

        if track.target.pivot:
            track.target.angle = track.target.angle

        self.has_ended = True
        return

class RotateByInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.target_angle : float = data['angle']
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        self.has_started = True
        track.target.angle += self.target_angle
        self.has_ended = True
        return

class RotateToInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.target_angle : float = data['angle']
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        self.has_started = True
        track.target.angle = self.target_angle
        self.has_ended = True
        return

class RotateByOverTimeInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.target_angle : float = data['angle']
        self.time : float = data['time']
        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style

        self.last_value : float
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            self.start_value = track.target.angle
            self.last_value = 0.0    
            return
        
        
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_ended = True
        
        new_offset : float = interpolation.lerp(0, self.target_angle, self.easing_style(alpha))
        prev_offset : float = self.last_value
        result : float = new_offset - prev_offset

        
        track.target.angle += result
        self.last_value = new_offset
    
class RotateToOverTimeInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.target_angle : float = data['angle']
        self.time : float = data['time']
        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style

        self.start_value : float
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            self.start_value = track.target.angle
            return
        
        
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_ended = True
        
        track.target.angle = interpolation.lerp(self.start_value, self.target_angle, self.easing_style(alpha))

class ImageGradientInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.source_name : str = data['source']
        self.target_index : int|float = data['target_index']
        self.anchor : RectSideAnchorStr|AnchorStr|None = data['dynamic_anchor']
        self.colorkey : str|ColorType|None = data['colorkey']

        self.time : float = data['time']

        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style
    
    def execute(self, track: AnimationTrack, current_index : int|None = None):
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            self.start_value = track.target.image
            self.last_value = track.target.image

        
        alpha = self.timer.get_time() / self.timer.duration
        if alpha > 1: 
            alpha = 1
            self.has_ended = True

        
        source : list[pygame.Surface] = track.target.__getattribute__(self.source_name)
        new_image : pygame.Surface = source[int(interpolation.lerp(0, self.target_index, self.easing_style(alpha)))]
        if new_image == self.last_value: return

        old_pos = None if self.anchor is None else self.get_any_anchor(track.target, self.anchor)    
        if self.colorkey: new_image.set_colorkey(self.colorkey)
        elif self.colorkey == 0: new_image.set_colorkey(None)

        track.target.image = new_image
        if track.target.pivot:
            track.target.pivot.original_image = new_image
            if self.colorkey is None:
                pass
            elif self.colorkey == 0:
                track.target.pivot.img_colorkey = None
            else:
                track.target.pivot.img_colorkey = self.colorkey

        track.target.rect = new_image.get_rect()

        if track.target.pivot:
            track.target.angle = track.target.angle

        
        if self.anchor is None or old_pos is None:
            track.target.align_rect()
        else:
            track.target.move_rect(self.anchor, old_pos)    
        self.last_value = new_image

class TweenPropertyInstruction(AnimationInstruction):
    def __init__(self, data):
        super().__init__(data)
        self.property_name : str = data['property']
        self.goal : Any = data['goal']

        self.time : float = data['time']

        self.easing_style : Callable[[float], float]
        easing_style : str|Callable[[float], float] = data['easing_style']
        if isinstance(easing_style, str): 
            self.easing_style = getattr(interpolation, easing_style)
        else:
            self.easing_style = easing_style

        self.start_value : TweenModule.TweenTrack
    
    def execute(self, track: AnimationTrack):
        if not self.has_started:
            self.has_started = True
            track.tasks.append(self)
            self.timer = Timer(self.time, track.time_source, track.timer_factor)
            new_tween = TweenModule.new_tween(track.target, TweenModule.TweenInfo(self.easing_style, self.time), {self.property_name : self.goal},
                                              True, True, True, track.time_source, track.timer_factor)
            self.start_value = new_tween
        
        tween : TweenModule.TweenTrack = self.start_value
        tween.update()
        if tween.has_finished:
            self.has_ended = True

# TODO : Add dataclasses

class Animation:
    ANIM_DATA = {}

    @classmethod
    def add_animation(cls, name : str, data : list[dict], override : bool = True):
        if name in cls.ANIM_DATA and not override:
            return
        cls.ANIM_DATA[name] = data

    @classmethod
    def get_animation(cls, name : str):
        if name in cls.ANIM_DATA:
            return Animation(cls.ANIM_DATA[name], name)
        else:
            print("AnimationError: Animation not found")
            return None

    
    def __init__(self, data : list[dict], name : str) -> None:
        self.data = data
        self.name : str = name
    
    def load(self, owner : 'Sprite', time_source : Callable[[], float]|None = None, timer_factor : float = 1):
        return AnimationTrack(owner, self.data, self.name, time_source, timer_factor)

    def load_file(self, path = "data/animations/animation_data.json"):
        with open(path, "r") as read_file:
            dictionary = json.load(read_file)
        
        self.ANIM_DATA += dictionary

def _sprite_hint():
    global Sprite
    from framework.game.sprite import Sprite