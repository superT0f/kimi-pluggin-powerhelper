# Phrase-of-the-Day Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the PowerHelper `hi-there` Skill with a daily English memory game ("What was yesterday's phrase?", "What will tomorrow's phrase be?") that persists state and records wins in a local hall-of-fame file.

**Architecture:** The Python script `tools/hi-there.py` gains sub-commands (`dashboard`, `check-answer`, `set-phrase`) and a JSON game-state file in `~/.cache/powerhelper/hi-there-game.json`. The Skill reads state, decides which sub-command to invoke, and renders the returned text. Wins are appended to `.data/hall-of-fame.md` (gitignored).

**Tech Stack:** Markdown, JSON, Python 3 standard library.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `tools/hi-there.py` | Dashboard + game engine: state transitions, phrase verification, hall-of-fame updates. |
| `skills/hi-there/SKILL.md` | Conversational Skill that inspects game state and calls the right sub-command. |
| `commands/hi-there.md` | Slash command entry point, same behavior as the Skill. |
| `.gitignore` | Ignores `.data/` and Python cache. |
| `README.md` | Documents the phrase-of-the-day game. |

---

### Task 1: Extend `tools/hi-there.py` with game engine

**Files:**
- Modify: `tools/hi-there.py`

- [ ] **Step 1: Replace the script with the game-enabled version**

Rewrite `tools/hi-there.py` with the following complete content:

```python
#!/usr/bin/env python3
"""hi-there daily terminal dashboard + phrase-of-the-day game for PowerHelper."""

import json
import random
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "powerhelper"
CACHE_FILE = CACHE_DIR / "hi-there.json"
GAME_FILE = CACHE_DIR / "hi-there-game.json"
HALL_OF_FAME_FILE = Path(".data") / "hall-of-fame.md"
CACHE_TTL_HOURS = 24

DEFAULT_LOCATION = "Combs-la-Ville"
WEATHER_URL = "https://wttr.in/{location}?format=3"
NEWS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
NEWS_COUNT = 5

MEMES = [
    r"""
    (\_/)  
    (o.o)  
    (> <)  
    """,
    r"""
     /\_/\
    ( o.o )
     > ^ <
    """,
    r"""
    ___________
   |  OH HAI   |
    -----------
        \
         \
           ^__^
           (oo)\_______
           (__)\       )\/\
               ||----w |
               ||     ||
    """,
    r"""
      ___
     |o o|
     |_<_|_____/
    """,
    r"""
       .-.
      (o o)
      | O \
       \   \
        `~~~'
    """,
]

PHASE_ASK_YESTERDAY = "ask_yesterday"
PHASE_AWAIT_YESTERDAY_ANSWER = "awaiting_yesterday_answer"
PHASE_ASK_TOMORROW = "ask_tomorrow"
PHASE_AWAIT_TOMORROW_PHRASE = "awaiting_tomorrow_phrase"


def now() -> datetime:
    return datetime.now(timezone.utc)


def today_str() -> str:
    return now().strftime("%Y-%m-%d")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_dashboard_cache() -> dict | None:
    data = load_json(CACHE_FILE)
    if not data:
        return None
    try:
        cached_at = datetime.fromisoformat(data["cached_at"])
        if now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (KeyError, ValueError):
        pass
    return None


def save_dashboard_cache(data: dict) -> None:
    data["cached_at"] = now().isoformat()
    save_json(CACHE_FILE, data)


def load_game_state() -> dict:
    data = load_json(GAME_FILE)
    if data:
        return data
    return {
        "phase": PHASE_ASK_YESTERDAY,
        "yesterdays_phrase": None,
        "tomorrows_phrase": None,
        "streak": 0,
        "last_played": None,
    }


def save_game_state(state: dict) -> None:
    save_json(GAME_FILE, state)


def maybe_rotate_day(state: dict) -> None:
    """Move tomorrow's phrase to yesterday when a new day starts."""
    if state["last_played"] != today_str():
        state["yesterdays_phrase"] = state.get("tomorrows_phrase")
        state["tomorrows_phrase"] = None
        state["phase"] = PHASE_ASK_YESTERDAY
        state["last_played"] = today_str()


