<!-- SPDX-License-Identifier: Apache-2.0 -->

# Releasing acmt001-mcp

This document defines **what merits a release** and **how to cut one**,
so versions are deliberate rather than ad-hoc.

## Versioning scheme

acmt001-mcp ships as one suite with
[`acmt001`](https://github.com/sebastienrousseau/acmt001) and
[`acmt001-lsp`](https://github.com/sebastienrousseau/acmt001-lsp) on one
version number: when the suite moves to `0.0.X`, acmt001-mcp ships
`0.0.X`. This keeps the agent surface aligned with the library's
`services` facade and lets a user install both at compatible versions
with a single pin. The scheduled `Suite Consistency` workflow
(`scripts/check_suite_consistency.py`) fails when the published members
disagree.

## What merits a release

Cut a new version when there is user-visible change to ship - bug fixes,
security or dependency patches, new tools / resources / prompts, or
documentation that ships in the package.

Do **not** cut a release that contains only a version-number bump with
no functional, security, or documentation change.

## Pre-flight checklist

A release is ready only when **all** of the following hold on `main`:

1. `make check` is green (lint + mypy --strict + 100% coverage + the
   example).
2. Every Dependabot / CodeQL / Scorecard alert is resolved or has a
   documented, expiring suppression.
3. `CHANGELOG.md` has a dated section for the new version describing the
   change set.
4. The version is identical in `pyproject.toml`,
   `acmt001_mcp/__init__.py`, `CHANGELOG.md`, `glama.json` and
   `server.json` (enforced by `scripts/verify_versions.py`, which the
   `Version sources agree` workflow runs). The Glama directory and the
   MCP registry read those two manifests; a release that forgets them
   shows an old version to every agent that browses for the server.

## Cutting the release

1. Bump the version in `pyproject.toml`, `acmt001_mcp/__init__.py`,
   `glama.json` and `server.json`, and add the `CHANGELOG.md` section,
   in a single PR.
2. Merge the PR to `main` once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s vX.Y.Z -m "acmt001-mcp vX.Y.Z" <merge-commit>
   git push origin vX.Y.Z
   ```

4. The tag triggers two workflows:
   - `release.yml` builds with Poetry, runs `twine check`, attaches a
     SLSA build provenance attestation, publishes to PyPI via OIDC
     trusted publishing (with PEP 740 attestations), signs every
     distribution keylessly with cosign, creates the GitHub release
     with generated notes, and attaches CycloneDX and SPDX SBOMs plus a
     licence manifest.
   - `publish-mcp.yml` stamps `server.json` from the tag, waits for
     PyPI to surface the version, and publishes to the MCP registry.

## After releasing

- Confirm the version is live on
  [PyPI](https://pypi.org/project/acmt001-mcp/) and the GitHub release is
  published (not draft).
- Verify a clean install: `pip install acmt001-mcp==X.Y.Z` and
  `acmt001-mcp --version`.
- Confirm the MCP registry and Glama show the new version.

## CI integrations

- **PyPI trusted publisher** (`release.yml`): configured at
  <https://pypi.org/manage/account/publishing/>. The publisher claim
  set is `repo:sebastienrousseau/acmt001-mcp:environment:pypi` with
  `workflow_ref` pointing at `.github/workflows/release.yml`.
- **MCP registry** (`publish-mcp.yml`): authenticates with the
  workflow's GitHub OIDC token; no secret to configure.
