import pygame
from typing import Any, Generator, cast, Literal, TypedDict
from math import floor, sin, pi
from random import shuffle, choice
import random
import framework.game.coroutine_scripts
from framework.game.coroutine_scripts import CoroutineScript
from framework.ui.ui_drawable import UiDrawable
import framework.utils.tween_module as TweenModule
from framework.ui import TextSprite, BaseDrawableInfo, TextSpriteInfo, UiPosition, TextStyle, UiFrame, BaseUiFrameInfo, UiSprite
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer, TimeSource
from framework.game.sprite import Sprite
from framework.utils.helpers import average, random_float, AnchorStr, AnchorNameList
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

class WaveDataDict(TypedDict):
    spawn_cooldown : float
    enemy_cooldown_penalty : float
    enemies : dict['EnemyType|BossType', int]
    bosses : list['BossType']

WAVES : dict[int, WaveDataDict] = {
    1 : {
        'spawn_cooldown' : 2.5,
        'enemy_cooldown_penalty' : 0.8,
        'enemies' : {'basic' : 3},
        'bosses' : []
    },

    2 : {
        'spawn_cooldown' : 2.4,
        'enemy_cooldown_penalty' : 0.8,
        'enemies' : {'basic' : 4, 'elite' : 1},
        'bosses' : []
    },

    3 : {
        'spawn_cooldown' : 2.3,
        'enemy_cooldown_penalty' : 0.8,
        'enemies' : {'basic' : 4, 'elite' : 1, 'gunner' : 1},
        'bosses' : []
    },

    4 : {
        'spawn_cooldown' : 2.2,
        'enemy_cooldown_penalty' : 0.8,
        'enemies' : {'basic' : 3, 'elite' : 2, 'gunner' : 2, 'runner' : 1},
        'bosses' : []
    },

    5 : {
        'spawn_cooldown' : 2.1,
        'enemy_cooldown_penalty' : 0.8,
        'enemies' : {'basic' : 4, 'elite' : 2, 'gunner' : 2, 'runner' : 2},
        'bosses' : []
    },

    6 : {
        'spawn_cooldown' : 2.0,
        'enemy_cooldown_penalty' : 0.6,
        'enemies' : {'basic' : 4, 'elite' : 4, 'gunner' : 3, 'runner' : 2},
        'bosses' : []
    },

    7 : {
        'spawn_cooldown' : 1.9,
        'enemy_cooldown_penalty' : 0.6,
        'enemies' : {'basic' : 5, 'elite' : 4, 'gunner' : 4, 'runner' : 3},
        'bosses' : []
    },

    8 : {
        'spawn_cooldown' : 1.8,
        'enemy_cooldown_penalty' : 0.6,
        'enemies' : {'basic' : 5, 'elite' : 5, 'gunner' : 5, 'runner' : 3},
        'bosses' : []
    },

    9 : {
        'spawn_cooldown' : 1.7,
        'enemy_cooldown_penalty' : 0.6,
        'enemies' : {'basic' : 5, 'elite' : 6, 'gunner' : 5, 'runner' : 3},
        'bosses' : []
    },

    10 : {
        'spawn_cooldown' : 1.6,
        'enemy_cooldown_penalty' : 0.6,
        'enemies' : {'basic' : 5, 'elite' : 6, 'gunner' : 6, 'runner' : 4},
        'bosses' : []
    },


    11 : {
        'spawn_cooldown' : 1.5,
        'enemy_cooldown_penalty' : 0.4,
        'enemies' : {'basic' : 6, 'elite' : 8, 'gunner' : 7, 'runner' : 5},
        'bosses' : []
    },

    12 : {
        'spawn_cooldown' : 1.4,
        'enemy_cooldown_penalty' : 0.4,
        'enemies' : {'basic' : 6, 'elite' : 8, 'gunner' : 8, 'runner' : 6},
        'bosses' : []
    },

    13 : {
        'spawn_cooldown' : 1.3,
        'enemy_cooldown_penalty' : 0.4,
        'enemies' : {'basic' : 7, 'elite' : 9, 'gunner' : 9, 'runner' : 6},
        'bosses' : []
    },

    14 : {
        'spawn_cooldown' : 1.2,
        'enemy_cooldown_penalty' : 0.4,
        'enemies' : {'basic' : 7, 'elite' : 9, 'gunner' : 9, 'runner' : 7},
        'bosses' : []
    },

    15 : {
        'spawn_cooldown' : 1.1,
        'enemy_cooldown_penalty' : 0.4,
        'enemies' : {'basic' : 7, 'elite' : 10, 'gunner' : 10, 'runner' : 7},
        'bosses' : []
    },
}