def fetch_weather(location: str) -> str:
    url = WEATHER_URL.format(location=location)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except urllib.error.URLError as exc:
        return f"Weather unavailable ({exc})"


def fetch_news() -> list[str]:
    try:
        with urllib.request.urlopen(NEWS_URL, timeout=10) as response:
            content = response.read()
        root = ET.fromstring(content)
        titles = []
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                titles.append(title.text.strip())
            if len(titles) >= NEWS_COUNT:
                break
        return titles
    except (urllib.error.URLError, ET.ParseError) as exc:
        return [f"News unavailable ({exc})"]


def render_dashboard(location: str, weather: str, news: list[str]) -> str:
    meme = random.choice(MEMES)
    lines = [
        "----------------------------------------------------------------",
        "  ☀️  Good Morning! Here's your daily briefing",
        "----------------------------------------------------------------",
    ]
    for meme_line in meme.strip("\n").splitlines():
        lines.append(f"{meme_line:^64}")
    lines.extend([
        "----------------------------------------------------------------",
        f"  🌤️  Weather in {location}",
        f"     {weather}",
        "----------------------------------------------------------------",
        "  📰  News",
    ])
    for headline in news:
        safe = headline.encode("ascii", "replace").decode("ascii")
        truncated = (safe[:56] + "...") if len(safe) > 59 else safe
        lines.append(f"     • {truncated}")
    lines.extend([
        "----------------------------------------------------------------",
        "  Run /powerhelper:hi-there for a fresh page",
        "----------------------------------------------------------------",
    ])
    return "\n".join(lines)


def cmd_dashboard(args: list[str]) -> str:
    location = args[0] if args else DEFAULT_LOCATION
    cached = load_dashboard_cache()
    if cached:
        weather = cached["weather"]
        news = cached["news"]
    else:
        weather = fetch_weather(location)
        news = fetch_news()
        save_dashboard_cache({"weather": weather, "news": news})
    return render_dashboard(location, weather, news)


def explain_game() -> str:
    return (
        "🎮 Welcome to the Phrase of the Day mini-game!\n"
        "\n"
        "Each morning I will ask you: 'What was yesterday's phrase?'\n"
        "If you remember it, you score a point and extend your streak.\n"
        "Then I will ask: 'What will tomorrow's phrase be?'\n"
        "Your answer becomes the phrase to remember for the next day.\n"
        "Your wins are recorded in .data/hall-of-fame.md\n"
        "\n"
        "Let's start! What will tomorrow's phrase be?"
    )


def cmd_check_answer(answer: str) -> str:
    state = load_game_state()
    maybe_rotate_day(state)

    if state["phase"] == PHASE_ASK_YESTERDAY and state["yesterdays_phrase"] is None:
        # First day ever or new day without a set phrase.
        state["phase"] = PHASE_AWAIT_TOMORROW_PHRASE
        save_game_state(state)
        return explain_game()

    correct = (answer or "").strip().lower()
    expected = (state.get("yesterdays_phrase") or "").strip().lower()

    if state["phase"] != PHASE_AWAIT_YESTERDAY_ANSWER:
        state["phase"] = PHASE_AWAIT_YESTERDAY_ANSWER
        save_game_state(state)
        return "🤔 I'm waiting for yesterday's phrase. What was it?"

    if correct == expected and expected:
        state["streak"] = state.get("streak", 0) + 1
        state["phase"] = PHASE_ASK_TOMORROW
        save_game_state(state)
        return (
            f"🎉 Correct! Streak: {state['streak']}\n"
            "What will tomorrow's phrase be?"
        )
    else:
        state["streak"] = 0
        state["phase"] = PHASE_ASK_TOMORROW
        save_game_state(state)
        return (
            f"😅 Not quite. Yesterday's phrase was: '{state.get('yesterdays_phrase')}'\n"
            "Streak reset to 0.\n"
            "What will tomorrow's phrase be?"
        )


def update_hall_of_fame(phrase: str, streak: int) -> None:
    HALL_OF_FAME_FILE.parent.mkdir(parents=True, exist_ok=True)
    header = "# Hall of Fame\n\n| Date | Phrase | Streak |\n| --- | --- | --- |\n"
    row = f"| {today_str()} | {phrase} | {streak} |\n"
    if not HALL_OF_FAME_FILE.exists():
        HALL_OF_FAME_FILE.write_text(header + row, encoding="utf-8")
    else:
        text = HALL_OF_FAME_FILE.read_text(encoding="utf-8")
        HALL_OF_FAME_FILE.write_text(text + row, encoding="utf-8")


