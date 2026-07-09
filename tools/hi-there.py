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
PROFILE_FILE = Path(".data") / "player.md"
PROFILE_VALUES_FILE = Path(".data") / "player.json"
PROFILE_PENDING_FILE = Path(".data") / "profile-pending.json"
CACHE_TTL_HOURS = 24

DEFAULT_LOCATION = "Combs-la-Ville"

DEFAULT_PROFILE_MD = """# Player Profile

Add new rows to any table. On the next run the assistant will ask for any empty or new required field.

## identity

| field | type | required | value |
|---|---|---|---|
| pseudo | text | yes | |
| gender | text | yes | |
| age | number | no | |

## preferences

| field | type | required | value |
|---|---|---|---|
| style | enum:serious,relaxed,casual | yes | |
| theme | enum:light,dark | yes | |
"""
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


# ---------------------------------------------------------------------------
# Player profile
# ---------------------------------------------------------------------------


def ensure_profile_file() -> None:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PROFILE_FILE.exists():
        PROFILE_FILE.write_text(DEFAULT_PROFILE_MD, encoding="utf-8")


def parse_profile_spec() -> dict[str, list[dict]]:
    """Parse player.md into {section: [{field, type, required, value}, ...]}."""
    ensure_profile_file()
    text = PROFILE_FILE.read_text(encoding="utf-8")
    sections: dict[str, list[dict]] = {}
    current_section = None
    in_table = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip().lower()
            sections[current_section] = []
            in_table = False
            continue
        if current_section is None:
            continue
        if "|" not in line:
            in_table = False
            continue
        parts = [p.strip() for p in line.split("|")]
        # Drop exactly the leading/trailing empty cells caused by the outer Markdown pipes.
        if parts and parts[0] == "":
            parts.pop(0)
        if parts and parts[-1] == "":
            parts.pop()
        if not parts:
            continue
        if parts[0].lower() == "field":
            in_table = True
            continue
        if not in_table or len(parts) < 4:
            continue
        if parts[0].startswith("-"):
            continue
        field_type = parts[1].lower()
        options = []
        if field_type.startswith("enum:"):
            options = [opt.strip() for opt in field_type.split(":", 1)[1].split(",")]
            field_type = "enum"
        sections[current_section].append({
            "field": parts[0],
            "type": field_type,
            "required": parts[2].lower() in ("yes", "true", "y"),
            "options": options,
            "value": parts[3] if len(parts) > 3 else "",
        })
    return sections


def load_profile_values() -> dict[str, str]:
    data = load_json(PROFILE_VALUES_FILE)
    return data if data else {}


def save_profile_values(values: dict[str, str]) -> None:
    PROFILE_VALUES_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_json(PROFILE_VALUES_FILE, values)


def pending_profile_field() -> dict | None:
    data = load_json(PROFILE_PENDING_FILE)
    if data and data.get("field"):
        return data
    return None


def set_pending_profile_field(field: str, section: str, meta: dict) -> None:
    PROFILE_PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_json(PROFILE_PENDING_FILE, {"field": field, "section": section, "meta": meta})


def clear_pending_profile_field() -> None:
    if PROFILE_PENDING_FILE.exists():
        PROFILE_PENDING_FILE.unlink()


def missing_profile_fields(spec: dict) -> list[tuple[str, str, dict]]:
    """Return [(section, field, meta), ...] for fields that need a value."""
    values = load_profile_values()
    missing: list[tuple[str, str, dict]] = []
    for section, fields in spec.items():
        for meta in fields:
            value = values.get(meta["field"], "").strip()
            if value:
                continue
            if not meta["required"]:
                continue
            missing.append((section, meta["field"], meta))
    return missing


def question_for_field(meta: dict) -> str:
    field = meta["field"]
    ftype = meta["type"]
    options = meta.get("options", [])
    if ftype == "text":
        return f"Please enter your {field}:"
    if ftype == "number":
        return f"Please enter your {field} (number, optional — press Enter to skip):"
    if ftype == "yes/no":
        return f"{field.capitalize()}? (yes/no):"
    if ftype == "enum" and options:
        return f"Please choose your {field} ({'/'.join(options)}):"
    return f"Please enter your {field}:"


