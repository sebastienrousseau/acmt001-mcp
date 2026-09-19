"""Sphinx configuration for acmt001-mcp documentation."""

from __future__ import annotations

import importlib.metadata

project = "acmt001-mcp"
author = "Sebastien Rousseau"
copyright = "2023-2026, Sebastien Rousseau"

try:
    release = importlib.metadata.version("acmt001-mcp")
except importlib.metadata.PackageNotFoundError:
    release = "0.0.0+dev"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "myst_parser",
]

# MyST options: enable Markdown directives without breaking standard
# CommonMark renders.
myst_enable_extensions = ["colon_fence", "deflist", "linkify"]
# The README's ```mermaid fence is a diagram, not code to highlight.
myst_fence_as_directive = ["mermaid"]
# Resolve the README's in-page links (#install, #tools, ...) to headings.
myst_heading_anchors = 3

# Allow myst_parser to ingest the top-level README.md.
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Furo theme: lightweight, modern, mobile-friendly.
html_theme = "furo"
html_title = f"acmt001-mcp {release}"

# Cross-link to the Python stdlib. The acmt001 site publishes no
# Sphinx inventory, so it is linked by URL from the pages instead.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# ``pydantic.Field`` is imported into the server module for the
# parameter annotations; it is not part of this package's API, and its
# own annotations use forward references the type-hint extension cannot
# resolve from here.
suppress_warnings = ["sphinx_autodoc_typehints.forward_reference"]

# Autodoc defaults.
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
