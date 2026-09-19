# acmt001-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes the [acmt001](https://github.com/sebastienrousseau/acmt001)
ISO 20022 Account Management library as agent tools: discover `acmt`
message types, inspect input schemas, validate records and financial
identifiers, and generate XSD-validated XML from a conversation.

```{toctree}
:maxdepth: 2
:caption: Contents

readme
api
benchmarks
adr/index
roadmap
changelog
```

## What it is

Seven tools, one prompt and two resources over the `acmt001.services`
facade, the same layer the library's CLI and REST API use, so every
interface behaves identically. Tools return JSON; a failure is an
`{"error": ...}` payload, never an exception the client would see as a
bare "Error executing tool".

| Tool | Purpose |
|------|---------|
| `list_message_types` | The 34 supported `acmt` message types and their names |
| `get_required_fields` | The mandatory input fields for one message type |
| `get_input_schema` | The full JSON Schema of a message type's flat input record |
| `validate_records` | A row-by-row validation report for a batch of records |
| `validate_identifier` | Offline IBAN, BIC or LEI check |
| `generate_message` | XSD-validated `acmt` XML from in-memory records |
| `verify_lei_online` | Live GLEIF lookup of a LEI (needs the `online` extra) |

The `onboard_corporate_account` prompt teaches a client the tool order for
onboarding an account; the `acmt001://message-types` and
`acmt001://describe/{message_type}` resources expose the catalogue to
clients that read resources rather than call tools.

## Why

Account opening, maintenance, switching and closing messages are
structured, schema-bound documents that agents get subtly wrong when they
write XML by hand. Putting the library behind typed tools with closed-set
enums and explicit error envelopes lets an agent discover the contract,
validate before it generates, and never ship an invalid file.

## Install

```sh
pip install acmt001-mcp             # Python 3.10+
pip install "acmt001-mcp[online]"   # adds httpx for verify_lei_online
```

## Transports

```sh
acmt001-mcp                                   # stdio (default)
acmt001-mcp --transport streamable-http       # HTTP on 127.0.0.1:8000/mcp
acmt001-mcp --transport sse --port 8001       # the older HTTP+SSE transport
```

Streamable HTTP serves both current protocol revisions (2026-07-28
stateless with `server/discover`, and 2025-11-25 with the `initialize`
handshake) on one endpoint. The listener binds loopback unless told
otherwise and carries no authentication; put it behind a gateway before
binding a routable address. See ADR 0001 for the decision.

## Quality gates

Every change passes a 100% line and branch coverage gate, a 100%
docstring gate (`interrogate`), property-based tests (Hypothesis), a
mutation-testing floor over the tool handlers (`mutmut`), ruff, black and
strict mypy, and a benchmark that runs in CI so it cannot rot.

## Quick links

- [Source on GitHub](https://github.com/sebastienrousseau/acmt001-mcp)
- [PyPI release](https://pypi.org/project/acmt001-mcp/)
- [Sibling: acmt001-lsp](https://github.com/sebastienrousseau/acmt001-lsp)
- [Core library: acmt001](https://github.com/sebastienrousseau/acmt001)

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
