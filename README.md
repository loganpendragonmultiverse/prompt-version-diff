# Prompt Version Diff

Prompt Version Diff compares two local prompt files and groups added and removed nonblank lines into visible categories: constraints, context, examples, and instructions. It uses documented deterministic cues—never an AI model—so every classification is reproducible and reviewable.

## Three-minute use

```sh
python -m pip install "prompt-version-diff @ https://github.com/loganpendragonmultiverse/prompt-version-diff/releases/download/v1.0.0/prompt_version_diff-1.0.0-py3-none-any.whl"
prompt-version-diff prompt-old.md prompt-new.md --markdown changes.md --json changes.json
```

The exit code is `1` when meaningful lines changed, `0` when they match, and `2` for unreadable input. Blank-line-only formatting changes are ignored.

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

Version 1.0.0 is feature complete for line-oriented prompt review. Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md), security reports follow [SECURITY.md](SECURITY.md), and the project uses the MIT License.
