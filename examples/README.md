# acmt001-mcp examples

Runnable, self-contained examples for the acmt001 MCP server. Run any of them
from the repository root:

```sh
python examples/<name>.py
```

| Example | Demonstrates |
|---------|--------------|
| [`mcp_tools.py`](mcp_tools.py) | Calling the server's six MCP tools in-process — `list_message_types`, `validate_identifier`, and `generate_message` |

The examples import directly from `acmt001_mcp.server`, so install this package
(and the core `acmt001` library it depends on) first:

```sh
pip install acmt001-mcp   # Python 3.10+
```

> While the core `acmt001` library is not yet on PyPI, install it from source
> first: `pip install "git+https://github.com/sebastienrousseau/acmt001.git"`.
