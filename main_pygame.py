# filename: main_pygame.py
import pygame
import sys
import os
import debug 

try:
    from config import * 
    from game_pygame import GameController
    from pygame_ui import load_assets, draw_game_state, draw_text, get_card_image, draw_tutorial_overlay 
    from player import Player
    from card import Card
    from typing import Union, Any, Dict, List, Optional, Tuple
except ImportError as e:
    print(f"CRITICAL Error importing game modules: {e}")
    debug.log_error(f"ImportError: {e}", include_traceback=True)
    sys.exit(1)
except Exception as e:
    print(f"CRITICAL An unexpected error occurred during imports: {e}")
    debug.log_error(f"Unexpected import error: {e}", include_traceback=True)
    sys.exit(1)

tutorial_active = False
current_tutorial_image_index = 0

def show_tutorial_screen(show: bool):
    """Shows or hides the tutorial overlay."""
    global tutorial_active, current_tutorial_image_index
    tutorial_active = show
    if show:
        current_tutorial_image_index = 0 
        debug.log_ui("Tutorial activated.")
    else:
        debug.log_ui("Tutorial deactivated.")

def main():
    global tutorial_active, current_tutorial_image_index 

    try:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        debug.log_startup("Pygame initialized successfully.")
    except pygame.error as e:
        print(f"CRITICAL Pygame initialization failed: {e}")
        debug.log_error(f"Pygame initialization error: {e}", include_traceback=True)
        sys.exit(1)

    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Decrypt & Defend")
        clock = pygame.time.Clock()
        debug.log_startup("Screen and clock setup complete.")
    except pygame.error as e:
        print(f"CRITICAL Failed to set up screen: {e}")
        debug.log_error(f"Screen setup error: {e}", include_traceback=True)
        pygame.quit()
        sys.exit(1)

    loaded_tutorial_images = []
    try:
        _bg_img, _card_imgs, _card_back_img, _tut_imgs = load_assets() 
        if not _card_back_img or not _card_imgs:
             print("CRITICAL ERROR: Essential card images (faces or back) failed to load. Cannot run.")
             debug.log_error("Essential card images missing after load_assets.")
             pygame.quit()
             sys.exit(1)
        assets = {
            'background': _bg_img,
            'cards': _card_imgs,
            'back': _card_back_img,
            'tutorial_images': _tut_imgs
        }
        loaded_tutorial_images = _tut_imgs 
        if not loaded_tutorial_images:
            debug.log_warning("No tutorial images loaded. Tutorial button may not function correctly.")

        debug.log_startup("Assets loaded.")
    except Exception as e:
        print(f"CRITICAL Fatal error loading assets: {e}")
        debug.log_error(f"Asset loading exception: {e}", include_traceback=True)
        pygame.quit()
        sys.exit(1)

    controller = GameController()
    controller.start_new_game(ai_difficulty=AI_DIFFICULTY_LEVEL)
    debug.log_startup(f"Game started with AI difficulty from config: {AI_DIFFICULTY_LEVEL}")

    if not controller.game_state or not controller.game_state.players or not controller.game_state.players[0]:
       
        print("CRITICAL Error: Game state or human player not initialized correctly by controller.")
        debug.log_error("Game state or human player not initialized by controller.")
        screen.fill(BLACK)
        
        try:
            font_error_render = FONT_LARGE
        except NameError:
            font_error_render = pygame.font.SysFont('arial', 48)
        draw_text(screen, "Game Init Failed!", font_error_render, RED, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(3000)
        pygame.quit()
        sys.exit(1)


    human_player = controller.game_state.players[0]
    if human_player.is_ai:
        debug.log_warning("Player 0 is configured as AI. UI might not be fully interactive for P0.")

    ui_state: Dict[str, Any] = {
        'selected_card_index': None,
        'selected_card_obj': None,
        'message': None,
        'message_timer': 0,
        'clickable_rects': {"buttons": {}, "tutorial_nav": {}}, 
        'action_pending': None,
        'hand_current_y': HAND_HIDDEN_Y,
        'hand_hovered': False,
        'question_popup_dismiss_pending': False,
        'bonus_point_selected': False,
    }

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        clicked_this_frame = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    clicked_this_frame = True
                    debug.log_ui("Left mouse button clicked at {}", mouse_pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if tutorial_active: 
                        show_tutorial_screen(False)
                    else: 
                        running = False
                if event.key == pygame.K_r and not tutorial_active: 
                    debug.log_event("Restarting game (R pressed).")
                
                    controller.start_new_game(ai_difficulty=AI_DIFFICULTY_LEVEL)
                    if controller.game_state and controller.game_state.players:
                        human_player = controller.game_state.players[0]
                    else:
                        debug.log_error("Failed to restart game properly. Exiting.")
                        running = False; break
                    ui_state['selected_card_index'] = None
                    ui_state['selected_card_obj'] = None
                    ui_state['action_pending'] = None
                    ui_state['question_popup_dismiss_pending'] = False
                    ui_state['bonus_point_selected'] = False
                    ui_state['message'] = None
                    ui_state['message_timer'] = 0
                    controller.animation_details = None
                    show_tutorial_screen(False) 


        if not running: break

        if ui_state['message_timer'] > 0:
           
            ui_state['message_timer'] -= dt_ms
            if ui_state['message_timer'] <= 0:
                ui_state['message'] = None
                ui_state['message_timer'] = 0


        
        if controller.animation_details and \
           controller.animation_details['is_active'] and \
           controller.animation_details.get('start_pos') is None and \
           controller.animation_details['player_who_initiated_action'].is_ai:
            
            debug.log_ui("Setting up AI animation positions in main_pygame.")
            anim_data = controller.animation_details
            ai_player = anim_data['player_who_initiated_action']
            action_details = anim_data['action_to_perform_on_complete']
            start_x_ai, start_y_ai = DECK_POS_OPPONENT
            anim_data['start_pos'] = (start_x_ai + SCALED_CARD_WIDTH // 2, start_y_ai + SCALED_CARD_HEIGHT // 2)
            anim_data['current_pos'] = anim_data['start_pos']
            target_caravan_idx_ai = -1
            target_player_for_ai_action = None
            if action_details['type'] == 'place_initial_card':
                target_caravan_idx_ai = action_details['caravan_index']
                target_player_for_ai_action = ai_player
            elif action_details['type'] == 'play_card':
                target_caravan_idx_ai = action_details['target_caravan_index']
                target_player_for_ai_action = action_details['target_player']
            if target_caravan_idx_ai != -1 and target_player_for_ai_action and controller.game_state:
                caravan_base_x_ai = CARAVAN_START_X + target_caravan_idx_ai * CARAVAN_SPACING
                is_ai_targeting_own = (target_player_for_ai_action == ai_player)
                caravan_base_y_ai = OPPONENT_CARAVAN_Y if is_ai_targeting_own else PLAYER_CARAVAN_Y
                num_cards_on_target_caravan = 0
                if 0 <= target_caravan_idx_ai < len(target_player_for_ai_action.caravans):
                    caravan_obj = target_player_for_ai_action.caravans[target_caravan_idx_ai]
                    num_cards_on_target_caravan = len(caravan_obj.cards)
                end_y_offset_ai = num_cards_on_target_caravan * CARAVAN_CARD_Y_OFFSET
                anim_data['end_pos'] = (
                    caravan_base_x_ai + SCALED_CARD_WIDTH // 2,
                    caravan_base_y_ai + end_y_offset_ai + SCALED_CARD_HEIGHT // 2
                )
                debug.log_ui("AI animation positions set: start={}, end={}", anim_data['start_pos'], anim_data['end_pos'])
            else:
                debug.log_warning("Could not determine end_pos for AI animation. Action: {}. Cancelling anim.", action_details)
                if controller.animation_details: controller.animation_details['is_active'] = False
                if controller.game_state and controller.game_actions:
                    controller.execute_validated_action(ai_player, action_details)
                controller.animation_details = None


        if controller.game_state:
            controller.update(dt_ms)
            controller.game_state.update_message_timer(dt_ms) 

        hand_hover_zone_y_start = HAND_REVEALED_Y - 20
        hand_hover_zone_height = SCREEN_HEIGHT - hand_hover_zone_y_start + 20
        hand_hover_rect = pygame.Rect(0, hand_hover_zone_y_start, SCREEN_WIDTH, hand_hover_zone_height)
        if human_player and human_player.hand and hand_hover_rect.collidepoint(mouse_pos):
            ui_state['hand_hovered'] = True
        else:
            ui_state['hand_hovered'] = False
        target_y = HAND_REVEALED_Y if ui_state['hand_hovered'] else HAND_HIDDEN_Y
        lerp_factor = 0.18
        ui_state['hand_current_y'] += (target_y - ui_state['hand_current_y']) * lerp_factor
        if abs(target_y - ui_state['hand_current_y']) < 1:
            ui_state['hand_current_y'] = target_y


        animation_active_for_input_block = controller.animation_details and controller.animation_details['is_active']

        if tutorial_active and clicked_this_frame:
            tutorial_nav_rects = ui_state.get('clickable_rects', {}).get('tutorial_nav', {})
            prev_rect = tutorial_nav_rects.get('prev')
            next_rect = tutorial_nav_rects.get('next')
            close_rect = tutorial_nav_rects.get('close')

            click_handled_by_tutorial = False
            if prev_rect and prev_rect.collidepoint(mouse_pos):
                if current_tutorial_image_index > 0:
                    current_tutorial_image_index -= 1
                click_handled_by_tutorial = True
            elif next_rect and next_rect.collidepoint(mouse_pos):
                if current_tutorial_image_index < len(loaded_tutorial_images) - 1:
                    current_tutorial_image_index += 1
                else: 
                    show_tutorial_screen(False)
                click_handled_by_tutorial = True
            elif close_rect and close_rect.collidepoint(mouse_pos):
                show_tutorial_screen(False)
                click_handled_by_tutorial = True

            if click_handled_by_tutorial:
                clicked_this_frame = False
        elif controller.game_state and not controller.game_state.game_over and not tutorial_active:
            gs = controller.game_state
            current_player_on_turn = gs.get_current_player()

            if gs.question_popup_active and current_player_on_turn == human_player and not human_player.is_ai:
                
                if clicked_this_frame:
                    popup_interaction_handled = False
                    if ui_state.get('question_popup_dismiss_pending', False):
                        gs.question_feedback = ""
                        if QUESTION_POPUP_RECT.collidepoint(mouse_pos): 
                            gs.question_answered_correctly_this_popup = True
                            gs.next_turn() 
                            ui_state['question_popup_dismiss_pending'] = False
                            popup_interaction_handled = True
                            debug.log_ui("Question popup dismissed.")
                    elif "question_options" in ui_state.get("clickable_rects", {}):
                        for option_item in ui_state["clickable_rects"]["question_options"]:
                            
                            if option_item["rect"].collidepoint(mouse_pos):
                                q_data = gs.current_question_data
                                if q_data:
                                    if option_item["index"] == q_data["answer_index"]:
                                        gs.question_feedback = "Correct! Click popup to continue."
                                        ui_state['question_popup_dismiss_pending'] = True
                                        debug.log_event("Question answered correctly by human.")
                                    else:
                                        gs.question_feedback = "Incorrect. Try Again!"
                                        debug.log_event("Question answered incorrectly by human.")
                                popup_interaction_handled = True
                                break
                    if popup_interaction_handled:
                        clicked_this_frame = False


            elif gs.awaiting_bonus_point_placement and gs.player_awarded_bonus == human_player:
                
                if clicked_this_frame:
                    click_handled_for_bonus = False
                    active_bonus_rect = ui_state.get('clickable_rects', {}).get('active_bonus_point')
                    if active_bonus_rect and active_bonus_rect.collidepoint(mouse_pos):
                        ui_state['bonus_point_selected'] = not ui_state['bonus_point_selected']
                        if ui_state['bonus_point_selected']:
                            ui_state['message'] = "Bonus Point selected. Click a caravan."
                        else:
                            ui_state['message'] = "Click Bonus Point, then target caravan."
                        ui_state['message_timer'] = 3000
                        click_handled_for_bonus = True

                    elif ui_state['bonus_point_selected']:
                        target_player_for_bonus: Optional[Player] = None
                        target_caravan_idx_for_bonus = -1
                        for item in ui_state.get('clickable_rects', {}).get('p_caravans', []):
                            if item['rect'].collidepoint(mouse_pos):
                                target_player_for_bonus = human_player
                                target_caravan_idx_for_bonus = item['index']
                                click_handled_for_bonus = True; break
                        if not click_handled_for_bonus and gs.get_opponent(human_player):
                            opponent = gs.get_opponent(human_player)
                            if opponent:
                                for item in ui_state.get('clickable_rects', {}).get('o_caravans', []):
                                    if item['rect'].collidepoint(mouse_pos):
                                        target_player_for_bonus = opponent
                                        target_caravan_idx_for_bonus = item['index']
                                        click_handled_for_bonus = True; break

                        if target_player_for_bonus is not None and target_caravan_idx_for_bonus != -1:
                            action_data_bonus = {
                                'type': 'apply_bonus_point_effect',
                                'target_player': target_player_for_bonus,
                                'target_caravan_index': target_caravan_idx_for_bonus
                            }
                            if controller.execute_validated_action(gs.player_awarded_bonus, action_data_bonus):
                                gs.awaiting_bonus_point_placement = False
                                gs.player_awarded_bonus = None
                                ui_state['bonus_point_selected'] = False
                                gs.human_player_awaiting_move_after_question = True 
                                ui_state['message'] = "Bonus applied! Now take your turn."; ui_state['message_timer'] = 2500
                            else:
                                ui_state['message'] = "Failed to apply bonus point."; ui_state['message_timer'] = 2000
                    if click_handled_for_bonus:
                        clicked_this_frame = False


            elif controller.is_ai_turn() and \
                 not animation_active_for_input_block and \
                 not gs.human_player_awaiting_move_after_question:
                controller.run_ai_turn()
            elif controller.is_player_turn(human_player) and \
                 not animation_active_for_input_block:
                if clicked_this_frame:
                    click_handled_for_action = False
                    buttons = ui_state.get('clickable_rects', {}).get('buttons', {})
                    for action_name, rect in buttons.items():
                        if rect.collidepoint(mouse_pos):
                            click_handled_for_action = True
                            action_data: Dict[str, Any] = {'type': action_name}
                            perform_action_immediately = True

                            if action_name == 'show_tutorial':
                                show_tutorial_screen(True)
                                action_data = {}
                                perform_action_immediately = False
                            elif action_name == 'quit': running = False; break
                            elif action_name == 'discard_card':
                                if ui_state['selected_card_index'] is not None:
                                    action_data['card_index'] = ui_state['selected_card_index']
                                else:
                                    ui_state['message'] = "Select a card from hand to discard."
                                    ui_state['message_timer'] = 1500
                                    action_data = {}
                            elif action_name == 'discard_caravan':
                                ui_state['action_pending'] = 'discard_caravan'
                                ui_state['message'] = "Click YOUR caravan to discard it."
                                ui_state['message_timer'] = 3000
                                ui_state['selected_card_index'] = None
                                ui_state['selected_card_obj'] = None
                                action_data = {}
                                perform_action_immediately = False
                            elif action_name == 'pass':
                                pass

                            if action_data.get('type') and perform_action_immediately:
                                if controller.execute_validated_action(human_player, action_data):
                                    gs.human_player_awaiting_move_after_question = False
                                    ui_state['selected_card_index'] = None
                                    ui_state['selected_card_obj'] = None
                                    ui_state['action_pending'] = None
                            break 

                    if not click_handled_for_action: 
                        for item in ui_state.get('clickable_rects', {}).get('hand', []):
                            if item['rect'].collidepoint(mouse_pos):
                                click_handled_for_action = True
                                if ui_state['selected_card_index'] == item['index'] and \
                                   ui_state['selected_card_obj'] == item['card']:
                                    ui_state['selected_card_index'] = None
                                    ui_state['selected_card_obj'] = None
                                    ui_state['message'] = None; ui_state['message_timer'] = 0
                                    ui_state['action_pending'] = None
                                    debug.log_ui("Card deselected from hand: {}", item['card'])
                                else:
                                    ui_state['selected_card_index'] = item['index']
                                    ui_state['selected_card_obj'] = item['card']
                                    card_name = str(item['card'])
                                    msg = f"{card_name} selected. Click YOUR EMPTY caravan." if gs.is_setup_phase() \
                                          else f"{card_name} selected. Click target or action button."
                                    ui_state['message'] = msg; ui_state['message_timer'] = 3000
                                    ui_state['action_pending'] = None
                                    debug.log_ui("Card selected from hand: {} at index {}", card_name, item['index'])
                                break
                    if not click_handled_for_action:
                        target_player_for_action: Optional[Player] = None
                        target_caravan_idx_for_action = -1
                        animation_end_pos_human: Optional[Tuple[int,int]] = None
                        for item in ui_state.get('clickable_rects', {}).get('p_caravans', []):
                            if item['rect'].collidepoint(mouse_pos):
                                target_player_for_action = human_player
                                target_caravan_idx_for_action = item['index']
                                caravan_obj = human_player.caravans[target_caravan_idx_for_action]
                                num_cards_on_target = len(caravan_obj.cards)
                                end_y_offset = num_cards_on_target * CARAVAN_CARD_Y_OFFSET
                                animation_end_pos_human = (
                                    item['rect'].centerx,
                                    PLAYER_CARAVAN_Y + end_y_offset + SCALED_CARD_HEIGHT // 2
                                )
                                click_handled_for_action = True; break
                        if not click_handled_for_action and gs.get_opponent(human_player):
                            opponent = gs.get_opponent(human_player)
                            if opponent:
                                for item in ui_state.get('clickable_rects', {}).get('o_caravans', []):
                                    if item['rect'].collidepoint(mouse_pos):
                                        target_player_for_action = opponent
                                        target_caravan_idx_for_action = item['index']
                                        caravan_obj = opponent.caravans[target_caravan_idx_for_action]
                                        num_cards_on_target = len(caravan_obj.cards)
                                        end_y_offset = num_cards_on_target * CARAVAN_CARD_Y_OFFSET
                                        animation_end_pos_human = (
                                            item['rect'].centerx,
                                            OPPONENT_CARAVAN_Y + end_y_offset + SCALED_CARD_HEIGHT // 2
                                        )
                                        click_handled_for_action = True; break
                        if target_player_for_action is not None and target_caravan_idx_for_action != -1:
                            action_data_for_caravan_click: Dict[str, Any] = {}
                            card_for_animation: Optional[Card] = None
                            animation_start_pos_human: Optional[Tuple[int,int]] = None
                            if gs.is_setup_phase():
                                if target_player_for_action == human_player and \
                                   ui_state['selected_card_obj'] and \
                                   ui_state['selected_card_obj'].is_numeric():
                                    action_data_for_caravan_click = {
                                        'type': 'place_initial_card',
                                        'card_index': ui_state['selected_card_index'],
                                        'caravan_index': target_caravan_idx_for_action
                                    }
                                    card_for_animation = ui_state['selected_card_obj']
                                elif target_player_for_action != human_player:
                                     ui_state['message'] = "Cannot place on opponent during setup."; ui_state['message_timer'] = 2000
                                elif not ui_state['selected_card_obj']:
                                     ui_state['message'] = "Select a NUMERIC card from hand first."; ui_state['message_timer'] = 2500
                                else:
                                     ui_state['message'] = "First card on caravan must be NUMERIC."; ui_state['message_timer'] = 2500
                            elif ui_state['action_pending'] == 'discard_caravan':
                                if target_player_for_action == human_player:
                                    action_data_for_caravan_click = {'type': 'discard_caravan', 'caravan_index': target_caravan_idx_for_action}
                                else:
                                    ui_state['message'] = "Can only discard YOUR OWN caravans."; ui_state['message_timer'] = 2000
                            elif ui_state['selected_card_obj']:
                                action_data_for_caravan_click = {
                                    'type': 'play_card',
                                    'card_index': ui_state['selected_card_index'],
                                    'target_player': target_player_for_action,
                                    'target_caravan_index': target_caravan_idx_for_action
                                }
                                card_for_animation = ui_state['selected_card_obj']
                            else:
                                ui_state['message'] = "Select card from hand or an action button first."; ui_state['message_timer'] = 2000

                            if action_data_for_caravan_click.get('type'):
                                if card_for_animation and ui_state['selected_card_index'] is not None:
                                    hand_rects = ui_state.get('clickable_rects', {}).get('hand', [])
                                    selected_hand_item = next((hr_item for hr_item in hand_rects if hr_item['index'] == ui_state['selected_card_index']), None)
                                    if selected_hand_item:
                                        animation_start_pos_human = selected_hand_item['rect'].center

                                    if animation_start_pos_human and animation_end_pos_human:
                                        debug.log_ui("Initiating animation for human player action: {}", action_data_for_caravan_click)
                                        if controller.initiate_action_with_animation(
                                            human_player, action_data_for_caravan_click,
                                            card_for_animation, animation_start_pos_human, animation_end_pos_human
                                        ):
                                            gs.human_player_awaiting_move_after_question = False
                                        ui_state['selected_card_index'] = None
                                        ui_state['selected_card_obj'] = None
                                        ui_state['action_pending'] = None
                                    else: # Fallback if animation positions aren't determined
                                        debug.log_warning("Could not determine animation start/end for human. Executing directly.")
                                        if controller.execute_validated_action(human_player, action_data_for_caravan_click):
                                            gs.human_player_awaiting_move_after_question = False
                                            ui_state['selected_card_index'] = None; ui_state['selected_card_obj'] = None
                                            ui_state['action_pending'] = None
                                else: # No animation needed (e.g. discard caravan)
                                    if controller.execute_validated_action(human_player, action_data_for_caravan_click):
                                        gs.human_player_awaiting_move_after_question = False
                                        ui_state['selected_card_index'] = None; ui_state['selected_card_obj'] = None
                                        ui_state['action_pending'] = None

                    if clicked_this_frame and not click_handled_for_action: 
                        if ui_state['selected_card_index'] is not None or ui_state['action_pending'] is not None:
                            ui_state['selected_card_index'] = None
                            ui_state['selected_card_obj'] = None
                            ui_state['action_pending'] = None
                            ui_state['message'] = None; ui_state['message_timer'] = 0
                            debug.log_ui("Deselected card/action due to background click.")


        
        if controller.animation_details and \
           not controller.animation_details['is_active'] and \
           controller.animation_details.get('action_to_perform_on_complete'):
           
            anim_data = controller.animation_details
            player_for_action = anim_data['player_who_initiated_action']
            action_to_do = anim_data['action_to_perform_on_complete']
            debug.log_action("Executing action post-animation for {}: {}", player_for_action.name, action_to_do)
            if controller.execute_validated_action(player_for_action, action_to_do):
                if controller.game_state and not player_for_action.is_ai : 
                    if controller.game_state.human_player_awaiting_move_after_question: 
                         controller.game_state.human_player_awaiting_move_after_question = False 
            controller.animation_details = None

        elif controller.game_state and controller.game_state.game_over and not tutorial_active:
            if clicked_this_frame:
                buttons = ui_state.get('clickable_rects', {}).get('buttons', {})
               
                if "quit" in buttons and buttons["quit"].collidepoint(mouse_pos): 
                    
                    debug.log_event("Restarting game from game over screen.")
                    controller.start_new_game(ai_difficulty=AI_DIFFICULTY_LEVEL)
                    if controller.game_state and controller.game_state.players:
                        human_player = controller.game_state.players[0]
                    ui_state['selected_card_index'] = None 
                   
                    show_tutorial_screen(False) 


      
        screen.fill(BLACK) 
        if controller.game_state and human_player:
            
            draw_game_state(screen, controller.game_state, human_player, assets, ui_state, controller)
        else:
           
            try:
                font_error_render = FONT_LARGE
            except NameError:
                font_error_render = pygame.font.SysFont('arial', 48)
            draw_text(screen, "Error: Game State Critical Failure", font_error_render, RED, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2))


        
        if tutorial_active:
            tutorial_nav_rects_for_draw = ui_state.get('clickable_rects', {}).get('tutorial_nav', {})
            if not tutorial_nav_rects_for_draw.get('prev'): 
                 debug.log_warning("Tutorial nav rects missing in ui_state. Defining defaults for drawing.")
                 prev_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
                 prev_btn_rect_tut.center = (TUTORIAL_PREV_BTN_CENTER_X, TUTORIAL_NAV_Y)
                 next_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
                 next_btn_rect_tut.center = (TUTORIAL_NEXT_BTN_CENTER_X, TUTORIAL_NAV_Y)
                 close_btn_rect_tut = pygame.Rect(0, 0, TUTORIAL_BTN_WIDTH, TUTORIAL_BTN_HEIGHT)
                 close_btn_rect_tut.center = (TUTORIAL_CLOSE_BTN_CENTER_X, TUTORIAL_NAV_Y)
                 tutorial_nav_rects_for_draw = {'prev': prev_btn_rect_tut, 'next': next_btn_rect_tut, 'close': close_btn_rect_tut}

            draw_tutorial_overlay(screen, current_tutorial_image_index, tutorial_nav_rects_for_draw)

        pygame.display.flip()
   
    pygame.quit()
    debug.log_event("Pygame quit. Exiting.")
    sys.exit()

if __name__ == "__main__":
   
    script_dir = os.path.dirname(os.path.abspath(__file__))
    actual_asset_path = os.path.join(script_dir, ASSET_DIR)
    if not os.path.isdir(actual_asset_path):
        print(f"\n--- CRITICAL ERROR ---")
        print(f"Asset directory '{ASSET_DIR}' not found at expected location: '{actual_asset_path}'")
        print(f"Please ensure an '{ASSET_DIR}' folder exists in the same directory as this script,")
        print(f"and contains all required image assets (cards AND tutorial images).")
        print("----------------------\n")
        try: input("Press Enter to exit...") 
        except EOFError: pass
        sys.exit(1)

    try:
         debug.log_startup("Main script started.")
         debug.print_deck_composition_check()
         main()
    except Exception as e:
         print("\n--- An Unexpected Error Occurred During Runtime ---")
         print(f"Error Type: {type(e).__name__}")
         print(f"Error Details: {e}")
         import traceback
         traceback.print_exc() 
         debug.log_error(f"Unhandled exception in main: {e}", include_traceback=True)
         print("--------------------------------------------------\n")
         pygame.quit()
         try: input("An error occurred. Press Enter to exit...")
         except EOFError: pass
         sys.exit(1)