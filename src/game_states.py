import pygame
from typing import Any, Generator
from math import floor, sin, pi
from random import shuffle, choice
import random
import framework.game.coroutine_scripts
from framework.game.coroutine_scripts import CoroutineScript
import framework.utils.tween_module as TweenModule
from framework.ui import TextSprite, BaseDrawableInfo, TextSpriteInfo, UiPosition, TextStyle
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer, TimeSource
from framework.game.sprite import Sprite
from framework.utils.helpers import average, random_float
from framework.ui import BrightnessOverlay
from framework.utils.base_particle_effects import ParticleEffect

class GameState:
    def __init__(self, game_object : 'Game'):
        self.game = game_object

    def main_logic(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def handle_key_event(self, event : pygame.Event):
        pass

    def handle_mouse_event(self, event : pygame.Event):
        pass

    def cleanup(self):
        pass

class NormalGameState(GameState):
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        
        pause_ui1 = BrightnessOverlay(BaseDrawableInfo(UiPosition((0, 0), 'topleft'), name='pause_overlay', zindex=9999), window_size, -60)
        pause_ui2 = TextSprite(BaseDrawableInfo(UiPosition(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center'), name='pause_text', zindex=1000),
                               TextSpriteInfo('Paused', TextStyle(self.game.font_70, 'White', False, 'Black', 2, colorkey=(0, 255, 0))))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game, self)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.pause()

class NetworkTestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False) #type: ignore
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : NetworkTestPattern = NetworkTestPattern()
        host_arg : str = "true" if pygame.key.get_pressed()[pygame.K_f] else "false"
        core_object.log("Hosting : ", host_arg.capitalize())
        peer_id : str = "fsafgasg12345abcsss5"
        self.network_key : str = "tmp_" + peer_id + host_arg
        core_object.networker.create_peer(peer_id, host_arg, self.network_key)
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        self.test_pattern.initialize(self.game.game_timer.get_time, self.network_key)
        

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            self.game.alert_player(f"Received data {event.data}")
            core_object.log(f"pygame : Received data {event.data}")
        elif event.type == core_object.networker.NETWORK_ERROR_EVENT:
            self.game.alert_player(f"Network error occured : {event.info}")
            core_object.log(f"pygame : Network error occured : {event.info}")
        elif event.type == core_object.networker.NETWORK_CLOSE_EVENT:
            self.game.alert_player("Network connection closed")
            core_object.log(f"pygame : Network connection closed")
        elif event.type == core_object.networker.NETWORK_DISCONNECT_EVENT:
            self.game.alert_player("Network disconnected")
            core_object.log("pygame : Network disconnected")
        elif event.type == core_object.networker.NETWORK_CONNECTION_EVENT:
            self.game.alert_player("Network connected")
            core_object.log("pygame : Network connected")

class NetworkTestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource, net_key : str):
        return super().initialize(time_source, net_key)
    
    @staticmethod
    def corou(time_source : TimeSource, net_key : str) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50

        new_textsprite : TextSprite = TextSprite(BaseDrawableInfo(UiPosition((480, 10), 'midtop'), name="Progress"),
                                                  TextSpriteInfo("Waiting...", TextStyle(textsprite_font, "White", False, "Black", 2, colorkey=(0, 255, 0))))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        core_object.networker.send_network_message("DONE!!!", net_key)
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

