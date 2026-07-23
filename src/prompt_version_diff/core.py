"""Deterministic prompt-line comparison and categorization."""

from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass
from typing import Literal

Category = Literal["constraint", "context", "example", "instruction"]


@dataclass(frozen=True)
class ChangedLine:
    """One added or removed nonblank line."""

    line: int
    category: Category
    text: str


@dataclass(frozen=True)
class PromptDiff:
    """Complete prompt comparison."""

    added: tuple[ChangedLine, ...]
    removed: tuple[ChangedLine, ...]
    unchanged_lines: int

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation."""
        return asdict(self)


def categorize(text: str) -> Category:
    """Classify a line using visible, documented cues."""
    lowered = text.strip().casefold()
    if lowered.startswith(("example:", "examples:", "for example", "e.g.", "e.g:")):
        return "example"
    if lowered.startswith(("context:", "background:", "role:", "you are ")):
        return "context"
    constraint_cues = (
        " must ",
        " never ",
        " do not ",
        " don't ",
        " cannot ",
        " required ",
        " only ",
    )
    padded = f" {lowered} "
    if any(cue in padded for cue in constraint_cues) or lowered.startswith(
        ("must ", "never ", "only ")
    ):
        return "constraint"
    return "instruction"


def meaningful_lines(text: str) -> list[tuple[int, str]]:
    """Return numbered nonblank lines while preserving supplied text."""
    return [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if line.strip()
    ]


def changed(items: list[tuple[int, str]], indexes: range) -> list[ChangedLine]:
    """Convert selected numbered lines into categorized records."""
    return [
        ChangedLine(items[index][0], categorize(items[index][1]), items[index][1])
        for index in indexes
    ]


def compare_text(before: str, after: str) -> PromptDiff:
    """Compare two prompts by nonblank line sequence."""
    old = meaningful_lines(before)
    new = meaningful_lines(after)
    matcher = difflib.SequenceMatcher(
        a=[line for _, line in old], b=[line for _, line in new], autojunk=False
    )
    added: list[ChangedLine] = []
    removed: list[ChangedLine] = []
    unchanged = 0
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            unchanged += old_end - old_start
        if tag in {"delete", "replace"}:
            removed.extend(changed(old, range(old_start, old_end)))
        if tag in {"insert", "replace"}:
            added.extend(changed(new, range(new_start, new_end)))
    return PromptDiff(tuple(added), tuple(removed), unchanged)
