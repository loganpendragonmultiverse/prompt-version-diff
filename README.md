# Prompt Version Diff

> ⭐ **Gold Star Project**
> I consider this project complete. Fixes, maintenance and good new ideas are still welcome.
> [About Gold Stars](https://www.loganpendragonforge.com/open-source/?gold=1)

Prompt Version Diff compares two local prompt files and groups added and removed nonblank lines into visible categories: constraints, context, examples, and instructions. It uses documented deterministic cues—never an AI model—so every classification is reproducible and reviewable.

## Version 1.1.2 — 2026-10-18

Create reports only at new, distinct destinations. Existing inputs and reports are never overwritten; ordinary report-write failures recover unchanged new reports created by that invocation. Comparison and categorization behavior is unchanged.

## Three-minute use

```sh
python -m pip install .
prompt-version-diff prompt-old.md prompt-new.md --markdown changes.md --json changes.json
```

The exit code is `1` when meaningful lines changed, `0` when they match, and `2` for invalid input or report/terminal output errors. Blank-line-only formatting changes are ignored.

Report directories must already exist. Both destinations are checked and exclusively reserved before either report is written. If an ordinary write or terminal-output failure occurs, unchanged reports created by that invocation are removed so you can correct the destination and retry. Existing files are preserved. Recovery checks new reports’ identity and contents and names paths it cannot safely recover. Abrupt process termination and power-loss atomicity across files are not promised, and text already read from stdout cannot be recalled.

## Privacy and limitations

Files remain local. Reports repeat prompt text and can expose supplied context, so review them before sharing. Categories are lexical review aids, not semantic understanding. The tool does not detect every instruction, resolve conflicts, judge prompt quality, compare model behavior, or send content to an API.

## Development

```sh
python -m pip install -e ".[dev]"
ruff format --check . && ruff check .
mypy src tests
pytest
python -m build
```

The original release is feature complete for line-oriented prompt review. Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md), security reports follow [SECURITY.md](SECURITY.md), and the project uses the MIT License.

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.

## Optional context windows

Use `--context N` (or `compare_text(before, after, context=N)`) to include N neighboring nonblank lines on each side of a change. Adjacent windows merge; distant changes stay separate. Context records retain original physical line numbers and lexical categories. Blank lines and CRLF differences remain ignored, matching the existing comparison. The default `--context 0` preserves the original JSON keys and Markdown output; positive context adds `hunks` with `before` and `after` records. Added/removed totals and exit codes still count changes only.
