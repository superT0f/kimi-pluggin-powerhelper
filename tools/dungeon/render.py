"""Rendering helpers for Dungeon Arena."""

from pathlib import Path

import tcod
from tools.dungeon.constants import (
    COLOR_DARK_GROUND,
    COLOR_DARK_WALL,
    COLOR_WHITE,
    MAP_HEIGHT,
    MAP_WIDTH,
    MSG_HEIGHT,
    MSG_WIDTH,
    MSG_X,
    PANEL_HEIGHT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_FLOOR,
    TILE_WALL,
)


def _find_tileset() -> str | None:
    """Locate the tcod bundled tileset."""
    import tcod as _tcod

    pkg_root = Path(_tcod.__file__).parent
    candidate = pkg_root / ".." / "dejavu10x10_gs_tc.png"
    if candidate.exists():
        return str(candidate.resolve())
    for parent in pkg_root.parents:
        for sub in ("dejavu10x10_gs_tc.png", "data/dejavu10x10_gs_tc.png"):
            candidate = parent / sub
            if candidate.exists():
                return str(candidate.resolve())
    return None


def setup() -> tuple[tcod.context.Context, tcod.Console]:
    """Create tcod context and root console."""
    tileset_path = _find_tileset()
    if tileset_path:
        tileset = tcod.tileset.load_tilesheet(
            tileset_path,
            32,
            8,
            tcod.tileset.CHARMAP_TCOD,
        )
    else:
        tileset = tcod.tileset.load_tilesheet(
            "dejavu10x10_gs_tc.png",
            32,
            8,
            tcod.tileset.CHARMAP_TCOD,
        )
    context = tcod.context.new_terminal(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        tileset=tileset,
        title="PowerHelper Dungeon Arena",
        vsync=True,
    )
    root = tcod.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
    return context, root


def draw_map(console: tcod.Console, dungeon: list[list[int]]) -> None:
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = dungeon[y][x]
            if tile == TILE_WALL:
                console.print(x, y, "#", fg=COLOR_DARK_WALL)
            else:
                console.print(x, y, ".", fg=COLOR_DARK_GROUND)


def draw_entities(console: tcod.Console, entities: list) -> None:
    for entity in entities:
        if entity.hp > 0:
            console.print(entity.x, entity.y, entity.glyph, fg=entity.color)


def draw_ui(
    console: tcod.Console,
    player,
    wave: int,
    messages: list[str],
    stats: dict,
) -> None:
    """Draw bottom panel with HP, wave, stats, and messages."""
    panel_y = SCREEN_HEIGHT - PANEL_HEIGHT
    for y in range(panel_y, SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            console.print(x, y, " ", bg=(20, 20, 20))

    bar_text = f"HP: {player.hp}/{player.max_hp}"
    console.print(2, panel_y + 1, bar_text, fg=COLOR_WHITE)

    console.print(22, panel_y + 1, f"Wave: {wave}", fg=COLOR_WHITE)
    console.print(32, panel_y + 1, f"LVL {stats['level']} {stats['title']}", fg=COLOR_WHITE)
    console.print(32, panel_y + 2, f"XP: {stats['xp']}", fg=COLOR_WHITE)

    for i, msg in enumerate(messages[-MSG_HEIGHT:]):
        console.print(MSG_X, panel_y + 1 + i, msg, fg=COLOR_WHITE)


def render_all(
    context: tcod.context.Context,
    root: tcod.Console,
    dungeon: list[list[int]],
    entities: list,
    player,
    wave: int,
    messages: list[str],
    stats: dict,
) -> None:
    draw_map(root, dungeon)
    draw_entities(root, entities)
    draw_ui(root, player, wave, messages, stats)
    context.present(root)