def cmd_set_phrase(phrase: str) -> str:
    state = load_game_state()
    maybe_rotate_day(state)

    clean = (phrase or "").strip()
    if not clean:
        return "Please provide a non-empty phrase for tomorrow."

    state["tomorrows_phrase"] = clean
    state["phase"] = PHASE_ASK_YESTERDAY
    save_game_state(state)

    streak = state.get("streak", 0)
    update_hall_of_fame(clean, streak)

    return (
        f"✅ Tomorrow's phrase is set: '{clean}'\n"
        f"Current streak: {streak}\n"
        "See you tomorrow for the next round!"
    )


def cmd_start_game(args: list[str]) -> str:
    """Entry point used by the Skill/command to show dashboard + start the game turn."""
    location = args[0] if args else DEFAULT_LOCATION
    dashboard = cmd_dashboard([location])
    state = load_game_state()
    maybe_rotate_day(state)

    if state["yesterdays_phrase"] is None:
        state["phase"] = PHASE_AWAIT_TOMORROW_PHRASE
        save_game_state(state)
        return dashboard + "\n\n" + explain_game()

    if state["phase"] == PHASE_ASK_YESTERDAY:
        state["phase"] = PHASE_AWAIT_YESTERDAY_ANSWER
        save_game_state(state)
        question = "What was yesterday's phrase?"
    elif state["phase"] == PHASE_AWAIT_YESTERDAY_ANSWER:
        question = "What was yesterday's phrase?"
    elif state["phase"] in (PHASE_ASK_TOMORROW, PHASE_AWAIT_TOMORROW_PHRASE):
        question = "What will tomorrow's phrase be?"
    else:
        question = "What was yesterday's phrase?"

    return dashboard + "\n\n🎮 " + question


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: hi-there.py <dashboard|start|check-answer|set-phrase> [args...]")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "dashboard":
        print(cmd_dashboard(args))
    elif command == "start":
        print(cmd_start_game(args))
    elif command == "check-answer":
        answer = args[0] if args else ""
        print(cmd_check_answer(answer))
    elif command == "set-phrase":
        phrase = args[0] if args else ""
        print(cmd_set_phrase(phrase))
    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Validate Python syntax**

Run:

```bash
python3 -m py_compile tools/hi-there.py && echo "syntax OK"
```

Expected output:

```
syntax OK
```

- [ ] **Step 3: Test the dashboard sub-command**

Run:

```bash
python3 tools/hi-there.py dashboard
```

Expected outcome: the dashboard prints with weather, news, and an ASCII meme.

- [ ] **Step 4: Test the first-day game flow**

Run:

```bash
python3 tools/hi-there.py start
```

Expected outcome: dashboard + game explanation + prompt for tomorrow's phrase.

Run:

```bash
python3 tools/hi-there.py set-phrase "the early bird catches the worm"
```

Expected outcome: confirmation message, `~/.cache/powerhelper/hi-there-game.json` updated, `.data/hall-of-fame.md` created.

- [ ] **Step 5: Test the second-day game flow**

Manually edit `~/.cache/powerhelper/hi-there-game.json` so that `last_played` is yesterday and `tomorrows_phrase` is set. Then run:

```bash
python3 tools/hi-there.py start
```

Expected outcome: dashboard + "What was yesterday's phrase?".

Run:

```bash
python3 tools/hi-there.py check-answer "the early bird catches the worm"
```

Expected outcome: correct message, streak incremented, prompt for tomorrow's phrase.

Run:

```bash
python3 tools/hi-there.py set-phrase "a journey of a thousand miles begins with a single step"
```

Expected outcome: confirmation, hall of fame updated.

- [ ] **Step 6: Commit the script changes**

```bash
git add tools/hi-there.py
git commit -m "feat: add phrase-of-the-day game engine"
```

---

### Task 2: Update the `hi-there` Skill

**Files:**
- Modify: `skills/hi-there/SKILL.md`

- [ ] **Step 1: Rewrite the Skill file**

