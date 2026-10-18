# Changelog

## 1.1.2 - 2026-10-18

- Refuse existing, source-alias and duplicate report destinations without changing either input.
- Reserve both report names exclusively and recover unchanged new reports after ordinary write or stdout failures.
- Return actionable status 2 for output errors instead of a traceback; keep lexical comparison behavior unchanged.

## 1.1.1 - 2026-10-16

- Correct release wording and include dated release history and development notes in source distributions.
- Preserve version 1.1.0 comparison/auditing behavior; update package and runtime version declarations only.

## 1.1.0 - 2026-10-15

- Add opt-in `--context N` and Python API context windows with original line numbers and categories.
- Merge neighboring windows while preserving default output and meaningful-line counts.

## 1.0.0 - 2026-07-22

- Added deterministic nonblank-line comparison.
- Added constraint, context, example, and instruction categories.
- Added Markdown and JSON reports with original line numbers.
