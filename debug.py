# filename: debug.py
import traceback

DEBUG_MODE = True

ENABLE_STARTUP_DEBUG = False
ENABLE_GAME_EVENT_DEBUG = False
ENABLE_AI_DEBUG = True
ENABLE_ACTION_DEBUG = False
ENABLE_UI_DEBUG = False
ENABLE_WARNING_DEBUG = True

def log_startup(message: str, *args):
    if DEBUG_MODE and ENABLE_STARTUP_DEBUG:
        if args:
            print(f"[STARTUP] {message.format(*args)}")
        else:
            print(f"[STARTUP] {message}")

def log_event(message: str, *args):
    if DEBUG_MODE and ENABLE_GAME_EVENT_DEBUG:
        if args:
            print(f"[EVENT] {message.format(*args)}")
        else:
            print(f"[EVENT] {message}")

def log_ai(message: str, *args):
    if DEBUG_MODE and ENABLE_AI_DEBUG:
        if args:
            print(f"[AI] {message.format(*args)}")
        else:
            print(f"[AI] {message}")

def log_action(message: str, *args):
    if DEBUG_MODE and ENABLE_ACTION_DEBUG:
        if args:
            print(f"[ACTION] {message.format(*args)}")
        else:
            print(f"[ACTION] {message}")

def log_ui(message: str, *args):
    if DEBUG_MODE and ENABLE_UI_DEBUG:
        if args:
            print(f"[UI] {message.format(*args)}")
        else:
            print(f"[UI] {message}")

def log_warning(message: str, *args):
    if DEBUG_MODE and ENABLE_WARNING_DEBUG:
        if args:
            print(f"[WARNING] {message.format(*args)}")
        else:
            print(f"[WARNING] {message}")

def log_error(message: str, *args, include_traceback: bool = False):
    if args:
        print(f"[ERROR] {message.format(*args)}")
    else:
        print(f"[ERROR] {message}")
    if include_traceback:
        traceback.print_exc()

def print_deck_composition_check():
    if DEBUG_MODE and ENABLE_STARTUP_DEBUG:
        from config import STANDARD_DECK_COMPOSITION, NUMERIC_RANKS, FACE_RANKS, SPECIAL_RANKS, SUITS
        expected_deck_size = (len(NUMERIC_RANKS) * len(SUITS)) + \
                             (len(FACE_RANKS) * len(SUITS)) + \
                             len(SPECIAL_RANKS) 

        actual_size = len(STANDARD_DECK_COMPOSITION)
        if actual_size != expected_deck_size:
            log_warning(
                "Deck composition has {} cards, but expected {} based on ranks and suits.",
                actual_size,
                expected_deck_size
            )
        else:
            log_startup(
                "Deck composition check passed: {} cards.",
                actual_size
            )