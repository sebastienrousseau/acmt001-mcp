# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-07-02

The **discoverability** cut. Registers `acmt001-mcp` with the official
Model Context Protocol Registry, adds MCP-spec conformance CI, and
positions the server as part of the ISO 20022 MCP Suite. No functional
or API changes.

### Added

- **Official MCP Registry integration.** `acmt001-mcp` is now
  registered with the official Model Context Protocol Registry
  (`registry.modelcontextprotocol.io`) as
  `io.github.sebastienrousseau/acmt001-mcp`. A new `server.json` at
  the repo root provides the registry metadata (PyPI package
  identifier, stdio transport), and the README carries an
  `mcp-name: io.github.sebastienrousseau/acmt001-mcp` marker that the
  registry uses to verify PyPI package ownership.
- **Auto-publish workflow** (`.github/workflows/publish-mcp.yml`).
  Authenticates to the MCP Registry via GitHub OIDC (no secrets
  required) on every `v*.*.*` tag push, syncs the tag version into
  `server.json`, and runs `mcp-publisher publish`. Registry metadata
  now stays in lockstep with each PyPI release automatically.
- **Protocol conformance CI** (`.github/workflows/mcp-inspect.yml`).
  Runs `@modelcontextprotocol/inspector --cli` against `tools/list`
  on every push and PR. Continuous validation of MCP protocol
  conformance across all 6 tools.
- **Glama directory manifest** (`glama.json`). Adds a Glama listing
  in the verified-owner tier so the description and tags are
  author-controlled.
- **Suite discoverability.** The README now cross-links the sibling
  banking MCP servers under a "Related MCP Servers" section,
  positioning `acmt001-mcp` as part of the ISO 20022 MCP Suite
  alongside `pain001-mcp`, `bankstatementparser-mcp`, `camt053-mcp`,
  and `noyalib-mcp`.

### Changed

- GitHub repository description and topics refreshed: description now
  positions the server as part of the ISO 20022 MCP Suite; topics
  extended with `account-opening`, `anthropic`, `claude`,
  `claude-desktop`, `financial-services`, `iso-20022`, `mcp-server`,
  `payments`, `sepa`, and `stdio`.

### No functional / API changes

- Same 6 MCP tools as v0.0.1. This release is metadata, CI, and
  discoverability only. Existing Claude Desktop / Cursor / Zed
  configurations continue to work unchanged.

## [0.0.1] - 2026-06-16

### Added

- Initial release of `acmt001-mcp`, a Model Context Protocol (MCP) server that
  exposes the [`acmt001`](https://github.com/sebastienrousseau/acmt001) ISO
  20022 acmt Account Management library as tools for AI agents and assistants
- `acmt001-mcp` console script that runs the FastMCP server over stdio
- Six MCP tools, all delegating to the shared `acmt001.services` facade so they
  behave identically to the CLI and REST API:
  - `list_message_types` — list the 34 supported acmt message types
  - `get_required_fields` — required input fields for a message type
  - `get_input_schema` — full input JSON Schema for a message type
  - `validate_records` — validate flat records against a message type
  - `validate_identifier` — validate an IBAN, BIC, or LEI
  - `generate_message` — generate a validated acmt XML message
- Graceful error handling: tools return an `{"error": ...}` payload on a
  `ValueError` rather than raising
- Python 3.10+ support; depends on `acmt001` (>=0.0.1) and `mcp` (>=1.2)
- Runnable example (`examples/mcp_tools.py`) invoking the tools in-process

[0.0.2]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.1
