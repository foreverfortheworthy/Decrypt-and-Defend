# filename: game_pygame.py
import pygame
import debug
from game_state import GameState
from game_actions import GameActions
from config import (
    AI_PAUSE_DURATION_MS, CARD_ANIMATION_DURATION_MS,
    DECK_POS_OPPONENT,
    CARAVAN_START_X, CARAVAN_SPACING, SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT,
    OPPONENT_CARAVAN_Y, PLAYER_CARAVAN_Y, CARAVAN_CARD_Y_OFFSET
)
from player import Player
from card import Card
from typing import Union, Dict, Any, Optional, Tuple, List

class GameController:
    def __init__(self):
        self.game_state: Optional[GameState] = None
        self.game_actions: Optional[GameActions] = None
        self.ai_thinking_start_time: int = 0
        self.pending_ai_action: Optional[Dict[str, Any]] = None
        self._message: Optional[str] = None
        self._message_timer: int = 0
        self.animation_details: Optional[Dict[str, Any]] = None

    def start_new_game(self, ai_difficulty: int = 0):
        try:
            self.game_state = GameState(ai_player_difficulty=ai_difficulty)
            self.game_actions = GameActions(self.game_state)
            self.game_state.start_game()
        except Exception as e:
            debug.log_error(f"FATAL: Could not initialize GameState/GameActions: {e}", include_traceback=True)
            self.game_state = None
            self.game_actions = None
            self.set_message("Error: Game failed to initialize!", 10000)
            return

        self.ai_thinking_start_time = 0
        self.pending_ai_action = None
        self.animation_details = None

        if self.game_state.get_current_player():
            player_name = self.game_state.get_current_player().name
            phase_msg = "(Setup). Place first card." if self.game_state.is_setup_phase() else "Turn."
            self.set_message(f"{player_name}'s {phase_msg}", 3000 if self.game_state.is_setup_phase() else 1500)
        else:
            self.set_message("Game Ready. Error in getting first player.", 2000)

    def set_message(self, text: Optional[str], duration_ms: int = 2000):
        self._message = text
        self._message_timer = duration_ms if text else 0
        debug.log_ui("Controller message set: '{}' for {}ms", text, duration_ms)

    def update_animation(self, dt_ms: int):
        if self.animation_details and self.animation_details['is_active']:
            anim = self.animation_details
            if anim.get('start_pos') is None or \
               anim.get('end_pos') is None or \
               anim.get('current_pos') is None:
                debug.log_ui("Animation active but start/end/current_pos not yet set. Skipping position update.")
                return

            anim['elapsed_ms'] += dt_ms
            anim['progress'] = min(1.0, anim['elapsed_ms'] / anim['duration_ms'])
            start_x, start_y = anim['start_pos']
            end_x, end_y = anim['end_pos']
            anim['current_pos'] = (
                start_x + (end_x - start_x) * anim['progress'],
                start_y + (end_y - start_y) * anim['progress']
            )
            if anim['progress'] >= 1.0:
                anim['is_active'] = False
                debug.log_ui("Animation visually complete for card: {}", anim['card_to_animate'])

    def update(self, dt_ms: int):
        if not self.game_state:
            return
        if self._message_timer > 0:
            self._message_timer -= dt_ms
            if self._message_timer <= 0:
                self._message = None
                self._message_timer = 0
        self.update_animation(dt_ms)
        if self.game_state.game_over:
            winner = self.game_state.winner
            win_msg = f"Game Over! {'Draw!' if not winner else f'{winner.name} Wins!'}"
            if self._message != win_msg:
                self.set_message(win_msg, 100000)

    def get_current_message(self) -> Optional[str]:
        if self._message and self._message_timer > 0:
            return self._message
        if not self.game_state:
            return "Game not initialized."
        if self.game_state.game_over:
            return self._message
        current_player = self.game_state.get_current_player()
        if not current_player:
            return "Error: No current player."
        if self.is_ai_turn() and self.ai_thinking_start_time > 0 and self.pending_ai_action is None:
            return f"{current_player.name} (AI) is thinking..."
        phase_str = "(Setup)" if self.game_state.is_setup_phase() else ""
        return f"{current_player.name}'s Turn {phase_str}"

    def is_player_turn(self, player: Player) -> bool:
        if not self.game_state or self.game_state.game_over or not player:
            return False
        return self.game_state.get_current_player() == player

    def is_ai_turn(self) -> bool:
        if not self.game_state or self.game_state.game_over:
            return False
        current_player = self.game_state.get_current_player()
        return current_player is not None and current_player.is_ai

    def needs_setup_action(self, player: Player) -> bool:
        if not self.game_state or not self.game_state.is_setup_phase() or not player:
            return False
        if player != self.game_state.get_current_player():
            return False
        return any(not c.cards for c in player.caravans)

    def initiate_action_with_animation(self, player: Player, action_intent: Dict[str, Any],
                                       card_to_animate: Optional[Card],
                                       start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        if not self.game_state or not self.game_actions:
            self.set_message("Game Error: State not initialized.", 2000)
            return False
        if self.game_state.game_over:
            return False
        if player != self.game_state.get_current_player():
            self.set_message("Not your turn!", 1500)
            return False
        if self.animation_details and self.animation_details['is_active']:
            self.set_message("Wait for current animation to finish.", 1500)
            return False

        if card_to_animate:
            self.animation_details = {
                'is_active': True,
                'card_to_animate': card_to_animate,
                'card_image_surface': None,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'current_pos': start_pos,
                'progress': 0.0,
                'duration_ms': CARD_ANIMATION_DURATION_MS,
                'elapsed_ms': 0,
                'action_to_perform_on_complete': action_intent,
                'player_who_initiated_action': player
            }
            debug.log_ui("Animation initiated for card: {} from {} to {}", card_to_animate, start_pos, end_pos)
            return True
        else:
            return self.execute_validated_action(player, action_intent)

    def execute_validated_action(self, player: Player, action: Dict[str, Any]) -> bool:
        if not self.game_state or not self.game_actions: return False
        action_was_successful = self.game_actions.execute_action(player, action)
        if action_was_successful:
            if self.game_state.check_game_over():
                return True
            action_ends_turn = True
            if self.game_state.is_setup_phase():
                all_players_setup_done = all(all(c.cards for c in p_iter.caravans) for p_iter in self.game_state.players)
                if all_players_setup_done:
                    self.game_state.complete_setup_phase()
                    next_player_after_setup = self.game_state.get_current_player()
                    if next_player_after_setup:
                         self.set_message(f"Setup Complete! {next_player_after_setup.name} starts.", 2500)
                    action_ends_turn = False
            if action_ends_turn and not self.game_state.game_over:
                self.game_state.next_turn()
                next_player = self.game_state.get_current_player()
                if next_player and self.is_player_stuck(next_player) and not self.game_state.game_over:
                    stuck_msg = f"{next_player.name} has no moves! Turn automatically passed."
                    self.set_message(stuck_msg, 2500)
                    debug.log_event(stuck_msg)
                    pass_success = self.game_actions.execute_action(next_player, {"type": "pass"})
                    if pass_success:
                        if self.game_state.check_game_over(): return True
                        self.game_state.next_turn()
            return True
        else:
            return False

    def run_ai_turn(self):
        if (not self.game_state or not self.game_actions or self.game_state.game_over or
                not self.is_ai_turn() or self.game_state.question_popup_active or
                (self.animation_details and self.animation_details['is_active'])):
            return
        ai_player = self.game_state.get_current_player()
        if not ai_player: return
        if self.ai_thinking_start_time == 0 and self.pending_ai_action is None:
            if self.is_player_stuck(ai_player):
                debug.log_ai("AI {} is stuck. Attempting pass.", ai_player.name)
                self.set_message(f"AI {ai_player.name} has no moves. Passing.", 2000)
                self.execute_validated_action(ai_player, {"type": "pass"})
                return
            if not ai_player.hand and ai_player.deck:
                ai_player.draw_card()
                if self.is_player_stuck(ai_player):
                    debug.log_ai("AI {} drew a card and is still stuck. Attempting pass.", ai_player.name)
                    self.set_message(f"AI {ai_player.name} drew, still stuck. Passing.", 2000)
                    self.execute_validated_action(ai_player, {"type": "pass"})
                    return
            self.ai_thinking_start_time = pygame.time.get_ticks()
            self._message = None
            self._message_timer = 0
            debug.log_ai("AI {} started thinking.", ai_player.name)

        if self.ai_thinking_start_time > 0 and self.pending_ai_action is None:
            current_time = pygame.time.get_ticks()
            if current_time - self.ai_thinking_start_time >= AI_PAUSE_DURATION_MS:
                chosen_action: Optional[Dict[str, Any]] = None
                if self.game_state.is_setup_phase():
                    card_idx = ai_player.get_ai_initial_card()
                    if card_idx != -1:
                        empty_caravan_idx = next((i for i, c in enumerate(ai_player.caravans) if not c.cards), -1)
                        if empty_caravan_idx != -1:
                            chosen_action = {
                                "type": "place_initial_card", "card_index": card_idx,
                                "caravan_index": empty_caravan_idx,
                            }
                        else: chosen_action = {"type": "pass"}
                    else: chosen_action = {"type": "pass"}
                else:
                    chosen_action = ai_player.get_ai_action(self.game_state)
                    if chosen_action is None: chosen_action = {"type": "pass"}
                self.pending_ai_action = chosen_action
                self.ai_thinking_start_time = 0
                debug.log_ai("AI {} finished thinking. Pending action: {}", ai_player.name, self.pending_ai_action)

        if self.pending_ai_action is not None:
            action_to_execute = self.pending_ai_action
            self.pending_ai_action = None
            debug.log_ai("AI {} attempting to execute: {}", ai_player.name, action_to_execute)
            card_to_animate_obj: Optional[Card] = None
            action_type = action_to_execute.get("type")
            if action_type in ["play_card", "place_initial_card"]:
                card_idx = action_to_execute.get("card_index", -1)
                if 0 <= card_idx < len(ai_player.hand):
                    card_to_animate_obj = ai_player.hand[card_idx]
                else:
                    debug.log_warning("AI action {} had invalid card_index: {}. AI passing.", action_type, card_idx)
                    self.execute_validated_action(ai_player, {"type": "pass"})
                    return
            if card_to_animate_obj:
                 self.animation_details = {
                    'is_active': True,
                    'card_to_animate': card_to_animate_obj,
                    'card_image_surface': None,
                    'start_pos': None,
                    'end_pos': None,
                    'current_pos': None,
                    'progress': 0.0,
                    'duration_ms': CARD_ANIMATION_DURATION_MS,
                    'elapsed_ms': 0,
                    'action_to_perform_on_complete': action_to_execute,
                    'player_who_initiated_action': ai_player
                }
                 debug.log_ui("AI action {} for card {} requires animation. Positions to be set by UI.", action_type, card_to_animate_obj)
            else:
                self.execute_validated_action(ai_player, action_to_execute)

    def is_player_stuck(self, player: Player) -> bool:
        if not self.game_state or not player:
            return True
        if player.hand:
            return False
        if player.deck:
            return False
        can_discard_any_caravan = any(
            caravan.cards and not self.game_state.is_caravan_sold_by_anyone(player, i)
            for i, caravan in enumerate(player.caravans)
        )
        if can_discard_any_caravan:
            return False
        return True