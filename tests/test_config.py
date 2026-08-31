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
    "SCI_SUP_SHIFT_USERGROUP_ID",
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
    # with no SCI_SUP_SHIFT_USERGROUP_ID, only DAY_OBS is mentioned
    assert cfg.mention_usergroup_ids == (cfg.usergroup_id,)


def test_sci_sup_group_is_mentioned_but_not_the_authorizer(clean_env):
    for name in REQUIRED:
        clean_env.setenv(name, "x")
    clean_env.setenv("DAY_OBS_USERGROUP_ID", "S_DAYOBS")
    clean_env.setenv("SCI_SUP_SHIFT_USERGROUP_ID", "S_SCISUP")
    cfg = load_config()
    assert cfg.usergroup_id == "S_DAYOBS"  # still the only authorizer
    assert cfg.mention_usergroup_ids == ("S_DAYOBS", "S_SCISUP")


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
