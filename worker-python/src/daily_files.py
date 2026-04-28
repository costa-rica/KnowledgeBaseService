"""Daily root-level NickVault file preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from loguru import logger

PACIFIC = ZoneInfo("America/Los_Angeles")


class DailyFileConflictError(RuntimeError):
    """Raised when a root draft cannot be filed without overwriting content."""


@dataclass
class DailyFilePreparationResult:
    """Summary of daily root-file preparation actions."""

    created: list[Path] = field(default_factory=list)
    deleted_empty: list[Path] = field(default_factory=list)
    moved: list[tuple[Path, Path]] = field(default_factory=list)
    skipped_existing: list[Path] = field(default_factory=list)
    skipped_missing: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class DailyFileSpec:
    """Configuration for one daily root-level draft file type."""

    prefix: str
    destination_dir: str
    template_factory: Callable[[str], str]

    def filename(self, compact_date: str) -> str:
        return f"{self.prefix}-{compact_date}.md"


def daily_template(iso_date: str) -> str:
    """Return the default French daily-note template."""
    return f"""---
date: {iso_date}
mood:
energy:
---

# Quotidien {iso_date}

## Priorités

- [ ]

## Notes

"""


def messages_template(iso_date: str) -> str:
    """Return the default messages log template."""
    return f"""# Messages {iso_date}

"""


def journal_template(iso_date: str) -> str:
    """Return the default journal template."""
    return f"""# Journal {iso_date}

"""


SPECS = (
    DailyFileSpec("daily", "Daily", daily_template),
    DailyFileSpec("messages", "Messages", messages_template),
    DailyFileSpec("journal", "Journal", journal_template),
)


def prepare_daily_root_files(
    vault_path: str | Path,
    *,
    now: datetime | None = None,
    dry_run: bool = False,
) -> DailyFilePreparationResult:
    """File yesterday's root drafts and create today's root drafts.

    Dates are resolved in America/Los_Angeles regardless of the server timezone.
    The function is intentionally conservative: it never overwrites destination
    files, and only deletes yesterday's root drafts when they are empty or still
    exactly match the generated template.
    """
    vault = Path(vault_path)
    if not vault.is_dir():
        raise FileNotFoundError(f"Vault path does not exist: {vault}")

    pacific_now = _pacific_now(now)
    today = pacific_now.date()
    yesterday = today - timedelta(days=1)
    today_compact = today.strftime("%Y%m%d")
    today_iso = today.isoformat()
    yesterday_compact = yesterday.strftime("%Y%m%d")
    yesterday_iso = yesterday.isoformat()

    result = DailyFilePreparationResult()

    for spec in SPECS:
        _file_yesterday_root_file(
            vault, spec, yesterday_compact, yesterday_iso, dry_run, result
        )

    for spec in SPECS:
        _create_today_root_file(vault, spec, today_compact, today_iso, dry_run, result)

    _log_result(result, dry_run)
    return result


def _pacific_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(PACIFIC)
    if now.tzinfo is None:
        return now.replace(tzinfo=PACIFIC)
    return now.astimezone(PACIFIC)


def _file_yesterday_root_file(
    vault: Path,
    spec: DailyFileSpec,
    compact_date: str,
    iso_date: str,
    dry_run: bool,
    result: DailyFilePreparationResult,
) -> None:
    root_path = vault / spec.filename(compact_date)
    if not root_path.exists():
        result.skipped_missing.append(root_path)
        return

    content = root_path.read_text()
    if _is_empty_or_template_only(content, spec.template_factory(iso_date)):
        result.deleted_empty.append(root_path)
        if not dry_run:
            root_path.unlink()
        return

    destination_dir = vault / spec.destination_dir
    destination_path = destination_dir / root_path.name

    if destination_path.exists():
        if _is_empty_or_template_only(content, spec.template_factory(iso_date)):
            result.deleted_empty.append(root_path)
            if not dry_run:
                root_path.unlink()
            return
        raise DailyFileConflictError(
            f"Destination already exists for meaningful root file: "
            f"{root_path} -> {destination_path}"
        )

    result.moved.append((root_path, destination_path))
    if not dry_run:
        destination_dir.mkdir(parents=True, exist_ok=True)
        root_path.rename(destination_path)


def _create_today_root_file(
    vault: Path,
    spec: DailyFileSpec,
    compact_date: str,
    iso_date: str,
    dry_run: bool,
    result: DailyFilePreparationResult,
) -> None:
    root_path = vault / spec.filename(compact_date)
    if root_path.exists():
        result.skipped_existing.append(root_path)
        return

    result.created.append(root_path)
    if not dry_run:
        root_path.write_text("")


def _is_empty_or_template_only(content: str, template: str) -> bool:
    return _normalize(content) in {"", _normalize(template)}


def _normalize(content: str) -> str:
    return content.replace("\r\n", "\n").strip()


def _log_result(result: DailyFilePreparationResult, dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    logger.info(
        "{}Daily root-file preparation complete: created={}, moved={}, "
        "deleted_empty={}, skipped_existing={}, skipped_missing={}",
        prefix,
        len(result.created),
        len(result.moved),
        len(result.deleted_empty),
        len(result.skipped_existing),
        len(result.skipped_missing),
    )
