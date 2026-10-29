# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `13`
- **Total Classes**: `13`
- **Total Top-Level Functions**: `15`
- **Total Class Methods**: `97`
- **Total Source Lines**: `1390`

---

## 📦 Modules & Exported Symbols

### [`tally/__init__.py`](tally/__init__.py)
> *Tally: a dependency-free, local-first expense ledger.*

**Size**: `3` lines (`83` bytes)

---

### [`tally/__main__.py`](tally/__main__.py)
> *`python -m tally` entry point.*

**Size**: `7` lines (`95` bytes)

---

### [`tally/cli.py`](tally/cli.py)
> *Command-line interface: `add`, `list` and `summary` over one ledger file.*

**Size**: `155` lines (`6482` bytes)

**Functions:**
- `def build_parser()` - *The command grammar; `--db` selects the ledger file for every command.*
- `def run_add(ledger, args)` - *Validate the arguments, record the expense and echo it.*
- `def run_edit(ledger, args)` - *Apply the given fields and echo the updated expense.*
- `def run_remove(ledger, args)` - *Delete one expense and echo what was removed.*
- `def run_list(ledger, args)` - *Print one line per expense, or say the ledger is empty.*
- `def run_summary(ledger, args)` - *Print per-category totals and the grand total.*
- `def main(argv)` - *Run one command; user errors print the Why/Fix triad and exit 1.*

---

### [`tally/errors.py`](tally/errors.py)
> *Every user-facing failure carries a message, a reason and a repair (PRINCIPLE-011 R6).*

**Size**: `15` lines (`547` bytes)

**Classes:**
- `class TallyError` - *A failure the CLI reports as `Error:` / `Why:` / `Fix:` without a traceback.*
  - Method `.__init__(message, why, fix)`
  - Method `.render()` - *The three-line report the CLI prints on stderr.*

---

### [`tally/ledger.py`](tally/ledger.py)
> *Expense operations: the one place that assigns ids and computes category totals.*

**Size**: `115` lines (`4658` bytes)

**Classes:**
- `class Ledger` - *Add and read expenses through a `StateStore`; it owns no storage logic itself.*
  - Method `.__init__(store)`
  - Method `.add(amount_cents, category, note, spent_on)` - *Record one expense with the next free id.*
  - Method `.edit(expense_id, amount_cents, category, note, spent_on)` - *Change the given fields of one expense, keeping every other field.*
  - Method `.remove(expense_id)` - *Delete one expense and return it.*
  - Method `._missing(expense_id)` - *The triad for an id the ledger does not contain.*
  - Method `.entries(category, from_date, to_date)` - *Every expense, oldest first, optionally narrowed to one category or date range.*
  - Method `.summary(from_date, to_date)` - *Total cents per category, with categories in alphabetical order.*
  - Method `.total(from_date, to_date)` - *Total cents across every category in the given date range.*

---

### [`tally/models.py`](tally/models.py)
> *Expense value objects and money/date parsing shared by storage and the CLI.*

**Size**: `197` lines (`7560` bytes)

**Classes:**
- `class Expense` - *One recorded expense; money is integer cents so no float rounding can drift.*
  - Method `.as_dict()` - *The persisted form; keys are the on-disk schema from ADR-001.*
  - Method `.from_dict(data)` - *Rebuild an expense, refusing a record that would corrupt totals.*

**Functions:**
- `def parse_amount(text)` - *Convert a decimal amount such as `12.50` to integer cents.*
- `def format_cents(cents)` - *Render integer cents as a plain decimal string, e.g. 1250 -> `12.50`.*
- `def normalize_category(text)` - *Trim and lowercase a category, refusing empty or oversized values.*
- `def normalize_note(text)` - *Trim a note and refuse one that would dwarf a ledger line.*
- `def parse_date(text)` - *Validate an ISO date and return it unchanged, so stored dates sort lexically.*
- `def parse_id(text)` - *Convert an expense id such as `3` to a positive integer.*
- `def parse_month(text)` - *Validate a month in YYYY-MM format, returning canonical YYYY-MM.*
- `def resolve_date_range(from_date, to_date, month)` - *Validate and resolve --from, --to and --month into an ISO (start_date, end_date) pair.*

---

### [`tally/storage.py`](tally/storage.py)
> *Crash-resilient JSON storage for the ledger (PRINCIPLE-013).*

**Size**: `259` lines (`10895` bytes)

**Classes:**
- `class StateStore` - *The ledger file, its backup and its lock, addressed by one path.*
  - Method `.__init__(path)`
  - Method `.read()` - *Every recorded expense; a missing ledger is an empty one.*
  - Method `.update(mutate)` - *Apply `mutate` to the ledger and persist its result under one held lock.*
  - Method `._load()` - *Parse the ledger, recovering from a readable backup before giving up on it.*
  - Method `._backup_or_empty(reason, quarantine, allow_empty)` - *Use the backup when it parses; otherwise quarantine or refuse as the caller requires.*
  - Method `._read_backup()` - *The parsed backup, or None when it is absent or unreadable.*
  - Method `._decode(data)` - *Validate the document envelope and rebuild every expense.*
  - Method `._save(expenses)` - *Write the ledger atomically, keeping the previous version as a backup.*
  - Method `._write_backup()` - *Replace the backup atomically, keeping the old one when the copy fails.*
  - Method `._replace(temp_path)` - *Replace the ledger, retrying only transient sharing violations on Windows (ADR-002).*
  - Method `._fsync_directory(directory)` - *Flush the directory entry on POSIX; Windows cannot fsync a directory handle.*
  - Method `._quarantine()` - *Move a corrupt ledger aside so it can neither block reads nor be overwritten.*
  - Method `._lock()` - *Hold the advisory lock file for one read-modify-write.*
  - Method `._break_stale_lock()` - *Break a lock older than 30 seconds by atomically renaming it aside.*

