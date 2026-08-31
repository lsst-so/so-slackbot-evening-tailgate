"""load_config(): required vars raise, optional vars fall back to defaults."""
import pytest

from tailgate_bot.config import load_config

REQUIRED = (
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "TAILGATE_CHANNEL_ID",
    "DAY_OBS_USERGROUP_ID",
    "TAILGATE_MEETING_LINK",
)
OPTIONAL = (
    "TAILGATE_TIMEZONE",
    "TAILGATE_REMINDER_TIME",
    "TAILGATE_CUTOFF_TIME",
    "TAILGATE_MEETING_TIME_LABEL",
    "TAILGATE_DB_PATH",
    "TAILGATE_MENTION_USERGROUP",
)


@pytest.fixture
def clean_env(monkeypatch):
    for name in REQUIRED + OPTIONAL:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_missing_required_var_raises(clean_env):
    for name in REQUIRED[1:]:
        clean_env.setenv(name, "x")
    # SLACK_BOT_TOKEN still unset
    with pytest.raises(RuntimeError, match="SLACK_BOT_TOKEN"):
        load_config()


def test_defaults_when_optional_unset(clean_env):
    for name in REQUIRED:
        clean_env.setenv(name, "x")
    cfg = load_config()
    assert cfg.timezone == "America/Santiago"
    assert cfg.reminder_time == "16:15"
    assert cfg.cutoff_time == "16:25"
    assert cfg.meeting_time_label == "16:30"
    assert cfg.db_path == "tailgate_state.db"
    assert cfg.mention_usergroup is True


def test_optional_overrides_applied(clean_env):
    for name in REQUIRED:
        clean_env.setenv(name, "x")
    clean_env.setenv("TAILGATE_REMINDER_TIME", "17:00")
    clean_env.setenv("TAILGATE_DB_PATH", "/data/tailgate_state.db")
    cfg = load_config()
    assert cfg.reminder_time == "17:00"
    assert cfg.db_path == "/data/tailgate_state.db"


@pytest.mark.parametrize(
    "raw, expected",
    [("false", False), ("0", False), ("no", False), ("off", False),
     ("true", True), ("1", True), ("YES", True), ("On", True)],
)
def test_mention_usergroup_parsing(clean_env, raw, expected):
    for name in REQUIRED:
        clean_env.setenv(name, "x")
    clean_env.setenv("TAILGATE_MENTION_USERGROUP", raw)
    assert load_config().mention_usergroup is expected
