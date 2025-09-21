# filename: player.py
import random
import debug
import copy
from config import (
    NUM_CARAVANS, STARTING_HAND_SIZE, HAND_SIZE_LIMIT, STANDARD_DECK_COMPOSITION,
    CARAVAN_WIN_MAX, CARAVAN_WIN_MIN,
    SCORE_WIN_LANE_WITH_KING, SCORE_WIN_LANE, SCORE_BREAK_OPPONENT_WINNING_LANE,
    SCORE_SETUP_WIN, SCORE_MAJOR_DISRUPTION, SCORE_FLEXIBILITY_BONUS,
    SCORE_KING_PROGRESS, SCORE_BASIC_PROGRESS, SCORE_QUEEN_SYNERGY_PER_CARD,
    UTILITY_VALUE_QUEEN, UTILITY_VALUE_JACK, UTILITY_VALUE_KING,
    CHEAT_PROPHECY_SCORE_BONUS
)
from caravan import Caravan
from card import Card
from typing import TYPE_CHECKING, Dict, Any, List, Optional, Set

if TYPE_CHECKING:
    from game_state import GameState

class Player:
    def __init__(self, name: str, is_ai: bool = False, ai_difficulty: int = 0):
        self.name = name
        self.is_ai = is_ai
        self.ai_difficulty = ai_difficulty
        self.hand: List[Card] = []
        self.caravans: List[Caravan] = [Caravan() for _ in range(NUM_CARAVANS)]
        self.deck: List[Card] = self._create_own_deck()
        if not self.deck:
            raise RuntimeError(f"Deck creation failed for player {self.name}")

    def _create_own_deck(self) -> List[Card]:
        new_deck: List[Card] = [Card(spec['rank'], spec['suit']) for spec in STANDARD_DECK_COMPOSITION]
        random.shuffle(new_deck)
        return new_deck

    def draw_card(self) -> bool:
        if self.deck and len(self.hand) < HAND_SIZE_LIMIT:
            card = self.deck.pop()
            self.hand.append(card)
            return True
        return False

    def deal_starting_hand(self):
        self.hand = []
        for _ in range(STARTING_HAND_SIZE):
            if not self.draw_card():
                break

    def get_ai_action(self, game_state: 'GameState') -> Optional[Dict[str, Any]]:
        opponent = game_state.get_opponent(self)
        if not opponent:
            return {"type": "pass"}

        possible_actions: List[Dict[str, Any]] = []
        unseen_cards = game_state.get_unseen_cards()

        if self.ai_difficulty == 0 and self.deck:
            top_card = self.deck[-1]
            if top_card.is_numeric():
                for i in range(len(self.hand)):
                    temp_hand = self.hand[:i] + self.hand[i+1:] + [top_card]
                    for caravan_idx, caravan in enumerate(self.caravans):
                        if caravan.can_add_numeric(top_card):
                            sim_caravan = caravan.deep_copy()
                            sim_caravan.add_card(top_card)
                            new_total = sim_caravan.total()
                            if 22 <= new_total <= 26 and new_total > opponent.caravans[caravan_idx].total():
                                play_action = {
                                    "type": "play_card",
                                    "target_player": self,
                                    "target_caravan_index": caravan_idx,
                                }
                                cheat_action = {
                                    "score": CHEAT_PROPHECY_SCORE_BONUS + new_total,
                                    "action": {
                                        "type": "cheat_deck_swap_and_play",
                                        "card_from_hand_index": i,
                                        "play_action": play_action,
                                    }
                                }
                                #possible_actions.append(cheat_action)
                                break
                    if any(pa['score'] > CHEAT_PROPHECY_SCORE_BONUS for pa in possible_actions): break

        for card_index, card in enumerate(self.hand):
            if card.is_numeric():
                for caravan_index, my_caravan in enumerate(self.caravans):
                    if game_state.is_caravan_sold_by_player(self, caravan_index) or not my_caravan.can_add_numeric(card):
                        continue

                    sim_caravan = my_caravan.deep_copy()
                    sim_caravan.add_card(card)
                    new_total = sim_caravan.total()
                    if new_total > CARAVAN_WIN_MAX: continue

                    score = 0
                    opponent_caravan = opponent.caravans[caravan_index]
                    if CARAVAN_WIN_MIN <= new_total <= CARAVAN_WIN_MAX and new_total > opponent_caravan.total():
                        score = SCORE_WIN_LANE + new_total
                    elif CARAVAN_WIN_MIN <= new_total <= CARAVAN_WIN_MAX:
                        score = SCORE_SETUP_WIN + new_total
                    else:
                        score = SCORE_BASIC_PROGRESS + new_total

                    last_num, _ = my_caravan.get_last_numeric_card_info()
                    if last_num and card.suit == my_caravan.suit:
                        is_ascending = my_caravan.direction == "up" and card.value > last_num.value
                        is_descending = my_caravan.direction == "down" and card.value < last_num.value
                        if not (is_ascending or is_descending):
                            score += SCORE_FLEXIBILITY_BONUS

                    if score > 0:
                        possible_actions.append({"score": score, "action": {"type": "play_card", "card_index": card_index, "target_player": self, "target_caravan_index": caravan_index}})

            elif card.is_face_card():
                target_map = {
                    "king": [self],
                    "jack": [opponent],
                    "queen": [opponent]
                }
                for target_player in target_map.get(card.rank, []):
                    for caravan_index, target_caravan in enumerate(target_player.caravans):
                        if not target_caravan.cards or game_state.is_caravan_sold_by_anyone(self, caravan_index):
                            continue

                        score = 0
                        if card.rank == "king":
                            last_num, _ = target_caravan.get_last_numeric_card_info()
                            if last_num:
                                new_total = target_caravan.total() + last_num.value
                                if new_total > CARAVAN_WIN_MAX: continue
                                op_caravan = opponent.caravans[caravan_index]
                                if CARAVAN_WIN_MIN <= new_total <= CARAVAN_WIN_MAX and new_total > op_caravan.total():
                                    score = SCORE_WIN_LANE_WITH_KING + new_total
                                else:
                                    score = SCORE_KING_PROGRESS + last_num.value

                        elif card.rank == "jack":
                            op_total_before = target_caravan.total()
                            sim_caravan = target_caravan.deep_copy()
                            _, last_num_idx = sim_caravan.get_last_numeric_card_info()
                            sim_caravan.cards = sim_caravan.cards[:last_num_idx]
                            points_removed = op_total_before - sim_caravan.total()

                            if CARAVAN_WIN_MIN <= op_total_before <= CARAVAN_WIN_MAX:
                                score = SCORE_BREAK_OPPONENT_WINNING_LANE + points_removed
                            else:
                                score = SCORE_MAJOR_DISRUPTION + points_removed

                        elif card.rank == "queen":
                            my_synergy_cards = sum(1 for c in self.hand if c.is_numeric() and c.suit == card.suit)
                            op_denial_count = 0
                            if self.ai_difficulty <= 1:
                                op_hand_sim = [c for c in unseen_cards if c.is_numeric()] # Approximation
                                op_denial_count = sum(1 for c in op_hand_sim if c.suit != card.suit) / len(unseen_cards) * len(opponent.hand)

                            score = target_caravan.total() + (my_synergy_cards * SCORE_QUEEN_SYNERGY_PER_CARD) + (op_denial_count * 10)

                        if score > 0:
                            possible_actions.append({"score": score, "action": {"type": "play_card", "card_index": card_index, "target_player": target_player, "target_caravan_index": caravan_index}})

        if not any(a['action']['type'] == 'discard_caravan' for a in possible_actions):
            for i, caravan in enumerate(self.caravans):
                if caravan.cards and caravan.total() > CARAVAN_WIN_MAX and not game_state.is_caravan_sold_by_anyone(self, i):
                    possible_actions.append({'score': 15, 'action': {'type': 'discard_caravan', 'caravan_index': i}})

        if len(self.hand) >= HAND_SIZE_LIMIT or not possible_actions:
            card_to_discard_idx, lowest_potential = -1, 9999
            my_caravan_suits = {c.suit for c in self.caravans if c.suit}

            for idx, card in enumerate(self.hand):
                potential = 0
                if card.is_numeric():
                    potential = card.value
                    if card.suit in my_caravan_suits: potential += 20
                elif card.rank == "king": potential = UTILITY_VALUE_KING
                elif card.rank == "queen": potential = UTILITY_VALUE_QUEEN
                elif card.rank == "jack": potential = UTILITY_VALUE_JACK

                if potential < lowest_potential:
                    lowest_potential = potential
                    card_to_discard_idx = idx

            if card_to_discard_idx != -1:
                score = 5 if not possible_actions else 25
                possible_actions.append({"score": score, "action": {"type": "discard_card", "card_index": card_to_discard_idx}})

        if not possible_actions:
            return {"type": "pass"}

        possible_actions.sort(key=lambda x: x["score"], reverse=True)

        chosen_index = 0
        if self.ai_difficulty > 0:
            chosen_index = self.ai_difficulty - 1

        chosen_index = min(chosen_index, len(possible_actions) - 1)
        chosen_index = max(0, chosen_index)

        selected_action_info = possible_actions[chosen_index]
        debug.log_ai(f"AI ({self.name}) Chose action (Score: {selected_action_info['score']:.1f}): {selected_action_info['action']}")
        return selected_action_info["action"]

    def get_ai_initial_card(self) -> int:
        best_idx, highest_val = -1, -1
        for i, card in enumerate(self.hand):
            if card.is_numeric() and card.value > highest_val:
                highest_val = card.value
                best_idx = i
        return best_idx

    def __repr__(self) -> str:
        return f"Player(Name='{self.name}', AI={self.is_ai}, Hand:{len(self.hand)}, Deck:{len(self.deck)})"