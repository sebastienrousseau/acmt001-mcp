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

# Annotations for the single tool that reaches an external system. Unlike every
# other tool here, ``verify_lei_online`` performs a live HTTP GET against the
# public GLEIF LEI register, so it is open-world (``openWorldHint=True``). It is
# still a non-destructive, idempotent read: it never mutates remote state, and
# the same LEI yields the same record barring an upstream data change.
_EXTERNAL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# GLEIF (Global Legal Entity Identifier Foundation) public REST API endpoint for
# a single LEI record. See https://api.gleif.org/. This is the one external
# system this server contacts, and only from ``verify_lei_online``.
_GLEIF_LEI_RECORD_URL = "https://api.gleif.org/api/v1/lei-records/{lei}"

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


@server.tool(
    title="Verify a LEI against the live GLEIF register",
    annotations=_EXTERNAL,
)
def verify_lei_online(
    lei_code: Annotated[
        str,
        Field(
            description=(
                "A 20-character ISO 17442 Legal Entity Identifier to look up "
                "in the live GLEIF register, e.g. '5493001KJTIIGC8Y1R12'. Use "
                "validate_identifier(kind='lei', ...) first for a purely "
                "offline check-digit/format check."
            )
        ),
    ],
) -> dict:
    """Verify a LEI against the live GLEIF register (reaches the network).

    Unlike ``validate_identifier``, which checks an LEI's format and check
    digits entirely offline, this tool performs a live HTTP GET against the
    public GLEIF REST API (``api.gleif.org``) to confirm the LEI is actually
    registered and to return the registered entity's details. It therefore
    requires network access and is marked open-world.

    Requires the optional ``online`` extra (``pip install acmt001-mcp[online]``)
    for the ``httpx`` HTTP client; without it a graceful ``{"error": ...}`` is
    returned rather than raising.

    Returns a dict with the ``lei``, registered ``legal_name``, entity
    ``status``, ``country``, and registration ``registration_status``,
    ``initial_registration_date``, ``last_update_date`` and
    ``next_renewal_date``. On failure returns ``{"error": ...}``: an
    ``LEI not found`` error for an unregistered LEI (HTTP 404), or a
    ``GLEIF API unavailable`` error for any other non-200 response or a
    transport/connection error.

    Args:
        lei_code: A 20-character ISO 17442 Legal Entity Identifier.
    """
    try:
        import httpx
    except ImportError:
        return {
            "error": (
                "verify_lei_online requires the optional 'online' extra; "
                "install it with: pip install acmt001-mcp[online]"
            )
        }

    url = _GLEIF_LEI_RECORD_URL.format(lei=lei_code)
    try:
        response = httpx.get(
            url,
            timeout=10.0,
            headers={"Accept": "application/vnd.api+json"},
        )
    except httpx.HTTPError as exc:
        return {"error": f"GLEIF API unavailable: {exc}"}

    if response.status_code == 404:
        return {"error": f"LEI not found: {lei_code}"}
    if response.status_code != 200:
        return {"error": f"GLEIF API unavailable: HTTP {response.status_code}"}

    attributes = response.json().get("data", {}).get("attributes", {})
    entity = attributes.get("entity", {})
    registration = attributes.get("registration", {})

    return {
        "lei": attributes.get("lei", lei_code),
        "legal_name": entity.get("legalName", {}).get("name"),
        "status": entity.get("status"),
        "country": entity.get("legalAddress", {}).get("country"),
        "registration_status": registration.get("status"),
        "initial_registration_date": registration.get(
            "initialRegistrationDate"
        ),
        "last_update_date": registration.get("lastUpdateDate"),
        "next_renewal_date": registration.get("nextRenewalDate"),
    }


def main() -> None:
    """Run the Acmt001 MCP server over stdio (the ``acmt001-mcp`` entry point)."""
    server.run()


if __name__ == "__main__":
    main()
