"""Block Kit builders: pure functions, no Slack."""
from tailgate_bot import messages


def _section_text(blocks):
    return " ".join(
        b["text"]["text"] for b in blocks if b["type"] == "section"
    )


def test_reminder_has_single_confirm_button(make_cfg):
    blocks = messages.reminder_blocks(make_cfg())
    actions = [b for b in blocks if b["type"] == "actions"]
    assert len(actions) == 1
    buttons = actions[0]["elements"]
    assert len(buttons) == 1
    assert buttons[0]["action_id"] == "confirm_tailgate"


def test_reminder_mentions_meeting_and_cutoff_times(make_cfg):
    cfg = make_cfg(meeting_time_label="16:30", cutoff_time="16:25")
    text = _section_text(messages.reminder_blocks(cfg))
    assert "16:30" in text
    assert "16:25" in text


def test_reminder_tags_the_usergroup_by_default(make_cfg):
    cfg = make_cfg(usergroup_id="S99999")
    text = _section_text(messages.reminder_blocks(cfg))
    assert "<!subteam^S99999>" in text


def test_reminder_usergroup_tag_can_be_disabled(make_cfg):
    cfg = make_cfg(usergroup_id="S99999", mention_usergroup=False)
    text = _section_text(messages.reminder_blocks(cfg))
    assert "<!subteam^" not in text


def test_reminder_tags_every_configured_group(make_cfg):
    cfg = make_cfg(mention_usergroup_ids=("S_DAYOBS", "S_SCISUP"))
    text = _section_text(messages.reminder_blocks(cfg))
    assert "<!subteam^S_DAYOBS>" in text
    assert "<!subteam^S_SCISUP>" in text


def test_reminder_fallback_is_plain_text(make_cfg):
    text = messages.reminder_text_fallback(make_cfg())
    assert isinstance(text, str)
    assert "Tailgate" in text


def test_confirmed_notice_includes_meeting_link(make_cfg):
    cfg = make_cfg(meeting_link="https://meet.example/xyz")
    blocks = messages.confirmed_notice_blocks(cfg)
    assert "https://meet.example/xyz" in _section_text(blocks)


def test_cancelled_notice_says_cancelled(make_cfg):
    text = _section_text(messages.cancelled_notice_blocks(make_cfg()))
    assert "cancelled" in text.lower()


def test_resolved_reminder_drops_the_button(make_cfg):
    cfg = make_cfg()
    for status in ("confirmed", "cancelled"):
        blocks = messages.reminder_resolved_blocks(cfg, status)
        assert all(b["type"] != "actions" for b in blocks)
