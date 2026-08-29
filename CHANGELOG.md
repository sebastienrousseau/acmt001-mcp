# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.9] - 2026-08-29

Aligns the `acmt001` suite on one version number, and adds the two gates
that were missing: a benchmark and a scheduled drift check.

### Added

- `benches/bench_tool_dispatch.py` measures what an agent waits for: the
  dispatch floor, the metadata lookups used to build a request, and the
  two batch tools side by side. It records the asymmetry between them —
  `validate_records` is linear in batch size while `generate_message`
  renders only the first record for a single-account message type, so a
  hundred-record batch costs a hundred validations and yields one
  message.
- `docs/benchmarks.md` explaining that result and when it bites.
- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow compare this tree, and every published member of
  the suite, against PyPI.
- `tests/test_suite_conformance.py`, the shared suite conformance gate.
- `SECURITY.md`, written for an MCP server: the stdio transport has no
  authentication of its own, tool inputs arrive from a model rather than
  a person who read the docs, and `verify_lei_online` is the one tool
  that makes an outbound call.

### Changed

- Version aligned to `0.0.9` across `acmt001`, `acmt001-lsp` and
  `acmt001-mcp`. These three ship as one suite and had drifted to
  `0.0.5`, `0.0.2` and `0.0.8` respectively.

## [0.0.8] - 2026-08-28

The first release since 0.0.6. `0.0.7` was bumped in the tree but never
tagged or published, so everything below has been sitting unreleased —
including the `cryptography` advisory floor.

### Changed

- **The `acmt001` floor moves to `>=0.0.5`,** from `>=0.0.2`. 0.0.5 is
  the first release built against `xmlschema >=4.3.2`. The floor has to
  move with it: anything lower admits 0.0.4, which pins
  `xmlschema<4.0.0` and cannot be installed beside `pain001` or
  `camt053`. A resolver that lands there reports `ResolutionImpossible`
  without naming the cause.

- Licensing ships as `Apache-2.0 OR MIT` (#18).

### Fixed

- **`cryptography` floored at 50.0.0** — the release that patches a
  high-severity advisory — and `acmt001` taken at 0.0.4 (#16, #17).
  Cut as `0.0.7` in the tree, but never published, so no dependent has
  had it.

### Added

- Online GLEIF LEI verification tool (#14).
- Prompts and resources, for parity across the MCP suite (#13).

## [0.0.6] - 2026-07-16

Undocumented at the time; reconstructed from the commit history.

### Fixed

- `mcp` capped below 2.0. 2.0 removed `mcp.server.fastmcp`, the import
  this server uses, which broke a plain `pip install .` (#12).

### Changed

- Release workflow emits real provenance and an SBOM on publish (#11).
- README cross-links the full ISO 20022 MCP suite.

## [0.0.5] - 2026-07-11

The **quality & hardening** cut. Bundles the tooling/discoverability work
landed since 0.0.2 into a release, adds value-constraint enums and full test
coverage, and clears the dev-tooling security advisory. No breaking changes
to the six tools or their return shapes.

### Added

- **Value-constraint enums** on closed-set tool parameters (`message_type`,
  identifier `kind`), surfaced as JSON Schema `enum` metadata derived from the
  `acmt001` library's own constants so accepted values never drift.
- **Input-schema parameter descriptions** and MCP tool annotations
  (`readOnlyHint`/`idempotentHint`/…), tool titles, and usage guidance for
  richer client/Glama introspection.
- **`glama.json`** and a **`Dockerfile`** so Glama can build and score a
  release.
- Regression test asserting the `enum` metadata is emitted in each tool's
  input schema.

### Changed

- **100% statement + branch test coverage**, enforced inline via
  `--cov-fail-under=100`; CI installs the package editable so coverage data is
  collected.
- Corrected the module docstring's programmatic-import example to
  `acmt001_mcp.server`.

### Security

- Dev dependency **black** bumped to `^26.3.1` (arbitrary-file-write advisory
  in the cache-file path). The cryptography / pyarrow / pygments advisories
  are resolved upstream by `acmt001` >= 0.0.2.

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

[0.0.5]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.5
[0.0.2]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.1
