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

"""Model Context Protocol (MCP) server for Acmt001.

This server exposes the Acmt001 library's ISO 20022 ``acmt`` capabilities as
MCP tools so that any MCP-compatible client (Claude Desktop, IDEs, agents) can
discover message types, inspect input schemas, validate records and financial
identifiers, and generate validated XML messages.

Every tool is a thin, typed wrapper over :mod:`acmt001.services` -- the single
shared facade also used by the CLI, REST API, and LSP server -- so all
interfaces behave identically. Tools return JSON-serializable data (dicts,
lists, or strings); on a :class:`ValueError` they return an ``{"error": ...}``
dictionary rather than raising.

Launching the server:
    * As a console script (installed with the ``servers`` extra)::

        acmt001-mcp

    * Programmatically::

        from acmt001_mcp.server import main
        main()

    * In an MCP client config (e.g. Claude Desktop ``claude_desktop_config.json``)::

        {
          "mcpServers": {
            "acmt001": {
              "command": "acmt001-mcp"
            }
          }
        }

The server communicates over stdio (FastMCP's default transport).
"""

import json
from typing import Annotated

from acmt001 import services
from acmt001.constants import valid_xml_types
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from acmt001_mcp import __version__

server = FastMCP("acmt001")
# FastMCP does not expose a version kwarg; without this override the
# MCP SDK's own version leaks into serverInfo.version, breaking
# manifest/runtime coherence checks (e.g. Glama scoring).
server._mcp_server.version = __version__

# Shared MCP tool annotations. Every tool in this server is a pure,
# side-effect-free reader over the acmt001 ``services`` facade: each tool
# computes solely from its arguments and the JSON Schemas / XSD templates
# bundled with the acmt001 library. None opens a caller-supplied filesystem
# path or reaches an external system, so all are marked ``readOnlyHint`` +
# ``idempotentHint``, never ``destructiveHint``, and closed-world
# (``openWorldHint=False``).
#
# These hints let MCP clients (and the Glama quality grader) reason about
# safety, caching, and auto-approval without executing the tool.
_PURE_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

# ---------------------------------------------------------------------------
# Closed-set parameter enums.
#
# Every value below is derived from the acmt001 library's own source-of-truth
# constants (never hardcoded here), so the accepted set stays in lockstep with
# the backend. The ``enum`` is JSON Schema metadata only -- it lets MCP clients
# constrain/auto-complete inputs -- while the ``services`` facade continues to
# enforce these values at runtime.
# ---------------------------------------------------------------------------
_MESSAGE_TYPE_VALUES: list[str] = sorted(valid_xml_types)
_MESSAGE_TYPE_LIST = ", ".join(f"'{v}'" for v in _MESSAGE_TYPE_VALUES)

_MessageType = Annotated[
    str,
    Field(
        description=(
            "A supported ISO 20022 acmt message type, e.g. 'acmt.001.001.08' "
            "Account Opening Instruction. Must be exactly one of: "
            f"{_MESSAGE_TYPE_LIST} (see list_message_types)."
        ),
        json_schema_extra={"enum": _MESSAGE_TYPE_VALUES},
    ),
]

_IDENTIFIER_KIND_VALUES: list[str] = sorted(services._IDENTIFIER_VALIDATORS)
_IDENTIFIER_KIND_LIST = ", ".join(f"'{v}'" for v in _IDENTIFIER_KIND_VALUES)

_IdentifierKind = Annotated[
    str,
    Field(
        description=(
            "The financial identifier scheme to validate against "
            "(case-insensitive). Must be exactly one of: "
            f"{_IDENTIFIER_KIND_LIST}."
        ),
        json_schema_extra={"enum": _IDENTIFIER_KIND_VALUES},
    ),
]


@server.tool(title="List acmt message types", annotations=_PURE_READ)
def list_message_types() -> list[dict]:
    """List every supported ISO 20022 acmt message type and its human name.

    Use this first, before any generation or validation call, to discover the
    exact ``message_type`` strings this server accepts (e.g.
    ``acmt.001.001.08`` Account Opening Instruction). Do not use it to fetch a
    type's fields or schema -- call ``get_required_fields`` or
    ``get_input_schema`` for that.

    Returns a list of ``{"message_type": ..., "name": ...}`` dictionaries, one
    per supported message type (e.g. ``acmt.001.001.08``).
    """
    try:
        return services.list_message_types()
    except ValueError as exc:
        return [{"error": str(exc)}]


