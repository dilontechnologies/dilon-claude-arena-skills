# Set up Arena in Claude — Quick Start

This connects Arena to your Claude Desktop so you can pull up items, BOMs,
changes, and quality processes right from a chat. Takes about 5 minutes.

**You'll need:**
- A Windows PC with **Claude Desktop** installed
- The **3 values** your Arena admin sends you (Client ID, Client Secret, Workspace ID)

---

## Steps

1. **Unzip** the folder your Arena admin sent you (right-click → Extract All). Put it
   somewhere easy, like your Desktop.

2. **Check you have Python 3.10 or newer.** Open **PowerShell** (Start menu →
   type "PowerShell") and type:

   ```
   python --version
   ```

   If it shows 3.10 or higher, you're set. If it says a lower number or
   "not recognized," install Python from <https://www.python.org/downloads/>
   and **tick "Add python.exe to PATH"** during install, then continue.

3. **Run the installer.** Open the **`installer`** folder, then **right-click
   `Install-ArenaMCP.ps1` → "Run with PowerShell."**

   - If Windows blocks it, paste this into PowerShell once, press Enter, then
     redo this step:
     ```
     Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
     ```

4. **Paste your 3 values when asked.** The installer will prompt you for the
   Client ID, Client Secret, and Workspace ID — paste each one your Arena admin gave you.
   It sets everything up and runs a quick login test to confirm they work.

5. **Fully restart Claude Desktop.** Close it completely (check the system tray
   in the bottom-right so it's not still running), then open it again.

6. **Test it.** In a new chat, type:

   > Run the arena whoami tool

   If you see `auth: ok`, you're connected. Try:

   > Search Arena for items with number starting with <prefix> and show the top 5.

---

## If you get stuck

- **"python not recognized"** → Python isn't installed (or PATH wasn't checked).
  Do step 2 again.
- **The login test failed** → one of the three values is off. Send your Arena admin the
  error message and they'll sort it out, then just run the installer again.
- **Claude doesn't show any Arena tools** → make sure you *fully* closed and
  reopened Claude Desktop (not just the window).

Anything else, send it to your Arena admin.
