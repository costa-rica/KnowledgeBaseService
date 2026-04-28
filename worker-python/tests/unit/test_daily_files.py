"""Unit tests for daily root-level NickVault file preparation."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.daily_files import (
    DailyFileConflictError,
    daily_template,
    journal_template,
    messages_template,
    prepare_daily_root_files,
)

PACIFIC = ZoneInfo("America/Los_Angeles")


def test_creates_today_root_files_as_empty(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)

    result = prepare_daily_root_files(tmp_path, now=now)

    assert (tmp_path / "daily-20260427.md").read_text() == ""
    assert (tmp_path / "messages-20260427.md").read_text() == ""
    assert (tmp_path / "journal-20260427.md").read_text() == ""
    assert result.created == [
        tmp_path / "daily-20260427.md",
        tmp_path / "messages-20260427.md",
        tmp_path / "journal-20260427.md",
    ]


def test_deletes_yesterday_empty_root_files(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    yesterday_daily = tmp_path / "daily-20260426.md"
    yesterday_messages = tmp_path / "messages-20260426.md"
    yesterday_journal = tmp_path / "journal-20260426.md"
    yesterday_daily.write_text("")
    yesterday_messages.write_text("")
    yesterday_journal.write_text("")

    result = prepare_daily_root_files(tmp_path, now=now)

    assert not yesterday_daily.exists()
    assert not yesterday_messages.exists()
    assert not yesterday_journal.exists()
    assert result.deleted_empty == [yesterday_daily, yesterday_messages, yesterday_journal]


def test_does_not_overwrite_existing_today_files(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    existing = tmp_path / "daily-20260427.md"
    existing.write_text("already started")

    result = prepare_daily_root_files(tmp_path, now=now)

    assert existing.read_text() == "already started"
    assert existing in result.skipped_existing
    assert (tmp_path / "messages-20260427.md").exists()
    assert (tmp_path / "journal-20260427.md").exists()


def test_deletes_yesterday_template_only_root_files(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    yesterday_daily = tmp_path / "daily-20260426.md"
    yesterday_messages = tmp_path / "messages-20260426.md"
    yesterday_journal = tmp_path / "journal-20260426.md"
    yesterday_daily.write_text(daily_template("2026-04-26"))
    yesterday_messages.write_text(messages_template("2026-04-26"))
    yesterday_journal.write_text(journal_template("2026-04-26"))

    result = prepare_daily_root_files(tmp_path, now=now)

    assert not yesterday_daily.exists()
    assert not yesterday_messages.exists()
    assert not yesterday_journal.exists()
    assert result.deleted_empty == [yesterday_daily, yesterday_messages, yesterday_journal]


def test_moves_yesterday_meaningful_root_files_to_destination_folders(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    daily_root = tmp_path / "daily-20260426.md"
    messages_root = tmp_path / "messages-20260426.md"
    journal_root = tmp_path / "journal-20260426.md"
    daily_root.write_text(daily_template("2026-04-26") + "\n- Terminer le plan\n")
    messages_root.write_text(messages_template("2026-04-26") + "\nTelegram: hello\n")
    journal_root.write_text(journal_template("2026-04-26") + "\nA real entry.\n")

    result = prepare_daily_root_files(tmp_path, now=now)

    assert not daily_root.exists()
    assert not messages_root.exists()
    assert not journal_root.exists()
    assert (tmp_path / "Daily" / "daily-20260426.md").read_text().endswith("- Terminer le plan\n")
    assert (tmp_path / "Messages" / "messages-20260426.md").read_text().endswith("Telegram: hello\n")
    assert (tmp_path / "Journal" / "journal-20260426.md").read_text().endswith("A real entry.\n")
    assert result.moved == [
        (daily_root, tmp_path / "Daily" / "daily-20260426.md"),
        (messages_root, tmp_path / "Messages" / "messages-20260426.md"),
        (journal_root, tmp_path / "Journal" / "journal-20260426.md"),
    ]


def test_dry_run_reports_actions_without_mutating_files(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    daily_root = tmp_path / "daily-20260426.md"
    daily_root.write_text("meaningful")

    result = prepare_daily_root_files(tmp_path, now=now, dry_run=True)

    assert daily_root.exists()
    assert not (tmp_path / "Daily" / "daily-20260426.md").exists()
    assert not (tmp_path / "daily-20260427.md").exists()
    assert result.moved == [(daily_root, tmp_path / "Daily" / "daily-20260426.md")]
    assert tmp_path / "daily-20260427.md" in result.created


def test_destination_conflict_preserves_root_file_and_raises(tmp_path):
    now = datetime(2026, 4, 27, 3, 0, tzinfo=PACIFIC)
    root = tmp_path / "daily-20260426.md"
    dest_dir = tmp_path / "Daily"
    dest_dir.mkdir()
    dest = dest_dir / "daily-20260426.md"
    root.write_text("root content")
    dest.write_text("destination content")

    with pytest.raises(DailyFileConflictError):
        prepare_daily_root_files(tmp_path, now=now)

    assert root.read_text() == "root content"
    assert dest.read_text() == "destination content"


def test_uses_pacific_date_even_when_input_datetime_is_utc(tmp_path):
    utc_now = datetime(2026, 4, 27, 10, 0, tzinfo=ZoneInfo("UTC"))

    prepare_daily_root_files(tmp_path, now=utc_now)

    assert (tmp_path / "daily-20260427.md").exists()
    assert not (tmp_path / "daily-20260426.md").exists()
