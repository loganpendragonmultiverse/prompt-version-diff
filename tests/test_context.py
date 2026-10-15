from pathlib import Path

import pytest

from prompt_version_diff.cli import main, markdown
from prompt_version_diff.core import compare_text


def test_default_shape_and_blank_crlf_behavior() -> None:
    result = compare_text("one\r\n\r\ntwo\r\n", "one\n \ntwo\n")
    assert result.to_dict() == {"added": (), "removed": (), "unchanged_lines": 2}
    assert compare_text("one", "one", context=2).hunks == ()


@pytest.mark.parametrize(
    "before,after", [("a\nb", "A\nb"), ("a\nb", "a\nB"), ("", "new"), ("old", "")]
)
def test_context_clips_boundaries(before: str, after: str) -> None:
    result = compare_text(before, after, context=10)
    assert result.hunks is not None and len(result.hunks) == 1
    assert [x.text for x in result.hunks[0].before] == before.splitlines()
    assert [x.text for x in result.hunks[0].after] == after.splitlines()


def test_adjacent_hunks_merge_and_repeated_lines_keep_numbers() -> None:
    result = compare_text(
        "Context: start\r\n\r\na\r\nrepeat\r\nb\r\nrepeat\r\nend",
        "Context: start\n\nA\nrepeat\nB\nrepeat\nend",
        context=1,
    )
    assert result.hunks is not None and len(result.hunks) == 1
    assert [x.line for x in result.hunks[0].before] == [1, 3, 4, 5, 6]
    assert result.hunks[0].before[0].category == "context"
    assert [x.line for x in result.added] == [3, 5]
    assert "Context windows" in markdown(result)


def test_distant_changes_get_separate_windows() -> None:
    result = compare_text("a\nb\nc\nd\ne\nf\ng", "A\nb\nc\nd\ne\nf\nG", context=1)
    assert result.hunks is not None and len(result.hunks) == 2


def test_context_cli_and_validation(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_text("old")
    b.write_text("new")
    assert main([str(a), str(b), "--context", "1"]) == 1
    with pytest.raises(SystemExit):
        main([str(a), str(b), "--context", "-1"])
    with pytest.raises(ValueError):
        compare_text("a", "b", context=-1)
