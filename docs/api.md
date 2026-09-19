# Python API reference

The standalone server's importable Python surface (used by the runnable
example and any agent that wraps the server instance directly).

```{eval-rst}
.. automodule:: acmt001_mcp
   :members:
   :undoc-members:
```

## Tool, prompt and resource module

Every tool, the prompt and both resources are plain functions registered
on the ``server`` object at import time, so they can be called in-process
without a transport.

```{eval-rst}
.. automodule:: acmt001_mcp.server
   :members:
   :undoc-members:
   :show-inheritance:
```

## Transports and command line

```{eval-rst}
.. automodule:: acmt001_mcp._transports
   :members:

.. automodule:: acmt001_mcp._cli
   :members:
```