DEFAULT_WAVE : WaveDataDict = {
        'spawn_cooldown' : 1,
        'enemy_cooldown_penalty' : 0.05,
        'enemies' : {'basic' : 10, 'elite' : 20, 'gunner' : 20, 'runner' : 12},
        'bosses' : []
    }

class ActiveWaveGameState(NormalGameState):
    FIRST_WAVE : int = 1
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
            self.curr_wave = self.FIRST_WAVE
            core_object.bg_manager.play('main_theme', 1) # TODO : Make sure music is handled properly in the future
        else:
            self.player = prev.player
            self.score = prev.prev_state.score
            self.score_sprite = prev.prev_state.score_sprite
            self.curr_wave = prev.prev_state.curr_wave + 1
            prev.prev_state.deactivate()

        self.control_script : WaveControlScript = WaveControlScript()
        wave_data : WaveDataDict
        if self.curr_wave in WAVES:
            wave_data = WAVES[self.curr_wave]
        else:
            wave_data = DEFAULT_WAVE
            self.game.alert_player(f"Could not load wave data for wave {self.curr_wave}!", 0.35)
        self.control_script.initialize(self, core_object.game_tsource or Timer.base_time_source, wave_data)

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
        core_object.bg_manager.stop_all_music()
        ...

    def deactivate(self):
        self.remove_connections()

