# PowerHelper Dungeon Arena — Design Spec

Date: 2026-07-09  
Status: approved

## Goal

Add a terminal mini-game to PowerHelper that lets the player earn XP in a D&D-style arena brawler. The game uses `python-tcod` for rendering and integrates with the existing player profile stored in `.data/player.json`.

## Architecture

```
commands/
├── hello.md
├── hi-there.md
└── dungeon.md          # slash command /powerhelper:dungeon
skills/
├── using-powerhelper/
├── hi-there/
└── dungeon/            # skill triggered by keywords
    └── SKILL.md
tools/
├── hi-there.py
└── dungeon/
    ├── __init__.py
    ├── main.py         # entry point: parse args, launch tcod
    ├── engine.py       # main loop, entities, combat, waves
    ├── render.py       # tcod rendering (map, UI, logs)
    ├── progression.py  # read/write stats & XP from .data/player.json
    └── constants.py    # window size, colors, monster types
```

## Gameplay — Arena Brawler

- **Map**: single 40×20 room surrounded by walls.
- **Player**: `@` controlled with `ZQSD`, arrow keys, or numpad.
- **Waves**: every N turns, new monsters spawn at the room edges.
- **Monsters**:
  - Goblin `g`: low HP, fast, low damage.
  - Orc `o`: high HP, slow, high damage.
  - Skeleton `s`: medium stats, undead flavor.
- **Combat**: turn-based. Bumping into a monster attacks it. The monster attacks on its turn.
- **End condition**: player dies → game over.
- **Score**: waves survived + monsters killed = XP reward.

## RPG Stats System

Stats are stored under `dungeon_stats` in `.data/player.json`:

```json
{
  "xp": 0,
  "level": 1,
  "title": "Squire",
  "str": 10,
  "dex": 10,
  "con": 10
}
```

- **STR**: increases damage dealt.
- **DEX**: increases dodge chance and attack initiative.
- **CON**: increases max HP.
- **Level up**: every `100 × current_level` XP. Each level grants +1 point to assign to STR, DEX, or CON. In this first version the point is auto-assigned to CON (survivability) to keep the post-game flow non-interactive.
- **Titles**: level-based titles displayed in the `hi-there` dashboard.
  - 1: Squire
  - 5: Knight
  - 10: Champion
  - (extendable)

At the end of each run, earned XP is added, level-ups are applied, and stats are written back to `.data/player.json`.

## Plugin Integration

- **Slash command**: `/powerhelper:dungeon` runs `python3 tools/dungeon/main.py`.
- **Skill keywords**: `play dungeon`, `arena`, `fight`, `dungeon run` trigger the same binary.
- **Requirements**: `tcod` is listed in `requirements-dungeon.txt`.
- **Missing dependency handling**: if `tcod` is not installed, the tool prints:
  ```
  ⚔️  Dungeon Arena requires python-tcod.
  Install it with: pip install tcod
  ```

## Error Handling

- **Missing `tcod`**: clear install message, no crash.
- **Terminal too small**: prompt the user to resize, then exit cleanly.
- **Corrupted player data**: `progression.py` resets stats to defaults when JSON is invalid.
- **Save strategy**: stats are only written at the end of a run, never mid-game.

## Future Extensions

- Data-driven monsters and waves via YAML/JSON files.
- Loot and equipment.
- Multiple rooms / floor exits.
- Persistent high-score board.