@server.tool(title="Get required fields", annotations=_PURE_READ)
def get_required_fields(
    message_type: _MessageType,
) -> list[str]:
    """List only the required input field names for an acmt message type.

    Use this for a quick checklist of the mandatory columns before building
    account records. When you need full type/format constraints (not just
    which fields are required), call ``get_input_schema`` instead.

    Args:
        message_type: A supported ISO 20022 acmt message type.
    """
    try:
        return services.get_required_fields(message_type)
    except ValueError as exc:
        return [f"error: {exc}"]


@server.tool(title="Get input JSON Schema", annotations=_PURE_READ)
def get_input_schema(
    message_type: _MessageType,
) -> dict:
    """Return the full JSON Schema for a message type's flat input record.

    Use this to learn every field, its type, and its constraints before
    assembling records, or to drive a form/UI. For just the required-field
    names use ``get_required_fields``; to actually check records against this
    schema use ``validate_records``.

    Args:
        message_type: A supported ISO 20022 acmt message type.
    """
    try:
        return services.get_input_schema(message_type)
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool(title="Validate records against schema", annotations=_PURE_READ)
def validate_records(
    message_type: _MessageType,
    records: Annotated[
        list[dict],
        Field(
            description=(
                "One or more flat account records, each a dict of field name "
                "-> value; validated against the message type's input JSON "
                "Schema (see get_input_schema / get_required_fields)."
            )
        ),
    ],
) -> dict:
    """Validate flat account records against a message type's input JSON Schema.

    Use this before ``generate_message`` to catch structural/type errors per
    record and get a row-by-row error report. This checks JSON-Schema shape
    only; to validate a single financial identifier in isolation use
    ``validate_identifier``.

    Returns a report ``{"valid": bool, "total": int, "valid_count": int,
    "errors": [...]}``.

    Args:
        message_type: A supported ISO 20022 acmt message type.
        records: One or more flat account records to validate.
    """
    try:
        return services.validate_records(message_type, records)
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool(title="Validate IBAN, BIC or LEI", annotations=_PURE_READ)
def validate_identifier(
    kind: _IdentifierKind,
    value: Annotated[
        str,
        Field(
            description=(
                "The identifier value to check, e.g. an IBAN, BIC/SWIFT code, "
                "or LEI; validated according to the given kind."
            )
        ),
    ],
) -> dict:
    """Validate a single financial identifier (IBAN, BIC, or LEI).

    Use this for a one-off identifier check with a clear pass/fail. To
    validate identifiers embedded across a whole batch of account records,
    prefer ``validate_records`` rather than calling this per field.

    Returns ``{"kind": str, "value": str, "valid": bool}``.

    Args:
        kind: One of ``"iban"``, ``"bic"``, or ``"lei"`` (case-insensitive).
        value: The identifier value to check.
    """
    try:
        return services.validate_identifier(kind, value)
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool(title="Generate acmt XML from records", annotations=_PURE_READ)
def generate_message(
    message_type: _MessageType,
    records: Annotated[
        list[dict],
        Field(
            description=(
                "One or more flat account records, each a dict of field name "
                "-> value, from which the acmt XML is generated; run "
                "validate_records first to surface record-level errors."
            )
        ),
    ],
) -> str:
    """Generate a validated ISO 20022 acmt XML message from in-memory records.

    This is the primary generation tool: pass account records you already
    hold in memory and receive an XSD-validated XML document; no file is
    written. Run ``validate_records`` first to surface record-level errors,
    and ``list_message_types`` to confirm the ``message_type`` string.

    Returns the validated XML document as a string, or an ``{"error": ...}``
    payload (serialized) if generation fails.

    Args:
        message_type: A supported ISO 20022 acmt message type.
        records: One or more flat account records.
    """
    try:
        return services.generate(message_type, records)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Prompt.
