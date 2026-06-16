#!/usr/bin/env python3
"""Example: call the acmt001-mcp server's tools in-process.

Usage:
    pip install acmt001-mcp     # requires Python 3.10+
    python examples/mcp_tools.py

The acmt001 MCP server (launched as ``acmt001-mcp`` over stdio) exposes the
acmt001 library to AI agents. This example invokes the same tools directly
through the FastMCP instance, without a transport, to show what an agent would
receive.
"""

import asyncio

from acmt001_mcp.server import server

# A single flat account-opening record (one account, one owner organisation).
record = [
    {
        "msg_id": "ACMT-MSG-0001",
        "creation_date_time": "2026-01-15T10:30:00",
        "process_id": "ACMT-PRC-0001",
        "account_id": "GB29NWBK60161331926819",
        "account_currency": "EUR",
        "account_name": "Treasury Operating Account",
        "account_type_cd": "CACC",
        "account_servicer_bic": "NWBKGB2LXXX",
        "account_owner_name": "Acme Embedded Finance Ltd",
        "account_owner_country": "GB",
        "org_full_legal_name": "Acme Embedded Finance Limited",
        "org_country_of_operation": "GB",
        "org_id_lei": "5493001KJTIIGC8Y1R12",
    }
]


async def main() -> None:
    tools = await server.list_tools()
    print("Registered MCP tools:", [t.name for t in tools])

    async def call(name, args):
        result = await server.call_tool(name, args)
        # FastMCP returns a (content, structured) tuple or content blocks;
        # pull the first text payload for display.
        content = result[0] if isinstance(result, tuple) else result
        text = content[0].text if content else ""
        return text

    print(
        "list_message_types  ->",
        (await call("list_message_types", {}))[:60],
        "…",
    )
    print(
        "validate_identifier ->",
        await call(
            "validate_identifier",
            {"kind": "lei", "value": "5493001KJTIIGC8Y1R12"},
        ),
    )
    xml = await call(
        "generate_message",
        {"message_type": "acmt.007.001.05", "records": record},
    )
    print("generate_message    ->", xml[:46], "…")


if __name__ == "__main__":
    asyncio.run(main())