class WaveControlScript(CoroutineScript[float, str|None]):
    def initialize(self, state : ActiveWaveGameState, time_source : TimeSource, wave_data : WaveDataDict):
        return super().initialize(state, time_source, wave_data)

    @staticmethod
    def corou(state : ActiveWaveGameState, time_source : TimeSource, wave_data : WaveDataDict):
        base_cooldown : float = wave_data['spawn_cooldown']
        base_enemy_penalty : float = wave_data['enemy_cooldown_penalty']
        enemies_left : dict[EnemyType|BossType, int] = wave_data['enemies'].copy()
        initial_avg_weight : float = WaveControlScript.calculate_average_weight(enemies_left)
        spawn_timer : Timer = Timer(base_cooldown, time_source)
        spawn_timer.start_time -= base_cooldown
        delta = yield
        
        while any(val > 0 for val in enemies_left.values()):
            pressed = pygame.key.get_pressed() # debug
            if pressed[pygame.K_CAPSLOCK] and pressed[pygame.K_o]:
                enemies_left.clear()

            if spawn_timer.isover():
                chosen_enemy_type : EnemyType|BossType|None = WaveControlScript.select_enemy_to_spawn(enemies_left, initial_avg_weight)
                if chosen_enemy_type is None:
                    enemies_left.clear()
                else:
                    WaveControlScript.spawn_enemy(chosen_enemy_type)
                    enemies_left[chosen_enemy_type] -= 1
                spawn_timer.set_duration(base_cooldown + base_enemy_penalty * len(BaseEnemy.active_elements))
            delta = yield

        while len(BaseEnemy.active_elements) > 0:
            delta = yield

        if state.curr_wave % 5 == 0:
            spawn_timer.set_duration(2.0)
            while not spawn_timer.isover():
                delta = yield
            state.player.heal_to_max()
        return 'Done'

    @staticmethod
    def select_enemy_to_spawn(enemies_left : dict['EnemyType|BossType', int], init_weight : float) -> 'EnemyType|BossType|None':
        weights_left : float = WaveControlScript.calculate_average_weight(enemies_left) # TODO : Better logic
        if weights_left == 0:
            if not any(val > 0 for val in enemies_left.values()):
                return None
            return random.choices(list(enemies_left.keys()), list(enemies_left.values()), k=1)[0]
        weight_ratio : float = init_weight / weights_left
        enemy_chances : dict['EnemyType|BossType', float] = {}
        for enemy_type in enemies_left:
            if enemies_left[enemy_type] <= 0:
                continue
            enemy_base_weight : float = ENEMY_WEIGHT_DICT[enemy_type]
            if weight_ratio < 1: # if the wave is too easy
                if enemy_base_weight < weights_left:
                    enemy_chances[enemy_type] = weight_ratio ** 2
                elif enemy_base_weight < init_weight:
                    enemy_chances[enemy_type] = weight_ratio
                elif enemy_base_weight < (init_weight + abs(init_weight - weights_left)):
                    enemy_chances[enemy_type] = 1 / weight_ratio
                else:
                    enemy_chances[enemy_type] = 1 / (weight_ratio ** 2)
            else: # if the wave is too hard
                if enemy_base_weight > weights_left:
                    enemy_chances[enemy_type] = (1 / weight_ratio) ** 2
                elif enemy_base_weight > init_weight:
                    enemy_chances[enemy_type] = (1 / weight_ratio)
                elif enemy_base_weight > (init_weight - abs(weights_left - init_weight)):
                    enemy_chances[enemy_type] = weight_ratio
                else:
                    enemy_chances[enemy_type] = weight_ratio ** 2

            enemy_chances[enemy_type] *= enemies_left[enemy_type]

        if not enemy_chances:
            return None
        return random.choices(list(enemy_chances.keys()), list(enemy_chances.values()), k=1)[0]


    @staticmethod
    def calculate_average_weight(enemies : dict['EnemyType|BossType', int]):
        if any(val > 0 for val in enemies.values()):
            return sum(ENEMY_WEIGHT_DICT[k] * enemies[k] for k in enemies) / sum(enemies[k] for k in enemies)
        else:
           return 0

    @staticmethod
    def spawn_enemy(enemy_type : 'EnemyType|BossType') -> 'BaseEnemy':
        match enemy_type:
            case 'basic':
                return BasicEnemy.spawn('midbottom', pygame.Vector2(random.randint(0 + 50, 960 - 50), -20))
            case 'elite':
                return EliteEnemy.spawn('midbottom', pygame.Vector2(random.randint(0 + 50, 960 - 50), -20))
            case 'gunner':
                return GunnerEnemy.spawn('midbottom', pygame.Vector2(random.randint(0 + 50, 960 - 50), -20))
            case 'runner':
                return RunnerEnemy.spawn('midbottom', pygame.Vector2(random.randint(0 + 50, 960 - 50), -20))
            case _:
                raise ValueError(f"Cannot spawn enemy type {enemy_type}")

