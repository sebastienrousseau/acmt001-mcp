<!-- SPDX-License-Identifier: Apache-2.0 -->

# acmt001-mcp Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about acmt001-mcp without
prior context.

## The pipeline

```
MCP client (Claude Desktop, IDE, agent)
        |  stdio, streamable HTTP or SSE (JSON-RPC)
        v
acmt001_mcp/server.py        (MCP server: tools, resources, prompt)
        |  thin typed wrappers
        v
acmt001.services             (list_message_types, get_required_fields,
        |                     get_input_schema, validate_records,
        |                     validate_identifier, generate_message)
        v
ISO 20022 acmt XML / structured data
```

Tools are deliberately thin: every one is a small adapter that
delegates to the
[`acmt001`](https://github.com/sebastienrousseau/acmt001) library's
`services` facade and returns a JSON-serialisable result. The same
facade backs the library's CLI and REST API, so every interface behaves
identically.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `acmt001_mcp/server.py` | The MCP server, all tool / resource / prompt registrations |
| **Entry point** | `acmt001_mcp.server:main` (console script: `acmt001-mcp`) | Launches the server over stdio, or over streamable HTTP / SSE with `--transport` (`_cli.py` + `_transports.py`, ADR 0001) |
| **SDK shim** | `acmt001_mcp/_mcp_compat.py` | Builds the server on either supported major of the `mcp` SDK (2.x `MCPServer`, 1.x `FastMCP`) |
| **Version** | `acmt001_mcp/__init__.py` | Single source of truth (`__version__`) |
| **Tests** | `tests/test_mcp_server.py`, `tests/test_transports.py`, `tests/test_mcp_sdk_compat.py`, `tests/test_suite_conformance.py` | In-process regressions, the command line, the SDK shim, and the shared suite conformance gate |
| **Examples** | `examples/mcp_tools.py` | Runnable in-process walkthrough of the tools |
| **Benchmarks** | `benches/bench_tool_dispatch.py` | What an agent waits for per tool; `docs/benchmarks.md` explains the result |
| **Release helpers** | `scripts/verify_versions.py`, `scripts/check_suite_consistency.py` | Assert every restatement of the version agrees; compare the published suite against PyPI |

## Tools, resources, prompts

The current MCP surface:

- **Tools** - `list_message_types`, `get_required_fields`,
  `get_input_schema`, `validate_records`, `validate_identifier`,
  `generate_message`, and `verify_lei_online` (the one tool that makes
  an outbound call; needs the `online` extra).
- **Resources** - `acmt001://message-types` (the catalogue as JSON) and
  `acmt001://describe/{message_type}` (required fields plus the input
  JSON Schema of one type).
- **Prompts** - `onboard_corporate_account(company_name=..., country=...)`
  (guided instruction template).

## Key design decisions

- **Delegation, not duplication.** Every tool is a thin wrapper over
  `acmt001.services`. If you want a new tool, port the matching helper
  from `acmt001` rather than re-implementing it here.
- **Errors as data.** Tools never raise. A `ValueError`, and a schema
  failure on the rendered XML, is turned into an `{"error": ...}`
  payload so the agent can reason about failure without parsing
  tracebacks.
- **Loopback by default.** stdio needs no socket. The HTTP transports
  bind `127.0.0.1` unless told otherwise and add no authentication of
  their own; a routable deployment sits behind a gateway (ADR 0001).
- **One outbound call, and it is named.** `verify_lei_online` is the
  only tool that reaches the network; its GLEIF answers are cached for
  five minutes so a session does not repeat a lookup.
- **Coverage enforced at 100%** line+branch; only defensive guards are
  `# pragma: no cover`.

## Extension points

- **Add a tool:** add a function under `@server.tool(...)` in
  `acmt001_mcp/server.py`; pair it with tests in
  `tests/test_mcp_server.py` and add it to `EXPECTED_TOOLS` there.
- **Add a resource:** `@server.resource("acmt001://...")` decorator.
- **Add a prompt:** `@server.prompt()` decorator.
- **Match a new `acmt001` feature:** when a new `services` helper lands
  upstream, port it as a tool here in the same release window.

## Where to look first

- Runnable example: [`examples/`](examples/)
- Decisions: [`docs/adr/`](docs/adr/index.md)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`acmt001`](https://github.com/sebastienrousseau/acmt001)