---

### [`tests/__init__.py`](tests/__init__.py)
> *Test package for Tally.*

**Size**: `1` lines (`30` bytes)

---

### [`tests/test_cli.py`](tests/test_cli.py)
> *End-to-end tests of the command-line interface through `main`.*

**Size**: `210` lines (`8458` bytes)

**Classes:**
- `class CliTests`
  - Method `.setUp()`
  - Method `.run_cli(*arguments)`
  - Method `.test_add_then_list_then_summary()`
  - Method `.test_list_on_empty_ledger()`
  - Method `.test_edit_updates_every_given_field()`
  - Method `.test_edit_can_clear_a_note()`
  - Method `.test_edit_without_fields_reports_why_and_fix()`
  - Method `.test_edit_invalid_amount_reports_why_and_fix()`
  - Method `.test_edit_missing_id_reports_why_and_fix()`
  - Method `.test_remove_deletes_one_entry()`
  - Method `.test_remove_bad_id_reports_why_and_fix()`
  - Method `.test_remove_missing_id_reports_why_and_fix()`
  - Method `.test_invalid_amount_reports_why_and_fix()`
  - Method `.test_missing_command_is_argument_misuse()`
  - Method `.test_list_filter_by_month()`
  - Method `.test_list_filter_by_date_range()`
  - Method `.test_summary_filter_by_month()`
  - Method `.test_summary_filter_by_date_range()`
  - Method `.test_list_month_conflict_reports_why_and_fix()`
  - Method `.test_summary_start_after_end_reports_why_and_fix()`
  - Method `.test_list_invalid_month_reports_why_and_fix()`

---

### [`tests/test_ledger.py`](tests/test_ledger.py)
> *Tests for the ledger operations on top of the state store.*

**Size**: `134` lines (`6220` bytes)

**Classes:**
- `class LedgerTests`
  - Method `.setUp()`
  - Method `.test_add_assigns_consecutive_ids()`
  - Method `.test_entries_are_oldest_first()`
  - Method `.test_entries_filter_by_category()`
  - Method `.test_summary_totals_each_category()`
  - Method `.test_entries_survive_a_new_ledger_instance()`
  - Method `.test_edit_changes_only_the_given_fields()`
  - Method `.test_edit_can_clear_a_note()`
  - Method `.test_edit_without_fields_is_refused()`
  - Method `.test_edit_missing_id_changes_nothing()`
  - Method `.test_edit_survives_a_new_ledger_instance()`
  - Method `.test_remove_drops_only_the_named_id()`
  - Method `.test_remove_missing_id_changes_nothing()`
  - Method `.test_next_id_follows_the_highest_remaining_entry()`
  - Method `.test_entries_filter_by_date_range()`
  - Method `.test_entries_filter_by_category_and_date_range()`
  - Method `.test_summary_filters_by_date_range()`

---

### [`tests/test_models.py`](tests/test_models.py)
> *Tests for money, date and category parsing.*

**Size**: `131` lines (`4248` bytes)

**Classes:**
- `class AmountTests`
  - Method `.test_parses_decimal_amounts_to_cents()`
  - Method `.test_rejects_non_positive_amounts()`
  - Method `.test_rejects_fractions_of_a_cent()`
  - Method `.test_rejects_garbage()`
  - Method `.test_formats_cents_with_two_places()`
- `class IdTests`
  - Method `.test_parses_positive_ids()`
  - Method `.test_rejects_text_and_non_positive_ids()`
- `class LabelTests`
  - Method `.test_category_is_trimmed_and_lowercased()`
  - Method `.test_empty_category_is_refused()`
  - Method `.test_note_is_trimmed()`
  - Method `.test_iso_date_is_kept()`
  - Method `.test_invalid_date_is_refused()`
- `class MonthTests`
  - Method `.test_parses_iso_month()`
  - Method `.test_rejects_invalid_months()`
- `class DateRangeTests`
  - Method `.test_resolve_date_range_month()`
  - Method `.test_resolve_date_range_from_to()`
  - Method `.test_resolve_date_range_from_after_to()`
  - Method `.test_resolve_date_range_month_conflict()`

---

### [`tests/test_package.py`](tests/test_package.py)
> *Metadata tests for the importable package.*

**Size**: `21` lines (`566` bytes)

**Classes:**
- `class PackageMetadataTests`
  - Method `.test_module_version_matches_pyproject()`

---

### [`tests/test_storage.py`](tests/test_storage.py)
> *Fault-injection tests for the atomic ledger store (PRINCIPLE-013).*

**Size**: `142` lines (`6153` bytes)

**Classes:**
- `class StoreFaultTests`
  - Method `.setUp()`
  - Method `._write(expenses)`
  - Method `.test_malformed_json_recovers_from_backup()`
  - Method `.test_zero_byte_ledger_recovers_from_backup()`
  - Method `.test_backup_is_written_before_replacement()`
  - Method `.test_unknown_version_is_refused_in_place()`
  - Method `.test_insufficient_disk_space_writes_nothing()`
  - Method `.test_concurrent_writers_lose_no_entries()`
  - Method `.test_replace_does_not_retry_a_non_transient_error()`
  - Method `.test_replace_retries_a_permission_error_then_succeeds()`
  - Method `.test_fsync_directory_failure_is_reported()`
  - Method `.test_backup_failure_is_reported_and_the_write_continues()`
  - Method `.test_unreadable_ledger_without_backup_is_refused()`
  - Method `.test_failed_backup_replace_keeps_the_previous_backup()`

---
