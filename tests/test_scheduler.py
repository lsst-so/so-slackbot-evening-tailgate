"""Scheduler wiring: jobs are registered at the configured times.

``build_scheduler`` only assembles the scheduler (it does not start it),
so no job ever fires and there is nothing to shut down.
"""
from tailgate_bot.scheduler import build_scheduler


def test_registers_reminder_and_cutoff_jobs(make_cfg):
    sched = build_scheduler(client=object(), cfg=make_cfg(), store=object())
    ids = {job.id for job in sched.get_jobs()}
    assert ids == {"tailgate_reminder", "tailgate_cutoff"}


def test_jobs_use_configured_times_and_timezone(make_cfg):
    cfg = make_cfg(reminder_time="16:15", cutoff_time="16:25")
    sched = build_scheduler(client=object(), cfg=cfg, store=object())
    by_id = {job.id: job for job in sched.get_jobs()}

    reminder = by_id["tailgate_reminder"].trigger
    cutoff = by_id["tailgate_cutoff"].trigger
    assert "hour='16'" in str(reminder) and "minute='15'" in str(reminder)
    assert "hour='16'" in str(cutoff) and "minute='25'" in str(cutoff)
    assert str(reminder.timezone) == "America/Santiago"
