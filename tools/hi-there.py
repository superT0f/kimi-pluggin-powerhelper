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
