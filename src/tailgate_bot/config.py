"""Configuration loaded from environment variables (see .env.example)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    slack_bot_token: str
    slack_app_token: str
    channel_id: str
    usergroup_id: str
    meeting_link: str
    timezone: str
    reminder_time: str  # "HH:MM", 24h
    cutoff_time: str    # "HH:MM", 24h
    meeting_time_label: str
    db_path: str
    mention_usergroup: bool


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return val


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def load_config() -> Config:
    return Config(
        slack_bot_token=_require("SLACK_BOT_TOKEN"),
        slack_app_token=_require("SLACK_APP_TOKEN"),
        channel_id=_require("TAILGATE_CHANNEL_ID"),
        usergroup_id=_require("DAY_OBS_USERGROUP_ID"),
        meeting_link=_require("TAILGATE_MEETING_LINK"),
        timezone=os.environ.get("TAILGATE_TIMEZONE", "America/Santiago"),
        reminder_time=os.environ.get("TAILGATE_REMINDER_TIME", "16:15"),
        cutoff_time=os.environ.get("TAILGATE_CUTOFF_TIME", "16:25"),
        meeting_time_label=os.environ.get("TAILGATE_MEETING_TIME_LABEL", "16:30"),
        db_path=os.environ.get("TAILGATE_DB_PATH", "tailgate_state.db"),
        mention_usergroup=_env_bool("TAILGATE_MENTION_USERGROUP", True),
    )
