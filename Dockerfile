# syntax=docker/dockerfile:1.6
# Multi-stage build for a minimal acmt001-mcp image.
#
# The container runs the FastMCP server over stdio so an MCP client can
# launch it directly with ``docker run -i --rm acmt001-mcp``.

# The base image is pinned by digest (OpenSSF Scorecard Pinned-Dependencies);
# Dependabot's docker ecosystem keeps the tag and digest current.
FROM python:3.14-slim@sha256:0514bc76712d64f8bb48adcb95b1ab0d88c69fee95d62fe4c18ee948bee9b1e1 AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# pyproject.toml carries ``readme = "README.md"``, so README.md must be
# present at build-time for the package install to resolve the package
# metadata.
COPY pyproject.toml README.md ./
COPY requirements/docker.txt ./requirements/docker.txt
COPY acmt001_mcp ./acmt001_mcp

# Install the hash-pinned runtime dependencies (poetry-core among them, the
# build backend), build this package's wheel against them
# (--no-build-isolation), and install it with --no-deps, inside a
# self-contained virtualenv. A local wheel, not `pip install .`: Scorecard
# counts a non-editable install of a directory as unpinned.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes -r requirements/docker.txt \
    && /opt/venv/bin/pip wheel --no-deps --no-build-isolation --wheel-dir /tmp/wheel . \
    && /opt/venv/bin/pip install --no-deps /tmp/wheel/*.whl \
    && rm -rf /tmp/wheel


FROM python:3.14-slim@sha256:0514bc76712d64f8bb48adcb95b1ab0d88c69fee95d62fe4c18ee948bee9b1e1

LABEL org.opencontainers.image.title="acmt001-mcp" \
      org.opencontainers.image.description="Model Context Protocol server for the acmt001 ISO 20022 account-management library." \
      org.opencontainers.image.source="https://github.com/sebastienrousseau/acmt001-mcp" \
      org.opencontainers.image.licenses="Apache-2.0"

# Non-root user (MCP clients launch the container with stdio; no extra
# privileges needed).
RUN groupadd --system mcp && useradd --system --gid mcp --home /home/mcp mcp \
    && mkdir -p /home/mcp \
    && chown -R mcp:mcp /home/mcp

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER mcp
WORKDIR /home/mcp

# A non-zero exit here means an import / dependency mismatch; the MCP
# client will see it before the first tool call.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import acmt001_mcp.server" || exit 1

ENTRYPOINT ["acmt001-mcp"]
