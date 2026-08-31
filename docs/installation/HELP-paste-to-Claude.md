# If you're stuck, let Claude help

If the installer or setup gives you trouble, open Claude (desktop or claude.ai),
**copy everything below the line into the chat**, then add your own sentence
describing what happened (and paste any error text you saw).

> ⚠️ One safety note: when you paste an error message, do **not** include your
> Client Secret. If an error shows it, delete that part before sending.

If Claude can't resolve it, or it turns out to be about your Arena account,
send it to your Arena admin — some fixes (credentials, workspace access,
permissions) only an Arena admin can make.

----- copy from here --------------------------------------------------------

I'm setting up a local "Arena PLM" MCP server so Arena works inside my Claude
Desktop on Windows. Please help me troubleshoot. Here's how it's supposed to
work, so you have the context:

INSTALLER
- I run `Install-ArenaMCP.ps1` (right-click → Run with PowerShell) from the
  `installer` folder inside the repo/folder I downloaded.
- It installs to `%USERPROFILE%\arena-mcp`, creates a Python virtual environment
  at `%USERPROFILE%\arena-mcp\.venv`, and pip-installs `mcp`, `httpx`, and
  `python-dotenv`.
- It prompts me for three values (ARENA_CLIENT_ID, ARENA_CLIENT_SECRET,
  ARENA_WORKSPACE_ID) and writes them to `%USERPROFILE%\arena-mcp\.env`.
- It runs a quick Arena login test and prints the result.
- It registers an MCP server named `arena` in Claude Desktop's config file
  (`claude_desktop_config.json`), with the command pointing at
  `.venv\Scripts\python.exe` and the argument `arena_mcp_server.py`. The config
  lives at either `%APPDATA%\Claude\` (standard install) or, for the Microsoft
  Store version, under
  `%LOCALAPPDATA%\Packages\Claude*\LocalCache\Roaming\Claude\`.

REQUIREMENTS
- Windows, Python 3.10+, Claude Desktop.
- My Arena user must be an Employee or Partner user (Supplier users can't use the
  API), in the target workspace, which is Access-Policies-enabled.

COMMON PROBLEMS AND FIXES (please walk me through whichever matches)
1. "python is not recognized" → Python isn't installed or wasn't added to PATH.
   Install from python.org and tick "Add python.exe to PATH", then re-run.
2. The script is blocked from running → run this once in PowerShell, then re-run
   the installer: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
3. Login test says 400 → one of my three values is wrong (Client ID / Secret /
   Workspace ID). Re-run the installer and re-enter them.
4. Login test says 401 → my Arena user may not be set up for API/OAuth access, or
   is a Supplier user. This one needs my Arena admin.
5. Claude shows no Arena tools after install → I need to FULLY quit Claude Desktop
   (not just close the window — check the system tray) and reopen it.
6. To re-run safely: I can just run `Install-ArenaMCP.ps1` again; it's repeatable.

Please figure out which situation I'm in from what I tell you next, and give me
the exact steps. Here's what happened:
[describe your problem here and paste any error text — minus the Client Secret]

----- copy to here ----------------------------------------------------------
