<#
    Install-ArenaMCP.ps1
    ---------------------
    One-step installer for the Arena PLM MCP server on Claude Desktop (Windows).

    What it does:
      1. Copies the server files to  %USERPROFILE%\arena-mcp
      2. Creates a Python virtual environment and installs dependencies
      3. Asks you for your three Arena values and writes a local .env
      4. Does a quick Arena login test so you know the credentials work
      5. Registers the server with Claude Desktop (edits claude_desktop_config.json)

    How to run:
      - Right-click this file  ->  "Run with PowerShell"
      -   ...or open PowerShell in this folder and run:  .\Install-ArenaMCP.ps1
      - If Windows blocks the script, first run this once, then try again:
            Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

    Nothing here touches Arena's data. It only sets up software on your PC.
#>

$ErrorActionPreference = "Stop"

function Write-Step($msg)  { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "  [ok] $msg"   -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "  [!]  $msg"   -ForegroundColor Yellow }

Write-Host "Arena PLM MCP - Claude Desktop installer" -ForegroundColor White

# ---------------------------------------------------------------------------
# 0. Paths
# ---------------------------------------------------------------------------
$RepoRoot   = Split-Path $PSScriptRoot -Parent
$ServerDir  = Join-Path $RepoRoot "arena_mcp"
$EnvDir     = Join-Path $RepoRoot "env"
$InstallDir = Join-Path $env:USERPROFILE "arena-mcp"
$VenvDir    = Join-Path $InstallDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ServerPath = Join-Path $InstallDir "arena_mcp_server.py"

# ---------------------------------------------------------------------------
# 1. Copy files
# ---------------------------------------------------------------------------
Write-Step "Copying server files to $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Force (Join-Path $ServerDir "arena_mcp_server.py") (Join-Path $InstallDir "arena_mcp_server.py")
# Copy-Item -Recurse merges into an existing destination directory instead of
# replacing it, so a re-run over an existing install would leave stale/deleted
# modules in place. Remove the old package first so each install is a clean copy.
Remove-Item -Recurse -Force (Join-Path $InstallDir "server") -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force (Join-Path $ServerDir "server") (Join-Path $InstallDir "server") -Exclude "__pycache__"
foreach ($f in @("requirements.txt", ".env.example", "environment.example.json")) {
    Copy-Item -Force (Join-Path $EnvDir $f) (Join-Path $InstallDir $f)
}
Write-Ok "Files copied."

# ---------------------------------------------------------------------------
# 2. Find Python 3.10+
# ---------------------------------------------------------------------------
Write-Step "Looking for Python 3.10 or newer"
$pythonCmd = $null
foreach ($c in @("python", "py", "python3")) {
    try { $ver = & $c --version 2>&1 } catch { continue }
    if ($LASTEXITCODE -eq 0 -and "$ver" -match "Python (\d+)\.(\d+)") {
        $maj = [int]$Matches[1]; $min = [int]$Matches[2]
        if ($maj -gt 3 -or ($maj -eq 3 -and $min -ge 10)) {
            $pythonCmd = $c
            Write-Ok "Found $ver  (command: $c)"
            break
        }
    }
}
if (-not $pythonCmd) {
    Write-Warn2 "No Python 3.10+ found on this machine."
    Write-Host  "  Install Python from https://www.python.org/downloads/ (check 'Add python.exe to PATH'),"
    Write-Host  "  then run this script again."
    Read-Host "`nPress Enter to exit"
    exit 1
}

# ---------------------------------------------------------------------------
# 3. Virtual environment + dependencies
# ---------------------------------------------------------------------------
Write-Step "Creating virtual environment and installing dependencies"
if (-not (Test-Path $VenvPython)) {
    & $pythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment." }
}
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r (Join-Path $InstallDir "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies." }
Write-Ok "Dependencies installed."

# ---------------------------------------------------------------------------
# 4. Collect Arena credentials and write .env
# ---------------------------------------------------------------------------
Write-Step "Enter your Arena credentials"
Write-Host "  (Your Arena admin gives you these three values. They are stored only"
Write-Host "   on this PC, in $InstallDir\.env.)"
Write-Host ""
$clientId    = Read-Host "  ARENA_CLIENT_ID"
$secretSec   = Read-Host "  ARENA_CLIENT_SECRET" -AsSecureString
$workspaceId = Read-Host "  ARENA_WORKSPACE_ID"
$yourName    = Read-Host "  Your name (for Arena audit label, optional)"

# Convert the secure string back to plain text so it can be saved to .env
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSec)
$clientSecret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

$usageReason = if ([string]::IsNullOrWhiteSpace($yourName)) { "Dilon Claude" } else { "Dilon Claude / $yourName" }

$envLines = @(
    "ARENA_CLIENT_ID=$clientId",
    "ARENA_CLIENT_SECRET=$clientSecret",
    "ARENA_WORKSPACE_ID=$workspaceId",
    "ARENA_USAGE_REASON=$usageReason"
)
[System.IO.File]::WriteAllLines((Join-Path $InstallDir ".env"), $envLines, [System.Text.Encoding]::ASCII)
Write-Ok "Saved credentials to $InstallDir\.env"

