# Development record

Version 1.0.0 implements the complete initial scope: local line-sequence comparison, transparent lexical categories, and reviewable reports. Semantic equivalence, conflict detection, model execution, and quality scoring are excluded.

## 1.1.0 - 2026-10-15

Add opt-in `--context N` and Python API context windows with original line numbers and categories. Merge neighboring windows while preserving default output and meaningful-line counts.

See README.md for interface details and TESTING.md for the verification gate.
Published on GitHub after independent review and passing PR, main, and tag checks.

## 1.1.1 - 2026-10-16

Documentation and version declarations only. Library implementation and tests are unchanged from 1.1.0.

## 1.1.2 - Unreleased

Protect inputs and existing reports with distinct new output paths and exclusive creation. Render all data before reserving names, reserve both before writing, and recover only unchanged new reports owned by a failed invocation. Keep comparison semantics unchanged. Do not claim multi-file crash/power-loss atomicity.