def validate_profile_value(meta: dict, value: str) -> tuple[bool, str]:
    ftype = meta["type"]
    options = meta.get("options", [])
    if ftype == "number":
        if not value.strip():
            return True, ""
        try:
            float(value)
            return True, value
        except ValueError:
            return False, "That doesn't look like a number. Try again."
    if ftype == "yes/no":
        normalized = value.strip().lower()
        if normalized in ("yes", "y"):
            return True, "yes"
        if normalized in ("no", "n"):
            return True, "no"
        return False, "Please answer yes or no."
    if ftype == "enum" and options:
        if value.strip().lower() in [opt.lower() for opt in options]:
            return True, value.strip()
        return False, f"Please choose one of: {', '.join(options)}."
    return True, value.strip()


def render_profile_summary(values: dict[str, str]) -> str:
    lines = ["  👤  Player Profile"]
    for key, val in values.items():
        display = val if val else "—"
        lines.append(f"     • {key.capitalize()}: {display}")
    return "\n".join(lines)


def cmd_profile_setup() -> str:
    """Start or continue the interactive profile setup."""
    spec = parse_profile_spec()
    missing = missing_profile_fields(spec)

    if not missing:
        clear_pending_profile_field()
        return ""

    section, field, meta = missing[0]
    set_pending_profile_field(field, section, meta)
    total = len(missing)
    return (
        "----------------------------------------------------------------\n"
        f"  👤  Profile setup ({total} question{'s' if total > 1 else ''} left)\n"
        "----------------------------------------------------------------\n"
        f"{question_for_field(meta)}"
    )


def cmd_set_profile(value: str) -> str:
    """Store the answer for the pending profile field and continue."""
    pending = pending_profile_field()
    if not pending:
        return cmd_profile_setup() or cmd_start_game([])

    meta = pending["meta"]
    ok, cleaned = validate_profile_value(meta, value)
    if not ok:
        return (
            f"{cleaned}\n"
            f"{question_for_field(meta)}"
        )

    values = load_profile_values()
    values[pending["field"]] = cleaned
    save_profile_values(values)

    # Continue with the next missing field.
    spec = parse_profile_spec()
    missing = missing_profile_fields(spec)
    if missing:
        section, field, meta = missing[0]
        set_pending_profile_field(field, section, meta)
        total = len(missing)
        return (
            "----------------------------------------------------------------\n"
            f"  👤  Profile setup ({total} question{'s' if total > 1 else ''} left)\n"
            "----------------------------------------------------------------\n"
            f"{question_for_field(meta)}"
        )

    clear_pending_profile_field()
    return "✅ Profile complete!\n" + cmd_start_game([])


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


def render_dashboard(location: str, weather: str, news: list[str], profile_values: dict[str, str] | None = None) -> str:
    meme = random.choice(MEMES)
    lines = [
        "----------------------------------------------------------------",
        "  ☀️  Good Morning! Here's your daily briefing",
        "----------------------------------------------------------------",
    ]
    if profile_values:
        lines.append(render_profile_summary(profile_values))
        lines.append("----------------------------------------------------------------")
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
    location = args[0].strip() if args and args[0].strip() else DEFAULT_LOCATION
    cached = load_dashboard_cache()
    if cached:
        weather = cached["weather"]
        news = cached["news"]
    else:
        weather = fetch_weather(location)
        news = fetch_news()
        save_dashboard_cache({"weather": weather, "news": news})
    profile_values = load_profile_values()
    return render_dashboard(location, weather, news, profile_values)


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
    location = args[0].strip() if args and args[0].strip() else DEFAULT_LOCATION

    # 1. Profile setup takes precedence until complete.
    profile_prompt = cmd_profile_setup()
    if profile_prompt:
        return profile_prompt

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
        print("Usage: hi-there.py <dashboard|start|check-answer|set-phrase|profile|set-profile> [args...]")
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
    elif command == "profile":
        print(cmd_profile_setup() or "Profile already complete.")
    elif command == "set-profile":
        value = args[0] if args else ""
        print(cmd_set_profile(value))
    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
