"""Command-line interface."""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

from prompt_version_diff.core import PromptDiff, compare_text
from prompt_version_diff.output import write_reports


def markdown(result: PromptDiff) -> str:
    """Render a readable diff report."""
    lines = [
        "# Prompt version diff",
        "",
        f"- Added lines: {len(result.added)}",
        f"- Removed lines: {len(result.removed)}",
        f"- Unchanged nonblank lines: {result.unchanged_lines}",
    ]
    for heading, items, marker in (("Added", result.added, "+"), ("Removed", result.removed, "-")):
        lines.extend(["", f"## {heading}", ""])
        for category in ("constraint", "context", "example", "instruction"):
            matching = [item for item in items if item.category == category]
            if matching:
                lines.extend([f"### {category.title()}", ""])
                lines.extend(f"- `{marker}{item.line}` {item.text}" for item in matching)
                lines.append("")
    if result.hunks is not None:
        lines.extend(["", "## Context windows", ""])
        for number, hunk in enumerate(result.hunks, 1):
            lines.extend([f"### Hunk {number}", ""])
            for side, items in (("Before", hunk.before), ("After", hunk.after)):
                lines.extend([f"#### {side}", ""])
                lines.extend(f"- `{item.line}` [{item.category}] {item.text}" for item in items)
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parser() -> argparse.ArgumentParser:
    """Build the parser."""
    result = argparse.ArgumentParser(
        description="Compare and categorize two local prompt versions."
    )
    result.add_argument("before", type=Path)
    result.add_argument("after", type=Path)
    result.add_argument("--json", type=Path, dest="json_output")
    result.add_argument("--markdown", type=Path, dest="markdown_output")
    result.add_argument(
        "--context",
        type=int,
        default=0,
        metavar="N",
        help="include N neighboring nonblank lines around each change",
    )
    return result


def _write_stdout(rendered: str) -> None:
    # Write real terminal/pipe descriptors directly: a failed buffered flush would
    # otherwise be retried at interpreter shutdown and replace status 2 with 120.
    try:
        fd = sys.stdout.fileno()
    except (AttributeError, io.UnsupportedOperation):
        sys.stdout.write(rendered)
        sys.stdout.flush()
        return
    data = rendered.encode(sys.stdout.encoding or "utf-8", sys.stdout.errors or "strict")
    sent = 0
    while sent < len(data):
        count = os.write(fd, data[sent : sent + 65536])
        if count <= 0:
            raise OSError("terminal write made no progress")
        sent += count


def main(argv: list[str] | None = None) -> int:
    """Run the command."""
    args = parser().parse_args(argv)
    try:
        result = compare_text(
            args.before.read_text(encoding="utf-8-sig"),
            args.after.read_text(encoding="utf-8-sig"),
            context=args.context,
        )
        rendered = markdown(result)
        outputs = []
        if args.json_output:
            outputs.append((args.json_output, json.dumps(result.to_dict(), indent=2) + "\n"))
        if args.markdown_output:
            outputs.append((args.markdown_output, rendered))

        def deliver() -> None:
            _write_stdout(rendered)

        write_reports(outputs, deliver)
    except (OSError, ValueError) as error:
        parser().error(str(error))
    return 1 if result.added or result.removed else 0
