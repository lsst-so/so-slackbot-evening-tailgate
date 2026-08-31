"""The two daily jobs: post the reminder, and enforce the cutoff."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from config import Config
from state import StateStore
import messages

logger = logging.getLogger(__name__)


def today_str(cfg: Config) -> str:
    return datetime.now(ZoneInfo(cfg.timezone)).date().isoformat()


def post_reminder(client, cfg: Config, store: StateStore) -> None:
    date = today_str(cfg)
    resp = client.chat_postMessage(
        channel=cfg.channel_id,
        text=messages.reminder_text_fallback(cfg),
        blocks=messages.reminder_blocks(cfg),
    )
    store.start_new_day(date, resp["ts"])
    logger.info("Posted tailgate reminder for %s (ts=%s)", date, resp["ts"])


def check_cutoff(client, cfg: Config, store: StateStore) -> None:
    date = today_str(cfg)
    if not store.cancel_if_pending(date):
        logger.info("Cutoff check for %s: nothing to do (already resolved or no reminder)", date)
        return

    client.chat_postMessage(channel=cfg.channel_id, blocks=messages.cancelled_notice_blocks(cfg),
                             text=messages.cancelled_notice_blocks(cfg)[0]["text"]["text"])

    record = store.get(date)
    if record and record.message_ts:
        client.chat_update(
            channel=cfg.channel_id,
            ts=record.message_ts,
            text="Evening Tailgate Meeting — cancelled for today (no confirmation).",
            blocks=messages.reminder_resolved_blocks(cfg, "cancelled"),
        )
    logger.info("Cancelled tailgate meeting for %s (no confirmation by cutoff)", date)
