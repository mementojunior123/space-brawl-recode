import pygame
from typing import Any, Generator, cast
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
            self.player = Player.spawn('midbottom', pygame.Vector2(480, 520))
            self.score = 0
            self.score_sprite = TextSprite(BaseDrawableInfo(UiPosition((15, 10), 'topleft'), name='score_sprite'), 
                                    TextSpriteInfo('Score : 0', TextStyle(self.game.font_50, 'White', False, 'Black', 2)))
            core_object.main_ui.add(self.score_sprite)
            self.score_sprite.position.y += 30 # TODO : Remove after debug
            self.curr_wave = 1
            core_object.bg_manager.play('main_theme', 1) # TODO : Make sure music is handled properly in the future
        else:
            self.player = prev.player
            self.score = prev.prev_state.score
            self.score_sprite = prev.prev_state.score_sprite
            self.curr_wave = prev.prev_state.curr_wave + 1
            prev.prev_state.deactivate()

        self.control_script : WaveControlScript = WaveControlScript()
        self.control_script.initialize(core_object.game_tsource or Timer.base_time_source)

        self.game.alert_player(f'Wave {self.curr_wave} start')
        self.make_connections()

    def main_logic(self, delta : float):
        super().main_logic(delta)
        if self.player.current_hp <= 0:
            self.transition_to_gameover("Game over!")
        result = self.control_script.process_frame(delta)
        if result == 'Done':
            self.transition_to_shop()
        

    def transition_to_shop(self):
        core_object.game.state = ShopGameState(self.game, self)

    def transition_to_gameover(self, message : str):
        self.deactivate()
        core_object.game.state = GameOverGameState(self.game, message, self)
 
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
        while len(BaseEnemy.active_elements) > 0:
            delta = yield
        return 'Done'
    
class ShopGameState(NormalGameState):
    def __init__(self, game_object : 'Game', prev : 'ActiveWaveGameState'):
        self.game : Game = game_object
        self.player : Player = prev.player
        self.prev_state : ActiveWaveGameState = prev

        self.test_timer : Timer = Timer(2, core_object.game_tsource)

        self.game.alert_player("The shop has not been implemented yet...")
        core_object.log(self.select_upgrades())

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

    def select_upgrades(self, amount : int = 3, target_tier : int = 1, rarity_bonus_tier : int = 0) -> list[tuple['UpgradeName', int]]:
        wave_num : int = self.prev_state.curr_wave
        type_distribution : dict[UpgradeType, int] = {upgrade_type : 0 for upgrade_type in UpgradeType}
        random_list : list[int] = [random.randint(1, 1000) for _ in range(amount)]
        guaranteed : dict[UpgradeType, int]
        random_given : list[UpgradeType]
        match wave_num % 10:
            case 1|2|4:
                guaranteed = {UpgradeType.MINOR : 1}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 100 
                    else UpgradeType.ABILITY if random_list[i] <= 200
                    else UpgradeType.MAJOR if random_list[i] <= 300
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 3:
                guaranteed = {}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 100 
                    else UpgradeType.ABILITY if random_list[i] <= 200
                    else UpgradeType.MAJOR if random_list[i] <= 360
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 5:
                guaranteed = {UpgradeType.MINOR : 2}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 400 
                    else UpgradeType.ABILITY if random_list[i] <= 600
                    else UpgradeType.MAJOR if random_list[i] <= 1000
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 6|7|9:
                guaranteed = {UpgradeType.MINOR : 1}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 120 
                    else UpgradeType.ABILITY if random_list[i] <= 240
                    else UpgradeType.MAJOR if random_list[i] <= 360
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 8:
                guaranteed = {}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 120 
                    else UpgradeType.ABILITY if random_list[i] <= 220
                    else UpgradeType.MAJOR if random_list[i] <= 440
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 0:
                guaranteed = {UpgradeType.SECONDARY_FIRE : 2}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 400 
                    else UpgradeType.ABILITY if random_list[i] <= 600
                    else UpgradeType.MAJOR if random_list[i] <= 1000
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case _:
                guaranteed = {}
                random_given = []
        for upgrade_type in UpgradeType:
            type_distribution[upgrade_type] += random_given.count(upgrade_type)
            if upgrade_type in guaranteed:
                type_distribution[upgrade_type] += guaranteed[upgrade_type]
        print(type_distribution, "#1")

        selected : list[tuple[UpgradeName, int]] = []

        if (type_distribution[UpgradeType.SECONDARY_FIRE] > 0
            and self.player.upgrades.curr_alt_fire.rank < src.upgrades.MAX_RANK[self.player.upgrades.curr_alt_fire.name]
            and random.random() <= 1):

            type_distribution[UpgradeType.SECONDARY_FIRE] -= 1
            selected.append((self.player.upgrades.curr_alt_fire.name, self.player.upgrades.curr_alt_fire.rank + 1))

        if (type_distribution[UpgradeType.ABILITY] > 0
            and self.player.upgrades.curr_ability.rank < src.upgrades.MAX_RANK[self.player.upgrades.curr_ability.name]
            and random.random() <= 0.5):

            type_distribution[UpgradeType.ABILITY] -= 1
            selected.append((self.player.upgrades.curr_ability.name, self.player.upgrades.curr_ability.rank + 1))

        for _ in range(type_distribution[UpgradeType.PERK]):
            if random.random() <= 0.5:
                eligible_existing_perks : list[tuple[UpgradeName, int]] = [
                    (perk.name, perk.rank + 1) for perk in 
                    filter(lambda p : p.rank < src.upgrades.MAX_RANK[p.name], self.player.upgrades.curr_perks)
                ]
                if not eligible_existing_perks:
                    break
                selected.append(random.choice(eligible_existing_perks))
                type_distribution[UpgradeType.PERK] -= 1

        for upgrade_type in type_distribution:
            for _ in range(type_distribution[upgrade_type]):
                result = self.select_random_upgrade_of_type(upgrade_type, target_tier, rarity_bonus_tier, 
                                                                   [s[0] for s in selected])
                if result is None:
                    result = self.select_random_upgrade_of_type(UpgradeType.MINOR, target_tier, rarity_bonus_tier, 
                                                                   [s[0] for s in selected])
                    if result is None:
                        result = ('BonusNormalDamage', 1)
                        core_object.log(f'Failed to select an upgrade ({upgrade_type.value}, {target_tier}) --> using a fallback!')
                selected.append(result)

        return selected

    
    def select_random_upgrade_of_type(self, upgrade_type : 'UpgradeType', target_tier : int, 
                                      rarity_bonus_tier : int = 0,
                                      already_selected : list['UpgradeName']| None = None) -> tuple['UpgradeName', int]|None:
        if already_selected is None: already_selected = []
        eligible : list[UpgradeName] = Upgrade.get_list_of_all(upgrade_type)
        if upgrade_type in (UpgradeType.ABILITY, UpgradeType.PERK, UpgradeType.SECONDARY_FIRE): # getting upgrades you already have was already handled
            eligible = [x for x in filter(
                lambda name : all(upg.name != name and upg.name not in already_selected 
                                  for upg in self.player.upgrades.upgrades), eligible
            )]

        possibilites : dict[tuple[UpgradeName, int], float] = {}

        for upgrade_name, weight_info in src.upgrades.BASE_WEIGHTS.items():
            weight_set, ignore_rarity_tier = weight_info
            for rank, weight in weight_set.items():
                rarity_tier, individual_weight = weight

                result : float = individual_weight
                if not ignore_rarity_tier:
                    result *= self.calculate_rarity_tier_modifier(rarity_tier, target_tier, rarity_bonus_tier)
                if result <= 0:
                    continue
                possibilites[(upgrade_name, rank)] = result

        if not possibilites:
            return None

        final_result : list[tuple[UpgradeName, int]] = random.choices(list(possibilites.keys()), list(possibilites.values()), k=1)
        return final_result[0]

    @staticmethod
    def calculate_rarity_tier_modifier(actual_tier : int, target_tier : int, rarity_bonus_tier : int = 0) -> float:
        effective_tier : float = actual_tier
        tier_difference : float = target_tier - actual_tier
        if abs(tier_difference) > 1.5:
            return 0
        return pygame.math.clamp(-0.4 * tier_difference * tier_difference + 1, 0, 1) # Used desmos


    @staticmethod
    def combine_type_distribution_dicts(dicts : list[dict['UpgradeType', int]]) -> dict['UpgradeType', int]:
        result : dict[UpgradeType, int] = {}
        for d in dicts:
            for upgrade_type, value in d.items():
                if upgrade_type not in result:
                    result[upgrade_type] = value
                else:
                    result[upgrade_type] += value
        return result

    