class UpgradeCard(UiFrame):
    CARD_SIZE : tuple[int, int] = (180, 250)
    DEFAULT_FONT_SIZE : int = 24
    DEFAULT_COLOR : pygame.typing.ColorLike = pygame.Color("White")
    BG_COLOR : pygame.typing.ColorLike = pygame.Color("Grey")

    def __init__(self, start_position : pygame.Vector2, anchor : AnchorStr|pygame.typing.Point, 
                 text_list : list[tuple[str, 'ShopTextOptions']], border_info : tuple[pygame.typing.ColorLike, int],
                 associated_index : int = 0):
        base_drawable_info = BaseDrawableInfo(UiPosition(start_position, anchor), zindex=-5)
        ui_frame_info = BaseUiFrameInfo(self.CARD_SIZE, True)
        elements : list[UiDrawable] = []
        prev_bottom : int = border_info[1]
        for text, text_options in text_list:
            new_sprite : TextSprite = self.create_text_part(text, text_options, border_info[1] + 4, prev_bottom)
            elements.append(new_sprite)
            prev_bottom = new_sprite.get_local_draw_rect().bottom

        bg_element_surf : pygame.Surface = pygame.Surface(self.CARD_SIZE)
        bg_element_surf.fill(self.BG_COLOR)
        pygame.draw.rect(bg_element_surf, border_info[0], pygame.Rect((0, 0), self.CARD_SIZE), border_info[1])

        bg_element : UiSprite = UiSprite(BaseDrawableInfo(UiPosition((0, 0), (0, 0)), zindex=-2), bg_element_surf)
        elements.append(bg_element)
        super().__init__(base_drawable_info, elements, ui_frame_info)
        self.upgrade_index : int = associated_index
        self.transition_state : tuple[Literal['in', 'out', 'selected'], float]|None = None
        self.transition_timer : Timer = Timer(-1, core_object.game_tsource)
        self.transition_done : bool|None = None

    def create_text_part(self, text_to_show : str, text_options : 'ShopTextOptions', margin : int, prev_bottom : int = 10) -> TextSprite:
        pos : pygame.Vector2|int|None = text_options['pos']
        if pos is None:
            pos = prev_bottom + 4
        if isinstance(pos, int):
            pos = pygame.Vector2(self.CARD_SIZE[0] / 2, pos)
        anchor : AnchorStr
        if text_options['anchor'] in AnchorNameList:
            anchor = text_options['anchor']
        else:
            match text_options['anchor']:
                case 'bottom':
                    anchor = 'midbottom'
                case 'y':
                    anchor = 'midtop'
                case 'top':
                    anchor = 'midtop'
                case 'centery':
                    anchor = 'center'
                case _:
                    anchor = 'center'
        ui_position : UiPosition = UiPosition(pos, anchor)

        text_style : TextStyle
        if 'text_style' in text_options:
            text_style = text_options['text_style']
        else:
            font_size : int = text_options.get('font_size', self.DEFAULT_FONT_SIZE)
            color : pygame.typing.ColorLike = text_options.get('color', self.DEFAULT_COLOR)
            font : pygame.Font
            if f"font_{font_size}" in core_object.asset_manager.fonts:
                font = core_object.asset_manager.get_font(f"font_{font_size}") or pygame.Font(r'assets/fonts/Pixeltype.ttf', font_size)
            else:
                font = pygame.Font(r'assets/fonts/Pixeltype.ttf', font_size)

            text_style = TextStyle(font, color, False, max_line_length=self.CARD_SIZE[0] - 2 * margin)

        return TextSprite(BaseDrawableInfo(ui_position), TextSpriteInfo(text_to_show, text_style))

    def transition_in(self):
        if self.transition_state is not None:
            return
        self.transition_timer.set_duration(1.5)
        self.transition_state = ('in', self.position.value.y)
        self.transition_done = False

    def transition_out(self):
        if self.transition_state is not None and self.transition_state[0] in ('out', 'selected'):
            return
        self.transition_timer.set_duration(1.5)
        self.transition_state = ('out', self.position.value.y)
        self.transition_done = False

    def transition_selected(self):
        if self.transition_state is not None and self.transition_state[0] in ('out', 'selected'):
            return
        self.transition_timer.set_duration(1.5)
        self.transition_state = ('selected', self.position.value.y)
        self.transition_done = False

    def update(self, delta : float):
        if self.transition_state is not None:
            alpha : float = self.transition_timer.get_time() / self.transition_timer.duration
            wanted_transition : Literal['in', 'out', 'selected'] = self.transition_state[0]
            effective_alpha : float = interpolation.quad_ease_out(alpha) if wanted_transition == 'in' else interpolation.quad_ease_in(alpha)
            opacity_target : float|None = 0.2 if wanted_transition == 'selected' else None
            y_pos_target : int = 300 if wanted_transition == 'in' else -40 if wanted_transition == 'out' else 541 + 40 + int(self.size.y)
            if opacity_target:
                self.opacity = pygame.math.lerp(1, opacity_target, alpha)
            self.position.y = pygame.math.lerp(self.transition_state[1], y_pos_target, effective_alpha)
            if alpha >= 1:
                self.transition_done = True if wanted_transition != 'in' else None
                self.transition_state = None
                self.transition_timer.set_duration(-1)
        super().update(delta)
    
