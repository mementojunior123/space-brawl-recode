import pygame
from .ui_position import AnyUiPosition, UiPosition

from framework.utils.helpers import AnchorStr

from typing import Literal, TypeAlias, overload, Iterable, Any, Callable
from dataclasses import dataclass
import dataclasses

TransformedRect : TypeAlias = dict[Literal['topleft', 'topright', 'bottomright', 'bottomleft'], pygame.Vector2]
CustomEventCallback : TypeAlias = Callable[["UiDrawable", pygame.Event], None]

@dataclass
class BaseDrawableInfo:
    position : AnyUiPosition
    parent : "UiSpriteGroup|None" = None
    name : str|None = None
    tag : int = 0
    start_visible : bool = True
    zindex : int = 0
    data : Any = None

    relevant_events : Iterable[int] = tuple()
    custom_event_handlers : Iterable[CustomEventCallback] = tuple()
    fire_tag_events : bool = True
    obstructs_cliks : bool = True

    angle : float = 0
    scale : float|pygame.typing.Point = 1
    opacity : float = 1

    final_anchor : AnchorStr|pygame.typing.Point|None = None

    def __post_init__(self):
        ...

class UiDrawable:
    TAG_EVENT : int = pygame.event.custom_type()
    @staticmethod
    def unpack_drawable_list(drawables : list["UiDrawable"]) -> list["UiDrawable"]:
        result : list[UiDrawable] = []
        for drawable in drawables:
            if drawable.unpack and isinstance(drawable, UiSpriteGroup):
                result.extend(drawable.elements)
            else:
                result.append(drawable)
        result.sort(key=lambda d : d.zindex)
        return result

    @staticmethod
    def get_clicked(drawables : list["UiDrawable"], click_pos : pygame.typing.Point, 
                    do_unpack : bool = False, do_sort : bool = False) -> list["UiDrawable"]:
        if do_unpack:
            drawables = UiDrawable.unpack_drawable_list(drawables)
        elif do_sort:
            drawables.sort(key=lambda d : d.zindex)
        result = []
        for drawable in reversed(drawables):
            if drawable.collidepoint(click_pos):
                result.append(drawable)
                if drawable.obstructs_clicks:
                    break
        return result

    @staticmethod
    def get_draw_rect_from_transformed(transformed_rect : TransformedRect):
        min_x = min(val.x for val in transformed_rect.values())
        max_x = max(val.x for val in transformed_rect.values())
        min_y = min(val.y for val in transformed_rect.values())
        max_y = max(val.y for val in transformed_rect.values())
        return pygame.Rect((round(min_x), round(min_y)), (round(max_x - min_x), round(max_y - min_y)))

    def __init__(self, info : BaseDrawableInfo):
        self.position : AnyUiPosition = info.position
        self.name : str|None = info.name
        self.tag : int = info.tag
        self.visible : bool = info.start_visible
        self.unpack : bool = False
        self._parent : "UiSpriteGroup|None" = info.parent
        self.zindex : int = info.zindex
        self.data : Any = info.data

        self._relevant_custom_events : set[int] = set(info.relevant_events)
        self._custom_event_handlers : list[CustomEventCallback] = list(info.custom_event_handlers)
        self.do_fire_tag_events : bool = info.fire_tag_events
        self.obstructs_clicks : bool = info.obstructs_cliks

        self._angle : float = info.angle
        self._scale : pygame.Vector2 = pygame.Vector2((info.scale, info.scale) if isinstance(info.scale, (float, int)) else info.scale)
        self._opacity : float = info.opacity
        self._zombie : bool = False

    @property
    def relevant_custom_events(self) -> set[int]:
        return self._relevant_custom_events

    @relevant_custom_events.setter
    def relevant_custom_events(self, new_val : Iterable[int]):
        self._relevant_custom_events = set(new_val)

    @property
    def size(self) -> pygame.Vector2:
        raise NotImplementedError

    @property
    def parent(self) -> "UiSpriteGroup|None":
        return self._parent

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, new_value : float):
        if new_value != self._angle:
            self._angle = new_value
            self._render()
            self._trigger_parent_frame_update()

    @property
    def scale(self) -> pygame.Vector2:
        return self._scale

    @scale.setter
    def scale(self, new_value : float|pygame.typing.Point):
        if isinstance(new_value, (float, int)):
            new_value = pygame.Vector2(new_value, new_value)
        elif not isinstance(new_value, pygame.Vector2):
            new_value = pygame.Vector2(new_value)
        if new_value != self._scale:
            self._scale = new_value
            self._render()
            self._trigger_parent_frame_update()

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, new_value : float):
        if new_value != self._opacity:
            self._opacity = new_value
            self._render()
            self._trigger_parent_frame_update(False)

    @property
    def is_zombie(self) -> bool:
        return self._zombie

    def delete(self):
        if self.parent is None:
            return
        self.parent.remove(self)
        self._zombie = True

    def change_parent_to(self, parent : "UiSpriteGroup"):
        if self.parent:
            self.parent.remove(self)
        parent.add(self)

    def change_anchor(self, new_anchor : AnchorStr|pygame.typing.Point):
        self.position = UiPosition(self.position.calculate_anchor(self.size, new_anchor, self._angle), new_anchor)

    def get_layout_parent(self) -> "BaseLayout|None":
        current_ancestor : UiSpriteGroup|None = self.parent
        while isinstance(current_ancestor, UiDrawable) and not isinstance(current_ancestor, BaseLayout):
            current_ancestor = current_ancestor.parent
        return current_ancestor

    def get_frame_parent(self) -> "UiFrame|None":
        current_ancestor : UiSpriteGroup|None = self.parent
        while isinstance(current_ancestor, UiDrawable) and not isinstance(current_ancestor, UiFrame):
            current_ancestor = current_ancestor.parent
        return current_ancestor

    def get_frame_ancestors(self, stop : "UiFrame|None" = None) -> list["UiFrame"]|None:
        """Note : If stop is not in the ancestor list, None is returned instead."""
        current_frame : UiFrame|None = self.get_frame_parent()
        ancestor_list : list[UiFrame] = []
        while current_frame is not None:
            ancestor_list.append(current_frame)
            if current_frame == stop and stop is not None:
                return ancestor_list
            current_frame = current_frame.get_frame_parent()
        if stop is not None and stop not in ancestor_list:
            return None
        return ancestor_list

    def get_true_angle(self, local_override : TransformedRect|None = None) -> float:
        result : float
        if local_override is None:
            result = self._angle
        else:
            result = (local_override['topright'] - local_override['topleft']).angle_to(pygame.Vector2(1, 0))
        current_sprite = self
        while (current_sprite := current_sprite.parent) is not None:
            if (isinstance(current_sprite, UiFrame)) and current_sprite.do_clip:
                break
            result += current_sprite.angle
        return result

    def get_true_scale(self, local_override : TransformedRect|None = None) -> pygame.Vector2:
        result : pygame.Vector2
        if local_override is None:
            result = self._scale
        else:
            size : pygame.Vector2 = self.size
            result = pygame.Vector2((local_override['topright'] - local_override['topleft']).magnitude() / size.x, 
                                    (local_override['bottomleft'] - local_override['topleft']).magnitude() / size.y)
        current_sprite = self
        while (current_sprite := current_sprite.parent) is not None:
            if (isinstance(current_sprite, UiFrame)) and current_sprite.do_clip:
                break
            result *= current_sprite.scale.elementwise()
        return result

    def get_true_opacity(self) -> float:
        result : float = self._opacity
        current_sprite = self
        while (current_sprite := current_sprite.parent) is not None:
            if (isinstance(current_sprite, UiFrame)) and current_sprite.do_clip:
                break
            result *= current_sprite.opacity
        return result
    
    def get_local_rotoscaled_rect(self, use_parent_layout : bool = False) -> TransformedRect:
        raise NotImplementedError

    def get_world_rotoscaled_rect(self, frame : "UiFrame|None" = None, override_local_rect : TransformedRect|None = None,
                                  use_parent_layout : bool = False) -> TransformedRect|None:
        """Note : If frame is given and not an ancestor, None is returned.
        If None is passed in as a frame, gets window pos"""
        raise NotImplementedError
    
    def get_local_draw_rect(self, use_parent_layout : bool = False) -> pygame.Rect:
        raise NotImplementedError

    @overload
    def get_world_draw_rect(self, frame : None = None,
                                  use_parent_layout : bool = False) -> pygame.Rect: ...
    @overload
    def get_world_draw_rect(self, frame : "UiFrame",
                                  use_parent_layout : bool = False) -> pygame.Rect|None: ...
    
    def get_world_draw_rect(self, frame : "UiFrame|None" = None,
                                  use_parent_layout : bool = False) -> pygame.Rect|None:
        """Note : If frame is given and not an ancestor, None is returned.
                If None is passed in as a frame, gets window pos"""
        raise NotImplementedError

    def collidepoint(self, point : pygame.typing.Point):
        return self.get_world_draw_rect().collidepoint(point)

    def add_custom_event_handler(self, custom_event_handler : CustomEventCallback):
        if custom_event_handler not in self._custom_event_handlers:
            self._custom_event_handlers.append(custom_event_handler)

    def remove_custom_event_handler(self, custom_event_handler : CustomEventCallback):
        if custom_event_handler in self._custom_event_handlers:
            self._custom_event_handlers.remove(custom_event_handler)

    def clear_custom_event_handlers(self):
        self._custom_event_handlers.clear()

    def _trigger_parent_frame_update(self, do_update_layout : bool = True):
        if frame_parent := self.get_frame_parent():
            frame_parent.on_child_update(do_update_layout)

    def calculate_overriden_draw_pos(self, local_override : TransformedRect|None = None, frame : "UiFrame|None" = None) -> pygame.Rect|None:
        tranfs_rect : TransformedRect|None = local_override if frame is None else self.get_world_rotoscaled_rect(frame, local_override)
        if tranfs_rect is None:
            return None
        return UiDrawable.get_draw_rect_from_transformed(tranfs_rect)

    def calculate_draw_rect(self, override_pos_global : pygame.Rect|None, override_pos_local: TransformedRect|None = None,
                            frame : "UiFrame|None" = None) -> pygame.Rect|None:
        draw_rect : pygame.Rect|None
        if override_pos_global is not None:
            draw_rect = override_pos_global
        elif override_pos_local is not None:
            draw_rect = self.calculate_overriden_draw_pos(override_pos_local, frame)
        else:

            draw_rect = self.get_local_draw_rect() if frame is None else self.get_world_draw_rect(frame)
        if draw_rect is None:
            return None
        return draw_rect

    def draw(self, display : pygame.Surface, frame : "UiFrame|None" = None, 
             override_pos_local: TransformedRect|None = None, override_pos_global : pygame.Rect|None = None):
        """
        When frame is None: draw at local pos
        when frame is not None: convert from local to frame world pos, then draw
        Note : If the frame passed in is not an ancestor of this item, it will be ignored.
        Note 2 : The frame passed in must be the first frame in the hierarchy after the draw target

        """
        raise NotImplementedError

    def _render(self):
        raise NotImplementedError
    
    def update(self, delta : float):
        pass

    def on_click(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.do_fire_tag_events:
                pygame.event.post(pygame.Event(UiDrawable.TAG_EVENT, 
                {"tag" : self.tag, "name" : self.name, 'trigger_type' : 'click', 'trigger_event' : event}))

    def handle_custom_event(self, event : pygame.Event):
        for event_handler in self._custom_event_handlers:
            event_handler(self, event)

class UiSpriteGroup(UiDrawable):
    def __init__(self, base_drawable_info : BaseDrawableInfo, elements : list[UiDrawable]):
        super().__init__(base_drawable_info)
        self.elements : list[UiDrawable] = [element for element in elements]
        for element in self.elements:
            if element.parent != self and element.parent:
                if element in element.parent.elements: element.parent.remove(element)
            element._parent = self

    @property
    def relevant_custom_events(self) -> set[int]:
        sets_to_merge : list[set[int]] = [element.relevant_custom_events for element in self.elements]
        result : set[int] = self._relevant_custom_events
        for set_to_merge in sets_to_merge:
            result |= set_to_merge
        return result
    
    @relevant_custom_events.setter
    def relevant_custom_events(self, new_val : Iterable[int]):
        self._relevant_custom_events = set(new_val)

    @property
    def size(self) -> pygame.Vector2:
        return pygame.Vector2(self.get_local_draw_rect().size)

    @staticmethod
    def does_match(target : UiDrawable, drawable : UiDrawable|None, name : str|None, tag : int|None,
                   match_all : bool) -> bool:
        if drawable is None and name is None and tag is None:
            return False
        if not match_all:
            return target == drawable or target.name == name or target.tag == tag
        else:
            if target != drawable and drawable is not None:
                return False
            elif target.name != name and name is not None:
                return False
            elif target.tag != tag and tag is not None:
                return False
            return True


    def search_children(self, drawable : UiDrawable|None = None, name : str|None = None, tag : int|None = None,
                        match_all : bool = False) -> UiDrawable|None:
        if drawable is None and name is None and tag is None:
            return None
        for child in self.elements:
            if self.does_match(child, drawable, name, tag, match_all):
                return child
        return None

    def search_children_multiple(self, drawable : UiDrawable|None = None, name : str|None = None, tag : int|None = None,
                        match_all : bool = False) -> list[UiDrawable]:
        result : list[UiDrawable] = []
        if drawable is None and name is None and tag is None:
            return result
        for child in self.elements:
            if self.does_match(child, drawable, name, tag, match_all):
                result.append(child)
        return result

    def search_descendants(self, drawable : UiDrawable|None = None, name : str|None = None, tag : int|None = None,
                        match_all : bool = False) -> UiDrawable|None:
        if drawable is None and name is None and tag is None:
            return None
        for child in self.elements:
            if self.does_match(child, drawable, name, tag, match_all):
                return child
            elif isinstance(child, UiSpriteGroup) and (child_result := child.search_descendants(drawable, name, tag, match_all)):
                return child_result
        return None

    def search_descendants_multiple(self, drawable : UiDrawable|None = None, name : str|None = None, tag : int|None = None,
                            match_all : bool = False) -> list[UiDrawable]:
        result : list[UiDrawable] = []
        if drawable is None and name is None and tag is None:
            return result
        for child in self.elements:
            if self.does_match(child, drawable, name, tag, match_all):
                result.append(child)
            if isinstance(child, UiSpriteGroup) and (child_result := child.search_descendants_multiple(drawable, name, tag, match_all)):
                result.extend(child_result)
        return result

    def get_local_rotoscaled_rect(self, use_parent_layout : bool = False) -> TransformedRect:
        local_draw_rect : pygame.Rect = self.get_local_draw_rect(use_parent_layout=use_parent_layout)
        return {'topleft' : pygame.Vector2(local_draw_rect.topleft), 'topright' : pygame.Vector2(local_draw_rect.topright),
                'bottomleft' : pygame.Vector2(local_draw_rect.bottomleft), 'bottomright' : pygame.Vector2(local_draw_rect.bottomright)}
    
    def get_local_draw_rect(self, use_parent_layout : bool = False) -> pygame.Rect:
        if not self.elements:
            return pygame.Rect(0, 0, 0, 0)
        return (self.elements[0].get_local_draw_rect(use_parent_layout=use_parent_layout)
                .unionall([e.get_local_draw_rect(use_parent_layout=use_parent_layout) for e in self.elements if e != self.elements[0]])
                )
    @overload
    def get_world_draw_rect(self, frame : None = None, use_parent_layout : bool = False) -> pygame.Rect: ...
    @overload
    def get_world_draw_rect(self, frame : "UiFrame", use_parent_layout : bool = False) -> pygame.Rect|None: ...
    def get_world_draw_rect(self, frame : "UiFrame|None" = None, use_parent_layout : bool = False) -> pygame.Rect|None:
        if not self.elements:
            return pygame.Rect(self.position.x, self.position.y, 0, 0)
        if self.get_frame_ancestors(frame) is None:
            return None
        children_rect : list[pygame.Rect] = []
        for element in self.elements:
            val : pygame.Rect|None = element.get_world_draw_rect(frame, use_parent_layout=use_parent_layout)
            if val is not None:
                children_rect.append(val)
        return children_rect[0].unionall(children_rect[1:])

    def get_world_rotoscaled_rect(self, frame : "UiFrame|None" = None, override_local_rect : TransformedRect|None = None, 
                                  use_parent_layout : bool = False) -> TransformedRect|None:
        world_draw_rect : pygame.Rect|None = self.get_world_draw_rect(frame, use_parent_layout=use_parent_layout)
        if world_draw_rect is None:
            return None
        return {'topleft' : pygame.Vector2(world_draw_rect.topleft), 'topright' : pygame.Vector2(world_draw_rect.topright),
                'bottomleft' : pygame.Vector2(world_draw_rect.bottomleft), 'bottomright' : pygame.Vector2(world_draw_rect.bottomright)}
        
    
    def draw(self, display : pygame.Surface, frame : "UiFrame|None" = None, 
             override_pos_local: TransformedRect|None = None, override_pos_global : pygame.Rect|None = None):
        if not self.visible:
            return
        self.elements.sort(key = lambda d : d.zindex)
        for element in self.elements:
            element.draw(display, frame)

    def _render(self):
        for element in self.elements:
            element._render()

    def update(self, delta : float):
        for element in self.elements:
            element.update(delta)
    
    def on_click(self, event : pygame.Event):
        super().on_click(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for element in self.elements:
                if element.collidepoint(event.pos):
                    element.on_click(event)

    def handle_custom_event(self, event : pygame.Event):
        super().handle_custom_event(event)
        for element in self.elements:
            if event.type in element.relevant_custom_events:
                element.handle_custom_event(event)
    
    def add(self, new_element : UiDrawable):
        if new_element not in self.elements:
            self.elements.append(new_element)
            new_element._parent = self

    def add_multiple(self, new_elements : Iterable[UiDrawable]):
        prev_element : UiDrawable|None = None
        for element in new_elements:
            if prev_element is not None:
                if prev_element not in self.elements:
                    self.elements.append(prev_element)
                    prev_element._parent = self
            prev_element = element
        if prev_element is None:
            return
        self.add(prev_element)

    def remove(self, element : UiDrawable):
        if element not in self.elements:
            raise ValueError("Element is not a chlid of this sprite group.")
        self.elements.remove(element)
        element._parent = None

    def __contains__(self, item):
        return item in self.elements

    def __getitem__(self, index : int):
        return self.elements[index]

    def __delitem__(self, index : int):
        val = self.elements[index]
        if isinstance(val, list):
            for v in val: self.remove(v)
            return
        self.remove(val)

def local_imports2():
    global UiFrame
    from .ui_frame import UiFrame
    global BaseLayout
    from .layouts.base_layout import BaseLayout