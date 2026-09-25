# Releasing

This repo follows the governed branch/release model documented in full in
[`.claude/branching-strategy.md`](.claude/branching-strategy.md) — read that
first for branch types, branch flow, direct-push rules, PR requirements, and
versioning/tagging mechanics. This file covers only what's specific to this
repo and not in the template.

## Version sync

Two files must always agree:

- `VERSION.txt` (repo root) - the definitive source CI reads to derive the
  release tag.
- `.claude-plugin/plugin.json`'s `version` field - what Claude Code itself
  reads (e.g. for `/plugin list`).

`tests/test_version_sync.py` enforces this locally and in CI on every run.
`ci-release.yml` additionally verifies the derived tag isn't already taken.

## PR template selection

`.github/PULL_REQUEST_TEMPLATE/` has three templates (`bug-fix`, `feature`,
`release`). GitHub shows a template chooser when opening a PR — pick the one
matching the PR type.

## What's deliberately not here

This repo adapts the `nav3-repo-template` governance pattern the same way
`dilon-claude-tools` did, dropping pieces that don't apply to a Python/plugin
repo: the Docker/devcontainer build job, SBOM generation, the
`verification/test-catalog.md` ISO-62304 traceability catalog, and submodule
deploy keys (no submodules here). CI runs the pytest suite directly
(`pytest tests/`) instead of the template's `scripts/ci-*.sh` indirection.
