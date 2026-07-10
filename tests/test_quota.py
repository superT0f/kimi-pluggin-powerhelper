from pathlib import Path
from tools.quota import parse_usage, compute_alerts, tier_for_pct, reminder, session_check, ALERT_FILE


USAGE_TEXT = """Daily usage: 14500 / 20000 tokens (72.5%)
Weekly usage: 34000 / 100000 tokens (34.0%)"""


def test_parse_usage_extracts_daily_and_weekly():
    result = parse_usage(USAGE_TEXT)
    assert result["daily"] == {"used": 14500, "total": 20000, "pct": 72.5}
    assert result["weekly"] == {"used": 34000, "total": 100000, "pct": 34.0}


def test_parse_usage_handles_missing_weekly():
    result = parse_usage("Daily usage: 1000 / 20000 tokens (5.0%)")
    assert "daily" in result
    assert "weekly" not in result


def test_tier_for_pct_below_threshold():
    assert tier_for_pct(69.9) == 0


def test_tier_for_pct_at_thresholds():
    assert tier_for_pct(70.0) == 70
    assert tier_for_pct(74.9) == 70
    assert tier_for_pct(75.0) == 75
    assert tier_for_pct(99.9) == 95
    assert tier_for_pct(100.0) == 100


def test_compute_alerts_triggers_at_70():
    state = {}
    result = compute_alerts({"daily": {"used": 14500, "total": 20000, "pct": 72.5}}, state)
    assert "Daily quota at 72.5%" in result
    assert state["daily"]["last_alert_pct"] == 70


def test_compute_alerts_resets_on_lower_usage():
    state = {"daily": {"last_alert_pct": 80, "last_alert_date": "2026-07-09"}}
    result = compute_alerts({"daily": {"used": 1000, "total": 20000, "pct": 5.0}}, state)
    assert state["daily"]["last_alert_pct"] == 0
    assert "reset" in result.lower()


def test_compute_alerts_no_duplicate_for_same_tier():
    state = {"daily": {"last_alert_pct": 70}}
    result = compute_alerts({"daily": {"used": 15000, "total": 20000, "pct": 75.0}}, state)
    assert "75.0%" in result
    assert state["daily"]["last_alert_pct"] == 75


def test_reminder_silent_between_intervals():
    state = {"daily": {"turn_counter": 1}, "weekly": {"turn_counter": 1}}
    assert reminder(state) == ""


def test_reminder_every_n_turns():
    state = {"daily": {"turn_counter": 9}, "weekly": {"turn_counter": 9}}
    msg = reminder(state)
    assert "Tip" in msg
    assert state["daily"]["turn_counter"] == 10


def test_session_check_warns_on_active_alert():
    state = {"daily": {"last_alert_pct": 75}}
    msg = session_check(state)
    assert "75%" in msg


def test_session_check_silent_when_no_alert():
    assert session_check({}) == ""
