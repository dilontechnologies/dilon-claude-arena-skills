import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills" / "dilon-arena-eco-creator" / "scripts"
)

# Lets test modules for the live-calling scripts `import submit_change`
# etc. directly (needed so respx can patch httpx within this same test
# process -- a subprocess boundary would defeat respx entirely).
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def run_cli():
    """Run a pure-logic script as a subprocess, feeding it JSON (or raw
    text, for malformed-input tests) on stdin. Returns (returncode, stdout_json_or_None).
    """

    def _run(script_name: str, payload):
        text_input = payload if isinstance(payload, str) else json.dumps(payload)
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script_name)],
            input=text_input,
            capture_output=True,
            text=True,
        )
        try:
            stdout = json.loads(proc.stdout) if proc.stdout.strip() else None
        except json.JSONDecodeError:
            stdout = None
        return proc.returncode, stdout

    return _run
