"""Arena PLM MCP Server entrypoint.

All tool implementations live in server/ — see server/__init__.py for
the full module manifest. This file exists only because Claude Desktop
and Install-ArenaMCP.ps1 invoke `python arena_mcp_server.py` as a fixed
script path.
"""
import server
from server import *  # noqa: F401,F403 — re-exports every tool + config constant

if __name__ == "__main__":
    mcp.run()
