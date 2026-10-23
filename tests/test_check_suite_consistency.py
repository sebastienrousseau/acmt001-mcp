# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The scheduled suite check compares this tree with this package on PyPI.

The script was copied from the core ``acmt001`` repository, where the core
and the tree are the same distribution. Here they are not: comparing the
``acmt001-mcp`` tree with the published ``acmt001`` core reported a
never-released bump that did not exist. PyPI is never reached; the
published versions are substituted.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "check_suite_consistency.py"
)


@pytest.fixture
def script(monkeypatch):
    """The script as a module, with PyPI and the tree substituted."""
    spec = importlib.util.spec_from_file_location("suite_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def use(tree: str, published: dict[str, str | None]):
        monkeypatch.setattr(module, "tree_version", lambda: tree)
        monkeypatch.setattr(module, "published_version", published.get)
        return module.check()[0]

    return use


def test_tree_is_compared_with_this_distribution(script):
    """A released tree is clean when every member is on its number."""
    problems = script(
        "0.0.11",
        {
            "acmt001": "0.0.11",
            "acmt001-lsp": "0.0.11",
            "acmt001-mcp": "0.0.11",
        },
    )
    assert problems == []


def test_unreleased_bump_names_this_distribution(script):
    """A bump that never reached PyPI is reported against acmt001-mcp."""
    problems = script(
        "0.0.12",
        {
            "acmt001": "0.0.11",
            "acmt001-lsp": "0.0.11",
            "acmt001-mcp": "0.0.11",
        },
    )
    assert problems == [
        "acmt001-mcp: tree is 0.0.12 but PyPI has 0.0.11. Either the "
        "release was never tagged, or the tree is behind."
    ]


def test_core_on_another_number_is_not_a_tree_problem(script):
    """Members that disagree are reported as such, not as a stale tree."""
    problems = script(
        "0.0.11",
        {
            "acmt001": "0.0.9",
            "acmt001-lsp": "0.0.9",
            "acmt001-mcp": "0.0.11",
        },
    )
    assert problems == [
        "acmt001-mcp: published 0.0.11, but the suite is at 0.0.9"
    ]


def test_member_leading_the_core_is_reported(script):
    """A member published ahead of the core is a problem, never a pass."""
    problems = script(
        "0.0.12",
        {
            "acmt001": "0.0.11",
            "acmt001-lsp": "0.0.12",
            "acmt001-mcp": "0.0.12",
        },
    )
    assert problems == [
        "acmt001-lsp: published 0.0.12, but the suite is at 0.0.11",
        "acmt001-mcp: published 0.0.12, but the suite is at 0.0.11",
    ]


def test_unreadable_index_is_reported(script):
    """A member PyPI cannot answer for is a problem, never a pass."""
    problems = script(
        "0.0.11",
        {"acmt001": "0.0.11", "acmt001-mcp": "0.0.11"},
    )
    assert problems == ["acmt001-lsp: could not read PyPI"]
