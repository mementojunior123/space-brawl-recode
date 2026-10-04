import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.base_animation import Animation
from framework.utils.pivot_2d import Pivot2D

from typing import cast


class TestPlayer(Sprite, sprite_count = 1):
    debug_circle_size : int = 10
    debug_circle = pygame.Surface((debug_circle_size, debug_circle_size))
    debug_circle.set_colorkey((0, 255, 0))
    debug_circle.fill((0,255 ,0))
    pygame.draw.circle(debug_circle, 'Red', (debug_circle_size // 2, debug_circle_size // 2), debug_circle_size // 2)
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    test_anim : Animation = Animation.get_animation("test") #type: ignore
    #load assets
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    colors : list[str] = ["Red", "Green", "Blue", "Yellow", "Orange", "Purple", "Black", "White"]
    surface_list : list[pygame.Surface] = []
    surfaces : dict[str, pygame.Surface] = {}
    for color in colors:
        color_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
        pygame.draw.rect(color_image, color, (0,0, *IMAGE_SIZE))
        surfaces[color] = color_image
        surface_list.append(color_image)

    def __init__(self) -> None:
        super().__init__()
        self.color_images : dict[str, pygame.Surface]
        self.color_image_list : list[pygame.Surface]
        self.last_mouse_pos : tuple[int, int]

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        element.color_images = cls.surfaces
        element.color_image_list = cls.surface_list
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(-0, 30)
        element.last_mouse_pos = pygame.mouse.get_pos()
        track = cls.test_anim.load(element, core_object.game.game_timer.get_time)
        track.play()
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if keyboard_map[pygame.K_e]:
            self.angle += 5 * delta
        if keyboard_map[pygame.K_q]:
            self.angle -= 5 * delta
        if move_vector.magnitude(): move_vector.normalize()
        self.position += move_vector * speed * delta
        self.clamp_rect(pygame.Rect(0,0, *core_object.main_display.get_size()))
    
    def clean_instance(self):
        super().clean_instance()

    
    def draw(self, display : pygame.Surface):
        super().draw(display)
        display.blit(self.debug_circle, pygame.mouse.get_pos())
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEMOTION:
            self.last_mouse_pos = event.pos
    
    @classmethod
    def receive_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                element.handle_mouse_event(event)



class NetworkTestPlayer(Sprite, sprite_count = 1):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    def __init__(self) -> None:
        super().__init__()
        self.attempted_move : pygame.Vector2
        self.attempted_rotate : float
        self.is_host : bool

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, is_host : bool, color = "Red"):
        element = cls.inactive_elements[0]

        element.image = cls.test_image.copy()
        element.image.fill(color)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(-0, 30)
        element.current_camera = core_object.game.main_camera

        element.is_host = is_host
        element.attempted_move = pygame.Vector2(0,0)
        element.attempted_rotate = 0

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
        if self.is_host:
            self.update_host(delta)
        else:
            self.update_client(delta)
    
    def update_host(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if keyboard_map[pygame.K_e]:
            self.angle += 5 * delta
        if keyboard_map[pygame.K_q]:
            self.angle -= 5 * delta
        if move_vector.magnitude(): move_vector.normalize()
        self.position += move_vector * speed * delta
        self.clamp_rect(pygame.Rect(0,0, *core_object.main_display.get_size()))
    
    def update_client(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        target_angle_diff : float = 0
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if keyboard_map[pygame.K_e]:
            target_angle_diff += 5 * delta
        if keyboard_map[pygame.K_q]:
            target_angle_diff -= 5 * delta
        if move_vector.magnitude(): move_vector.normalize()
        self.attempted_move = move_vector * speed
        self.attempted_rotate = target_angle_diff
        self.position += self.attempted_move
        self.angle += self.attempted_rotate
    
    def clean_instance(self):
        super().clean_instance()
        del self.attempted_move
        del self.attempted_rotate
        del self.is_host

class NetworkSyncTestPlayer(Sprite, sprite_count = 1):
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    def __init__(self) -> None:
        super().__init__()
        self.other_is_host : bool

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, other_is_host : bool, color = "Red"):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        element.image = cls.test_image.copy()
        element.image.fill(color)
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(-0, 30)
        element.current_camera = core_object.game.main_camera

        element.other_is_host = other_is_host

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
        pass
    
    def sync_other_is_host(self, host_position : pygame.Vector2, host_angle : float):
        self.position = host_position
        self.angle = host_angle
    
    def sync_other_is_client(self, attempted_move : pygame.Vector2, attempted_rotate : float, delta_step : float):
        self.position += attempted_move * delta_step
        self.angle += attempted_rotate * delta_step
    
    def clean_instance(self):
        super().clean_instance()
        del self.other_is_host

def make_connections():
    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, TestPlayer.receive_event)
    core_object.event_manager.bind(pygame.MOUSEBUTTONUP, TestPlayer.receive_event)
    core_object.event_manager.bind(pygame.MOUSEMOTION, TestPlayer.receive_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, TestPlayer.receive_event)
    core_object.event_manager.unbind(pygame.MOUSEBUTTONUP, TestPlayer.receive_event)
    core_object.event_manager.unbind(pygame.MOUSEMOTION, TestPlayer.receive_event)