Replace `skills/hi-there/SKILL.md` with the following content:

```markdown
---
name: hi-there
description: Display a daily terminal dashboard and run the Phrase of the Day memory game
type: prompt
whenToUse: When the user says good morning, hi-there, daily briefing, answers the phrase-of-the-day question, or asks for a terminal dashboard
arguments:
  - location
---

You are the PowerHelper `hi-there` dashboard and the Phrase of the Day mini-game host.

All output must be in English.

## Rules

1. Inspect the current game state by reading `~/.cache/powerhelper/hi-there-game.json` via Bash.
2. Based on the `phase` field, call exactly one of the commands below and print its raw output without modification.
3. Never add extra commentary beyond the script output.

## Commands per phase

- If there is no game state file, or `yesterdays_phrase` is null:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" start "$location"
```

- If `phase` is `ask_yesterday` or `awaiting_yesterday_answer`:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" start "$location"
```

Then, when the user replies with their guess, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" check-answer "$ARGUMENTS"
```

- If `phase` is `ask_tomorrow` or `awaiting_tomorrow_phrase`:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" set-phrase "$ARGUMENTS"
```

If no `$ARGUMENTS` are given, prompt the user politely for the missing phrase.
```

- [ ] **Step 2: Verify frontmatter delimiters**

Run:

```bash
grep -q "^---$" skills/hi-there/SKILL.md && echo "frontmatter OK" || echo "frontmatter missing"
```

Expected output:

```
frontmatter OK
```

- [ ] **Step 3: Commit the Skill**

```bash
git add skills/hi-there/SKILL.md
git commit -m "feat: update hi-there skill for phrase game"
```

---

### Task 3: Update the slash command

**Files:**
- Modify: `commands/hi-there.md`

- [ ] **Step 1: Rewrite the command file**

Replace `commands/hi-there.md` with the following content:

```markdown
---
description: Display the daily hi-there terminal dashboard and run the Phrase of the Day game
---

You are the PowerHelper `hi-there` dashboard and the Phrase of the Day mini-game host.

All output must be in English.

Inspect the current game state by reading `~/.cache/powerhelper/hi-there-game.json` via Bash.

- If there is no game state, or `yesterdays_phrase` is null, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" start "$ARGUMENTS"
```

- If `phase` is `ask_yesterday` or `awaiting_yesterday_answer`, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" start "$ARGUMENTS"
```

When the user replies with their guess, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" check-answer "$ARGUMENTS"
```

- If `phase` is `ask_tomorrow` or `awaiting_tomorrow_phrase`, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" set-phrase "$ARGUMENTS"
```

Print the raw script output without modification. Do not add extra commentary.
```

- [ ] **Step 2: Verify the command file exists**

Run:

```bash
test -f commands/hi-there.md && echo "command file exists"
```

Expected output:

```
command file exists
```

- [ ] **Step 3: Commit the command**

```bash
git add commands/hi-there.md
git commit -m "feat: update /powerhelper:hi-there for phrase game"
```

---

### Task 4: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add `.data/` to `.gitignore`**

Append the following line to `.gitignore`:

```text
# Local game data
.data/
```

- [ ] **Step 2: Verify the entry**

Run:

```bash
grep -q "^\.data/" .gitignore && echo ".gitignore OK"
```

Expected output:

```
.gitignore OK
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore local game data directory"
```

---

### Task 5: Update the README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README**

Use the `Read` tool on `README.md`.

- [ ] **Step 2: Update the `hi-there` section**

Replace the existing `## \`hi-there\` daily dashboard` section with:

```markdown
## `hi-there` daily dashboard + Phrase of the Day game

A terminal dashboard that shows:

- an ASCII meme;
- the current weather in Combs-la-Ville (customizable);
- a short list of public news headlines;
- a 24-hour local cache to avoid repeated network calls;
- the **Phrase of the Day** mini-game.

### Dashboard usage

```text
/powerhelper:hi-there
```

Or simply say:

```text
good morning
```

To use a different location:

```text
/skill:hi-there Paris
```

### Phrase of the Day game

Each day the Skill asks:

1. "What was yesterday's phrase?"
2. "What will tomorrow's phrase be?"

If you remember yesterday's phrase, your streak increases and your win is recorded in `.data/hall-of-fame.md`.

#### First day

On the first run, the game is explained in English and you are asked to set tomorrow's phrase directly.

#### Example flow

```text
good morning
# dashboard + "What was yesterday's phrase?"