class ShopGameState(NormalGameState):
    def __init__(self, game_object : 'Game', prev : 'ActiveWaveGameState'):
        self.game : Game = game_object
        self.player : Player = prev.player
        self.prev_state : ActiveWaveGameState = prev

        self.test_timer : Timer = Timer(10, core_object.game_tsource)

        upgrade_count : int = 3
        target_tier : int = 1
        rarity_bonus_tier : int = 0

        self.candidates : list[Upgrade] = []

        for name, rank in self.select_upgrades(upgrade_count, target_tier, rarity_bonus_tier):
            result : Upgrade|None = Upgrade.from_name_and_rank(name, rank)
            if result is not None:
                self.candidates.append(result)

        self.upgrade_cards : list[UpgradeCard] = self.generate_card_list(self.candidates)

        self.selected_upgrade : Upgrade|None = None

        core_object.main_ui.add_multiple(self.upgrade_cards)

        self.control_script : ShopControlScript = ShopControlScript()
        self.control_script.initialize(self)

    def calculate_spacing(self, card_amount : int) -> int:
        available_space : int = core_object.main_display.get_size()[0] - (0 + 55)
        total_gap : int = available_space - (UpgradeCard.CARD_SIZE[0] * card_amount)
        gap : int
        if total_gap <= 0 or card_amount <= 1:
            gap = 1
        else:
            gap = total_gap // (card_amount - 1)
        spacing : int = gap + UpgradeCard.CARD_SIZE[0]
        return spacing

    def generate_card_list(self, upgrade_list : list['Upgrade']) -> list[UpgradeCard]:
        spacing = self.calculate_spacing(len(upgrade_list))
        
        upgrade_cards : list[UpgradeCard] = [UpgradeCard(pygame.Vector2(0 + spacing * i, -40), 'bottomleft', 
                                            upg.get_shop_description(self.player.upgrades.upgrades),
                                            upg.get_shop_border_info(), i) for i, upg in enumerate(upgrade_list)]

        return upgrade_cards

    def main_logic(self, delta : float):
        super().main_logic(delta)
        result : str|None = self.control_script.process_frame(delta)
        if result == 'Done':
            self.transition_to_wave()

    def check_collisions(self) -> UpgradeCard|None:
        for card in self.upgrade_cards:
            if card.transition_state is not None:
                continue
            if any(proj.team == Teams.ALLIED and proj.rect.colliderect(card.get_world_draw_rect()) 
                   for proj in BaseProjectile.active_elements):
                return card
        return None

    def transition_cards_in(self):
        for card in self.upgrade_cards:
            card.transition_in()

    def transition_cards_out(self):
        for card in self.upgrade_cards:
            if card.transition_state is None or card.transition_state[0] != 'selected':
                card.transition_out()

    def clear_cards(self):
        for card in self.upgrade_cards:
            core_object.main_ui.remove(card)
        self.upgrade_cards.clear()

    def transition_to_wave(self):
        if self.selected_upgrade:
            core_object.log(self.selected_upgrade)
            self.player.upgrades.apply_upgrade(self.selected_upgrade)
        self.player.upgrades.curr_ability.refresh_cooldown(True)
        self.player.upgrades.curr_alt_fire.refresh_cooldown(True)
        core_object.game.state = ActiveWaveGameState(self.game, self)
        self.deactivate()
 
    def make_connections(self):
        pass

    def remove_connections(self):
        pass

    def cleanup(self):
        self.deactivate()
        self.prev_state.deactivate()
        core_object.bg_manager.stop_all_music()
        ...
    
    def deactivate(self):
        self.remove_connections()
        self.clear_cards()

    def select_upgrades(self, amount : int = 3, target_tier : int = 1, rarity_bonus_tier : int = 0) -> list[tuple['UpgradeName', int]]:
        wave_num : int = self.prev_state.curr_wave
        type_distribution : dict[UpgradeType, int] = {upgrade_type : 0 for upgrade_type in UpgradeType}
        random_list : list[int] = [random.randint(1, 1000) for _ in range(amount)]
        guaranteed : dict[UpgradeType, int]
        random_given : list[UpgradeType]
        match wave_num % 5:
            case 1:
                guaranteed = {UpgradeType.MINOR : amount}
                random_given = []
            case 2:
                guaranteed = {UpgradeType.MINOR : 1}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 150 
                    else UpgradeType.ABILITY if random_list[i] <= 300
                    else UpgradeType.MAJOR if random_list[i] <= 450
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 3:
                guaranteed = {UpgradeType.MINOR : 1}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 400 
                    else UpgradeType.ABILITY if random_list[i] <= 800
                    else UpgradeType.MAJOR if random_list[i] <= 1000
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 4:
                guaranteed = {UpgradeType.MINOR : 1, UpgradeType.ABILITY : 1}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 250 
                    else UpgradeType.ABILITY if random_list[i] <= 450
                    else UpgradeType.MAJOR if random_list[i] <= 550
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case 0:
                guaranteed = {UpgradeType.SECONDARY_FIRE : 2}
                random_given = [(
                    UpgradeType.PERK if random_list[i] <= 400 
                    else UpgradeType.ABILITY if random_list[i] <= 800
                    else UpgradeType.MAJOR if random_list[i] <= 1000
                    else UpgradeType.MINOR
                ) for i in range(amount - sum(guaranteed.values()))]
            case _:
                guaranteed = {}
                random_given = []
        locked_out : bool = True
        if type_distribution[UpgradeType.MINOR] >= 0 or type_distribution[UpgradeType.MAJOR] >= 0 or type_distribution[UpgradeType.PERK] >= 0:
            locked_out = False
        for upgrade_type in UpgradeType:
            type_distribution[upgrade_type] += random_given.count(upgrade_type)
            if upgrade_type in guaranteed:
                type_distribution[upgrade_type] += guaranteed[upgrade_type]
        core_object.log(type_distribution, "#1")

        selected : list[tuple[UpgradeName, int]] = []

        if (type_distribution[UpgradeType.SECONDARY_FIRE] > 0
            and self.player.upgrades.curr_alt_fire.rank < src.upgrades.MAX_RANK[self.player.upgrades.curr_alt_fire.name]
            and random.random() <= 1):

            type_distribution[UpgradeType.SECONDARY_FIRE] -= 1
            selected.append((self.player.upgrades.curr_alt_fire.name, self.player.upgrades.curr_alt_fire.rank + 1))
            locked_out = False

        if (type_distribution[UpgradeType.ABILITY] > 0
            and self.player.upgrades.curr_ability.rank < src.upgrades.MAX_RANK[self.player.upgrades.curr_ability.name]
            and (random.random() <= 0.65
                  or not self.valid_random_upgrade_of_type_exsists(UpgradeType.ABILITY, target_tier, rarity_bonus_tier, 
                                                                   [s[0] for s in selected]))):

            type_distribution[UpgradeType.ABILITY] -= 1
            selected.append((self.player.upgrades.curr_ability.name, self.player.upgrades.curr_ability.rank + 1))
            locked_out = False

        perks_left : int = type_distribution[UpgradeType.PERK]
        if perks_left:
            for _ in range(perks_left):
                if random.random() <= 0.65 or not self.valid_random_upgrade_of_type_exsists(UpgradeType.PERK, target_tier, rarity_bonus_tier, 
                                                                   [s[0] for s in selected]):
                    eligible_existing_perks : list[tuple[UpgradeName, int]] = [
                        (perk.name, perk.rank + 1) for perk in 
                        filter(lambda p : p.rank < src.upgrades.MAX_RANK[p.name], self.player.upgrades.curr_perks)
                    ]
                    if not eligible_existing_perks:
                        break
                    selected.append(random.choice(eligible_existing_perks))
                    type_distribution[UpgradeType.PERK] -= 1

        if locked_out:
            core_object.log('Lock out detected')
            if type_distribution[UpgradeType.ABILITY] > 0:
                type_distribution[UpgradeType.ABILITY] -= 1
                type_distribution[UpgradeType.MAJOR] += 1
                core_object.log('Replaced an ability by a major perk')
            elif type_distribution[UpgradeType.SECONDARY_FIRE] > 0:
                type_distribution[UpgradeType.SECONDARY_FIRE] -= 1
                type_distribution[UpgradeType.MAJOR] += 1
                core_object.log('Replaced a secondary fire by a major perk')
            else:
                core_object.log('False alarm?')
                
        
        for upgrade_type in type_distribution:
            for _ in range(type_distribution[upgrade_type]):
                result = self.select_random_upgrade_of_type(upgrade_type, target_tier, rarity_bonus_tier, 
                                                                   [s[0] for s in selected])
                if result is None:
                    result = self.select_random_upgrade_of_type(UpgradeType.MINOR, target_tier + 1, rarity_bonus_tier, 
                                                                   [s[0] for s in selected])
                    if result is None:
                        result = ('BonusNormalDamage', 1)
                        core_object.log(f'Failed to select an upgrade ({upgrade_type.value}, {target_tier}) --> using a fallback!')
                selected.append(result)

        return selected

    def get_upgrade_possibilities(self, upgrade_type : 'UpgradeType', target_tier : int, 
                                      rarity_bonus_tier : int = 0,
                                      already_selected : list['UpgradeName']| None = None,
                                      debug : bool = False) -> dict[tuple['UpgradeName', int], float]:

        if already_selected is None: already_selected = []
        eligible : list[UpgradeName] = Upgrade.get_list_of_all(upgrade_type)
        filter_func = lambda name : (all(upg.name != name for upg in self.player.upgrades.upgrades) and (name not in already_selected))
        if upgrade_type in (UpgradeType.ABILITY, UpgradeType.PERK, UpgradeType.SECONDARY_FIRE): # getting upgrades you already have was already handled
            eligible = [x for x in filter(filter_func, eligible)]
        else:
            eligible = [x for x in filter(lambda name : name not in already_selected, eligible)]

        possibilites : dict[tuple[UpgradeName, int], float] = {}

        for upgrade_name in eligible:
            weight_info = src.upgrades.BASE_WEIGHTS[upgrade_name]
            weight_set, ignore_rarity_tier = weight_info
            for rank, weight in weight_set.items():
                if upgrade_type in (UpgradeType.ABILITY, UpgradeType.PERK) and rank != 1:
                    continue
                if upgrade_type == UpgradeType.SECONDARY_FIRE and rank != 0:
                    continue
                rarity_tier, individual_weight = weight

                result : float = individual_weight
                if not ignore_rarity_tier:
                    result *= self.calculate_rarity_tier_modifier(rarity_tier, target_tier, rarity_bonus_tier)
                if result <= 0:
                    continue
                possibilites[(upgrade_name, rank)] = result
        if debug: core_object.log(eligible, "-->", possibilites)
        return possibilites


    def valid_random_upgrade_of_type_exsists(self, upgrade_type : 'UpgradeType', target_tier : int, 
                                      rarity_bonus_tier : int = 0,
                                      already_selected : list['UpgradeName']| None = None,
                                      debug : bool = False) -> bool:
        return bool(self.get_upgrade_possibilities(upgrade_type, target_tier, rarity_bonus_tier, already_selected, debug))
    
    def select_random_upgrade_of_type(self, upgrade_type : 'UpgradeType', target_tier : int, 
                                      rarity_bonus_tier : int = 0,
                                      already_selected : list['UpgradeName']| None = None,
                                      debug : bool = False) -> tuple['UpgradeName', int]|None:

        possibilites : dict[tuple[UpgradeName, int], float] = self.get_upgrade_possibilities(upgrade_type, target_tier, 
                                                                                             rarity_bonus_tier, already_selected, debug)

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

