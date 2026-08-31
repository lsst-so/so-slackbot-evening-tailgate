"""The two daily jobs, driven with a fake Slack client."""
from tailgate_bot import jobs
from tailgate_bot.state import StateStore


def test_post_reminder_posts_and_records_pending(make_cfg, fake_client):
    cfg = make_cfg()
    store = StateStore(cfg.db_path)

    jobs.post_reminder(fake_client, cfg, store)

    date = jobs.today_str(cfg)
    rec = store.get(date)
    assert rec is not None
    assert rec.status == "pending"
    assert rec.message_ts == "1000.1"  # the ts the fake client handed back

    name, kwargs = fake_client.calls[0]
    assert name == "chat_postMessage"
    assert kwargs["channel"] == cfg.channel_id
    assert kwargs["blocks"]


def test_check_cutoff_cancels_and_edits_when_pending(make_cfg, fake_client):
    cfg = make_cfg()
    store = StateStore(cfg.db_path)
    jobs.post_reminder(fake_client, cfg, store)
    fake_client.calls.clear()

    jobs.check_cutoff(fake_client, cfg, store)

    date = jobs.today_str(cfg)
    assert store.get(date).status == "cancelled"
    assert fake_client.kinds() == ["chat_postMessage", "chat_update"]
    update_kwargs = fake_client.calls[-1][1]
    assert update_kwargs["ts"] == "1000.1"


def test_check_cutoff_noop_when_already_confirmed(make_cfg, fake_client):
    cfg = make_cfg()
    store = StateStore(cfg.db_path)
    jobs.post_reminder(fake_client, cfg, store)
    store.confirm(jobs.today_str(cfg), "UAAA")
    fake_client.calls.clear()

    jobs.check_cutoff(fake_client, cfg, store)

    assert fake_client.calls == []
    assert store.get(jobs.today_str(cfg)).status == "confirmed"


def test_check_cutoff_noop_when_no_reminder_posted(make_cfg, fake_client):
    cfg = make_cfg()
    store = StateStore(cfg.db_path)

    jobs.check_cutoff(fake_client, cfg, store)

    assert fake_client.calls == []


def test_check_cutoff_is_idempotent(make_cfg, fake_client):
    cfg = make_cfg()
    store = StateStore(cfg.db_path)
    jobs.post_reminder(fake_client, cfg, store)
    jobs.check_cutoff(fake_client, cfg, store)
    fake_client.calls.clear()

    jobs.check_cutoff(fake_client, cfg, store)  # second cutoff, same day

    assert fake_client.calls == []
