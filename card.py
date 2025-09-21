# filename: card.py
from config import CARD_VALUES, SUITS, FACE_RANKS, NUMERIC_RANKS, SPECIAL_RANKS

class Card:
    def __init__(self, rank: str, suit: str):
        clean_rank = rank.lower().strip() if isinstance(rank, str) else "unknown"
        clean_suit = suit.lower().strip() if isinstance(suit, str) else ""

        if clean_rank not in (NUMERIC_RANKS + FACE_RANKS + SPECIAL_RANKS):
            self.rank: str = "unknown"
        else:
            self.rank: str = clean_rank

        if self.rank == 'bonus_point':
             self.suit: str = ""
        elif self.rank != "unknown" and clean_suit not in SUITS :
            self.suit: str = ""
        else:
            self.suit: str = clean_suit

        self._value: int = CARD_VALUES.get(self.rank, 0)
        self._is_numeric: bool = self.rank in NUMERIC_RANKS
        self._is_face: bool = self.rank in FACE_RANKS
        self._is_bonus_point: bool = self.rank == 'bonus_point'
        self._is_special: bool = self._is_face or self._is_bonus_point

    @property
    def value(self) -> int:
        return self._value

    def is_numeric(self) -> bool:
        return self._is_numeric

    def is_face_card(self) -> bool:
        return self._is_face

    def is_bonus_point(self) -> bool:
        return self._is_bonus_point

    def is_special(self) -> bool:
        return self._is_special

    def __str__(self) -> str:
        rank_display = self.rank.replace("_", " ").title()
        if self.is_bonus_point():
            return rank_display
        elif self.suit:
            return f"{rank_display} of {self.suit.title()}"
        elif self.rank != "unknown":
            return rank_display
        else:
            return "Unknown Card"

    def __repr__(self) -> str:
        return f"Card('{self.rank}', '{self.suit}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))