class ShopControlScript(CoroutineScript[float, Literal['Done']|None]):
    def initialize(self, state : ShopGameState):
        return super().initialize(state)

    @staticmethod
    def corou(state : ShopGameState):
        delta : float = core_object.dt
        did_reroll : bool = False
        yield
        while True:
            state.transition_cards_in()
            while True:
                if state.selected_upgrade is not None and all(card.transition_done for card in state.upgrade_cards):
                    did_reroll = False
                    break
                hit_card : UpgradeCard|None = state.check_collisions()
                if hit_card:
                    state.selected_upgrade = state.candidates[hit_card.upgrade_index]
                    hit_card.transition_selected()
                    state.transition_cards_out()
                delta = yield

            state.clear_cards()
            if not did_reroll:
                tranfser_rank : int|None = None
                if state.selected_upgrade.upgrade_type == UpgradeType.SECONDARY_FIRE:
                    tranfser_rank = state.player.upgrades.get_rank_transfer(cast(SecondaryFireName, state.selected_upgrade.name))

                if tranfser_rank is not None and tranfser_rank != 0:
                    upgrade_list : list[Upgrade] = []
                    for i in range(1, tranfser_rank + 1):
                        new_upgrade : Upgrade|None = Upgrade.from_name_and_rank(state.selected_upgrade.name, i)
                        if new_upgrade is not None:
                            upgrade_list.append(new_upgrade)
                    state.upgrade_cards = state.generate_card_list(upgrade_list)
                    core_object.main_ui.add_multiple(state.upgrade_cards)
                    state.transition_cards_in()
                    state.game.alert_player("And here are a few bonuses...")
                    card_show_timer : Timer = Timer(5, core_object.game_tsource)
                    while not card_show_timer.isover():
                        delta = yield
                    state.transition_cards_out()
                    while any(not card.transition_done for card in state.upgrade_cards):
                        delta = yield
            else:
                wait_reroll_timer : Timer = Timer(0.5, core_object.game_tsource)
                while not wait_reroll_timer.isover():
                    delta = yield
                # Reroll logic goes here
                continue

            delay_timer : Timer = Timer(0.5, core_object.game_tsource)
            while not delay_timer.isover():
                delta = yield
            break
        return 'Done'
    
