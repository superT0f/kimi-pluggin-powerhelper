#!/usr/bin/env python3
"""hi-there daily terminal dashboard for the PowerHelper plugin."""

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


def now() -> datetime:
    return datetime.now(timezone.utc)


def load_cache() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"])
        if now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (KeyError, ValueError, json.JSONDecodeError):
        # Corrupted or malformed cache; will be overwritten.
        pass
    return None


def save_cache(data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["cached_at"] = now().isoformat()
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def main() -> int:
    location = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOCATION

    cached = load_cache()
    if cached:
        weather = cached["weather"]
        news = cached["news"]
    else:
        weather = fetch_weather(location)
        news = fetch_news()
        save_cache({"weather": weather, "news": news})

    print(render_dashboard(location, weather, news))
    return 0


if __name__ == "__main__":
    sys.exit(main())