the early bird catches the worm
# "Correct! Streak: 3" + "What will tomorrow's phrase be?"

a journey of a thousand miles begins with a single step
# "Tomorrow's phrase is set. See you tomorrow!"
```

### Requirements

- Python 3 must be installed and on `PATH`.
- Network access to `wttr.in` and `feeds.bbci.co.uk` (only on the first dashboard run of the day, or when the cache is stale).

### Cache

The dashboard cache lives at `~/.cache/powerhelper/hi-there.json`.
The game state lives at `~/.cache/powerhelper/hi-there-game.json`.
Both are refreshed automatically.
```

- [ ] **Step 3: Verify the section**

Run:

```bash
grep -q "## \`hi-there\` daily dashboard + Phrase of the Day game" README.md && echo "README section OK"
```

Expected output:

```
README section OK
```

- [ ] **Step 4: Commit the README update**

```bash
git add README.md
git commit -m "docs: document phrase-of-the-day game"
```

---

### Task 6: Validate and push

**Files:**
- Read: `tools/hi-there.py`
- Read: `skills/hi-there/SKILL.md`
- Read: `commands/hi-there.md`
- Read: `.gitignore`
- Read: `README.md`

- [ ] **Step 1: Confirm syntax and file presence**

Run:

```bash
python3 -m py_compile tools/hi-there.py && \
ls -1 tools/hi-there.py skills/hi-there/SKILL.md commands/hi-there.md .gitignore README.md
```

Expected output ends with the five file paths.

- [ ] **Step 2: Clean local test cache/state**

Run:

```bash
rm -rf ~/.cache/powerhelper/hi-there-game.json ~/.cache/powerhelper/hi-there.json .data
```

This simulates a fresh install for the final test.

- [ ] **Step 3: Run the first-day flow one last time**

Run:

```bash
python3 tools/hi-there.py start
```

Expected outcome: dashboard + game explanation.

Run:

```bash
python3 tools/hi-there.py set-phrase "test phrase"
```

Expected outcome: confirmation, `.data/hall-of-fame.md` created.

- [ ] **Step 4: Push to GitHub**

Run:

```bash
git status --short && git push
```

Expected outcome: working tree clean, push succeeds.

- [ ] **Step 5: Reinstall the plugin in Kimi Code CLI**

Inside Kimi Code CLI, run:

```text
/plugins install https://github.com/superT0f/kimi-pluggin-powerhelper
/reload
```

Expected outcome: plugin updates without errors.

- [ ] **Step 6: Test the conversational flow in Kimi Code CLI**

Inside Kimi Code CLI, run:

```text
good morning
```

Expected outcome: dashboard + game explanation (first day) or dashboard + "What was yesterday's phrase?" (subsequent day).

Then reply with a phrase and verify the streak/hall-of-fame logic.

---

## Self-Review

### Spec coverage

| Spec section | Implementing task |
| --- | --- |
| Python script with sub-commands `dashboard`, `start`, `check-answer`, `set-phrase` | Task 1 |
| Game state JSON with phases, streak, phrase rotation | Task 1 |
| First-day explanation in English | Task 1 |
| Hall of fame markdown file in `.data/` | Task 1 |
| Skill updated to read state and call correct sub-command | Task 2 |
| Slash command updated | Task 3 |
| `.data/` gitignored | Task 4 |
| README updated | Task 5 |
| End-to-end validation in Kimi Code CLI | Task 6 |

### Placeholder scan

No `TBD`, `TODO`, "implement later", "add appropriate error handling", "write tests for the above", or "similar to Task N" placeholders found.

### Type consistency

- Script sub-commands: `dashboard`, `start`, `check-answer`, `set-phrase`.
- Game phases: `ask_yesterday`, `awaiting_yesterday_answer`, `ask_tomorrow`, `awaiting_tomorrow_phrase`.
- Cache and state paths use `~/.cache/powerhelper/` consistently.
- Hall of fame path uses `.data/hall-of-fame.md` consistently.
