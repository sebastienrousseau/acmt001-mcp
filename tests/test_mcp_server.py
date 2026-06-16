# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Acmt001 MCP server."""

import asyncio
import json

import pytest

pytest.importorskip("mcp")

from mcp.server.fastmcp import FastMCP  # noqa: E402

import acmt001_mcp.server as server  # noqa: E402

EXPECTED_TOOLS = {
    "list_message_types",
    "get_required_fields",
    "get_input_schema",
    "validate_records",
    "validate_identifier",
    "generate_message",
}


def _registered_tool_names() -> set[str]:
    """Return the names of every tool registered on the FastMCP server.

    Prefers the synchronous ``_tool_manager.list_tools()`` introspection;
    falls back to the async ``list_tools()`` API if unavailable.
    """
    manager = getattr(server.server, "_tool_manager", None)
    if manager is not None and hasattr(manager, "list_tools"):
        return {tool.name for tool in manager.list_tools()}
    tools = asyncio.run(server.server.list_tools())
    return {tool.name for tool in tools}


def test_server_and_main_are_well_formed():
    """The module exposes a FastMCP server and a callable ``main``."""
    assert isinstance(server.server, FastMCP)
    assert callable(server.main)


def test_all_tools_registered():
    """All six tools are registered on the server."""
    assert _registered_tool_names() == EXPECTED_TOOLS


def test_list_message_types_returns_34():
    """The list tool reports every supported message type (34)."""
    result = server.list_message_types()
    assert isinstance(result, list)
    assert len(result) == 34
    assert all("message_type" in row and "name" in row for row in result)


def test_validate_identifier_valid_and_invalid():
    """A known-good and known-bad BIC are classified correctly."""
    good = server.validate_identifier("bic", "NWBKGB2LXXX")
    assert good == {"kind": "bic", "value": "NWBKGB2LXXX", "valid": True}

    bad = server.validate_identifier("bic", "NOTABIC")
    assert bad["valid"] is False


def test_validate_identifier_unsupported_kind_returns_error():
    """An unsupported identifier kind yields an error dict, not an exception."""
    result = server.validate_identifier("ssn", "123-45-6789")
    assert "error" in result


def test_generate_message_returns_xml(sample_record):
    """Generating acmt.007.001.05 yields a validated XML document."""
    xml = server.generate_message("acmt.007.001.05", [sample_record])
    assert isinstance(xml, str)
    assert xml.lstrip().startswith("<?xml")
    assert "Document" in xml


def test_invalid_message_type_returns_error_dict():
    """An unsupported message type returns an ``{"error": ...}`` dict."""
    result = server.get_required_fields("acmt.999.999.99")
    # get_required_fields returns a list; the error is surfaced as a string
    # entry. The schema-bearing tools return an error dict directly.
    schema_result = server.get_input_schema("acmt.999.999.99")
    assert isinstance(schema_result, dict)
    assert "error" in schema_result
    assert any("error" in str(item) for item in result)


def test_generate_message_error_is_serializable():
    """A failed generation returns a JSON-serializable error string."""
    out = server.generate_message("acmt.999.999.99", [{}])
    payload = json.loads(out)
    assert "error" in payload


def test_call_tool_through_fastmcp(sample_record):
    """Tools are invocable through the FastMCP dispatch layer."""

    async def go():
        result = await server.server.call_tool(
            "validate_identifier", {"kind": "bic", "value": "NWBKGB2LXXX"}
        )
        # call_tool returns a sequence of content blocks; extract the text.
        block = result[0] if isinstance(result, (list, tuple)) else result
        text = getattr(block, "text", None)
        if text is None and isinstance(result, tuple):
            # Newer FastMCP returns (content, structured) tuples.
            text = json.dumps(result[1])
        return json.loads(text)

    payload = asyncio.run(go())
    assert payload["valid"] is True
