import pygame
import random
from framework.core.base_menu import BaseMenu
from framework.ui import UiPosition, BaseDrawableInfo
from framework.ui import UiSprite, UiDrawable, UiSpriteGroup
from framework.ui import UiFrame, BaseUiFrameInfo, RowLayout, ColumnLayout
from framework.ui import TextSprite, TextSpriteInfo, TextStyle
from framework.ui import InputTextbox, InputTextboxInfo
from framework.ui import BaseUiElements
import framework.utils.tween_module as TweenModule
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer
from framework.ui import BrightnessOverlay
from math import floor, ceil, sin
from framework.utils.helpers import ColorType
from typing import Callable, cast

from framework.core.asset_manager import asset_manager

def noop():
    pass
test_image  = pygame.image.load('assets/graphics/button_templates/textbox_green_colorkey.png').convert()
test_image.set_colorkey((0, 255, 0))
class Menu(BaseMenu):
    """Implementation of the menu class."""
    font_40 = cast(pygame.Font, asset_manager.get_font("font_40"))
    font_50 = cast(pygame.Font, asset_manager.get_font("font_50"))
    font_60 = cast(pygame.Font, asset_manager.get_font("font_60"))
    font_70 = cast(pygame.Font, asset_manager.get_font("font_70"))
    font_150 = cast(pygame.Font, asset_manager.get_font("font_150"))

    @staticmethod
    def _get_core_object():
        """Function that imports the core object at runtime."""
        global core_object
        from framework.core.core import core_object
        BaseMenu._get_core_object()
    
    def init(self):
        """Initialises a menu object. Must be ran after runtime imports."""
        self._get_core_object()
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2
        centery = window_size[1] // 2
        wx, wy = window_size

        self.stage = 1
        
        self.stage_data : list[dict] = [{}, {}, {}]
        self.stages = [[], 
        [BaseUiElements.new_text_sprite('Game Title', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (centerx, window_size[1] - 15), (0.5, 1.4), 
        (Menu.font_40, 'Black', False), name='play_button'),
        BaseUiElements.new_button('BlueButton', 'Test', 1, 'bottomright', (wx - 15, window_size[1] - 15), (0.5, 1.4), 
        (Menu.font_40, 'Black', False), name='test_button')], #stage 1

        [BaseUiElements.new_button('BlueButton', 'Prev', 1, 'bottomleft', (20, window_size[1] - 25), (0.4, 1.0), 
        (Menu.font_40, 'Black', False), name='prev_button'),
        BaseUiElements.new_button('BlueButton', 'Next', 2, 'bottomright', (wx - 20, window_size[1] - 25), (0.4, 1.0), 
        (Menu.font_40, 'Black', False), name='next_button'),
        BaseUiElements.new_button('BlueButton', 'Back', 3, 'topleft', (15, 15), (0.4, 1.0), 
        (Menu.font_40, 'Black', False), name='back_button'),
        InputTextbox(BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.5), (0.5, 0.5)), zindex=50, name="test_input"), test_image,
                     "", TextStyle(Menu.font_40, "Black", False), text_pos=(0.1, 0.5), text_aligment='midleft', 
                     input_textbox_info=InputTextboxInfo(on_confirm_callbacks=[lambda t : core_object.log(t._text)], empty_text="Hello..."))]

        ]
        self.bg_color = (94, 129, 162)
        self.add_connections()

    def enter_stage_2(self):
        self.stage_data[2] = {'page_index' : 0, 'page_count' : 3, 'page_len' : 4, 'timer' : Timer(-1)}
        self.stages[2].append(self.get_stage_2_frame(0))
        self.stages[2].append(self.CustomRowStage2(["allassso", "25", "23"]))

    class CustomFrameStage2(UiFrame):
        def __init__(self, text_list : list[str]):
            size = (480, 540)
            base_drawable_info = BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.5), (0.5, 0.5)), name="test_frame",)
            ui_frame_info = BaseUiFrameInfo(size, do_clip=True)
            self.elements : list[UiDrawable] = []
            super().__init__(base_drawable_info, self.elements, ui_frame_info)

            for text, pos, anchor in zip(text_list, ((0, 0.15), (1, 0.15), (0, 0.85), (1, 0.85)), ((0, 0), (1, 0), (0, 1), (1, 1))):
                new_element = TextSprite(BaseDrawableInfo(UiPosition.from_normal_coords(pos, anchor, size), self),
                                         TextSpriteInfo(text, TextStyle(Menu.font_40, "Black", False, "White", 2, colorkey=(0, 255, 0))))
                self.add(new_element)

        def switch_text_list(self, new_text_list : list[str]):
            for element, text in zip(self.elements, new_text_list):
                if isinstance(element, TextSprite):
                    element.text = text

    class CustomColumnStage2(ColumnLayout):
        def __init__(self, text_list : list[str]):
            size = (100, 100)
            base_drawable_info = BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.9), (0.5, 0.5), (200, 100)), name="test_column",)
            ui_frame_info = BaseUiFrameInfo(size, do_clip=True)
            self.elements : list[UiDrawable] = []
            super().__init__(base_drawable_info, self.elements, ui_frame_info)
            for text in text_list:
                new_element = TextSprite(
                    BaseDrawableInfo(UiPosition.from_normal_coords(pygame.Vector2(0,0), pygame.Vector2(0,0), size), self),
                    TextSpriteInfo(text, TextStyle(Menu.font_40, "Black", False, "White", 2, colorkey=(0, 255, 0)))
                )
                self.add(new_element)

        def switch_text_list(self, new_text_list : list[str]):
            for element, text in zip(self.elements, new_text_list):
                if isinstance(element, TextSprite):
                    element.text = text

    class CustomRowStage2(RowLayout):
        def __init__(self, text_list : list[str]):
            size = (200, 100)
            base_drawable_info = BaseDrawableInfo(UiPosition.from_normal_coords((0.5, 0.9), (0.5, 0.5)), name="test_row",)
            ui_frame_info = BaseUiFrameInfo(size)
            self.elements : list[UiDrawable] = []
            super().__init__(base_drawable_info, self.elements, ui_frame_info)
            for text in text_list[:-2]:
                new_element = TextSprite(
                    BaseDrawableInfo(UiPosition.from_normal_coords(pygame.Vector2(0,0), pygame.Vector2(0,0), size), self),
                    TextSpriteInfo(text, TextStyle(Menu.font_40, "Black", False, "White", 2, colorkey=(0, 255, 0)))
                )
                self.add(new_element)
            self.add(Menu.CustomColumnStage2(text_list[-2:]))

        def switch_text_list(self, new_text_list : list[str]):
            for element, text in zip(self.elements, new_text_list):
                if isinstance(element, TextSprite):
                    element.text = text

    def get_shown_text(self, page_index : int) -> list[str]:
        long_list : list[str] = ["Arsenal", "Manchester City", "Manchester United", "Aston Villa", 
                                         "Liverpool", "Brighton", "Brentford", "Sunderland",
                                         "Tottenham", "West Ham", "Wolves", "Burnley"]
        shown_text = long_list[self.stage_data[2]['page_len'] * page_index: self.stage_data[2]['page_len'] * (page_index + 1)]
        return shown_text


    def get_stage_2_frame(self, page_index : int) -> "Menu.CustomFrameStage2":
        new_frame = self.CustomFrameStage2(self.get_shown_text(page_index))
        return new_frame
        
    def increment_stage2(self):
        new_index = (self.stage_data[2]['page_index'] + 1) % (self.stage_data[2]['page_count'])
        test_frame : Menu.CustomFrameStage2 = self.get_sprite_by_name(2, "test_frame") #type: ignore
        test_frame.switch_text_list(self.get_shown_text(new_index))
        self.stage_data[2]['page_index'] = new_index

    def decrement_stage2(self):
        new_index = (self.stage_data[2]['page_index'] - 1) % (self.stage_data[2]['page_count'])
        test_frame : Menu.CustomFrameStage2 = self.get_sprite_by_name(2, "test_frame") #type: ignore
        test_frame.switch_text_list(self.get_shown_text(new_index))
        self.stage_data[2]['page_index'] = new_index

    def exit_stage_2(self):
        frame_index = self.get_sprite_index(2, "test_frame")
        if frame_index is not None:
            self.stages[2].pop(frame_index)

        row_index = self.get_sprite_index(2, "test_row")
        if row_index is not None:
            self.stages[2].pop(row_index)
        self.stage_data[2].clear()

    
    def update(self, delta : float):
        """
        Function that runs every frame, allowing frame-based updates to happen.
            delta: The current delta factor. See core.py for more details on delta's functionement.
        """
        super().update(delta)
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
            case 2:
                time : float = stage_data['timer'].get_time()
                scale : float = abs(sin(time)) * 2
                opacity : float = sin(time) / 2 + 0.5
                test_frame : Menu.CustomFrameStage2 = self.get_sprite_by_name(2, "test_frame") #type: ignore
                test_input : InputTextbox = self.get_sprite_by_name(2, "test_input") #type: ignore
                test_row : Menu.CustomRowStage2 = self.get_sprite_by_name(2, "test_row") #type: ignore
                test_frame.scale = (scale, test_frame.scale.y)
                test_input.opacity = opacity
                test_row.angle = time * 90
    
    def handle_tag_event(self, event : pygame.Event):
        """
        Event handler for tag events.
            event: The event to handle.
        """
        if event.type != BaseMenu.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == "play_button":
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : 'test'}))
                if name == 'test_button':
                    self.goto_stage(2)
            case 2:
                if name == 'back_button':
                    self.goto_stage(1)
                elif name == 'prev_button':
                    self.decrement_stage2()
                elif name == 'next_button':
                    self.increment_stage2()
# TODO : Document the menu API (general workflow, interactivity, etc.)