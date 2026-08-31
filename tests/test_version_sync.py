import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_version_txt_matches_plugin_json():
    version_txt = (REPO_ROOT / "VERSION.txt").read_text().strip()
    plugin_json = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert version_txt == plugin_json["version"], (
        f"VERSION.txt ({version_txt!r}) and plugin.json's version "
        f"({plugin_json['version']!r}) must match."
    )
