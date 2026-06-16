# acmt001-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
the [`acmt001`](https://github.com/sebastienrousseau/acmt001) ISO 20022 Account
Management library as tools for AI agents and assistants.

Part of the **acmt001 suite**: [`acmt001`](https://pypi.org/project/acmt001/)
(core) · `acmt001-mcp` (this package) ·
[`acmt001-lsp`](https://pypi.org/project/acmt001-lsp/).

## Install

Requires **Python 3.10+** (it pulls in `acmt001` and the MCP SDK):

```sh
python -m pip install acmt001-mcp
```

## Run

Launch the server over stdio:

```sh
acmt001-mcp
```

Register it with any MCP client (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "acmt001": { "command": "acmt001-mcp" }
  }
}
```

## Tools

All tools delegate to the shared `acmt001.services` layer, so they behave
identically to the CLI and REST API.

| Tool | Purpose |
|------|---------|
| `list_message_types` | List the 34 supported acmt message types |
| `get_required_fields` | Required input fields for a message type |
| `get_input_schema` | Full input JSON Schema for a message type |
| `validate_records` | Validate flat records against a message type |
| `validate_identifier` | Validate an IBAN, BIC, or LEI |
| `generate_message` | Generate a validated acmt XML message |

## Licence

Apache-2.0.