# ---------------------------------------------------------------------------
# 5. Quick Arena login test (non-fatal)
# ---------------------------------------------------------------------------
Write-Step "Testing the Arena login"
$env:ARENA_TOKEN_URL     = "https://oauth.bom.com/oauth2/token"
$env:ARENA_CLIENT_ID     = $clientId
$env:ARENA_CLIENT_SECRET = $clientSecret
$env:ARENA_WORKSPACE_ID  = $workspaceId
$testScript = @'
import os, httpx
try:
    r = httpx.post(
        os.environ["ARENA_TOKEN_URL"],
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["ARENA_CLIENT_ID"],
            "client_secret": os.environ["ARENA_CLIENT_SECRET"],
            "workspace_id": os.environ["ARENA_WORKSPACE_ID"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    print("STATUS", r.status_code)
except Exception as e:
    print("STATUS error", e)
'@
# This step is meant to be non-fatal (a bad login just prints a warning below),
# but $ErrorActionPreference = "Stop" up top otherwise promotes every stderr
# line from the native python call into a terminating error once merged via
# 2>&1 — silently aborting the whole installer before it reaches Desktop
# registration. Relax it for just this call.
$prevErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$result = & $VenvPython -c $testScript 2>&1
$ErrorActionPreference = $prevErrorActionPreference
Remove-Item Env:\ARENA_CLIENT_ID, Env:\ARENA_CLIENT_SECRET, Env:\ARENA_WORKSPACE_ID, Env:\ARENA_TOKEN_URL -ErrorAction SilentlyContinue
if ("$result" -match "STATUS 200") {
    Write-Ok "Arena login succeeded - credentials are valid."
} else {
    Write-Warn2 "Arena login did NOT succeed. Details: $result"
    Write-Host  "  The install will still finish. Double-check the three values with your"
    Write-Host  "  Arena admin (a 400 usually means a wrong value; 401 usually means the"
    Write-Host  "  workspace isn't Access-Policies enabled). You can re-run this script anytime."
}

# ---------------------------------------------------------------------------
# 6. Register with Claude Desktop
# ---------------------------------------------------------------------------
Write-Step "Registering the server with Claude Desktop"

# Find the Claude Desktop config, covering both the standard installer and the
# Microsoft Store install.
$candidatePaths = @()
$candidatePaths += (Join-Path $env:APPDATA "Claude\claude_desktop_config.json")
$storeRoots = Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA "Packages") -Filter "Claude*" -Directory -ErrorAction SilentlyContinue
foreach ($root in $storeRoots) {
    $candidatePaths += (Join-Path $root.FullName "LocalCache\Roaming\Claude\claude_desktop_config.json")
}

# Prefer a path whose config file already exists; otherwise the first whose
# parent "Claude" folder exists; otherwise fall back to the standard path.
$configPath = $null
foreach ($p in $candidatePaths) { if (Test-Path $p) { $configPath = $p; break } }
if (-not $configPath) {
    foreach ($p in $candidatePaths) { if (Test-Path (Split-Path $p)) { $configPath = $p; break } }
}
if (-not $configPath) { $configPath = $candidatePaths[0] }

New-Item -ItemType Directory -Force -Path (Split-Path $configPath) | Out-Null

# Load existing config (or start fresh)
if (Test-Path $configPath) {
    $raw = Get-Content $configPath -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) { $config = [PSCustomObject]@{} }
    else {
        try { $config = $raw | ConvertFrom-Json }
        catch {
            $backup = "$configPath.bak"
            Copy-Item -Force $configPath $backup
            Write-Warn2 "Existing config wasn't valid JSON; backed it up to $backup and started fresh."
            $config = [PSCustomObject]@{}
        }
    }
} else {
    $config = [PSCustomObject]@{}
}

if (-not ($config.PSObject.Properties.Name -contains "mcpServers")) {
    $config | Add-Member -MemberType NoteProperty -Name mcpServers -Value ([PSCustomObject]@{})
}

$serverDef = [PSCustomObject]@{
    command = $VenvPython
    args    = @($ServerPath)
}

if ($config.mcpServers.PSObject.Properties.Name -contains "arena") {
    $config.mcpServers.arena = $serverDef
} else {
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name arena -Value $serverDef
}

$config | ConvertTo-Json -Depth 12 | Set-Content -Path $configPath -Encoding UTF8
Write-Ok "Registered 'arena' in: $configPath"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Step "All done"
Write-Host "  Final step - restart Claude Desktop completely so it loads the server:" -ForegroundColor White
Write-Host "    1. Close Claude Desktop."
Write-Host "    2. Make sure it's fully closed (check the system tray / Task Manager)."
Write-Host "    3. Open Claude Desktop again."
Write-Host ""
Write-Host "  Then, in a new chat, type:  Run the arena whoami tool" -ForegroundColor White
Write-Host "  You should see auth: ok and your Arena version."
Write-Host ""
Read-Host "Press Enter to close"
