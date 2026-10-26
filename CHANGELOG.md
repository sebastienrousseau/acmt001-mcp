# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- The release SBOMs (CycloneDX and the pip-licenses manifest) describe
  the shipped runtime set: the hash-pinned `requirements/docker.txt` the
  image installs, plus the package as a local wheel, in a venv of their
  own. `poetry install` had resolved afresh (no `poetry.lock` is
  committed here), and `poetry run` pointed the SBOM tools at their own
  interpreter, so the SBOM listed the tooling, not the runtime set.
- The MCP Inspector conformance job pins `@modelcontextprotocol/inspector`
  to 2.10.1, so a new npm publish cannot change what CI runs.

## [0.0.13] - 2026-10-23

Ships in lockstep with `acmt001` 0.0.13. The core's 0.0.12 is yanked:
it moved `services._IDENTIFIER_VALIDATORS`, which this server's 0.0.11
reads at import, so a fresh `pip install acmt001-mcp` failed to start.
`acmt001` 0.0.13 restores the name; this server never shipped 0.0.12.

### Security

- `mcp` is constrained to `>=1.30.0,!=2.0.*,!=2.1.*,<3`, so no release
  affected by GHSA-84m7-p3x7-pcfv (unbounded streamable HTTP session
  accumulation: mcp `>=1.8.0,<1.30.0` and `>=2.0.0,<2.2.0`) can resolve.
  The previous `>=1.2,<3` admitted them.
- Security floors on mcp's transitive stack, matching pacs008-mcp:
  `anyio >= 4.14.2`, `httpx2 >= 2.12.0`, `httpcore2 >= 2.10.0`,
  `pyjwt[crypto] >= 2.15.0`, `opentelemetry-api >= 1.45.1`
  (GHSA-xcq7-p3pf-p88h) and `certifi >= 2026.10.19` (PYSEC-2026-4320).

### Fixed

- `generate_message` answers a record whose date has a year the XSD date
  types cannot hold (`222222222026-01-15T10:30:00`) with an `{"error": ...}`
  payload. The schema check raised `OverflowError` out of the tool;
  found by the new Atheris harness, and present in 0.0.11 too.
- `scripts/check_suite_consistency.py` compares this tree with the
  published `acmt001-mcp`, not with the `acmt001` core it was copied
  from, so the scheduled Suite Consistency job no longer reports a
  never-released bump that does not exist. It still reports, correctly,
  any member that leads or lags the core.

### Added

- Coverage-guided fuzzing: `fuzz/fuzz_tools.py` (Atheris) feeds arbitrary
  text to `validate_identifier`, the message-type lookups, the
  onboarding prompt, `validate_records` and `generate_message`, run by
  the `Fuzz` workflow on every change and for 30 minutes weekly;
  `tests/test_untrusted_text.py` holds the fixed and property-based
  cases of the same contract, including that markup in a record value
  never becomes an element.
- A complexity gate in the lint job and `make check`:
  `scripts/check_complexity.py` (cyclomatic, Halstead, function and file
  length) and `complexipy` (cognitive), each against a committed
  baseline of the offenders that predate it, which may only shrink.
- `docs/POLICIES.md`, the toolchain policy the README's Python badge
  links to.

### Changed

- Requires `acmt001 >= 0.0.13, < 1`: the suite releases in lockstep.
- Every `pip install` in CI, the docs build and the container image is
  hash-pinned: `requirements/ci.txt`, `docs.txt`, `fuzz.txt` and
  `docker.txt`. The package goes on top with `--no-deps
  --no-build-isolation`, so its build backend (`poetry-core`) comes from
  those trees too instead of an unpinned isolated build; where the
  install is not editable (the docs build, the MCP Inspector job and the
  image), a wheel is built first and installed with `--no-deps`.
- The container image runs Python 3.14 (`python:3.14-slim`, pinned by
  digest) and drops the `ACMT001_PIP_SPEC` build argument and the git
  client it needed; the runtime dependencies come from
  `requirements/docker.txt`.
