"""Crash-resilient JSON storage for the ledger (PRINCIPLE-013).

A save copies the current file to `.bak`, writes a unique temporary file, fsyncs it, then
replaces the ledger atomically. A read that meets malformed JSON quarantines the file and falls
back to the backup, while a file declaring an unknown schema version is refused in place.
Every read-modify-write holds an advisory `.lock` file with a bounded wait.
"""

import json
import os
import shutil
import sys
import tempfile
import time
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional

from tally.errors import TallyError
from tally.models import Expense

STATE_VERSION = 1
MIN_FREE_BYTES = 10 * 1024 * 1024
LOCK_TIMEOUT_SECONDS = 3.0
LOCK_STALE_SECONDS = 30.0
REPLACE_ATTEMPTS = 5


class StateStore:
    """The ledger file, its backup and its lock, addressed by one path."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.backup_path = self.path.with_name(self.path.name + ".bak")
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    def read(self) -> List[Expense]:
        """Every recorded expense; a missing ledger is an empty one."""
        return self._load()

    def update(self, mutate: Callable[[List[Expense]], List[Expense]]) -> List[Expense]:
        """Apply `mutate` to the ledger and persist its result under one held lock."""
        with self._lock():
            expenses = self._load()
            updated = mutate(expenses)
            self._save(updated)
            return updated

    def _load(self) -> List[Expense]:
        """Parse the ledger, recovering from a readable backup before giving up on it."""
        if not self.path.exists():
            return []
        try:
            text = self.path.read_text(encoding="utf-8")
            data = json.loads(text)
        except OSError as exc:
            return self._backup_or_empty(
                f"could not read {self.path}: {exc}", quarantine=False, allow_empty=False
            )
        except ValueError:
            return self._backup_or_empty(f"{self.path} is not valid JSON", quarantine=True)
        return self._decode(data)

    def _backup_or_empty(self, reason: str, quarantine: bool,
                         allow_empty: bool = True) -> List[Expense]:
        """Use the backup when it parses; otherwise quarantine or refuse as the caller requires."""
        if quarantine:
            self._quarantine()
        backup = self._read_backup()
        if backup is not None:
            print(f"[WARN] {reason}; recovered from {self.backup_path.name}.", file=sys.stderr)
            return self._decode(backup)
        if not allow_empty:
            raise TallyError(
                f"{self.path} could not be read and has no usable backup.",
                reason,
                "fix the file's permissions or restore the .bak file; nothing was changed.",
            )
        print(f"[WARN] {reason}; starting with an empty ledger.", file=sys.stderr)
        return []

    def _read_backup(self) -> Optional[Dict[str, object]]:
        """The parsed backup, or None when it is absent or unreadable."""
        if not self.backup_path.exists():
            return None
        try:
            data = json.loads(self.backup_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _decode(self, data: object) -> List[Expense]:
        """Validate the document envelope and rebuild every expense."""
        if not isinstance(data, dict):
            raise TallyError(
                f"{self.path} does not hold a ledger object.",
                "the ledger is one JSON object with a version and an expenses list.",
                f"restore {self.backup_path.name}, or delete the file to start a new ledger.",
            )
        version = data.get("version")
        if version != STATE_VERSION:
            raise TallyError(
                f"{self.path} declares ledger version {version!r}; this build supports {STATE_VERSION}.",
                "a newer or unknown format could be misread and its data lost.",
                "use the Tally version that wrote it, or migrate the file by hand.",
            )
        records = data.get("expenses")
        if not isinstance(records, list):
            raise TallyError(
                f"{self.path} has no 'expenses' list.",
                "the ledger is one JSON object with a version and an expenses list.",
                f"restore {self.backup_path.name}, or delete the file to start a new ledger.",
            )
        return [Expense.from_dict(record) for record in records]

    def _save(self, expenses: List[Expense]) -> None:
        """Write the ledger atomically, keeping the previous version as a backup."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(self.path.parent).free
        if free < MIN_FREE_BYTES:
            raise TallyError(
                f"Only {free} bytes are free next to {self.path}.",
                "a ledger write needs at least 10 MB of headroom to stay crash-safe.",
                "free disk space, or point --db at another volume.",
            )
        payload = json.dumps(
            {"version": STATE_VERSION, "expenses": [e.as_dict() for e in expenses]},
            indent=2,
            ensure_ascii=False,
        )
        descriptor, temp_name = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}.tmp_"
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if self.path.exists():
                self._write_backup()
            self._replace(temp_path)
            self._fsync_directory(self.path.parent)
        finally:
            temp_path.unlink(missing_ok=True)

    def _write_backup(self) -> None:
        """Replace the backup atomically, keeping the old one when the copy fails."""
        temp_path: Optional[Path] = None
        try:
            descriptor, temp_name = tempfile.mkstemp(
                dir=self.path.parent, prefix=f".{self.backup_path.name}.tmp_"
            )
            temp_path = Path(temp_name)
            os.close(descriptor)
            shutil.copy2(self.path, temp_path)
            descriptor = os.open(temp_path, os.O_RDWR)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temp_path, self.backup_path)
        except OSError as exc:
            print(
                f"[WARN] Could not write backup {self.backup_path.name}: {exc}",
                file=sys.stderr,
            )
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _replace(self, temp_path: Path) -> None:
        """Replace the ledger, retrying only transient sharing violations on Windows (ADR-002)."""
        last_error: Optional[OSError] = None
        for attempt in range(REPLACE_ATTEMPTS):
            try:
                os.replace(temp_path, self.path)
                return
            except PermissionError as exc:
                last_error = exc
                if attempt < REPLACE_ATTEMPTS - 1:
                    time.sleep(0.02 * (2 ** attempt))
            except OSError as exc:
                last_error = exc
                break
        raise TallyError(
            f"Could not replace {self.path}: {last_error}",
            "another program may hold the ledger open, or the disk may be full or read-only.",
            "close programs using the file, check free space and permissions, then retry; "
            "the previous ledger is still intact.",
        )

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        """Flush the directory entry on POSIX; Windows cannot fsync a directory handle."""
        if os.name == "nt":
            return
        try:
            with closing(os.open(str(directory), os.O_RDONLY)) as descriptor:  # hygiene: allow raw directory descriptor closed by closing()
                os.fsync(descriptor)
        except OSError as exc:
            print(f"[WARN] Could not fsync directory {directory}: {exc}", file=sys.stderr)

    def _quarantine(self) -> None:
        """Move a corrupt ledger aside so it can neither block reads nor be overwritten."""
        destination = self.path.with_name(f".corrupt_{self.path.name}_{time.time_ns()}")
        try:
            os.replace(self.path, destination)
            print(f"[WARN] Moved unreadable ledger to {destination.name}.", file=sys.stderr)
        except OSError as exc:
            print(f"[WARN] Could not quarantine {self.path}: {exc}", file=sys.stderr)

    @contextmanager
    def _lock(self) -> Iterator[None]:
        """Hold the advisory lock file for one read-modify-write."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        acquired = False
        while not acquired:
            try:
                with self.lock_path.open("x", encoding="ascii") as handle:
                    handle.write(str(os.getpid()))
                acquired = True
            except FileExistsError:
                self._break_stale_lock()
                if time.monotonic() >= deadline:
                    raise TallyError(
                        f"Timed out waiting for {self.lock_path.name}.",
                        "another Tally process is changing the ledger.",
                        "wait for it to finish, then run the command again.",
                    )
                time.sleep(0.05)
            except OSError as exc:
                raise TallyError(
                    f"Could not create {self.lock_path.name}: {exc}",
                    "every ledger write needs the lock to avoid losing entries.",
                    "check the folder's permissions, then run the command again.",
                ) from exc
        try:
            yield
        finally:
            self.lock_path.unlink(missing_ok=True)

    def _break_stale_lock(self) -> None:
        """Break a lock older than 30 seconds by atomically renaming it aside."""
        try:
            age = time.time() - self.lock_path.stat().st_mtime
        except FileNotFoundError:
            return
        if age <= LOCK_STALE_SECONDS:
            return
        stale = self.lock_path.with_name(
            f"{self.lock_path.name}.stale_{time.time_ns()}"
        )
        try:
            os.replace(self.lock_path, stale)
        except FileNotFoundError:
            return
