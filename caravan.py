# filename: caravan.py
from card import Card
from config import CARAVAN_WIN_MIN, CARAVAN_WIN_MAX
from typing import Union, Tuple, List, Optional
import copy

class Caravan:
    def __init__(self):
        self.cards: List[Card] = []
        self.direction: Optional[str] = None
        self.suit: Optional[str] = None
        self._cached_total: int = 0
        self._needs_recalc: bool = True

    def _invalidate_cache(self):
        if not self._needs_recalc:
            self._needs_recalc = True

    def total(self) -> int:
        if not self._needs_recalc:
            return self._cached_total
        total_value = 0
        i = 0
        while i < len(self.cards):
            card = self.cards[i]
            if card.is_numeric():
                base_value = card.value
                multiplier = 1
                j = i + 1
                while j < len(self.cards) and self.cards[j].rank == "king":
                    multiplier *= 2
                    j += 1
                total_value += base_value * multiplier
                i = j
            elif card.rank == 'king':
                i += 1
            else:
                total_value += card.value
                i += 1
        self._cached_total = total_value
        self._needs_recalc = False
        return self._cached_total

    def is_winning(self) -> bool:
        t = self.total()
        return CARAVAN_WIN_MIN <= t <= CARAVAN_WIN_MAX

    def get_last_numeric_card_info(self) -> Tuple[Optional[Card], int]:
        for i in range(len(self.cards) - 1, -1, -1):
            if self.cards[i].is_numeric():
                return self.cards[i], i
        return None, -1

    def get_first_numeric_card(self) -> Optional[Card]:
        for card in self.cards:
            if card.is_numeric():
                return card
        return None

    def can_add_numeric(self, card_to_add: Card) -> bool:
        if not card_to_add.is_numeric():
            return False

        last_numeric_card, _ = self.get_last_numeric_card_info()

        if not last_numeric_card:
            return True

        if card_to_add.value == last_numeric_card.value:
            return False

        if self.suit and card_to_add.suit == self.suit:
            return True

        if self.direction == "up" and card_to_add.value > last_numeric_card.value:
            return True
        if self.direction == "down" and card_to_add.value < last_numeric_card.value:
            return True

        if self.direction is None:
            return True

        return False

    def add_card(self, card_to_add: Card) -> bool:
        if not card_to_add.is_numeric():
            return False
        if not self.can_add_numeric(card_to_add):
            return False

        self.cards.append(card_to_add)
        self._invalidate_cache()

        numeric_cards_in_caravan = [c for c in self.cards if c.is_numeric()]
        num_numeric = len(numeric_cards_in_caravan)

        if num_numeric == 1:
            self.suit = card_to_add.suit
        elif num_numeric >= 2 and self.direction is None:
            first_card = numeric_cards_in_caravan[0]
            second_card = numeric_cards_in_caravan[1]
            if second_card.value > first_card.value:
                self.direction = 'up'
            elif second_card.value < first_card.value:
                self.direction = 'down'
        return True

    def add_bonus_point_card_object(self, bonus_card: Card) -> bool:
        if bonus_card.rank != 'bonus_point':
            return False
        self.cards.append(bonus_card)
        self._invalidate_cache()
        return True

    def _add_special_card_raw(self, card_to_add: Card, target_index: int = -1):
        if not card_to_add.is_face_card():
            return
        if target_index == -1 or target_index > len(self.cards):
            self.cards.append(card_to_add)
        else:
            self.cards.insert(target_index, card_to_add)
        self._invalidate_cache()

    def _update_state_after_removal(self):
        self._invalidate_cache()
        if not self.cards:
            self.reset()
            return

        numeric_cards_remaining = [c for c in self.cards if c.is_numeric()]
        if not numeric_cards_remaining:
            self.suit = None
            self.direction = None
            return

        self.suit = numeric_cards_remaining[0].suit
        self.direction = None
        if len(numeric_cards_remaining) >= 2:
            first_num = numeric_cards_remaining[0]
            second_num = numeric_cards_remaining[1]
            if second_num.value > first_num.value:
                self.direction = 'up'
            elif second_num.value < first_num.value:
                self.direction = 'down'

    def reset(self) -> list[Card]:
        discarded_cards = self.cards[:]
        self.cards = []
        self.direction = None
        self.suit = None
        self._cached_total = 0
        self._needs_recalc = False
        return discarded_cards

    def deep_copy(self):
        return copy.deepcopy(self)

    def __str__(self) -> str:
        return ' '.join(repr(card) for card in self.cards) if self.cards else "[Empty]"

    def __repr__(self) -> str:
        total_str = f"{self._cached_total}{'' if self._needs_recalc else ' (cached)'}"
        return (f"Caravan(Cards=[{str(self)}], Dir={self.direction}, "
                f"Suit={self.suit}, Total={total_str})")