#
# A guided workflow prompt that teaches an MCP client the canonical tool order
# for onboarding a corporate account. Like the tools, it is a pure function of
# its arguments -- it renders guidance text and never touches the backend.
# ---------------------------------------------------------------------------
@server.prompt(title="Onboard a corporate account")
def onboard_corporate_account(
    company_name: Annotated[
        str,
        Field(
            description=(
                "The legal name of the company being onboarded; left blank "
                "for generic guidance."
            )
        ),
    ] = "",
    country: Annotated[
        str,
        Field(
            description=(
                "The ISO 3166-1 alpha-2 country code of the account owner, "
                "e.g. 'GB'; left blank for generic guidance."
            )
        ),
    ] = "",
) -> str:
    """Guide an agent through onboarding a corporate account end to end.

    Renders a step-by-step playbook naming the tools to call and their order:
    ``list_message_types`` to pick a message type, then
    ``get_required_fields`` / ``get_input_schema`` to learn the input record,
    then ``validate_records`` to check the batch, and finally
    ``generate_message`` to emit the validated acmt XML.

    Args:
        company_name: The legal name of the company being onboarded.
        country: The ISO 3166-1 alpha-2 country code of the account owner.

    Returns:
        A guidance string describing the recommended tool workflow.
    """
    subject = company_name.strip() or "a corporate account"
    where = f" in {country.strip()}" if country.strip() else ""
    return (
        f"You are onboarding {subject}{where} as an ISO 20022 acmt account.\n"
        "Follow this tool order:\n"
        "1. Call list_message_types to choose the right acmt message type "
        "(e.g. 'acmt.007.001.05' Account Opening Request).\n"
        "2. Call get_required_fields for a quick checklist, then "
        "get_input_schema for the full field types and constraints.\n"
        "3. Assemble one flat record per account and call validate_records to "
        "catch structural and identifier errors before generating.\n"
        "4. Once validate_records reports valid, call generate_message to emit "
        "the XSD-validated acmt XML document."
    )


# ---------------------------------------------------------------------------
# Resources.
#
# Read-only views over the acmt001 catalogue, reusing the same ``services``
# facade functions as the tools. The static resource exposes the full message
# type catalogue; the templated resource describes a single message type's
# input record. Both return a ``json.dumps`` string, mirroring the tools'
# JSON-serializable contract.
# ---------------------------------------------------------------------------
@server.resource(
    "acmt001://message-types",
    title="acmt message type catalogue",
    mime_type="application/json",
)
def message_types_resource() -> str:
    """Expose the full acmt message type catalogue as a JSON resource.

    This is the resource form of ``list_message_types``: it returns the same
    ``[{"message_type": ..., "name": ...}, ...]`` catalogue, serialized as a
    JSON string for clients that consume resources rather than tool calls.

    Returns:
        A JSON array string of ``{"message_type", "name"}`` objects.
    """
    return json.dumps(services.list_message_types())


@server.resource(
    "acmt001://describe/{message_type}",
    title="Describe an acmt message type",
    mime_type="application/json",
)
def describe_message_type_resource(message_type: _MessageType) -> str:
    """Describe a single acmt message type's input record as a JSON resource.

    This is the resource form of ``get_required_fields`` + ``get_input_schema``
    for one message type: it returns both the required-field names and the full
    input JSON Schema, serialized as a JSON string. On an unknown message type
    it returns an ``{"error": ...}`` payload instead of raising, mirroring the
    tools' error contract.

    Args:
        message_type: A supported ISO 20022 acmt message type.

    Returns:
        A JSON object string ``{"message_type", "required_fields",
        "input_schema"}``, or ``{"error": ...}`` for an unknown type.
    """
    try:
        return json.dumps(
            {
                "message_type": message_type,
                "required_fields": services.get_required_fields(message_type),
                "input_schema": services.get_input_schema(message_type),
            }
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


def main() -> None:
    """Run the Acmt001 MCP server over stdio (the ``acmt001-mcp`` entry point)."""
    server.run()


if __name__ == "__main__":
    main()
