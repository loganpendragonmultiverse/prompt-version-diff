"""Create new reports and recover unchanged reports after ordinary failures."""

from __future__ import annotations

import os
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class _Report:
    path: Path
    data: bytes
    fd: int | None = None
    identity: tuple[int, int] | None = None
    written: int = 0


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        value = path.lstat()
    except FileNotFoundError:
        return None
    return (value.st_dev, value.st_ino) if stat.S_ISREG(value.st_mode) else None


def _close(reports: list[_Report]) -> None:
    for report in reports:
        if report.fd is not None:
            fd, report.fd = report.fd, None
            os.close(fd)


def _recover(reports: list[_Report]) -> list[str]:
    retained = []
    for report in reversed(reports):
        if report.identity is None:
            continue
        try:
            if (
                _identity(report.path) == report.identity
                and report.path.read_bytes() == report.data[: report.written]
                and _identity(report.path) == report.identity
            ):
                report.path.unlink()
            elif os.path.lexists(report.path):
                retained.append(str(report.path))
        except OSError:
            retained.append(str(report.path))
    return retained


def write_reports(outputs: list[tuple[Path, str]], deliver: Callable[[], None]) -> None:
    """Reserve all destinations before writing; never replace existing files.

    Only unchanged files created by this call are recovered after failure.
    This is not an atomic transaction across a process crash or power loss.
    """
    paths = [path for path, _ in outputs]
    if len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("report destinations must be distinct new files")
    for path in paths:
        if os.path.lexists(path):
            raise ValueError(f"report already exists: {path}; choose a new destination")
        if not path.parent.is_dir():
            raise ValueError(f"report directory does not exist: {path.parent}")
    reports = [_Report(path, text.encode("utf-8")) for path, text in outputs]
    try:
        # Exclusive creation also rejects a file/symlink appearing after validation.
        for report in reports:
            report.fd = os.open(
                report.path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                0o600,
            )
            value = os.fstat(report.fd)
            report.identity = value.st_dev, value.st_ino
        for report in reports:
            assert report.fd is not None
            while report.written < len(report.data):
                count = os.write(report.fd, report.data[report.written : report.written + 65536])
                if count <= 0:
                    raise OSError("report write made no progress")
                report.written += count
            os.fsync(report.fd)
        _close(reports)
        deliver()
    except BaseException as error:
        _close(reports)
        retained = _recover(reports)
        if retained:
            raise OSError(
                "report operation failed; retained changed or inaccessible new reports: "
                + ", ".join(retained)
            ) from error
        raise
    finally:
        _close(reports)
