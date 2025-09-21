# filename: game_state.py
import random
import debug
from card import Card
from player import Player
from caravan import Caravan
from config import (
    STARTING_HAND_SIZE,
    NUM_CARAVANS,
    WINNING_CARAVANS_NEEDED,
    STANDARD_DECK_COMPOSITION,
)
from blurb import ALL_QUESTIONS_DATA
from typing import List, Dict, Optional, Set

class GameState:
    def __init__(self, player1_name="Player 1", player2_name="AI Player", ai_player_difficulty: int = 0):
        self.players: List[Player] = []
        try:
            p1 = Player(player1_name, is_ai=False)
            p2 = Player(player2_name, is_ai=True, ai_difficulty=ai_player_difficulty)
            self.players = [p1, p2]
            if not p1.deck or not p2.deck:
                 raise ValueError("Player deck creation failed during GameState init.")
        except Exception as e:
             debug.log_error(f"FATAL ERROR during Player/Deck initialization: {e}", include_traceback=True)

        self.current_player_index: int = 0
        self.turn_count: int = 0
        self.game_over: bool = False
        self.winner: Optional[Player] = None
        self._setup_phase: bool = True
        self.all_questions: List[Dict] = []
        self.current_question_index: int = -1
        self.question_popup_active: bool = False
        self.current_question_data: Optional[Dict] = None
        self.question_feedback: Optional[str] = None
        self.question_answered_correctly_this_popup: bool = False
        self._current_ui_message: Optional[str] = None
        self._current_ui_message_timer: int = 0
        self.awaiting_bonus_point_placement: bool = False
        self.player_awarded_bonus: Optional[Player] = None
        self.human_player_awaiting_move_after_question: bool = False

        self._master_card_list: List[Card] = []
        self.unseen_cards: Set[Card] = set()

    def set_message(self, text: Optional[str], duration_ms: int = 1500):
        self._current_ui_message = text
        self._current_ui_message_timer = duration_ms if text else 0

    def get_current_message_from_gamestate(self) -> Optional[str]:
        if self._current_ui_message and self._current_ui_message_timer > 0:
            return self._current_ui_message
        return None

    def update_message_timer(self, dt_ms: int):
        if self._current_ui_message_timer > 0:
            self._current_ui_message_timer -= dt_ms
            if self._current_ui_message_timer <= 0:
                self._current_ui_message = None

    def start_game(self):
        if not self.players:
             debug.log_error("Cannot start game, players list is empty.")
             self.game_over = True
             return

        self._master_card_list = [Card(spec['rank'], spec['suit']) for spec in STANDARD_DECK_COMPOSITION] * 2
        self.unseen_cards = set(self._master_card_list)

        self._setup_phase = True
        self.current_player_index = 0
        self.turn_count = 0
        self.game_over = False
        self.winner = None
        self.awaiting_bonus_point_placement = False
        self.player_awarded_bonus = None
        self.human_player_awaiting_move_after_question = False

        for player in self.players:
            player.deck = player._create_own_deck()
            player.deal_starting_hand()
            player.caravans = [Caravan() for _ in range(NUM_CARAVANS)]

            if player.is_ai:
                for card in player.hand:
                    if card in self.unseen_cards:
                        self.unseen_cards.remove(card)

        if not all(p.hand for p in self.players):
             debug.log_error("Failed to deal starting hands properly.")
             self.game_over = True
             return

        self.all_questions = list(ALL_QUESTIONS_DATA)
        random.shuffle(self.all_questions)
        self.current_question_index = -1
        self.question_popup_active = False
        debug.log_event("Game Started. Setup phase active. Player: {}", self.get_current_player().name)

    def track_played_card(self, card: Card):
        if card in self.unseen_cards:
            self.unseen_cards.remove(card)

    def get_unseen_cards(self) -> Set[Card]:
        return self.unseen_cards

    def get_current_player(self) -> Optional[Player]:
        if not self.players or not (0 <= self.current_player_index < len(self.players)):
            return None
        return self.players[self.current_player_index]

    def get_opponent(self, player: Player) -> Optional[Player]:
        if not player or player not in self.players or len(self.players) < 2:
            return None
        return self.players[1] if player == self.players[0] else self.players[0]

    def next_turn(self):
        if self.game_over:
            return
        if not self.players:
            debug.log_error("next_turn called with no players.")
            return

        current_p = self.get_current_player()
        if not current_p: return

        if self.awaiting_bonus_point_placement and self.player_awarded_bonus == current_p:
            return 

        if self.question_popup_active:
            if self.question_answered_correctly_this_popup and not current_p.is_ai:
                self.question_popup_active = False
                self.awaiting_bonus_point_placement = True
                self.player_awarded_bonus = current_p
                self.set_message("Correct! Click Bonus Point, then target caravan.", 3000)
                return 
            elif not current_p.is_ai and not self.question_answered_correctly_this_popup:
                return 

        if self.human_player_awaiting_move_after_question and not current_p.is_ai:
            self.human_player_awaiting_move_after_question = False

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        next_p = self.get_current_player()
        debug.log_event("Turn advances to {}.", next_p.name if next_p else "N/A")

        new_round_started = (not self.is_setup_phase() and self.current_player_index == 0)
        if new_round_started:
            self.turn_count += 1
            debug.log_event("Round {} started.", self.turn_count)

        if (next_p and not next_p.is_ai and new_round_started and
            self.turn_count > 0 and self.turn_count % 3 == 0 and
            (self.current_question_index + 1) < len(self.all_questions)):
            self.current_question_index += 1
            self.current_question_data = self.all_questions[self.current_question_index]
            self.question_popup_active = True

    def is_setup_phase(self) -> bool:
        return self._setup_phase

    def complete_setup_phase(self):
        if self._setup_phase:
            self._setup_phase = False
            self.current_player_index = 0
            self.turn_count = 0
            debug.log_event("Setup phase completed. {} starts.", self.players[0].name)

    def check_game_over(self) -> bool:
        if self.game_over: return True

        player1, player2 = self.players[0], self.players[1]
        p1_sales = self.get_sold_caravan_count(player1)
        p2_sales = self.get_sold_caravan_count(player2)

        if p1_sales >= WINNING_CARAVANS_NEEDED:
            self.game_over, self.winner = True, player1
            return True
        if p2_sales >= WINNING_CARAVANS_NEEDED:
            self.game_over, self.winner = True, player2
            return True

        p1_stuck = not player1.hand and not player1.deck
        p2_stuck = not player2.hand and not player2.deck
        if p1_stuck and p2_stuck:
            self.game_over = True
            if p1_sales > p2_sales: self.winner = player1
            elif p2_sales > p1_sales: self.winner = player2
            else: self.winner = None
            return True
        return False

    def get_sold_caravan_count(self, player: Player) -> int:
        return sum(1 for i in range(NUM_CARAVANS) if self.is_caravan_sold_by_player(player, i))

    def is_caravan_sold_by_player(self, caravan_owner: Player, caravan_index: int) -> bool:
        opponent = self.get_opponent(caravan_owner)
        if not opponent or not (0 <= caravan_index < NUM_CARAVANS):
            return False

        owner_caravan = caravan_owner.caravans[caravan_index]
        opponent_caravan = opponent.caravans[caravan_index]

        if not owner_caravan.is_winning():
            return False

        if not opponent_caravan.is_winning():
            return True

        return owner_caravan.total() > opponent_caravan.total()

    def is_caravan_sold_by_anyone(self, player_perspective: Player, caravan_index: int) -> bool:
        if self.is_caravan_sold_by_player(player_perspective, caravan_index):
            return True
        opponent = self.get_opponent(player_perspective)
        if opponent and self.is_caravan_sold_by_player(opponent, caravan_index):
            return True
        return False