class GameOverGameState(GameState):
    def __init__(self, game_object : "Game", text = "Game over!", prev_state : GameState|None = None): # TODO : Revamp this code at some point
        self.game : Game = game_object
        self.lost : bool = text == "Game over!"
        self.prev : GameState|None = prev_state
        self.control_script : GameOverControlScript = GameOverControlScript()
        prev_player : Any = getattr(self.prev, 'player', None)
        if not isinstance(prev_player, Player):
            prev_player = Player.active_elements[0]    
        self.control_script.initialize(self.game.game_timer.get_time, self, prev_player)
        self.game.alert_player(text)
        core_object.bg_manager.stop_all_music()

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
        player.visible = True
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

    global BaseProjectile, Teams
    from src.sprites.projectiles import BaseProjectile, Teams
    import src.sprites.projectiles
    src.sprites.projectiles.runtime_imports()

    global EnemyType, BossType, ENEMY_WEIGHT_DICT, BaseEnemy, BaseNormalEnemy
    global BasicEnemy, EliteEnemy, GunnerEnemy, RunnerEnemy
    from src.sprites.enemy import EnemyType, BossType, ENEMY_WEIGHT_DICT, BaseEnemy, BaseNormalEnemy
    from src.sprites.enemy import BasicEnemy, EliteEnemy, GunnerEnemy, RunnerEnemy
    import src.sprites.enemy
    src.sprites.enemy.runtime_imports()

    global Player
    from src.sprites.player import Player
    import src.sprites.player

    global Upgrade, PlayerUpgrades, UpgradeType, UpgradeName, ShopTextOptions, SecondaryFireName, MAX_RANK
    from src.upgrades import Upgrade, PlayerUpgrades, UpgradeType, UpgradeName, ShopTextOptions, SecondaryFireName, MAX_RANK
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
