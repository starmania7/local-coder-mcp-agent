from pathlib import Path

import pytest

from mcp_servers.local_coder import server


def test_allowed_root_from_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ALLOWED_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.delenv("ALLOWED_WORKSPACE_ROOTS", raising=False)

    workspace = tmp_path / "project"
    workspace.mkdir()

    assert server.validate_workspace(str(workspace)) == str(workspace.resolve())


def test_workspace_outside_allowed_root_is_rejected(monkeypatch, tmp_path: Path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()

    monkeypatch.setenv("ALLOWED_WORKSPACE_ROOT", str(allowed))
    monkeypatch.delenv("ALLOWED_WORKSPACE_ROOTS", raising=False)

    with pytest.raises(PermissionError):
        server.validate_workspace(str(outside))
