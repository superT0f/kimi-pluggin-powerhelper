#!/usr/bin/env python3
"""Quota watcher for PowerHelper.

Parses Kimi Code CLI /usage output and alerts on thresholds.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ALERT_FILE = Path(".data") / "quota-alerts.json"
REMINDER_EVERY_N_TURNS = 10
FIRST_ALERT_PCT = 70
TIER_STEP = 5


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_state(path: Path = ALERT_FILE) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict, path: Path = ALERT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_window(state: dict, window: str) -> dict:
    if window not in state:
        state[window] = {
            "last_alert_pct": 0,
            "last_alert_date": "",
            "turn_counter": 0,
        }
    return state[window]


def parse_usage(text: str) -> dict:
    """Extract daily and weekly usage numbers from /usage output."""
    result: dict = {}

    # Format 1: explicit lines like "Daily usage: 14500 / 20000 tokens (72.5%)"
    exact_patterns = [
        (r"daily[^\n]*?(?P<used>\d+)\s*/\s*(?P<total>\d+)[^\n]*?\((?P<pct>\d+(?:\.\d+)?)\s*%?\)", "daily"),
        (r"weekly[^\n]*?(?P<used>\d+)\s*/\s*(?P<total>\d+)[^\n]*?\((?P<pct>\d+(?:\.\d+)?)\s*%?\)", "weekly"),
    ]
    for pattern, window in exact_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[window] = {
                "used": int(match.group("used")),
                "total": int(match.group("total")),
                "pct": float(match.group("pct")),
            }

    # Format 2: Kimi Code CLI /usage panel
    #   Weekly limit  ████████████░░░░░░░░  59% used  resets in 2d 19h 47m
    #   5h limit      ███░░░░░░░░░░░░░░░░░  13% used  resets in 2h 47m
    weekly_match = re.search(
        r"weekly\s+limit\s+\S+\s+(?P<pct>\d+(?:\.\d+)?)%\s+used",
        text,
        re.IGNORECASE,
    )
    if weekly_match:
        result.setdefault("weekly", {
            "used": 0,
            "total": 0,
            "pct": float(weekly_match.group("pct")),
        })

    short_match = re.search(
        r"(?P<hours>\d+)h\s+limit\s+\S+\s+(?P<pct>\d+(?:\.\d+)?)%\s+used",
        text,
        re.IGNORECASE,
    )
    if short_match:
        result.setdefault("daily", {
            "used": 0,
            "total": 0,
            "pct": float(short_match.group("pct")),
        })

    return result


def tier_for_pct(pct: float) -> int:
    """Return the highest alert tier reached by pct, or 0 if below first alert."""
    if pct < FIRST_ALERT_PCT:
        return 0
    tier = FIRST_ALERT_PCT
    while tier + TIER_STEP <= 100 and pct >= tier + TIER_STEP:
        tier += TIER_STEP
    return tier


def compute_alerts(usage: dict, state: dict) -> str:
    """Update state and return a human-readable alert message."""
    messages = []
    for window in ("daily", "weekly"):
        data = usage.get(window)
        if not data:
            continue
        win_state = ensure_window(state, window)
        pct = data["pct"]
        tier = tier_for_pct(pct)
        last_tier = win_state.get("last_alert_pct", 0)

        # Detect reset: pct dropped more than 15 points below last tier.
        if last_tier > 0 and pct < max(0, last_tier - 15):
            win_state["last_alert_pct"] = 0
            win_state["last_alert_date"] = ""
            messages.append(f"🔄 {window.capitalize()} quota appears to have reset (now {pct:.1f}%).")
            last_tier = 0

        if tier > 0 and tier > last_tier:
            win_state["last_alert_pct"] = tier
            win_state["last_alert_date"] = today_str()
            messages.append(
                f"⚠️  {window.capitalize()} quota at {pct:.1f}% — threshold {tier}% reached."
            )

    if not messages:
        return "✅ No new quota threshold crossed."
    return "\n".join(messages)


def reminder(state: dict | None = None) -> str:
    """Increment turn counter and return a reminder every N turns."""
    if state is None:
        state = load_state()
    ensure_window(state, "daily")
    ensure_window(state, "weekly")
    state["daily"]["turn_counter"] += 1
    state["weekly"]["turn_counter"] += 1
    daily_count = state["daily"]["turn_counter"]
    weekly_count = state["weekly"]["turn_counter"]
    save_state(state)
    if daily_count % REMINDER_EVERY_N_TURNS == 0 or weekly_count % REMINDER_EVERY_N_TURNS == 0:
        return "💡 Tip: run /usage and say 'quota' to check your daily/weekly token usage."
    return ""


def session_check(state: dict | None = None) -> str:
    """On session start, remind if last alert was >= 70%."""
    if state is None:
        state = load_state()
    messages = []
    for window in ("daily", "weekly"):
        win_state = state.get(window, {})
        last_tier = win_state.get("last_alert_pct", 0)
        if last_tier >= FIRST_ALERT_PCT:
            messages.append(
                f"⚠️  Last {window} quota alert was {last_tier}%. "
                "Run /usage and say 'quota' to check the current level."
            )
    if messages:
        return "\n".join(messages)
    return ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: quota.py <check|remind|session>")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "check":
        text = " ".join(args)
        if not text:
            print("Please paste the output of /usage after the command.")
            return 0
        usage = parse_usage(text)
        if not usage:
            print("Could not parse /usage output.")
            print("Expected something like:")
            print("  'Daily usage: 12345 / 20000 tokens (61.7%)'")
            print("or the Kimi Code CLI /usage panel with 'Weekly limit ... 59% used'.")
            return 0
        state = load_state()
        result = compute_alerts(usage, state)
        save_state(state)
        print(result)
    elif command == "remind":
        msg = reminder()
        if msg:
            print(msg)
    elif command == "session":
        msg = session_check()
        if msg:
            print(msg)
    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
