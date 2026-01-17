"""
Central configuration file for the Minesweeper game.
Holds all constants, settings, and paths.
"""
import pygame
from enum import Enum
from events import Events


# Screen Dimensions
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
COLOR_DEPTH = 16

# Game Settings
# -----------------------------------------------------------------------------
FIELD_SIZE = (14, 8)
CELL_SIZE = 70
MINE_COUNT_DEFAULT = 10 # A default value if not provided by args
GAME_TITLE = "ASTEROIDSCANNER"
# -----------------------------------------------------------------------------

# Timing
# -----------------------------------------------------------------------------
GAME_OVER_RESET_DELAY = 3000 # ms
FAIL_VIEW_TIMER_LENGTH = 60 # seconds
# -----------------------------------------------------------------------------

# Colors
# -----------------------------------------------------------------------------
class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    DARK_BLUE = (20, 35, 60)
    DARK_RED = (60, 25, 10)
    CELL_REVEALED = (10, 15, 30)

    CELL_OUTLINE = (0, 65, 255)
    CELL_SELECTED = RED
# -----------------------------------------------------------------------------

# Asset Paths
# -----------------------------------------------------------------------------
class FontPaths:
    JERSEY_15 = "fonts/Jersey15-Regular.ttf"

class ImagePaths:
    CROSSHAIR = "img/crosshair64.png"
    ASTEROID = "img/asteroid64.png"
    BACKGROUND = "img/bg10.png"
# -----------------------------------------------------------------------------

# Font Sizes
# -----------------------------------------------------------------------------
class FontSizes:
    REGULAR = 24
    SUBTEXT = 40
    TITLE = 128
# -----------------------------------------------------------------------------

# Text Strings
# -----------------------------------------------------------------------------
STRINGS_GERMAN = {
    "revealed": "Aufgedeckte Felder: ",
    "mission_success": "Mission Erfolgreich.",
    "trajectory_restored": "Der Kurs wurde wiederhergestellt.",
    "critical_error": "Kritischer Systemfehler",
    "enter_prompt": "Drücken Sie ENTER zum Fortfahren",
    "seconds": " Sekunden",
    "until_reset": "bis zur Wiederherstellung"
}

STRINGS_ENGLISH = {
    "revealed": "Revealed Cells: ",
    "mission_success": "Mission Success.",
    "trajectory_restored": "Flight trajectory has been restored",
    "critical_error": "Critical System Error",
    "enter_prompt": "Press ENTER to continue",
    "seconds": " Seconds",
    "until_reset": "until reset"
}

# -----------------------------------------------------------------------------
# Keyboard Input Mapping
# -----------------------------------------------------------------------------
KEY_EVENT_MAP = {
    pygame.K_UP: Events.BUTTON_UP,
    pygame.K_w: Events.BUTTON_UP,
    pygame.K_DOWN: Events.BUTTON_DOWN,
    pygame.K_s: Events.BUTTON_DOWN,
    pygame.K_LEFT: Events.BUTTON_LEFT,
    pygame.K_a: Events.BUTTON_LEFT,
    pygame.K_RIGHT: Events.BUTTON_RIGHT,
    pygame.K_d: Events.BUTTON_RIGHT,
    pygame.K_RETURN: Events.BUTTON_ENTER,
    pygame.K_e: Events.BUTTON_ENTER,
    pygame.K_f: Events.BUTTON_FLAG,
    pygame.K_x: Events.BUTTON_FLAG,
    pygame.K_ESCAPE: Events.QUIT,
    pygame.K_k: Events.QUIT,

}
