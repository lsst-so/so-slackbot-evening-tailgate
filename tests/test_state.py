"""State machine: pending -> confirmed / cancelled, and the race guards."""
import pytest

from tailgate_bot.state import StateStore

DATE = "2026-08-31"


@pytest.fixture
def store(tmp_path):
    return StateStore(str(tmp_path / "s.db"))


def test_unknown_day_is_none(store):
    assert store.get(DATE) is None


def test_start_new_day_is_pending(store):
    store.start_new_day(DATE, "111.222")
    rec = store.get(DATE)
    assert rec.status == "pending"
    assert rec.message_ts == "111.222"
    assert rec.confirmed_by is None


def test_first_confirm_wins_second_loses(store):
    store.start_new_day(DATE, "1")
    assert store.confirm(DATE, "UAAA") is True
    assert store.confirm(DATE, "UBBB") is False
    rec = store.get(DATE)
    assert rec.status == "confirmed"
    assert rec.confirmed_by == "UAAA"
    assert rec.confirmed_at is not None


def test_confirm_without_reminder_rejected(store):
    assert store.confirm(DATE, "UAAA") is False


def test_cutoff_cancels_only_when_pending(store):
    store.start_new_day(DATE, "1")
    assert store.cancel_if_pending(DATE) is True
    assert store.get(DATE).status == "cancelled"
    assert store.cancel_if_pending(DATE) is False  # idempotent


def test_cutoff_noop_when_no_reminder(store):
    assert store.cancel_if_pending(DATE) is False


def test_cutoff_noop_after_confirm(store):
    store.start_new_day(DATE, "1")
    store.confirm(DATE, "UAAA")
    assert store.cancel_if_pending(DATE) is False
    assert store.get(DATE).status == "confirmed"


def test_confirm_after_cancel_rejected(store):
    store.start_new_day(DATE, "1")
    store.cancel_if_pending(DATE)
    assert store.confirm(DATE, "UAAA") is False


def test_start_new_day_resets_stale_row(store):
    store.start_new_day(DATE, "1")
    store.confirm(DATE, "UAAA")
    store.start_new_day(DATE, "2")  # next day's post reuses the same date row
    rec = store.get(DATE)
    assert rec.status == "pending"
    assert rec.message_ts == "2"
    assert rec.confirmed_by is None


def test_days_are_independent(store):
    store.start_new_day("2026-08-31", "1")
    store.start_new_day("2026-09-01", "2")
    store.confirm("2026-08-31", "UAAA")
    assert store.get("2026-08-31").status == "confirmed"
    assert store.get("2026-09-01").status == "pending"


def test_state_survives_reopen(tmp_path):
    path = str(tmp_path / "s.db")
    StateStore(path).start_new_day(DATE, "1")
    StateStore(path).confirm(DATE, "UAAA")
    assert StateStore(path).get(DATE).status == "confirmed"
