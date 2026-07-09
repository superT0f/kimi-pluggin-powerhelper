# Dungeon Arena Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a D&D-style arena brawler mini-game using `python-tcod`, integrated with the PowerHelper plugin and player profile.

**Architecture:** A modular Python package under `tools/dungeon/` handles rendering, game logic, and progression. A slash command and skill trigger the entry point. Stats and XP are persisted in `.data/player.json`.

**Tech Stack:** Python 3, python-tcod, standard library JSON/Path.

---

## File map

| File | Responsibility |
|---|---|
| `tools/dungeon/__init__.py` | Package marker. |
| `tools/dungeon/constants.py` | Screen size, colors, tile glyphs, monster definitions, title table. |
| `tools/dungeon/progression.py` | Read/write `dungeon_stats` in `.data/player.json`, level-up logic. |
| `tools/dungeon/render.py` | tcod console setup, drawing map, entities, UI panels, messages. |
| `tools/dungeon/engine.py` | Game loop, entity classes, combat, wave spawning, input handling. |
| `tools/dungeon/main.py` | Entry point: dependency check, terminal setup, run engine, save results. |
| `commands/dungeon.md` | Slash command `/powerhelper:dungeon`. |
| `skills/dungeon/SKILL.md` | Skill triggered by keywords. |
| `requirements-dungeon.txt` | Optional dependency list. |
| `README.md` | Updated documentation. |

---

### Task 1: Create dependency list and README note

**Files:**
- Create: `requirements-dungeon.txt`
- Modify: `README.md`

- [ ] **Step 1: Create requirements file**

```text
tcod>=16.0
```

- [ ] **Step 2: Add Dungeon section to README**

After the `hi-there` section, add:

```markdown
## Dungeon Arena mini-game

A D&D-style arena brawler powered by [python-tcod](https://python-tcod.readthedocs.io/).

### Installation

Dungeon Arena requires `python-tcod`:

```bash
pip install tcod
```

### Launch

```text
/powerhelper:dungeon
```

Or say:

```text
play dungeon
```

### Goal

Survive waves of monsters in a single-room dungeon. Earn XP, level up, and improve your STR, DEX, and CON stats. Stats are stored in `.data/player.json` and displayed in the `hi-there` dashboard.
```

- [ ] **Step 3: Commit**

```bash
git add requirements-dungeon.txt README.md
git commit -m "docs: add Dungeon Arena requirements and README section"
```

---

### Task 2: Implement progression module

**Files:**
- Create: `tools/dungeon/progression.py`
- Create: `tests/test_progression.py` (if tests exist; otherwise manual test)

- [ ] **Step 1: Write minimal failing test**

If the project has a `tests/` folder, create `tests/test_progression.py`:

```python
from pathlib import Path
import json
from tools.dungeon.progression import load_stats, add_xp, DEFAULT_STATS

TEST_FILE = Path(".data/test-player.json")

def test_load_default_when_missing():
    if TEST_FILE.exists():
        TEST_FILE.unlink()
    stats = load_stats(TEST_FILE)
    assert stats == DEFAULT_STATS

def test_add_xp_levels_up():
    stats = dict(DEFAULT_STATS)
    stats["xp"] = 90
    stats["level"] = 1
    stats = add_xp(stats, 20)
    assert stats["level"] == 2
    assert stats["xp"] == 10
    assert stats["con"] == DEFAULT_STATS["con"] + 1
```

If no `tests/` folder, skip to Step 3.

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_progression.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement progression.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_progression.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/dungeon/progression.py tests/test_progression.py
git commit -m "feat: add Dungeon Arena progression module"
```

---

### Task 3: Implement constants module

**Files:**
- Create: `tools/dungeon/constants.py`

- [ ] **Step 1: Write constants.py**

```python
"""Constants for Dungeon Arena."""

