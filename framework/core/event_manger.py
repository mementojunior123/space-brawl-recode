import pygame
from sys import exit
from typing import Callable, TypeAlias, Iterable

EventCallback : TypeAlias = Callable[[pygame.event.Event], None]

class EventManger:
    ANY_EVENT = pygame.event.custom_type()
    def __init__(self) -> None:
        self.bound_actions : dict[int, list[EventCallback]] = {pygame.QUIT : [self.close_game], self.ANY_EVENT : []}
    
    def close_game(self, event):
        pygame.quit()
        exit()
    
    def bind(self, event_type : int, actions_arg : Iterable[EventCallback]|EventCallback, duplicate = False):
        '''The action parameter must be a function or list of functions that accepts exactly one pygame.Event argument. 
        Returns False if the action fails to bind.'''
        actions : list[EventCallback]
        if not isinstance(actions_arg, Iterable):
            actions : list[EventCallback] = [actions_arg]
        else:
            actions = list(actions_arg)

        if event_type == pygame.QUIT:
            return False
        
        if (event_type in self.bound_actions):
            for action in actions:
                if action not in self.bound_actions[event_type] or duplicate is True:
                    self.bound_actions[event_type].append(action)
        else:
            self.bound_actions[event_type] = actions
        
        return True

    def unbind(self, event_type : int, target_actions_arg : Iterable[EventCallback]|EventCallback):
        '''Returns False if event_type or target_actions is not found.'''
        target_actions : list[EventCallback]
        if not isinstance(target_actions_arg, Iterable):
            target_actions = [target_actions_arg]
        else:
            target_actions = list(target_actions_arg)
        
        if event_type == pygame.QUIT:
            return False

        if event_type not in self.bound_actions:
            return False
        
        for action in target_actions:
            if action in self.bound_actions[event_type]:
                self.bound_actions[event_type].remove(action)
                
        return True
    
    def unbind_all(self, event_type : int):
        if event_type == pygame.QUIT:
            return False

        if event_type not in self.bound_actions:
            return False
        
        self.bound_actions.pop(event_type)
        return True
    
    def process_event(self, event : pygame.Event):
        if event.type in self.bound_actions:
            for callback in self.bound_actions[event.type]:
                callback(event)
        for callback in self.bound_actions[self.ANY_EVENT]:
            callback(event)
