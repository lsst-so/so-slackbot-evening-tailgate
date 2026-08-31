"""Block Kit message builders, kept separate from the handler logic."""
from .config import Config


def reminder_blocks(cfg: Config) -> list:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f":alarm_clock: *Evening Tailgate Meeting* is scheduled for "
                    f"*{cfg.meeting_time_label}* today.\n"
                    f"By default it is *cancelled* — a day-shift observing specialist "
                    f"must confirm below by *{cfg.cutoff_time}* for it to happen."
                ),
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Confirm Meeting", "emoji": True},
                    "style": "primary",
                    "action_id": "confirm_tailgate",
                }
            ],
        },
    ]


def reminder_text_fallback(cfg: Config) -> str:
    return (
        f"Evening Tailgate Meeting at {cfg.meeting_time_label} today — "
        f"cancelled by default unless confirmed by {cfg.cutoff_time}."
    )


def confirmed_notice_blocks(cfg: Config, updated: bool = False) -> list:
    prefix = "Evening Tailgate Meeting — confirmed" if updated else None
    text = (
        f":white_check_mark: *Evening Tailgate Meeting confirmed* for today at "
        f"*{cfg.meeting_time_label}*.\nJoin here: {cfg.meeting_link}"
    )
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]


def cancelled_notice_blocks(cfg: Config) -> list:
    text = (
        f":x: *Evening Tailgate Meeting is cancelled* today — no confirmation was "
        f"received by {cfg.cutoff_time}."
    )
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]


def reminder_resolved_blocks(cfg: Config, status: str) -> list:
    """Replacement blocks for the original reminder message once it's resolved
    (button removed either way)."""
    if status == "confirmed":
        text = f":white_check_mark: Evening Tailgate Meeting — confirmed for today."
    else:
        text = f":x: Evening Tailgate Meeting — cancelled for today (no confirmation)."
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