- GitHub Actions updated and pinned by commit SHA: checkout 7.0.1,
  setup-python 7.0.0, setup-node 7.1.0, upload-artifact 7.0.2,
  attest-build-provenance 4.2.2, gh-action-pypi-publish 1.14.2,
  sbom-action 0.24.3, scorecard-action 2.5.0, codeql-action 4.39.0.
- Development tools: ruff `>=0.1,<0.18`, mypy `>=1.11,<3.0`; the release
  tooling floors `virtualenv>=21.14.8` and `certifi>=2026.10.19`.
- The README badge row follows the portfolio template: Build, Registry,
  Docs, OpenSSF Scorecard, OpenSSF Best Practices, License, Python floor
  and Glama, every badge a 28 px shields.io image.
- `scripts/verify_versions.py` checks each manifest in its own helper; the
  output and exit codes are unchanged.
- `CITATION.cff` and `SECURITY.md` carry the current version again (they
  had been left at 0.0.10 and 0.0.9).

## [0.0.11] - 2026-10-04

### Changed

- Standardize license section heading in README to License for Glama directory and registry matcher consistency.
- Update locked dependencies to resolve transitive vulnerabilities.

## [0.0.10] - 2026-10-03

### Added

- Framework adapter module (`acmt001_mcp.adapters`) exporting acmt tools
  for LangChain, CrewAI, and LlamaIndex agents.
- Animated terminal `demo.gif` rendered via VHS from `.github/demo.tape`.
- `AGENTS.md` defining AI collaboration invariants and verification gates.
- SPDX Apache-2.0 OR MIT dual license compliance with `LICENSES/` tree.
- Mutation testing of the tool handlers with mutmut 3, gated in CI by
  `scripts/mutation_gate.py` (workflow `mutation.yml`). Tools, the prompt
  and the resources are now registered in one block instead of with
  decorators, because mutmut never mutates a decorated function; the
  catalogue a client sees is unchanged.
- Property-based tests (Hypothesis) over the logic the server owns: the
  path scrubber is idempotent, every failure is an `{"error": ...}`
  payload, `validate_records` reports are internally consistent, the
  describe resource agrees with the tools, the onboarding prompt is a
  pure function of its arguments, and the LEI cache round-trips copies
  and never exceeds its bound.
- A 100% docstring gate (`interrogate`) in the lint job.
- A rendered documentation site (Sphinx, furo) at
  <https://sebastienrousseau.github.io/acmt001-mcp/> with the README, the
  API reference, the benchmarks page, the ADRs, the roadmap and this
  changelog; built with warnings as errors and deployed from `main`.
- A test that runs `examples/mcp_tools.py`, so the example cannot rot.

- `--transport streamable-http` and `--transport sse`, with `--host` and
  `--port`. Streamable HTTP serves both current protocol revisions
  (2026-07-28 stateless with `server/discover`, and 2025-11-25 with the
  `initialize` handshake) on one endpoint and streams responses as
  server-sent events; `sse` serves the older HTTP+SSE transport. stdio
  stays the default and is unchanged. `--version` prints the version.
  ADR 0001 records the decision.

### Fixed

- `generate_message` returns an `{"error": ...}` payload when the rendered XML
  fails its XSD, instead of letting the library's `RuntimeError` escape; the
  SDK reported that as a bare "Error executing tool" with the reason kept on
  the server. The schema's install path is dropped from the message.

### Changed

- `verify_lei_online` remembers GLEIF answers (hits and not-found) for five
  minutes, bounded to 256 entries, so repeat lookups of one LEI in a session
  are answered without a round trip; transport failures are not cached.

- The server is built through a small compatibility shim so it runs on
  both supported majors of the `mcp` SDK: 2.x (`MCPServer`, the
  2026-07-28 stateless revision with `server/discover`) and 1.x
  (`FastMCP`). The dependency range is now `mcp>=1.2,<3`, so a fresh
  install gets 2.x and speaks the current protocol revision.

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

[0.0.11]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.11
[0.0.10]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.10
[0.0.5]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.5
[0.0.2]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/acmt001-mcp/releases/tag/v0.0.1
