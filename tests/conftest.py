"""Shared fixtures. Everything here is Slack-free so it runs in CI."""
import pytest

from tailgate_bot.config import Config


@pytest.fixture
def make_cfg(tmp_path):
    """Factory for a Config with test defaults; override fields via kwargs."""

    def _make(**overrides):
        base = dict(
            slack_bot_token="xoxb-test",
            slack_app_token="xapp-test",
            channel_id="C1",
            usergroup_id="S1",
            meeting_link="https://meet.example/tailgate",
            timezone="America/Santiago",
            reminder_time="16:15",
            cutoff_time="16:25",
            meeting_time_label="16:30",
            db_path=str(tmp_path / "state.db"),
            mention_usergroup=True,
        )
        base.update(overrides)
        base.setdefault("mention_usergroup_ids", (base["usergroup_id"],))
        return Config(**base)

    return _make


@pytest.fixture
def fake_client():
    """Stand-in for slack_bolt's web client: records calls, returns fake ts."""

    class FakeSlackClient:
        def __init__(self):
            self.calls = []
            self._ts = 0

        def chat_postMessage(self, **kwargs):
            self._ts += 1
            self.calls.append(("chat_postMessage", kwargs))
            return {"ok": True, "ts": f"1000.{self._ts}"}

        def chat_update(self, **kwargs):
            self.calls.append(("chat_update", kwargs))
            return {"ok": True}

        def kinds(self):
            return [name for name, _ in self.calls]

    return FakeSlackClient()