class GameOverGameState(GameState):
    def __init__(self, game_object : "Game", text = "Game over!", prev_state : GameState|None = None): # TODO : Revamp this code at some point
        self.game : Game = game_object
        self.lost : bool = text == "Game over!"
        self.control_script : GameOverControlScript = GameOverControlScript()
        prev_player : Any = getattr(self.prev, 'player', None)
        if not isinstance(prev_player, Player):
            prev_player = Player.active_elements[0]    
        self.control_script.initialize(self.game.game_timer.get_time, self, prev_player)
        self.game.alert_player(text)
        core_object.bg_manager.stop_all_music()
        self.prev = prev_state

    def main_logic(self, delta : float):
        Particle.update_all(delta)
        self.control_script.process_frame(delta)
        if self.control_script.is_over:
            self.game.fire_gameover_event()

    def cleanup(self):
        if self.prev: self.prev.cleanup()

class GameOverControlScript(CoroutineScript[float, str|None]):
    def initialize(self, time_source : TimeSource, state : GameOverGameState, player : 'Player'):
        return super().initialize(time_source, state, player)
    
    @staticmethod
    def corou(time_source : TimeSource, state : GameOverGameState, player : 'Player'):
        timer : Timer = Timer(1, time_source)
        delta : float = yield
        if delta is None: delta = core_object.dt
        while not timer.isover():
            delta = yield
        if not state.lost:
            return "Done"
        timer.set_duration(2)
        core_object.bg_manager.play_sfx('enemy_killed_sfx', 1.0)
        player_death_effect : ParticleEffect = cast(ParticleEffect, ParticleEffect.load_effect('boss_killed'))
        player_death_effect.play(player.position, timer.get_time)
        player.kill_instance()
        while not timer.isover():
            delta = yield
        return "Done"


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

    core_object.asset_manager.load_sound("assets/audio/music/theme2_trimmed_good.ogg", 'main_theme', 0.2)
    core_object.asset_manager.load_sound("assets/audio/music/theme1.ogg", 'boss_theme', 0.2)

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

    global Upgrade, PlayerUpgrades, UpgradeType, UpgradeName
    from src.upgrades import Upgrade, PlayerUpgrades, UpgradeType, UpgradeName
    import src.upgrades
    src.upgrades.runtime_imports()


class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    PausedGameState = PausedGameState
    ActiveWaveGameState = ActiveWaveGameState
    ShopGameState = ShopGameState
    GameOverGameState = GameOverGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    game_object.state = ActiveWaveGameState(game_object)
