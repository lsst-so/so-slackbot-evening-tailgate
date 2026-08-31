"""Evening Tailgate Meeting bot.

Runs a Slack Bolt app in Socket Mode (no public inbound URL needed) that:
  - posts a daily reminder with a "Confirm Meeting" button (see config.REMINDER_TIME),
  - only accepts confirmation from members of a designated Slack User Group,
  - posts an explicit cancellation message if nobody confirms by config.CUTOFF_TIME.

See README.md for setup and DESIGN.md for the full behavior spec.
"""
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import load_config
from .state import StateStore
from . import jobs
from . import messages
from .scheduler import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("tailgate_bot")

cfg = load_config()
store = StateStore(cfg.db_path)
app = App(token=cfg.slack_bot_token)


def _is_authorized(client, user_id: str) -> bool:
    resp = client.usergroups_users_list(usergroup=cfg.usergroup_id)
    return user_id in resp.get("users", [])


@app.action("confirm_tailgate")
def handle_confirm(ack, body, client, respond):
    ack()
    user_id = body["user"]["id"]
    date = jobs.today_str(cfg)

    if not _is_authorized(client, user_id):
        respond(
            response_type="ephemeral",
            text="Sorry, only day-shift observing specialists can confirm this meeting.",
        )
        return

    record = store.get(date)
    if record is None:
        respond(response_type="ephemeral", text="No pending confirmation found for today.")
        return

    if record.status == "cancelled":
        respond(
            response_type="ephemeral",
            text="Too late — today's meeting was already marked cancelled.",
        )
        return

    if record.status == "confirmed":
        respond(
            response_type="ephemeral",
            text=f"Already confirmed by <@{record.confirmed_by}>.",
        )
        return

    confirmed = store.confirm(date, user_id)
    if not confirmed:
        # Lost a race with another click between the read above and here.
        fresh = store.get(date)
        respond(
            response_type="ephemeral",
            text=f"Already confirmed by <@{fresh.confirmed_by}>." if fresh else "Already resolved.",
        )
        return

    notice_blocks = messages.confirmed_notice_blocks(cfg)
    notice_blocks.append(
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Confirmed by <@{user_id}>"}]}
    )
    client.chat_postMessage(
        channel=cfg.channel_id,
        text=f"Evening Tailgate Meeting confirmed for today at {cfg.meeting_time_label}.",
        blocks=notice_blocks,
    )

    if record.message_ts:
        client.chat_update(
            channel=cfg.channel_id,
            ts=record.message_ts,
            text="Evening Tailgate Meeting — confirmed for today.",
            blocks=messages.reminder_resolved_blocks(cfg, "confirmed"),
        )
    logger.info("Tailgate meeting confirmed for %s by %s", date, user_id)


def main():
    scheduler = build_scheduler(app.client, cfg, store)
    scheduler.start()
    logger.info(
        "Scheduler started: reminder at %s, cutoff at %s (%s)",
        cfg.reminder_time, cfg.cutoff_time, cfg.timezone,
    )
    handler = SocketModeHandler(app, cfg.slack_app_token)
    handler.start()


if __name__ == "__main__":
    main()
