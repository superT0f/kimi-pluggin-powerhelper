"""Constants for Dungeon Arena."""

SCREEN_WIDTH = 60
SCREEN_HEIGHT = 28
MAP_WIDTH = 40
MAP_HEIGHT = 20
PANEL_HEIGHT = 5
MSG_X = 2
MSG_WIDTH = 38
MSG_HEIGHT = PANEL_HEIGHT - 1

# Tile types
TILE_FLOOR = 0
TILE_WALL = 1

# Colors (R, G, B)
COLOR_DARK_WALL = (0, 0, 100)
COLOR_DARK_GROUND = (50, 50, 50)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 0)

# Monsters: name, glyph, color, hp, atk, def, xp_value, speed
MONSTERS = {
    "goblin": {
        "name": "Goblin",
        "glyph": "g",
        "color": (0, 255, 0),
        "hp": 8,
        "atk": 3,
        "def": 0,
        "xp": 10,
        "speed": 1,
    },
    "orc": {
        "name": "Orc",
        "glyph": "o",
        "color": (0, 200, 0),
        "hp": 18,
        "atk": 6,
        "def": 1,
        "xp": 25,
        "speed": 1,
    },
    "skeleton": {
        "name": "Skeleton",
        "glyph": "s",
        "color": (200, 200, 200),
        "hp": 12,
        "atk": 4,
        "def": 1,
        "xp": 15,
        "speed": 1,
    },
}

WAVE_INTERVAL = 20  # player turns between waves
