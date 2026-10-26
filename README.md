# tally

[![Built with AIKit](https://img.shields.io/badge/built%20with-AIKit-6f42c1)](https://github.com/AegeanWorks/AIKit)

A dependency-free, local-first expense ledger for the terminal. Record what you spend, list it,
and see where the money went. Everything stays in one readable JSON file on your machine.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: Python 3.10 or newer (standard library only; no third-party packages)
- **Canonical Regression Shield Gate**:
  ```bash
  python -m unittest discover
  ```
- **Try it now** (under 10 seconds, from this folder):
  ```bash
  python -m tally add 12.50 --category food --note lunch
  python -m tally add 3.00 --category transport
  python -m tally list
  python -m tally edit 1 --amount 13.00
  python -m tally remove 2
  python -m tally summary
  ```

### 🛠️ AIKit Commands (run from the AIKit folder)

| Role | Command |
|---|---|
| Status, task and gates | `python aikit.py status tally` |
| Phase 4: every gate | `python aikit.py check tally` |
| Repair memory and map, then check | `python aikit.py fix tally` |
| Resume an interrupted task | `python aikit.py resume tally` |

## 💡 How It Works

- **Money is integer cents.** Amounts are parsed with `Decimal`, never floats, so totals stay exact.
- **One ledger file.** `tally.json` (or `--db <path>`) holds `{"version": 1, "expenses": [...]}`.
- **Stable ids.** `list` shows each id, and `edit` or `remove` takes it. A new id is one past the
  highest remaining id, so deleting the newest entry frees that id for the next entry.
- **Crash-safe writes.** Each save keeps a `.bak`, writes a temporary file, fsyncs it, then
  replaces the ledger atomically. A transient Windows sharing violation is retried; any other
  replace failure is reported at once. A failed backup or directory fsync prints a warning. A
  malformed file is quarantined and the backup is restored.
- **One writer at a time.** Read-modify-write operations hold an advisory `.lock` with a 3-second
  wait; a lock older than 30 seconds is broken.
- **Date and month filtering.** `list` and `summary` accept `--month YYYY-MM` or `--from` and `--to`
  to view and total spending within specific periods.
- **Clear failures.** Every user error prints `Error:`, `Why:` and `Fix:`, and exits 1.

### Commands

```text
python -m tally [--db PATH] add AMOUNT [--category NAME] [--note TEXT] [--date YYYY-MM-DD]
python -m tally [--db PATH] edit ID [--amount AMOUNT] [--category NAME] [--note TEXT] [--date YYYY-MM-DD]
python -m tally [--db PATH] remove ID
python -m tally [--db PATH] list [--category NAME] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--month YYYY-MM]
python -m tally [--db PATH] summary [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--month YYYY-MM]
```

## 📦 What's Inside

```text
tally/
├── .aikit/                   <- this project's memory: record, ledger, decisions
├── .gitignore                <- transient AIKit state and local ledgers excluded
├── LICENSE
├── LICENSES/                 <- REUSE license texts
├── REUSE.toml                <- Machine-readable SPDX metadata
├── README.md
├── COMMERCIAL.md
├── pyproject.toml            <- package metadata and the `tally` console script
├── tally/
│   ├── __init__.py
│   ├── __main__.py           <- `python -m tally`
│   ├── cli.py                <- argument parsing and command output
│   ├── errors.py             <- the Error/Why/Fix triad
│   ├── ledger.py             <- add, edit, remove and read operations
│   ├── models.py             <- Expense value object and parsing rules
│   └── storage.py            <- atomic JSON store, backup, lock and recovery
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_ledger.py
    ├── test_models.py
    └── test_storage.py
```

## 📚 Design Notes

The on-disk schema, money representation and crash-safety choices are recorded in
`.aikit/decisions.md` (ADR-001).

## 📜 License

Free for personal use under the Aegean License 1.1 (AL-1.1); see [LICENSE](LICENSE). Any commercial use needs the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