SCREEN_WIDTH = 60
SCREEN_HEIGHT = 28
MAP_WIDTH = 40
MAP_HEIGHT = 20
PANEL_HEIGHT = 5
BAR_WIDTH = 16
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/dungeon/constants.py
git commit -m "feat: add Dungeon Arena constants"
```

---

### Task 4: Implement render module

**Files:**
- Create: `tools/dungeon/render.py`

- [ ] **Step 1: Write render.py**

```python
"""Rendering helpers for Dungeon Arena."""

import tcod
from tools.dungeon.constants import (
    COLOR_DARK_WALL,
    COLOR_DARK_GROUND,
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


def setup() -> tuple[tcod.context.Context, tcod.Console]:
    """Create tcod context and root console."""
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
```

Note: `dejavu10x10_gs_tc.png` is bundled with python-tcod. The path may need adjustment. If missing, fall back to a system font path or use `tcod.tileset.load_tilesheet` with the tcod package data path.

- [ ] **Step 2: Commit**

```bash
git add tools/dungeon/render.py
git commit -m "feat: add Dungeon Arena render module"
```

---

### Task 5: Implement engine module

**Files:**
- Create: `tools/dungeon/engine.py`

- [ ] **Step 1: Write engine.py**

```python
"""Core game logic for Dungeon Arena."""

import random
import tcod
from tools.dungeon.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    MONSTERS,
    TILE_FLOOR,
    TILE_WALL,
    WAVE_INTERVAL,
)


class Entity:
    def __init__(self, x: int, y: int, glyph: str, color, name: str, hp: int, atk: int, defense: int, xp: int):
        self.x = x
        self.y = y
        self.glyph = glyph
        self.color = color
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.defense = defense
        self.xp = xp

    def take_damage(self, amount: int) -> None:
        self.hp -= max(0, amount - self.defense)
        if self.hp < 0:
            self.hp = 0


