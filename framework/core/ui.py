import pygame
from framework.ui import UiDrawable
from framework.utils.my_timer import Timer
from typing import Callable

class Ui:
    def __init__(self, elements : list[UiDrawable]|None = None) -> None:
        if elements is None: elements = []
        self.elements : list[UiDrawable] = elements
        self.temp_elements : dict[UiDrawable, Timer] = {}
        self.complete_list : list[UiDrawable] = []
    
    def get_sprite(self, name : str|None = None, tag : int|None = None) -> UiDrawable|None:
        for element in self.complete_list:
            if name is not None:
                if element.name == name:
                    return element
            if tag is not None:
                if element.tag == tag:
                    return element
        return None
    
    def get_sprites(self, name : str|None = None, tag : int|None = None) -> list[UiDrawable]:
        return_list = []
        for element in self.complete_list:
            if name is not None:
                if element.name == name:
                    return_list.append(element)
            if tag is not None:
                if element.tag == tag:
                    if element not in return_list: return_list.append(element)
        
        return return_list

    def render(self, display : pygame.Surface):
        self.complete_list.sort(key = lambda ui_sprite : ui_sprite.zindex)
        for element in self.complete_list:
            element.draw(display)
        #print(self.complete_list, self.elements, self.temp_elements)
    
    def add(self, element : UiDrawable, duplicate = False):
        if element not in self.elements or duplicate == True:
            self.elements.append(element)
            self.complete_list.append(element)
    
    def add_multiple(self, elements : list[UiDrawable], duplicate = False):
        for element in elements:
            self.add(element, duplicate=duplicate)

    def remove(self, element : UiDrawable, remove_all_instances = False):
        if not remove_all_instances:
            if element in self.elements: 
                self.elements.remove(element)
                if element in self.temp_elements: self.temp_elements.pop(element)
                if element in self.complete_list: self.complete_list.remove(element)
        else:
            to_del = []
            for sprite in self.elements:
                if sprite == element: to_del.append(element)
            for item in to_del:
                self.elements.remove(item)
                if item in self.temp_elements: self.temp_elements.pop(item)
                if element in self.complete_list: self.complete_list.remove(item)
    
    def clear_all(self):
        self.elements.clear()
        self.temp_elements.clear()
        self.complete_list.clear()
    
    def add_temp(self, element : UiDrawable, time : float|Timer, override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        if element not in self.temp_elements or override == True:
            timer = time if isinstance(time, Timer) else Timer(time, time_source, time_scale)
            self.temp_elements[element] = timer
            self.complete_list.append(element)
    
    def update(self, delta : float):
        to_del : list[UiDrawable] = []

        for sprite in self.elements:
            sprite.update(delta)
            if sprite._zombie:
                to_del.append(sprite)
        for sprite in to_del:
            self.elements.remove(sprite)
            if sprite in self.complete_list:
                self.complete_list.remove(sprite)

        to_del.clear()

        for sprite in self.temp_elements:
            sprite.update(delta)
            if self.temp_elements[sprite].isover() or sprite._zombie: to_del.append(sprite)
        for sprite in to_del:
            self.temp_elements.pop(sprite)
            if sprite in self.complete_list: self.complete_list.remove(sprite)

    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            drawables : list[UiDrawable] = self.elements + list(self.temp_elements)
            clicked : list[UiDrawable] = UiDrawable.get_clicked(drawables, event.pos, do_unpack=True)
            for cliked_drawable in clicked:
                cliked_drawable.on_click(event)

    def handle_any_event(self, event : pygame.Event):
        for drawable in self.elements:
            if event.type in drawable.relevant_custom_events:
                drawable.handle_custom_event(event)

        for drawable in self.temp_elements:
            if event.type in drawable.relevant_custom_events:
                drawable.handle_custom_event(event)

    
    