class NetworkWaitingGameState(GameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.is_host : bool = True if pygame.key.get_pressed()[pygame.K_f] else False
        host_arg : str = "true" if self.is_host else "false"
        core_object.log("Hosting :", host_arg.capitalize())
        self.peer_id : str = "fsaffnaf_2players"
        self.network_key : str = "tmp_" + self.peer_id + host_arg
        core_object.networker.create_peer(self.peer_id, host_arg, self.network_key, debug_level=1)
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        self.ui_message : TextSprite = TextSprite(BaseDrawableInfo(UiPosition((480, 10), 'midtop'), name="waiting_message"),
                                                    TextSpriteInfo(f"Waiting for connection...\nHosting: {host_arg.capitalize()}\nPeer id: {self.peer_id}", 
                                                                TextStyle(self.game.font_40, "White", False, "Black", 2, colorkey=(0, 255, 0))))
        core_object.main_ui.add(self.ui_message)
        

    def main_logic(self, delta : float):
        pass

    def transition_to_play(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.main_ui.remove(self.ui_message)
        self.game.state = Network2PlayerTestGameState(self.game, self.network_key, self.peer_id, self.is_host)
    
    def cleanup(self):
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            #self.game.alert_player(f"Received data {event.data}")
            #core_object.log(f"pygame : Received data {event.data}")
            if event.data == "hello":
                self.transition_to_play()
        elif event.type == core_object.networker.NETWORK_ERROR_EVENT:
            self.game.alert_player(f"Network error occured : {event.info}")
            core_object.log(f"pygame : Network error occured : {event.info}")
        elif event.type == core_object.networker.NETWORK_CLOSE_EVENT:
            self.game.alert_player("Network connection closed")
            core_object.log(f"pygame : Network connection closed")
        elif event.type == core_object.networker.NETWORK_DISCONNECT_EVENT:
            self.game.alert_player("Network disconnected")
            core_object.log("pygame : Network disconnected")
        elif event.type == core_object.networker.NETWORK_CONNECTION_EVENT:
            self.game.alert_player("Network connected")
            core_object.log("pygame : Network connected")
            if not self.is_host:
                core_object.networker.send_network_message("hello", self.network_key)
                self.transition_to_play()

class Network2PlayerTestGameState(NormalGameState):
    def __init__(self, game_object : 'Game', network_key : str, peer_id : str, is_host : bool):
        self.game = game_object
        self.ping_timer : Timer = Timer(1, core_object.game.game_timer.get_time)
        host_pos, client_pos = pygame.Vector2(200, 100), pygame.Vector2(760, 440)
        host_color, client_color = "Red", "Blue"
        
        this_pos, other_pos = (host_pos, client_pos) if is_host else (client_pos, host_pos)
        this_color, other_color = (host_color, client_color) if is_host else (client_color, host_color)

        self.player : NetworkTestPlayer = NetworkTestPlayer.spawn(this_pos, is_host, this_color)
        self.other_player : NetworkSyncTestPlayer = NetworkSyncTestPlayer.spawn(other_pos, not is_host, other_color)
        core_object.log("Hosting:", str(is_host))
        src.sprites.test_player.make_connections()
        self.is_host : bool = is_host
        self.network_key : str = network_key
        self.peer_id : str = peer_id
        self.recent_messages : list[str] = []
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        

    def main_logic(self, delta : float):
        if self.ping_timer.isover():
            self.ping_timer.restart()
            core_object.networker.send_network_message("!!!ping!!!", self.network_key)

        for message in self.recent_messages:
            if self.is_host:
                self.parse_and_react_as_host(message)
            else:
                self.parse_and_react_as_client(message)
        self.recent_messages.clear()

        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
        if self.is_host:
            core_object.networker.send_network_message(
                  f"{self.player.x};{self.player.y};{self.player.angle};" 
                + f"{self.other_player.x};{self.other_player.y};{self.other_player.angle}", self.network_key
            )
        else:
            if self.player.attempted_move or self.player.attempted_rotate:
                core_object.networker.send_network_message(
                    f"{self.player.attempted_move.x};{self.player.attempted_move.y};{self.player.attempted_rotate};{delta}", self.network_key
                )
        
    
    def parse_and_react_as_host(self, data : str):
        args = data.split(";")
        if not (len(args) == 4):
            return
        self.other_player.sync_other_is_client(pygame.Vector2(float(args[0]), float(args[1])), float(args[2]), float(args[3]))
    
    def parse_and_react_as_client(self, data : str):
        args = data.split(";")
        if not (len(args) == 6):
            return
        self.other_player.sync_other_is_host(pygame.Vector2(float(args[0]), float(args[1])), float(args[2]))
        sync_position : pygame.Vector2 = pygame.Vector2(float(args[3]), float(args[4]))
        sync_angle : float = float(args[5])
        if (self.player.position - sync_position).magnitude() > 2:
            self.player.position = sync_position
        if abs(self.player.angle - sync_angle) > 2:
            self.player.angle = sync_angle
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        core_object.networker.destroy_peer(self.network_key)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            ...
            #self.game.alert_player(f"Received data {event.data}")
            #core_object.log(f"pygame : Received data {event.data}")
            self.recent_messages.append(event.data)
        elif event.type == core_object.networker.NETWORK_ERROR_EVENT:
            self.game.alert_player(f"Network error occured : {event.info}")
            core_object.log(f"pygame : Network error occured : {event.info}")
        elif event.type == core_object.networker.NETWORK_CLOSE_EVENT:
            self.game.alert_player("Network connection closed")
            core_object.log(f"pygame : Network connection closed")
        elif event.type == core_object.networker.NETWORK_DISCONNECT_EVENT:
            self.game.alert_player("Network disconnected")
            core_object.log("pygame : Network disconnected")
        elif event.type == core_object.networker.NETWORK_CONNECTION_EVENT:
            self.game.alert_player("Network connected")
            core_object.log("pygame : Network connected")
    
    def handle_key_event(self, event : pygame.Event):
        pass


class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False) #type: ignore
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : TestPattern = TestPattern()
        self.test_pattern.initialize(self.game.game_timer.get_time)
        core_object.bg_manager.play('test_music', 1.0)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        core_object.bg_manager.stop_all_music()
        core_object.bg_manager.play_sfx('test_sfx', 1.0)

class TestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50
        new_textsprite : TextSprite = TextSprite(BaseDrawableInfo(UiPosition((480, 10), 'midtop'), name="Progress"),
                                                  TextSpriteInfo("Waiting...", TextStyle(textsprite_font, "White", False, "Black", 2, colorkey=(0, 255, 0))))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            new_color = pygame.Color((c_off := round(pygame.math.lerp(255, 0, percentage / 100))), c_off, 255)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.style.text_color = new_color
            #new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

class PausedGameState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState):
        super().__init__(game_object)
        self.previous_state = previous
    
    def unpause(self):
        if not self.game.active: return
        self.game.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.game.state = self.previous_state

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.unpause()

def runtime_imports():
    global Game
    from framework.game.game_module import Game
    global core_object
    from framework.core.core import core_object

    #runtime imports for game classes
    global src
    global TestPlayer, NetworkTestPlayer, NetworkSyncTestPlayer
    import src.sprites.test_player
    from src.sprites.test_player import TestPlayer, NetworkTestPlayer, NetworkSyncTestPlayer


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    NetworkTestGameState = NetworkTestGameState
    PausedGameState = PausedGameState
    NetworkWaitingGameState = NetworkWaitingGameState
    Network2PlayerTestGameState = Network2PlayerTestGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    if event.mode == 'test' and (False):
        game_object.state = NetworkWaitingGameState(game_object)
    elif True:
        game_object.state = TestGameState(game_object)
    else:
        game_object.state = NetworkTestGameState(game_object)
