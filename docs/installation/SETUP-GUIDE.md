# Arena PLM for Claude Desktop — Setup Guide

This package lets a Claude Desktop user work with our Arena PLM workspace from
Claude's chat. It has **two parts**:

- **Part A — for your Arena admin:** create a login for the new user, once.
- **Part B — for the teammate:** run one installer on their Windows PC.

> **Verified environment (checked live on 2026-08-07):**
> - **Workspace ID to use:** ask your Arena admin, or use whichever named
>   environment they tell you to select (see `ARENA_ENVIRONMENT` in
>   `env/.env.example` if more than one workspace is configured).
> - **Arena version: 2026.2.0** — the server is confirmed working against it.
> - **Server build: full read/write (290 tools).** See the safety note in Part A.

> **What's in this repo**
> - `arena_mcp/arena_mcp_server.py` — the current server (full read/write: items, BOMs, changes, quality processes, suppliers, files, training, snapshot/restore, audit packs, and more)
> - `env/requirements.txt` — its Python dependencies (mcp, httpx, python-dotenv)
> - `env/.env.example` — a template for the credentials
> - `installer/Install-ArenaMCP.ps1` — the one-step installer
> - `docs/installation/SETUP-GUIDE.md` — this file

---

## Part A — Your Arena admin: create the teammate's own login

**Do not reuse your own Client Credential.** Arena's audit log records every API
call as whoever the Client Credential is bound to. If your teammate uses your
credential, all of their activity shows up in Arena as *you* — a problem in a
QMS. Give them their own so it's attributed correctly.

**Before you start — confirm these about the teammate (from Arena's API guide):**

- They are an **Employee or Partner user**, not a Supplier user. Supplier users
  cannot access the Arena REST API at all.
- Their Arena user has access to the **target workspace**, and that workspace is
  **Access Policies–enabled**.
- If your organization uses **Single Sign-On (SSO)**, API access should go through a
  **dedicated integration/partner user**, not an SSO-only login — so you may want
  to create a machine user for them rather than bind to their SSO account.
- Their access policy governs read vs. write: a **read-only Arena user can't
  write** through the API no matter how many tools the server exposes.

Then create the credential:

1. In Arena: **Settings → OAuth Applications → AI Engine OAuth2 Client** (your
   existing parent app).
2. Open the **Client Credentials** section and click **+** to add a new
   credential. Bind it to **the teammate** — either their own named Arena user
   (simplest) or a dedicated machine user you create for them under **Account
   Administration → Machine Users**.
3. Arena shows a **Client ID** and a **Client Secret**. **Copy the secret now —
   it's shown only once.** (Lost it? Just delete that credential and generate a
   new one.)
4. Send the teammate these three values over a secure channel:
   - `ARENA_CLIENT_ID`
   - `ARENA_CLIENT_SECRET`
   - `ARENA_WORKSPACE_ID` (the target workspace's ID)

### Important: this is the full read/write build

This server exposes ~290 tools, including create/update/delete, file uploads,
status routing, and restore-from-snapshot. Two things keep that safe:

- **Arena enforces the teammate's own permissions on every call.** The server
  can never do anything their Arena user isn't allowed to do — their access
  policy is the real guardrail.
- The most destructive tools (e.g. `cancel_change`, `close_quality_process`,
  `restore_from_snapshot`) **default to a dry-run preview** and only act when
  explicitly told to.

Still, if you'd rather hand a colleague a smaller surface, tell me and I'll cut
a read-only or reduced build instead — the install steps are identical.

---

## Part B — Teammate: install it (about 5 minutes)

**You need:** a Windows PC, Claude Desktop installed, and the three Arena values
from your Arena admin. No coding experience required.

1. **Download or clone** this repo somewhere easy, like your Desktop.
2. Make sure **Python 3.10 or newer** is installed. To check: open **PowerShell**
   and type `python --version`. If it's below 3.10 or "not recognized," install
   from <https://www.python.org/downloads/> and tick **"Add python.exe to PATH."**
3. Open the **`installer`** folder, then **right-click `Install-ArenaMCP.ps1` →
   "Run with PowerShell."**
   - If Windows blocks it, open PowerShell, run this once, then try again:
     `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
4. The installer will set up the server, **ask you for the three Arena values**
   (paste them in), run a quick Arena login test so you know right away if a
   value is wrong, and register the server with Claude Desktop for you.
5. When it finishes, **fully close and reopen Claude Desktop** (make sure it's
   completely closed first — check the system tray).
6. In a new chat, type: **`Run the arena whoami tool`**. You should see
   `auth: ok` and the Arena version. You're connected.

### Try it

- `Search Arena for items with number starting with <prefix> and show the top 5.`
- `Pull the BOM for item <item number> and group the children by category.`
- `List all changes still in review, owned by <name>.`

---

## If something goes wrong

- **"Arena login did NOT succeed" during install** — almost always one of the
  three values. A **400** means a wrong Client ID / Secret / Workspace ID.
  A **401** usually means that user isn't set up for Access-Policy/API use, or
  is a Supplier user (only Employee/Partner users can use the API). Fix with
  your Arena admin and re-run the installer.
- **Claude Desktop doesn't show the tools** — confirm you *fully* restarted it
  (not just closed the window). **Settings → Developer** (or **Extensions**)
  should list `arena`.
- **`401 Unauthorized` on a specific action** but `whoami` works — your Arena
  user lacks permission for that action. That's Arena's access policy doing its
  job.
- **Rate limit** — Arena caps API requests per workspace per day. If you hit it,
  wait until the next Pacific midnight. (Current usage is light, so this is
  unlikely.)

---

## Security notes

- Credentials live only in `%USERPROFILE%\arena-mcp\.env` on the teammate's PC.
  Don't share that file.
- Every API call is logged in Arena's audit system against the user the Client
  Credential is bound to (that's why Part A gives the teammate their own).
- The token is held in memory only; it's never written to disk.
