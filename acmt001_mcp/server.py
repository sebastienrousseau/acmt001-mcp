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

        from acmt001.mcp.server import main
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

from acmt001 import services
from mcp.server.fastmcp import FastMCP

server = FastMCP("acmt001")


@server.tool()
def list_message_types() -> list[dict]:
    """List every supported ISO 20022 acmt message type.

    Returns a list of ``{"message_type": ..., "name": ...}`` dictionaries, one
    per supported message type (e.g. ``acmt.001.001.08``).
    """
    try:
        return services.list_message_types()
    except ValueError as exc:
        return [{"error": str(exc)}]


@server.tool()
def get_required_fields(message_type: str) -> list[str]:
    """List the required input field names for a given acmt message type.

    Args:
        message_type: A supported ISO 20022 acmt message type.
    """
    try:
        return services.get_required_fields(message_type)
    except ValueError as exc:
        return [f"error: {exc}"]


@server.tool()
def get_input_schema(message_type: str) -> dict:
    """Return the JSON Schema describing the flat input record for a type.

    Args:
        message_type: A supported ISO 20022 acmt message type.
    """
    try:
        return services.get_input_schema(message_type)
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool()
def validate_records(message_type: str, records: list[dict]) -> dict:
    """Validate flat records against a message type's input JSON Schema.

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


@server.tool()
def validate_identifier(kind: str, value: str) -> dict:
    """Validate a financial identifier (IBAN, BIC, or LEI).

    Returns ``{"kind": str, "value": str, "valid": bool}``.

    Args:
        kind: One of ``"iban"``, ``"bic"``, or ``"lei"`` (case-insensitive).
        value: The identifier value to check.
    """
    try:
        return services.validate_identifier(kind, value)
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool()
def generate_message(message_type: str, records: list[dict]) -> str:
    """Generate a validated ISO 20022 acmt XML message from flat records.

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


def main() -> None:
    """Run the Acmt001 MCP server over stdio (the ``acmt001-mcp`` entry point)."""
    server.run()


if __name__ == "__main__":
    main()
