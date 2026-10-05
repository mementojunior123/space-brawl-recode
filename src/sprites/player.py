import pygame
from typing import Generator, TypeAlias, Literal, TypedDict, cast
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image, sign
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript

for i in range(8):
    core_object.asset_manager.load_surface(f"assets/graphics/player/player-{i}.png", f'player_cycle{i}', 'alpha_to_colorkey', 2, (0, 255, 0))

class Player(Sprite, sprite_count=1):
    animation_assets : dict[int, pygame.Surface] = {i : cast(pygame.Surface, core_object.asset_manager.get_surface(f"player_cycle{i}")) for i in range(8)}
    display_size = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.animation_images : dict[int, pygame.Surface]
        self.velocity : pygame.Vector2

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        element = cls.inactive_elements[0]

        element.animation_images = cls.animation_assets
        element.image = element.animation_images[0]
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element._position = pygame.Vector2(0, 0)
        element.velocity = pygame.Vector2(3, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        cls.unpool(element)
        return element

    def restrict_to_screen(self):
        MARGIN : int = 25
        if self.rect.right > Player.display_size[0] - MARGIN:
            self.move_rect("right", Player.display_size[0] - MARGIN)
            if self.velocity.x > 0: self.velocity.x = 0
        if self.rect.bottom > Player.display_size[1]:
            self.move_rect("bottom", Player.display_size[1])
        if self.rect.left < MARGIN:
            self.move_rect('left', MARGIN)
            if self.velocity.x < 0: self.velocity.x = 0
        if self.rect.top < 0:
            self.move_rect('top', 0)

    def update(self, delta : float):
        self.position += self.velocity * delta
        self.restrict_to_screen()

    def draw(self, display : pygame.Surface):
        super().draw(display)

    def take_damage(self, damage : float):
        pass

    def clean_instance(self):
        super().clean_instance()
        del self.animation_images
        del self.velocity