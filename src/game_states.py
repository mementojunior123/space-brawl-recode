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
from framework.utils.base_particle_effects import ParticleEffect, Particle

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
        Particle.update_all(delta)

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

SCORE_EVENT : int = pygame.event.custom_type()

class ActiveWaveGameState(NormalGameState):
    def __init__(self, game_object : 'Game', prev : 'ShopGameState|None' = None):
        self.game : Game = game_object
        self.player : Player
        self.score : int
        self.score_sprite : TextSprite
        self.curr_wave : int
        if prev is None:
            Background.spawn(540)
            Background.spawn(0)
            self.player = Player.spawn('midbottom', pygame.Vector2(480, 530))
            self.score = 0
            self.score_sprite = TextSprite(BaseDrawableInfo(UiPosition((15, 10), 'topleft'), name='score_sprite'), 
                                    TextSpriteInfo('Score : 0', TextStyle(self.game.font_50, 'White', False, 'White', 2)))
            self.curr_wave = 1
        else:
            self.player = prev.player
            self.score = prev.prev_state.score
            self.score_sprite = prev.prev_state.score_sprite
            self.curr_wave = prev.prev_state.curr_wave + 1
            prev.prev_state.deactivate()

        self.control_script : WaveControlScript = WaveControlScript()
        self.control_script.initialize(core_object.game_tsource or Timer.base_time_source)

        self.game.alert_player(f'Wave {self.curr_wave} start')

    def main_logic(self, delta : float):
        super().main_logic(delta)
        result = self.control_script.process_frame(delta)
        if result == 'Done':
            self.transition_to_shop()

    def transition_to_shop(self):
        core_object.game.state = ShopGameState(self.game, self)
 
    def on_score_event(self, event : pygame.Event):
        self.score += event.score
        self.score_sprite.text = f"Score : {self.score}"

    def make_connections(self):
        core_object.event_manager.bind(SCORE_EVENT, self.on_score_event)
        core_object.event_manager.bind(core_object.event_manager.ANY_EVENT, Player.receive_any_event)

    def remove_connections(self):
        core_object.event_manager.unbind(SCORE_EVENT, self.on_score_event)
        core_object.event_manager.unbind(core_object.event_manager.ANY_EVENT, Player.receive_any_event)

    def cleanup(self):
        self.deactivate()
        ...

    def deactivate(self):
        self.remove_connections()

class WaveControlScript(CoroutineScript[float, str|None]):
    def initialize(self, time_source : TimeSource, wave_data : dict|None = None):
        return super().initialize(time_source, wave_data)

    @staticmethod
    def corou(time_source : TimeSource, wave_data : dict|None = None):
        test_timer : Timer = Timer(2, time_source)
        test_timer.start_time -= 2
        delta = yield

        spawned : int = 0
        while spawned < 5:
            if test_timer.isover():
                BasicEnemy.spawn('midbottom', pygame.Vector2(random.randint(0 + 50, 960 - 50), -20))
                test_timer.restart()
                spawned += 1
            delta = yield
        return 'Done'
    
class ShopGameState(NormalGameState):
    def __init__(self, game_object : 'Game', prev : 'ActiveWaveGameState'):
        self.game : Game = game_object
        self.player : Player = prev.player
        self.prev_state : ActiveWaveGameState = prev

        self.test_timer : Timer = Timer(5, core_object.game_tsource)

        self.game.alert_player("The shop has not been implemented yet...")

    def main_logic(self, delta : float):
        super().main_logic(delta)
        if self.test_timer.isover():
            self.transition_to_wave()

    def transition_to_wave(self):
        core_object.game.state = ActiveWaveGameState(self.game, self)
        self.deactivate()
 
    def make_connections(self):
        pass

    def remove_connections(self):
        pass

    def cleanup(self):
        self.deactivate()
        self.prev_state.deactivate()
        ...
    
    def deactivate(self):
        self.remove_connections()


class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        Background.spawn(540)
        Background.spawn(0)
        Player.spawn('midbottom', pygame.Vector2(480, 530))
        BasicEnemy.spawn('midbottom', pygame.Vector2(480, -20))

    def main_logic(self, delta : float):
        super().main_logic(delta)
    
    def cleanup(self):
        pass

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

    global Background
    from src.sprites.background import Background
    import src.sprites.background

    global BaseProjectile
    from src.sprites.projectiles import BaseProjectile
    import src.sprites.projectiles
    src.sprites.projectiles.runtime_imports()

    global BaseEnemy, BasicEnemy
    from src.sprites.enemy import BaseEnemy, BasicEnemy
    import src.sprites.enemy
    src.sprites.enemy.runtime_imports()

    global Player
    from src.sprites.player import Player
    import src.sprites.player

    global Upgrade, PlayerUpgrades
    from src.upgrades import Upgrade, PlayerUpgrades
    import src.upgrades
    src.upgrades.runtime_imports()


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    PausedGameState = PausedGameState
    ActiveWaveGameState = ActiveWaveGameState
    ShopGameState = ShopGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    game_object.state = ActiveWaveGameState(game_object)
