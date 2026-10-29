# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: One JSON ledger with integer cents and atomic, locked writes
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: A first usable project needs a durable expense log without a database dependency,
  and money must not drift through binary floating-point rounding.
- **Decision**: Store every expense in one JSON document
  (`{"version": 1, "expenses": [{"id", "amount_cents", "category", "note", "spent_on"}]}`).
  Amounts are integer cents parsed with `Decimal`. Each save copies the current file to `.bak`,
  writes a unique temporary file, fsyncs it, then replaces the ledger; each read-modify-write holds
  `<ledger>.lock` for at most 3 seconds, and a lock older than 30 seconds is broken. Malformed JSON
  is quarantined and recovered from `.bak`; an unknown `version` is refused in place.
- **Consequences**: The file is easy to inspect, back up and edit by hand. Totals are exact. The
  whole ledger is held in memory per command, which is fine at personal-ledger scale but would need
  a different store for very large histories. Categories are free-form lowercase labels, so typos
  create separate categories rather than being rejected.

### ADR-002: Retry only sharing violations, and announce every degraded durability step
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The bootstrap retried every `OSError` from `os.replace` five times, so a full or
  read-only disk paid five sleeps before reporting the real cause, and a failed backup copy or
  POSIX directory fsync was discarded without a trace. AIKit's ADR-146 narrowed the same retry
  loop in the kit's own state writer.
- **Decision**: `os.replace` is retried only on `PermissionError`, with 20ms exponential backoff
  over five attempts; any other `OSError` is reported at once as a `TallyError` with the
  Error/Why/Fix triad. A failed `.bak` copy or directory fsync prints one `[WARN]` naming the path
  and the write continues, because the replacement already happened. Lock cleanup tolerates a lock
  that vanished while it was held, and breaking a stale lock that another process already removed
  is a no-op.
- **Consequences**: Transient Windows sharing violations still succeed, while ENOSPC and
  read-only failures surface immediately. A ledger can survive without a fresh backup or a
  directory barrier, but the operator sees the warning. The JSON schema, lock protocol and
  shutdown behaviour are unchanged.

### ADR-003: Edit and remove by the id `list` shows
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The bootstrap only appended. Correcting a typo or deleting a duplicate meant
  hand-editing `tally.json`, the one file the atomic store and backup exist to protect.
- **Decision**: Add `edit ID` and `remove ID`. `edit` changes any subset of `--amount`,
  `--category`, `--note` and `--date`, and refuses a call with no field. Both commands run through
  `StateStore.update`, so they hold the same lock, keep the same `.bak` and replace the ledger
  atomically. A missing id fails with the Error/Why/Fix triad. New ids are one past the highest
  remaining id, so deleting the newest entry frees its id for the next entry; every entry that
  remains keeps its id.
- **Consequences**: Mistakes are fixed without touching the JSON. The previous version stays in
  `.bak` until the next write. Because ids are derived from the live file, an id is a handle to a
  current entry, not a permanent historical key; a future schema that persists a counter would be
  the migration path if permanent identity is needed.

### ADR-004: Date range and month filtering for list and summary
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: `list` only allowed filtering by category, and `summary` always totaled all recorded
  expenses across the lifetime of the ledger. Users need to inspect and summarize expenses for
  specific periods, especially by month or custom date windows.
- **Decision**: Add `--from YYYY-MM-DD`, `--to YYYY-MM-DD`, and `--month YYYY-MM` (`-m`) options
  to both `list` and `summary`. `--month` resolves to inclusive start and end dates based on the
  calendar month (handling leap years). Combining `--month` with `--from` or `--to`, or specifying
  `--from` after `--to`, fails cleanly with the Error/Why/Fix triad. The stored ledger schema is
  unchanged; filtering operates on ISO-8601 string bounds during retrieval.
- **Consequences**: Users can analyze periodic spending without third-party tooling or spreadsheet
  exports. Backward compatibility is fully preserved for callers invoking `entries()` or `summary()`
  without date bounds.

### ADR-005: Refuse unreadable ledgers and replace backups atomically
- **Date**: 2026-10-29
- **Status**: Accepted
- **Context**: A Reforge review of the storage layer found that an unreadable ledger was treated as
  an empty one, so a later write could replace it, and that the backup was copied in place, so a
  crash during that copy could destroy the last good backup.
- **Decision**: `_load` raises the Error/Why/Fix triad when the ledger cannot be read and no
  readable backup exists; it never returns an empty list for that case. A backup is copied to a
  unique temporary file in the ledger directory, fsynced, and moved over `.bak` with `os.replace`,
  keeping the previous backup when the copy or replace fails.
- **Consequences**: A permissions or I/O failure leaves the ledger and backup untouched and asks the
  operator to repair access. A failed backup refresh still prints one `[WARN]` and the ledger write
  continues, as ADR-002 requires. The JSON schema, lock protocol and backup filename are unchanged.

## Licensing migration (v0.1.0-agpl)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `v0.1.0-agpl` remain under GNU AGPL-3.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes were removed from README.md and COMMERCIAL.md: the project is offered only under the Aegean License 1.1 (AL-1.1), with commercial use under ACL-1.0.

## License text cleanup (2026-10-29)

- The AL-1.1 texts no longer name GNU AGPL-3.0 inside the earlier-license and compatibility clauses; Section 10.3 still preserves earlier licenses generically. `LICENSE` and `LICENSES/LicenseRef-AL-1.1.txt` remain byte-identical.
