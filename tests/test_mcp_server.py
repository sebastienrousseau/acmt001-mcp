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
import sys

import httpx
import pytest
import respx

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
    "verify_lei_online",
}

# A synthetic, clearly-fake GLEIF-shaped response used only as a parsing
# fixture. The LEI and entity details below are invented test data, NOT a claim
# about any real registered entity; the assertions only check that the tool
# maps these fields into the documented return shape.
_TEST_LEI = "TEST0000000000000000"
_CANNED_GLEIF_RESPONSE = {
    "data": {
        "type": "lei-records",
        "id": _TEST_LEI,
        "attributes": {
            "lei": _TEST_LEI,
            "entity": {
                "legalName": {"name": "Example Test Entity", "language": "en"},
                "legalAddress": {"country": "GB", "city": "London"},
                "status": "ACTIVE",
            },
            "registration": {
                "initialRegistrationDate": "2020-01-01T00:00:00Z",
                "lastUpdateDate": "2024-06-01T00:00:00Z",
                "status": "ISSUED",
                "nextRenewalDate": "2025-06-01T00:00:00Z",
            },
        },
    }
}
_GLEIF_URL = server._GLEIF_LEI_RECORD_URL.format(lei=_TEST_LEI)


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


def _tool_input_schema(name: str) -> dict:
    """Return the JSON input schema a client sees for the named tool."""
    for tool in asyncio.run(server.server.list_tools()):
        if tool.name == name:
            return tool.inputSchema
    raise AssertionError(f"tool not registered: {name}")


def test_message_type_param_exposes_enum():
    """Closed-set message_type surfaces its 34 values as JSON-Schema enum."""
    prop = _tool_input_schema("get_input_schema")["properties"]["message_type"]
    assert prop["enum"] == server._MESSAGE_TYPE_VALUES
    assert len(prop["enum"]) == 34


def test_identifier_kind_param_exposes_enum():
    """Closed-set identifier kind surfaces iban/bic/lei as JSON-Schema enum."""
    prop = _tool_input_schema("validate_identifier")["properties"]["kind"]
    assert set(prop["enum"]) == {"iban", "bic", "lei"}


def test_server_and_main_are_well_formed():
    """The module exposes a FastMCP server and a callable ``main``."""
    assert isinstance(server.server, FastMCP)
    assert callable(server.main)


def test_all_tools_registered():
    """Every tool (including verify_lei_online) is registered on the server."""
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


def test_validate_records_valid_report(sample_record):
    """A well-formed record validates cleanly with a full report shape."""
    report = server.validate_records("acmt.007.001.05", [sample_record])
    assert isinstance(report, dict)
    assert report["valid"] is True
    assert report["total"] == 1
    assert report["valid_count"] == 1
    assert report["errors"] == []


def test_validate_records_reports_errors(sample_record):
    """A record missing a required field is reported as invalid, not raised."""
    incomplete = dict(sample_record)
    incomplete.pop("account_id", None)
    report = server.validate_records("acmt.007.001.05", [incomplete])
    assert report["valid"] is False
    assert report["valid_count"] < report["total"]
    assert report["errors"]


def test_validate_records_invalid_message_type_returns_error_dict():
    """An unsupported message type returns an ``{"error": ...}`` dict."""
    result = server.validate_records("acmt.999.999.99", [{}])
    assert isinstance(result, dict)
    assert "error" in result


def test_list_message_types_value_error_returns_error_list(monkeypatch):
    """A ValueError from the service surfaces as an ``[{"error": ...}]`` list."""

    def boom():
        raise ValueError("catalogue unavailable")

    monkeypatch.setattr(server.services, "list_message_types", boom)
    result = server.list_message_types()
    assert result == [{"error": "catalogue unavailable"}]


def test_main_runs_the_server(monkeypatch):
    """``main`` delegates to the FastMCP server's ``run`` over stdio."""
    calls = []
    monkeypatch.setattr(server.server, "run", lambda: calls.append(True))
    server.main()
    assert calls == [True]


def test_call_tool_through_fastmcp(sample_record):
    """Tools are invocable through the FastMCP dispatch layer."""

    async def go():
        result = await server.server.call_tool(
            "validate_identifier", {"kind": "bic", "value": "NWBKGB2LXXX"}
        )
        # call_tool returns a sequence of content blocks; extract the text.
        block = result[0] if isinstance(result, list | tuple) else result
        text = getattr(block, "text", None)
        if text is None and isinstance(result, tuple):
            # Newer FastMCP returns (content, structured) tuples.
            text = json.dumps(result[1])
        return json.loads(text)

    payload = asyncio.run(go())
    assert payload["valid"] is True


def test_verify_lei_online_is_open_world():
    """The GLEIF lookup tool is annotated open-world, unlike the pure readers."""
    assert server._EXTERNAL.openWorldHint is True
    assert server._PURE_READ.openWorldHint is False


@respx.mock
def test_verify_lei_online_parses_gleif_response():
    """A canned GLEIF response is mapped into the documented return shape."""
    respx.get(_GLEIF_URL).mock(
        return_value=httpx.Response(200, json=_CANNED_GLEIF_RESPONSE)
    )
    result = server.verify_lei_online(_TEST_LEI)
    assert result == {
        "lei": _TEST_LEI,
        "legal_name": "Example Test Entity",
        "status": "ACTIVE",
        "country": "GB",
        "registration_status": "ISSUED",
        "initial_registration_date": "2020-01-01T00:00:00Z",
        "last_update_date": "2024-06-01T00:00:00Z",
        "next_renewal_date": "2025-06-01T00:00:00Z",
    }


@respx.mock
def test_verify_lei_online_404_returns_not_found():
    """An HTTP 404 from GLEIF surfaces as an 'LEI not found' error dict."""
    respx.get(_GLEIF_URL).mock(return_value=httpx.Response(404))
    result = server.verify_lei_online(_TEST_LEI)
    assert result == {"error": f"LEI not found: {_TEST_LEI}"}


@respx.mock
def test_verify_lei_online_500_returns_unavailable():
    """A non-200, non-404 response surfaces as a 'GLEIF API unavailable' error."""
    respx.get(_GLEIF_URL).mock(return_value=httpx.Response(500))
    result = server.verify_lei_online(_TEST_LEI)
    assert result == {"error": "GLEIF API unavailable: HTTP 500"}


@respx.mock
def test_verify_lei_online_transport_error_returns_unavailable():
    """A transport/connection error surfaces as a 'GLEIF API unavailable' error."""
    respx.get(_GLEIF_URL).mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    result = server.verify_lei_online(_TEST_LEI)
    assert "error" in result
    assert result["error"].startswith("GLEIF API unavailable")


def test_verify_lei_online_missing_extra_returns_error(monkeypatch):
    """Without the 'online' extra (no httpx), a graceful install hint is returned."""
    # Force ``import httpx`` inside the tool to raise ImportError, simulating
    # an install without the optional [online] extra.
    monkeypatch.setitem(sys.modules, "httpx", None)
    result = server.verify_lei_online(_TEST_LEI)
    assert "error" in result
    assert "acmt001-mcp[online]" in result["error"]
