"""APScheduler wiring for the two daily jobs, in the observatory's local timezone."""
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from state import StateStore
import jobs


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":")
    return int(hour_str), int(minute_str)


def build_scheduler(client, cfg: Config, store: StateStore) -> BackgroundScheduler:
    tz = ZoneInfo(cfg.timezone)
    scheduler = BackgroundScheduler(timezone=tz)

    r_hour, r_min = _parse_hhmm(cfg.reminder_time)
    c_hour, c_min = _parse_hhmm(cfg.cutoff_time)

    scheduler.add_job(
        lambda: jobs.post_reminder(client, cfg, store),
        CronTrigger(hour=r_hour, minute=r_min, timezone=tz, day_of_week="mon-sun"),
        id="tailgate_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: jobs.check_cutoff(client, cfg, store),
        CronTrigger(hour=c_hour, minute=c_min, timezone=tz, day_of_week="mon-sun"),
        id="tailgate_cutoff",
        replace_existing=True,
    )
    return scheduler