def make_dungeon() -> list[list[int]]:
    """Create a single room with walls around."""
    dungeon = [[TILE_WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    for y in range(1, MAP_HEIGHT - 1):
        for x in range(1, MAP_WIDTH - 1):
            dungeon[y][x] = TILE_FLOOR
    return dungeon


def spawn_monster(wave: int) -> Entity:
    """Spawn a monster near the edges, scaling slightly with wave."""
    choices = ["goblin"] * 5 + ["skeleton"] * 3 + ["orc"] * 2
    if wave >= 3:
        choices += ["orc"] * 2
    if wave >= 5:
        choices += ["skeleton"] * 2
    key = random.choice(choices)
    data = MONSTERS[key]
    # Edge spawn
    edge = random.choice(["top", "bottom", "left", "right"])
    if edge == "top":
        x, y = random.randint(1, MAP_WIDTH - 2), 1
    elif edge == "bottom":
        x, y = random.randint(1, MAP_WIDTH - 2), MAP_HEIGHT - 2
    elif edge == "left":
        x, y = 1, random.randint(1, MAP_HEIGHT - 2)
    else:
        x, y = MAP_WIDTH - 2, random.randint(1, MAP_HEIGHT - 2)
    bonus = wave // 3
    return Entity(
        x, y,
        data["glyph"],
        data["color"],
        data["name"],
        data["hp"] + bonus,
        data["atk"] + bonus // 2,
        data["def"] + bonus // 3,
        data["xp"],
    )


def distance(a, b) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def move_towards(entity, target_x: int, target_y: int, dungeon: list[list[int]], entities: list) -> None:
    dx = target_x - entity.x
    dy = target_y - entity.y
    step_x = max(-1, min(1, dx))
    step_y = max(-1, min(1, dy))
    new_x = entity.x + step_x
    new_y = entity.y + step_y
    if dungeon[new_y][new_x] == TILE_WALL:
        return
    if any(e is not entity and e.hp > 0 and e.x == new_x and e.y == new_y for e in entities):
        return
    entity.x = new_x
    entity.y = new_y


def attack(attacker: Entity, defender: Entity, messages: list[str]) -> None:
    damage = max(1, attacker.atk - defender.defense)
    defender.take_damage(damage)
    messages.append(f"{attacker.name} hits {defender.name} for {damage}.")
    if defender.hp <= 0:
        messages.append(f"{defender.name} dies!")


def handle_input(event, player: Entity, dungeon: list[list[int]], entities: list, messages: list[str], stats: dict) -> bool:
    """Handle one player input. Returns True if a turn was consumed."""
    if event.type != "KEYDOWN":
        return False

    key = event.sym
    dx, dy = 0, 0
    if key in (tcod.event.K_UP, tcod.event.K_k, tcod.event.K_KP_8):
        dy = -1
    elif key in (tcod.event.K_DOWN, tcod.event.K_j, tcod.event.K_KP_2):
        dy = 1
    elif key in (tcod.event.K_LEFT, tcod.event.K_h, tcod.event.K_KP_4):
        dx = -1
    elif key in (tcod.event.K_RIGHT, tcod.event.K_l, tcod.event.K_KP_6):
        dx = 1
    elif key == tcod.event.K_ESCAPE:
        raise SystemExit
    else:
        return False

    target_x = player.x + dx
    target_y = player.y + dy
    if dungeon[target_y][target_x] == TILE_WALL:
        return False

    target = next((e for e in entities if e.hp > 0 and e.x == target_x and e.y == target_y), None)
    if target:
        attack(player, target, messages)
    else:
        player.x = target_x
        player.y = target_y
    return True


def run_game(stats: dict):
    """Main game loop. Returns (xp_earned, survived_waves)."""
    dungeon = make_dungeon()
    player = Entity(
        MAP_WIDTH // 2,
        MAP_HEIGHT // 2,
        "@",
        (255, 255, 255),
        "Player",
        20 + (stats["con"] - 10) * 2,
        5 + (stats["str"] - 10) // 2,
        (stats["dex"] - 10) // 3,
        0,
    )
    player.max_hp = player.hp
    entities = [player]
    messages = ["Welcome to Dungeon Arena! Survive the waves."]
    wave = 1
    turn = 0
    spawn_count = 2

    from tools.dungeon.render import setup, render_all
    context, root = setup()

    try:
        while True:
            render_all(context, root, dungeon, entities, player, wave, messages, stats)

            for event in tcod.event.wait():
                if handle_input(event, player, dungeon, entities, messages, stats):
                    turn += 1
                    break

            # Spawn new wave
            if turn > 0 and turn % WAVE_INTERVAL == 0:
                wave += 1
                spawn_count = min(spawn_count + 1, 8)
                messages.append(f"Wave {wave} incoming!")
                for _ in range(spawn_count):
                    entities.append(spawn_monster(wave))

            # Monster turns
            for entity in entities:
                if entity is player or entity.hp <= 0:
                    continue
                if distance(entity, player) == 1:
                    attack(entity, player, messages)
                else:
                    move_towards(entity, player.x, player.y, dungeon, entities)

            if player.hp <= 0:
                messages.append("You died!")
                render_all(context, root, dungeon, entities, player, wave, messages, stats)
                break
    finally:
        context.close()

    xp_earned = sum(e.xp for e in entities if e is not player and e.hp <= 0)
    return xp_earned, wave - 1
```

- [ ] **Step 2: Commit**

```bash
git add tools/dungeon/engine.py
git commit -m "feat: add Dungeon Arena engine module"
```

---

### Task 6: Implement main entry point

**Files:**
- Create: `tools/dungeon/main.py`
- Create: `tools/dungeon/__init__.py`

- [ ] **Step 1: Write main.py**

```python
#!/usr/bin/env python3
"""Entry point for Dungeon Arena."""

import sys
from pathlib import Path

from tools.dungeon.progression import add_xp, load_stats, save_stats


def main() -> int:
    try:
        import tcod
    except ImportError:
        print("⚔️  Dungeon Arena requires python-tcod.")
        print("Install it with: pip install tcod")
        return 1

    stats = load_stats()
    print("⚔️  Launching Dungeon Arena... Press WASD/arrows to move, bump monsters to attack, ESC to quit.")

    from tools.dungeon.engine import run_game
    xp_earned, survived = run_game(stats)

    stats = add_xp(stats, xp_earned)
    save_stats(stats)

    print(f"🏆 Run complete! Waves survived: {survived}. XP earned: {xp_earned}.")
    print(f"Level {stats['level']} {stats['title']} — STR {stats['str']} DEX {stats['dex']} CON {stats['con']} XP {stats['xp']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write __init__.py**

```python
"""Dungeon Arena package."""
```

- [ ] **Step 3: Commit**

```bash
git add tools/dungeon/main.py tools/dungeon/__init__.py
git commit -m "feat: add Dungeon Arena entry point"
```

---

### Task 7: Add slash command

**Files:**
- Create: `commands/dungeon.md`

- [ ] **Step 1: Write dungeon.md**

```markdown
---
description: Launch the Dungeon Arena mini-game
---

You are the PowerHelper Dungeon Arena launcher.

Run the game with:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/dungeon/main.py"
```

Print the raw script output without modification. Do not add extra commentary.
```

- [ ] **Step 2: Commit**

```bash
git add commands/dungeon.md
git commit -m "feat: add /powerhelper:dungeon slash command"
```

---

### Task 8: Add skill

**Files:**
- Create: `skills/dungeon/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: dungeon
description: Launch the Dungeon Arena mini-game
type: prompt
whenToUse: When the user says play dungeon, arena, fight, dungeon run, or asks to play the dungeon mini-game
---

You are the PowerHelper Dungeon Arena launcher.

All output must be in English.

Run the game with:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/dungeon/main.py"
```

Print the raw script output without modification. Do not add extra commentary.
```

- [ ] **Step 2: Commit**

```bash
git add skills/dungeon/SKILL.md
git commit -m "feat: add Dungeon Arena skill"
```

---

### Task 9: Integrate title into hi-there dashboard

**Files:**
- Modify: `tools/hi-there.py`

- [ ] **Step 1: Load dungeon title in dashboard**

In `tools/hi-there.py`, add a helper to load the dungeon title and display it in `render_dashboard`. Example:

```python
def load_dungeon_title() -> str:
    stats = load_json(Path(".data") / "player.json")
    if stats and "dungeon_stats" in stats:
        return f"{stats['dungeon_stats'].get('title', '')} LVL {stats['dungeon_stats'].get('level', 1)}"
    return ""
```

Add the title to the dashboard header next to the player profile.

- [ ] **Step 2: Commit**

```bash
git add tools/hi-there.py
git commit -m "feat: display dungeon title in hi-there dashboard"
```

---

### Task 10: Validate and push

- [ ] **Step 1: Run syntax checks**

```bash
python3 -m py_compile tools/dungeon/*.py
echo "Syntax OK"
```

- [ ] **Step 2: Run progression tests**

```bash
pytest tests/test_progression.py -v
```

Expected: PASS.

- [ ] **Step 3: Manual tcod test**

Install tcod:

```bash
pip install tcod
```

Run the game:

```bash
python3 tools/dungeon/main.py
```

Expected: terminal window opens, player `@` in center, monsters spawn, combat works, ESC quits, stats saved to `.data/player.json`.

- [ ] **Step 4: Push**

```bash
git push origin main
```

---

## Spec coverage check

| Spec requirement | Task |
|---|---|
| python-tcod rendering | Task 4, 6 |
| Modular structure | Tasks 2-6 |
| Arena brawler gameplay | Task 5 |
| STR/DEX/CON stats + XP | Tasks 2, 5, 9 |
| Slash command | Task 7 |
| Skill keywords | Task 8 |
| Missing dependency handling | Task 6 |
| README documentation | Task 1 |
| Title display in hi-there | Task 9 |

## Placeholder scan

No TBD, TODO, or vague steps. Each step includes concrete code or commands.
