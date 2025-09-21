# filename: game_actions.py
from card import Card
from caravan import Caravan
from player import Player
import debug
import random
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from game_state import GameState

class GameActions:
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state

    def execute_action(self, player: Player, action: Dict[str, Any]) -> bool:
        action_type = action.get("type")
        success = False
        should_draw_card = True

        if not player or player not in self.game_state.players:
            return False
        if player != self.game_state.get_current_player() and action_type not in ["apply_bonus_point_effect", "cheat_deck_swap_and_play"]:
            if not (action_type == "apply_bonus_point_effect" and player == self.game_state.player_awarded_bonus):
                return False

        try:
            debug.log_action("Player {} attempting action: {}", player.name, action)
            if action_type == "place_initial_card":
                success = self._execute_place_initial(player, action) if self.game_state.is_setup_phase() else False
                should_draw_card = False
            elif action_type == "play_card":
                success = self._execute_play_card(player, action) if not self.game_state.is_setup_phase() else False
            elif action_type == "discard_card":
                success = self._execute_discard_card(player, action) if not self.game_state.is_setup_phase() else False
            elif action_type == "discard_caravan":
                success = self._execute_discard_caravan(player, action) if not self.game_state.is_setup_phase() else False
            elif action_type == "pass":
                success = True
                should_draw_card = False
            elif action_type == "apply_bonus_point_effect":
                success = self._execute_apply_bonus_point_effect(player, action)
                should_draw_card = False
            elif action_type == "cheat_deck_swap_and_play":
                success = self._execute_cheat_deck_swap_and_play(player, action) if not self.game_state.is_setup_phase() else False
                should_draw_card = False
            else:
                debug.log_warning("Unknown action type received: {}", action_type)

        except Exception as e:
            debug.log_error(f"Error executing action {action_type} for {player.name}: {e}", include_traceback=True)
            success = False

        if success:
            if should_draw_card:
                if not player.draw_card():
                    self.game_state.track_played_card(player.hand[-1])
        return success

    def _execute_place_initial(self, player: Player, action: Dict[str, Any]) -> bool:
        card_index = action.get("card_index", -1)
        caravan_index = action.get("caravan_index", -1)
        if not (0 <= card_index < len(player.hand) and 0 <= caravan_index < len(player.caravans)):
            return False

        card = player.hand[card_index]
        target_caravan = player.caravans[caravan_index]
        if not card.is_numeric() or target_caravan.cards:
            return False

        if target_caravan.add_card(card):
            player.hand.pop(card_index)
            self.game_state.track_played_card(card)
            return True
        return False

    def _execute_play_card(self, player: Player, action: Dict[str, Any]) -> bool:
        card_index = action.get("card_index", -1)
        target_player_obj = action.get("target_player")
        target_caravan_idx = action.get("target_caravan_index", -1)

        if not (0 <= card_index < len(player.hand) and target_player_obj and 0 <= target_caravan_idx < len(target_player_obj.caravans)):
            return False

        card_to_play = player.hand[card_index]
        target_caravan = target_player_obj.caravans[target_caravan_idx]

        if card_to_play.is_bonus_point(): return False
        if not target_caravan.cards and not card_to_play.is_numeric(): return False
        if self.game_state.is_caravan_sold_by_player(target_player_obj, target_caravan_idx): return False
        if card_to_play.is_numeric() and target_player_obj != player: return False

        action_successful = False
        if card_to_play.is_numeric():
            if target_caravan.add_card(card_to_play):
                popped_card = player.hand.pop(card_index)
                self.game_state.track_played_card(popped_card)
                action_successful = True
        elif card_to_play.is_face_card():
             action_successful = self._handle_special_card(player, card_index, card_to_play, target_player_obj, target_caravan)

        return action_successful

    def _execute_apply_bonus_point_effect(self, player_who_answered: Player, action: Dict[str, Any]) -> bool:
        target_player_obj = action.get("target_player")
        target_caravan_idx = action.get("target_caravan_index", -1)

        if not (target_player_obj and 0 <= target_caravan_idx < len(target_player_obj.caravans)):
            return False

        target_caravan = target_player_obj.caravans[target_caravan_idx]
        bonus_card_instance = Card('bonus_point', '')

        if target_caravan.add_bonus_point_card_object(bonus_card_instance):
            self.game_state.track_played_card(bonus_card_instance)
            return True
        return False

    def _execute_discard_card(self, player: Player, action: Dict[str, Any]) -> bool:
        card_index = action.get("card_index", -1)
        if 0 <= card_index < len(player.hand):
            card = player.hand.pop(card_index)
            self.game_state.track_played_card(card)
            return True
        return False

    def _execute_discard_caravan(self, player: Player, action: Dict[str, Any]) -> bool:
        caravan_index = action.get("caravan_index", -1)
        if not (0 <= caravan_index < len(player.caravans)):
            return False
        if self.game_state.is_caravan_sold_by_player(player, caravan_index):
            return False

        target_caravan = player.caravans[caravan_index]
        if not target_caravan.cards:
            return False

        discarded = target_caravan.reset()
        for card in discarded:
            self.game_state.track_played_card(card)
        return True

    def _execute_cheat_deck_swap_and_play(self, player: Player, action: Dict[str, Any]) -> bool:
        if not player.is_ai or player.ai_difficulty != 0: return False

        card_from_hand_idx = action.get("card_from_hand_index", -1)
        if not (player.deck and 0 <= card_from_hand_idx < len(player.hand)):
            return False

        card_from_hand = player.hand.pop(card_from_hand_idx)
        card_from_deck = player.deck.pop()

        player.hand.append(card_from_deck)
        player.deck.append(card_from_hand) # Put it on top of the deck
        random.shuffle(player.deck) # Then shuffle to be fair-ish

        play_action = action.get("play_action")
        if not play_action: return False

        play_action["card_index"] = len(player.hand) - 1 # The new card is always at the end

        debug.log_ai(f"CHEAT: Swapped {card_from_hand} with {card_from_deck} from deck.")

        return self.execute_action(player, play_action)

    def _handle_special_card(self, player: Player, card_index: int, card: Card, target_player: Player, target_caravan: Caravan) -> bool:
        handler = self._SPECIAL_HANDLERS.get(card.rank)
        if handler and handler(self, player, card_index, card, target_player, target_caravan):
            popped_card = player.hand.pop(card_index)
            self.game_state.track_played_card(popped_card)
            return True
        return False

    def _handle_jack(self, player: Player, card_index: int, card_obj: Card, target_player: Player, target_caravan: Caravan) -> bool:
        last_num_card, last_num_idx = target_caravan.get_last_numeric_card_info()
        if last_num_card:
            cards_to_remove = target_caravan.cards[last_num_idx:]
            target_caravan.cards = target_caravan.cards[:last_num_idx]
            for card in cards_to_remove:
                self.game_state.track_played_card(card)
            target_caravan._update_state_after_removal()
            return True
        return False

    def _handle_queen(self, player: Player, card_index: int, card_obj: Card, target_player: Player, target_caravan: Caravan) -> bool:
        if target_caravan.cards and card_obj.suit:
            target_caravan.suit = card_obj.suit
            if target_caravan.direction == "up": target_caravan.direction = "down"
            elif target_caravan.direction == "down": target_caravan.direction = "up"
            target_caravan._invalidate_cache()
            return True
        return False

    def _handle_king(self, player: Player, card_index: int, card_obj: Card, target_player: Player, target_caravan: Caravan) -> bool:
        _, last_num_idx = target_caravan.get_last_numeric_card_info()
        if last_num_idx != -1:
            insert_pos = last_num_idx + 1
            while insert_pos < len(target_caravan.cards) and target_caravan.cards[insert_pos].rank == "king":
                insert_pos += 1
            target_caravan._add_special_card_raw(card_obj, target_index=insert_pos)
            return True
        return False

    _SPECIAL_HANDLERS = {
        "jack": _handle_jack,
        "queen": _handle_queen,
        "king": _handle_king,
    }