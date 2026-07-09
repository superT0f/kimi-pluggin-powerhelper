#!/usr/bin/env python3
"""Entry point for Dungeon Arena."""

import sys

from tools.dungeon.progression import add_xp, load_stats, save_stats


def main() -> int:
    try:
        import tcod
    except ImportError:
        print("⚔️  Dungeon Arena requires python-tcod.")
        print("Install it with: pip install tcod")
        return 1

    stats = load_stats()
    print(
        "⚔️  Launching Dungeon Arena... "
        "Press WASD/arrows to move, bump monsters to attack, ESC to quit."
    )

    from tools.dungeon.engine import run_game

    xp_earned, survived = run_game(stats)

    stats = add_xp(stats, xp_earned)
    save_stats(stats)

    print(f"🏆 Run complete! Waves survived: {survived}. XP earned: {xp_earned}.")
    print(
        f"Level {stats['level']} {stats['title']} — "
        f"STR {stats['str']} DEX {stats['dex']} CON {stats['con']} XP {stats['xp']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
