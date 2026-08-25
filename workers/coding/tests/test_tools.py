from pathlib import Path

import pytest

from workers.coding.tools import WorkspaceTools


def test_list_read_write_and_patch(tmp_path: Path):
    (tmp_path / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    tools = WorkspaceTools(str(tmp_path))

    assert tools.list_files() == ["sample.py"]
    assert tools.read_file("sample.py") == "VALUE = 1\n"

    assert tools.apply_patch("sample.py", "VALUE = 1", "VALUE = 2") == (
        "Patched sample.py"
    )
    assert tools.read_file("sample.py") == "VALUE = 2\n"

    tools.write_file("new.txt", "hello")
    assert tools.read_file("new.txt") == "hello"


def test_blocks_path_escape(tmp_path: Path):
    tools = WorkspaceTools(str(tmp_path))

    with pytest.raises(PermissionError):
        tools.read_file("../outside.txt")
