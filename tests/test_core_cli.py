"""Behavior tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from prompt_version_diff.cli import main, markdown
from prompt_version_diff.core import categorize, compare_text, meaningful_lines


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Never publish secrets.", "constraint"),
        ("Context: this is a library", "context"),
        ("Example: run pytest", "example"),
        ("Summarize the result.", "instruction"),
    ],
)
def test_categories(text: str, expected: str) -> None:
    assert categorize(text) == expected


def test_meaningful_lines_preserve_numbers() -> None:
    assert meaningful_lines("one\n\n three \n") == [(1, "one"), (3, "three")]


def test_compare_add_remove_replace() -> None:
    result = compare_text(
        "Context: old\nKeep this\nNever log\n", "Context: new\nKeep this\nExample: test\n"
    )
    assert result.unchanged_lines == 1
    assert [item.category for item in result.added] == ["context", "example"]
    assert [item.category for item in result.removed] == ["context", "constraint"]


def test_reordered_line_is_visible() -> None:
    result = compare_text("A\nB\n", "B\nA\n")
    assert len(result.added) == 1
    assert len(result.removed) == 1


def test_cli_outputs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = tmp_path / "before.md"
    after = tmp_path / "after.md"
    before.write_text("Summarize.\n", encoding="utf-8")
    after.write_text("Summarize.\nNever expose secrets.\n", encoding="utf-8")
    output = tmp_path / "diff.json"
    assert main([str(before), str(after), "--json", str(output)]) == 1
    assert json.loads(output.read_text(encoding="utf-8"))["added"][0]["category"] == "constraint"
    assert "Added lines: 1" in capsys.readouterr().out
    assert "### Constraint" in markdown(compare_text(before.read_text(), after.read_text()))


def test_identical_exit(tmp_path: Path) -> None:
    before = tmp_path / "before.md"
    after = tmp_path / "after.md"
    before.write_text("Same\n", encoding="utf-8")
    after.write_text("Same\n", encoding="utf-8")
    assert main([str(before), str(after)]) == 0
