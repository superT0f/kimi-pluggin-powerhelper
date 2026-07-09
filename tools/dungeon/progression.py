"""Progression system for Dungeon Arena.

Reads and writes dungeon_stats in .data/player.json.
"""

import json
from pathlib import Path

PLAYER_FILE = Path(".data") / "player.json"

DEFAULT_STATS = {
    "xp": 0,
    "level": 1,
    "title": "Squire",
    "str": 10,
    "dex": 10,
    "con": 10,
}

TITLES = {
    1: "Squire",
    5: "Knight",
    10: "Champion",
    20: "Legend",
}


def title_for_level(level: int) -> str:
    """Return the highest title the player has earned."""
    best = "Squire"
    for threshold, name in sorted(TITLES.items()):
        if level >= threshold:
            best = name
    return best


def xp_for_next_level(level: int) -> int:
    return 100 * level


def load_stats(path: Path = PLAYER_FILE) -> dict:
    """Load dungeon_stats from player.json, returning defaults if missing or corrupt."""
    if not path.exists():
        return dict(DEFAULT_STATS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stats = data.get("dungeon_stats", {})
        merged = dict(DEFAULT_STATS)
        merged.update(stats)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATS)


def save_stats(stats: dict, path: Path = PLAYER_FILE) -> None:
    """Merge dungeon_stats back into player.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["dungeon_stats"] = stats
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_xp(stats: dict, amount: int) -> dict:
    """Add XP and apply level-ups, auto-assigning +1 CON per level."""
    stats["xp"] = stats.get("xp", 0) + amount
    while stats["xp"] >= xp_for_next_level(stats["level"]):
        stats["xp"] -= xp_for_next_level(stats["level"])
        stats["level"] += 1
        stats["con"] += 1
    stats["title"] = title_for_level(stats["level"])
    return stats
