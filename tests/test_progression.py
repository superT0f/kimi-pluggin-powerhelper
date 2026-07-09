from pathlib import Path

from tools.dungeon.progression import DEFAULT_STATS, add_xp, load_stats, save_stats

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


def test_save_and_load_roundtrip():
    if TEST_FILE.exists():
        TEST_FILE.unlink()
    stats = dict(DEFAULT_STATS)
    stats["xp"] = 42
    stats["level"] = 3
    save_stats(stats, TEST_FILE)
    loaded = load_stats(TEST_FILE)
    assert loaded["xp"] == 42
    assert loaded["level"] == 3
