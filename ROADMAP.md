# acmt001-mcp Roadmap

This roadmap tracks what is planned for the MCP companion of the
[acmt001](https://github.com/sebastienrousseau/acmt001) library. It
summarises the CHANGELOG and the open issues; it does not promise work
that is not tracked there. Releases ship when the gates pass, not on a
calendar.

## v0.0.9 (current)

- Seven tools over `acmt001.services`: `list_message_types`,
  `get_required_fields`, `get_input_schema`, `validate_records`,
  `validate_identifier`, `generate_message`, `verify_lei_online`.
- Two resources (`acmt001://message-types`,
  `acmt001://describe/{message_type}`) and one prompt
  (`onboard_corporate_account`).
- 100% line+branch coverage gate, the shared suite conformance test, a
  dispatch benchmark, and a scheduled check that the published suite
  agrees with itself.
- One version number across `acmt001`, `acmt001-lsp` and `acmt001-mcp`.

## Next release (on `main`, unreleased)

- stdio, streamable HTTP (2026-07-28 and 2025-11-25) and SSE from one
  command line (ADR 0001).
- Runs on both supported majors of the `mcp` SDK through a
  compatibility shim.
- `generate_message` reports an XSD failure as an `{"error": ...}`
  payload; `verify_lei_online` caches GLEIF answers for five minutes.

## Beyond

No further work is scheduled. There are no open feature issues at the
time of writing. New tools follow the library: when a helper lands in
`acmt001.services`, it is ported here in the same release window.

## Out of scope (handled elsewhere)

- **Editor features** - see [`acmt001-lsp`](https://github.com/sebastienrousseau/acmt001-lsp).
- **The CLI and REST API** - see the core
  [`acmt001`](https://github.com/sebastienrousseau/acmt001) library.
