"""The runnable example must keep running against the current server."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "mcp_tools.py"


def test_mcp_tools_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """The example calls three tools in-process and prints their answers."""
    runpy.run_path(str(EXAMPLE), run_name="__main__")
    out = capsys.readouterr().out
    assert "Registered MCP tools:" in out
    assert "'verify_lei_online'" in out
    assert '"valid": true' in out
    assert "<?xml" in out
