"""Report collisions and ordinary-failure recovery preserve user data."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from prompt_version_diff import output
from prompt_version_diff.cli import main


def sources(tmp_path: Path) -> tuple[Path, Path]:
    before, after = tmp_path / "before.md", tmp_path / "after.md"
    before.write_bytes(b"Old prompt\r\n")
    after.write_bytes(b"New prompt\r\n")
    return before, after


@pytest.mark.parametrize("source", [0, 1])
@pytest.mark.parametrize("option", ["--json", "--markdown"])
def test_source_cannot_be_a_report(tmp_path: Path, source: int, option: str) -> None:
    before, after = sources(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main([str(before), str(after), option, str((before, after)[source])])
    assert exc.value.code == 2
    assert before.read_bytes() == b"Old prompt\r\n"
    assert after.read_bytes() == b"New prompt\r\n"


@pytest.mark.parametrize("bad", ["existing", "missing-parent", "duplicate"])
def test_preflight_does_not_leave_first_report(tmp_path: Path, bad: str) -> None:
    before, after = sources(tmp_path)
    first, second = tmp_path / "report.json", tmp_path / "report.md"
    if bad == "existing":
        second.write_text("Keep existing", encoding="utf-8")
    elif bad == "missing-parent":
        second = tmp_path / "absent" / "report.md"
    else:
        second = first
    with pytest.raises(SystemExit) as exc:
        main([str(before), str(after), "--json", str(first), "--markdown", str(second)])
    assert exc.value.code == 2 and not first.exists()
    if bad == "existing":
        assert second.read_text(encoding="utf-8") == "Keep existing"


def test_symlink_and_hardlink_inputs_preserved(tmp_path: Path) -> None:
    before, after = sources(tmp_path)
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(before)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(SystemExit):
        main([str(before), str(after), "--json", str(alias)])
    assert before.read_bytes() == b"Old prompt\r\n" and alias.is_symlink()
    cycle = tmp_path / "cycle.json"
    cycle.symlink_to(cycle)
    with pytest.raises(SystemExit) as exc:
        main([str(before), str(after), "--json", str(cycle)])
    assert exc.value.code == 2 and cycle.is_symlink()
    hardlink = tmp_path / "hardlink.json"
    os.link(after, hardlink)
    with pytest.raises(SystemExit):
        main([str(before), str(after), "--json", str(hardlink)])
    assert after.read_bytes() == b"New prompt\r\n"


def test_paired_reports_and_retry(tmp_path: Path) -> None:
    before, after = sources(tmp_path)
    first, second = tmp_path / "report.json", tmp_path / "report.md"
    assert main([str(before), str(after), "--json", str(first), "--markdown", str(second)]) == 1
    original = first.read_bytes(), second.read_bytes()
    with pytest.raises(SystemExit):
        main([str(before), str(after), "--json", str(first), "--markdown", str(second)])
    assert (first.read_bytes(), second.read_bytes()) == original
    assert main([str(before), str(after), "--json", str(tmp_path / "retry.json")]) == 1


@pytest.mark.parametrize("failure", ["reserve", "write", "zero-write", "fsync", "stdout"])
def test_runtime_failure_recovers_new_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    real_open, real_write = os.open, os.write
    calls = 0

    def reserve(path: Any, flags: int, mode: int = 0o777) -> int:
        if Path(path) == b:
            b.write_text("Created concurrently", encoding="utf-8")
        return real_open(path, flags, mode)

    def write(fd: int, data: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_write(fd, data[:2])
        if failure == "zero-write":
            return 0
        raise OSError("disk full")

    def fail(*args: Any) -> None:
        raise OSError("injected failure")

    if failure == "reserve":
        monkeypatch.setattr("prompt_version_diff.output.os.open", reserve)
    elif failure in {"write", "zero-write"}:
        monkeypatch.setattr("prompt_version_diff.output.os.write", write)
    elif failure == "fsync":
        monkeypatch.setattr("prompt_version_diff.output.os.fsync", fail)
    with pytest.raises(OSError):
        output.write_reports(
            [(a, "first report"), (b, "second report")],
            fail if failure == "stdout" else lambda: None,
        )
    assert not a.exists()
    if failure == "reserve":
        assert b.read_text(encoding="utf-8") == "Created concurrently"
    else:
        assert not b.exists()
        monkeypatch.undo()
        output.write_reports([(a, "retry first"), (b, "retry second")], lambda: None)
        assert a.read_text() == "retry first" and b.read_text() == "retry second"


@pytest.mark.parametrize("change", ["edit", "replace", "remove", "symlink"])
def test_recovery_preserves_concurrent_changes(tmp_path: Path, change: str) -> None:
    path = tmp_path / "report"
    other = tmp_path / "other"
    other.write_text("Other data", encoding="utf-8")

    def deliver() -> None:
        if change == "edit":
            path.write_text("Concurrent edit", encoding="utf-8")
        elif change == "replace":
            other.replace(path)
        else:
            path.unlink()
            if change == "symlink":
                path.symlink_to(other)
        raise OSError("stdout failed")

    with pytest.raises(OSError) as exc:
        output.write_reports([(path, "Original report")], deliver)
    if change == "remove":
        assert not path.exists()
    else:
        assert "retained" in str(exc.value)
        assert path.read_text(encoding="utf-8") in {"Concurrent edit", "Other data"}


def test_recovery_error_identifies_retained_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "report"
    real_unlink = Path.unlink

    def unlink(self: Path, missing_ok: bool = False) -> None:
        if self == path:
            raise PermissionError("cannot recover")
        real_unlink(self, missing_ok=missing_ok)

    def fail() -> None:
        raise OSError("stdout failed")

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises(OSError, match="retained.*report"):
        output.write_reports([(path, "content")], fail)
    assert path.read_text(encoding="utf-8") == "content"


def test_cli_output_error_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    before, after = sources(tmp_path)

    def fail(*args: Any) -> None:
        raise OSError("report disk unavailable")

    monkeypatch.setattr("prompt_version_diff.cli.write_reports", fail)
    with pytest.raises(SystemExit) as exc:
        main([str(before), str(after), "--json", str(tmp_path / "out")])
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "report disk unavailable" in error and "Traceback" not in error


def test_real_stdout_failure_returns_two_and_recovers_reports(tmp_path: Path) -> None:
    before, after = sources(tmp_path)
    report = tmp_path / "report.json"
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "prompt_version_diff",
                str(before),
                str(after),
                "--json",
                str(report),
            ],
            check=False,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        os.close(write_fd)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr and "Exception ignored" not in result.stderr
    assert not report.exists()


def test_terminal_short_and_zero_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    from prompt_version_diff.cli import _write_stdout

    class Terminal:
        encoding = "utf-8"
        errors = "strict"

        def fileno(self) -> int:
            return 999

    data = bytearray()

    def write(fd: int, value: bytes) -> int:
        assert fd == 999
        data.extend(value[:2])
        return min(2, len(value))

    monkeypatch.setattr("prompt_version_diff.cli.sys.stdout", Terminal())
    monkeypatch.setattr("prompt_version_diff.cli.os.write", write)
    _write_stdout("éabc")
    assert bytes(data).decode("utf-8") == "éabc"
    monkeypatch.setattr("prompt_version_diff.cli.os.write", lambda fd, value: 0)
    with pytest.raises(OSError, match="no progress"):
        _write_stdout("x")
