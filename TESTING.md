# Testing

Use an isolated Python environment and install `python -m pip install -e ".[dev]"`.
Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`.
The repository CI matrix covers Python 3.10 and 3.14 on Linux, Windows, and macOS.
New regressions live alongside the existing core/CLI tests.

## 1.1.2 output safety

Exercise source aliases, existing and duplicate destinations, symlinks, missing directories, reservation races, partial write/fsync failures, stdout failure, retained concurrent edits, retry and successful paired reports. Verify source and existing bytes remain unchanged, ordinary failures leave no unchanged new reports, output errors return status 2 without traceback, and the installed wheel runs the documented two-report command.
