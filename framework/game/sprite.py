import pygame
from framework.utils.base_animation import AnimationTrack, Animation
from typing import Any, Self, Type, TypeAlias, Iterable
from framework.utils.helpers import is_sorted
from framework.utils.pivot_2d import Pivot2D
from framework.game.sprite_renderer import SpriteCamera
from inspect import isclass

CollisionGroup : TypeAlias = list['Sprite']|Type['Sprite']

class Sprite:
    '''Base class for all game objects.'''
    active_elements : list[Self] = []
    inactive_elements : list[Self]  = []
    linked_classes : list[Type['Sprite']] = []

    ordered_sprites : list['Sprite'] = []
    registered_classes : list[Type['Sprite']] = []
    SPRITE_CLICKED : int = pygame.event.custom_type()

    def __init_subclass__(cls : Type['Sprite'], do_link : bool = True, sprite_count : int = 0):
        parents : list[Type[Sprite]] = list(cls.__bases__)
        cls.active_elements = []
        cls.inactive_elements = []
        cls.linked_classes : list[Type['Sprite']] = []
        if do_link:
            for parent in parents:
                for linked in (parent.linked_classes):
                    if linked not in cls.linked_classes:
                        cls.linked_classes.append(linked)
                if parent not in cls.linked_classes:
                    cls.linked_classes.append(parent)
            
            Sprite.register_class(cls)
        for _ in range(sprite_count): cls()
    
    def __init__(self) -> None:
        self._position : pygame.Vector2
        self.pivot : Pivot2D|None = None
        self.current_camera : bool|SpriteCamera = False
        self._image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask|None
        self.dynamic_mask : bool = False
        self.zindex : int
        self._zombie : bool = False
        for linked_class in self.linked_classes:
            linked_class.inactive_elements.append(self)
        self.inactive_elements.append(self)
    
    @property
    def image(self) -> pygame.Surface:
        return self._image
    
    @image.setter
    def image(self, new_surf : pygame.Surface):
        self._image = new_surf
        if self.dynamic_mask:
            if new_surf is None:
                self.mask = None
            else:
                self.mask = pygame.mask.from_surface(new_surf)
    
    def align_rect(self):
        self.rect.center = round(self.true_position)
    
    def move_rect(self, anchor : str, position : pygame.Vector2|int|tuple[int,int]):
        self.rect.__setattr__(anchor, position)
        self.true_position = pygame.Vector2(self.rect.center)
    
    def clamp_rect(self, area : pygame.Rect):
        if self.rect.left < area.left: self.move_rect('left', area.left)
        if self.rect.right > area.right: self.move_rect('right', area.right)
        if self.rect.top < area.top: self.move_rect('top', area.top)
        if self.rect.bottom > area.bottom: self.move_rect('bottom', area.bottom)
    
    @property
    def position(self) -> pygame.Vector2:
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            return self._position
        else:
            return self.pivot.origin
    
    @position.setter
    def position(self, new_val : pygame.Vector2):
        if not hasattr(self, 'pivot'): self.pivot = None
        if self.pivot is None:
            self._position = new_val
        else:
            self.pivot.origin = new_val
        
        self.align_rect()
    
    @property
    def true_position(self) -> pygame.Vector2:
        if self.pivot is None:
            return self._position
        else:
            return self.pivot.position
    
    @true_position.setter
    def true_position(self, new_val):
        if self.pivot is None:
            self._position = new_val
        else:
            self.pivot.position = new_val
        
        self.align_rect()
    
    @property
    def angle(self) -> float:
        if self.pivot is None:
            raise AttributeError("Cannot change angle when there is no pivot!")
        return self.pivot.angle
    
    @angle.setter
    def angle(self, new_val : float):
        if self.pivot is None:
            raise AttributeError("Cannot change angle when there is no pivot!")
        self.pivot.angle = new_val
        self.image, self.rect, new_pos = self.pivot.rotate_og_image() if self.pivot.original_image else self.pivot.rotate_image(self._image)
        self.align_rect()

    @classmethod
    def register_class(cls : Type['Sprite'], class_to_register : Type['Sprite']):
        if class_to_register not in cls.registered_classes:
            cls.registered_classes.append(class_to_register)
    
    @property
    def active(self):
        return (self in self.__class__.active_elements) or (self in Sprite.active_elements)

    @classmethod
    def pool(cls : Type[Self], element : Self):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        for linked_class in cls.linked_classes + [cls]:
            if element in linked_class.active_elements:
                linked_class.active_elements.remove(element)         
            
            if element not in linked_class.inactive_elements:
                linked_class.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls : Type[Self], element : Self):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''
        for linked_class in cls.linked_classes + [cls]:
            if element not in linked_class.active_elements:
                linked_class.active_elements.append(element)

            if element in linked_class.inactive_elements:
                linked_class.inactive_elements.remove(element)

    @classmethod
    def pool_elements(cls : Type['Self']):
        '''Pools every element of the class'''
        while len(cls.active_elements) > 0:
            cls.pool(cls.active_elements[0])
    
    @staticmethod
    def pool_all_sprites():
        while len(Sprite.active_elements) > 0:
            element = Sprite.active_elements[0]
            cls = element.__class__
            cls.pool(element)

    @classmethod
    def spawn(cls, *args, **kwargs):
        raise NotImplementedError('Sub-class must implement the spawn method; Base-classes cannot be instanciated')

    def clean_instance(self):
        self.pivot = None
        self._zombie = False
        self.mask = None

        del self._image
        del self.rect
        del self._position
        del self.zindex

    def kill_instance(self):
        self.clean_instance()
        self.self_destruct()
    
    def kill_instance_safe(self):
        self._zombie = True
    
    @classmethod
    def clean_all_instances(cls : Type[Self]):
        for element in cls.active_elements:
            element.clean_instance()
    
    @classmethod
    def kill_all_instances(cls : Type[Self]):
        for element in cls.active_elements:
            element.clean_instance()
        cls.pool_elements()
    
    @staticmethod
    def clean_all_sprites():
        for element in Sprite.active_elements:
            element.clean_instance()
    
    @staticmethod
    def kill_all_sprites():
        for element in Sprite.active_elements:
            element.clean_instance()
        Sprite.pool_all_sprites()
    
    def update(self, delta : float):
        pass
    
    @classmethod
    def update_class(cls : Type[Self], delta : float):
        pass

    def self_destruct(self):
        cls = self.__class__
        cls.pool(self)
    
    @staticmethod
    def clear_zombies(elements : list['Sprite']):
        to_kill : list[Sprite] = []
        for element in elements:
            if element._zombie:
                element._zombie = False
                to_kill.append(element)
        for element in to_kill:
            element.kill_instance()

    @classmethod
    def update_all(cls : Type[Self], delta : float):
        for element in cls.active_elements:
            element.update(delta)
        cls.clear_zombies(cls.active_elements) #type: ignore (wdym covariance???)
    
    @staticmethod
    def update_all_sprites(delta : float):
        for element in Sprite.active_elements:
            element.update(delta)
        Sprite.clear_zombies(Sprite.active_elements)
    
    @staticmethod
    def update_all_registered_classes(delta : float):
        for sprite_subclass in Sprite.registered_classes:
            sprite_subclass.update_class(delta)
    
    def draw(self, display : pygame.Surface):
        if self.current_camera is True:
            pass
        elif not self.current_camera:
            display.blit(self.image, self.rect)
        else:
            self.current_camera.render_sprite(self, display)
    
    @classmethod
    def draw_all(cls : Type[Self], display):
        for element in cls.active_elements:
            element.draw(display)

    @property
    def x(self):
       return self.position.x
    @x.setter
    def x(self, value):
        self.position.x = value
    @property
    def y(self):
        return self.position.y
    @y.setter
    def y(self, value):
        self.position.y = value


    def is_colliding(self, other : 'Sprite'):
        if not self.rect.colliderect(other.rect): return False
        if (not other.mask) or (not self.mask):
            return False
        if self.mask.overlap(other.mask,(other.rect.x - self.rect.x ,other.rect.y - self.rect.y)): return True
        return False

    def is_collding_rect(self, other : 'Sprite'):
        return self.rect.colliderect(other.rect)

    def _handle_collision_group_argument(self, collision_groups_arg : CollisionGroup|list[CollisionGroup]) -> list[list['Sprite']]:
        if not collision_groups_arg:
            return []
        collision_groups : list[CollisionGroup]
        if not isinstance(collision_groups_arg, list):
            collision_groups = [collision_groups_arg]
        elif isinstance(collision_groups_arg[0], Sprite):
            collision_groups = [collision_groups_arg] #type: ignore
        else:
            collision_groups = collision_groups_arg #type: ignore
        result : list[list[Sprite]] = []
        for collision_group in collision_groups:
            actual_group = collision_group.active_elements if isclass(collision_group) else collision_group
            result.append(actual_group)
        return result

    def get_colliding(self, collision_groups : CollisionGroup|list[CollisionGroup]):
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses mask collision.'''
        for collision_group in self._handle_collision_group_argument(collision_groups):
            for element in collision_group:
                if self.is_colliding(element) and not element._zombie: return element     
        return None
    
    def get_rect_colliding(self, collision_groups : list[CollisionGroup]|CollisionGroup):
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses a bounding box check.'''
        for collision_group in self._handle_collision_group_argument(collision_groups):
            for element in collision_group:
                if self.is_collding_rect(element) and not element._zombie: return element
        return None
    
    def get_all_colliding(self, collision_groups : list[CollisionGroup]|CollisionGroup) -> list['Sprite']:
        '''Returns all entities colliding this sprite within collision_group. Uses mask collision.'''
        return_val : list['Sprite'] = []
        for collision_group in self._handle_collision_group_argument(collision_groups):
            for element in collision_group:
                if self.is_colliding(element) and not element._zombie:
                    return_val.append(element)
        return return_val

    def get_all_rect_colliding(self, collision_groups : list[CollisionGroup]|CollisionGroup) -> list['Sprite']:
        '''Returns all entities colliding this sprite within collision_group. Uses a bounding box check.'''
        return_val : list['Sprite'] = []
        for collision_group in self._handle_collision_group_argument(collision_groups):
            for element in collision_group:
                if self.is_collding_rect(element) and not element._zombie: 
                    return_val.append(element)
        return return_val

    def on_collision(self, other : 'Sprite'):
        pass

    def is_active(self):
        return self in self.__class__.active_elements
    
    @staticmethod
    def draw_all_sprites(display : pygame.Surface):
        #if not is_sorted(cls.active_elements, key=lambda sprite : sprite.zindex):
        Sprite.active_elements.sort(key=lambda sprite : sprite.zindex)
        for element in Sprite.active_elements:
            element.draw(display)

    
    @staticmethod
    def get_sprite_class_by_name(name : str) -> Type['Sprite']|None:
        for sprite_class in Sprite.registered_classes:
            if sprite_class.__name__ == name:
                return sprite_class
        return None
    
    @classmethod
    def handle_mouse_event_Sprite(cls, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.touch: return
            if event.button not in (1, 2, 3):
                return
            press_pos : tuple = event.pos
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : -1})
            pygame.event.post(new_event)
    
    @classmethod
    def handle_touch_event_Sprite(cls, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * core_object.main_display.get_width()
            y = event.y * core_object.main_display.get_height()
            press_pos : tuple[int, int] = (round(x), round(y))
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : event.finger_id})
            pygame.event.post(new_event)
    
    @classmethod
    def _core_hint(cls):
        global core_object
        from framework.core.core import core_object
            