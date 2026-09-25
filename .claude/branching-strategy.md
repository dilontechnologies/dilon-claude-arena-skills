# Branching Strategy

## Branch Types

### Feature branches — `DEV/<first_name>/<description>`

Use for all new feature work and non-trivial enhancements.

**Triggers:**
- "Let's add a new feature"
- "Let's implement X"
- "Let's build support for X"

**Examples:** `DEV/brennan/ble-init`, `DEV/alex/uart-framing`

Target: always open PRs against the appropriate `REL/v*.*.*` branch, never directly against `master`.

---

### Bug branches — `BUG/<developer_name>/<description>`

Use when pulling in a GitHub issue, fixing a regression, or making a non-trivial fix to a release branch.

**Triggers:**
- "Let's pull the following issue from GitHub"
- "There's a bug in X"
- A fix on a release branch is too substantial for a direct commit (see [Direct Push Rules](#direct-push-rules) below)

**Examples:** `BUG/brennan/uart-overflow`, `BUG/alex/ble-reconnect-crash`

Target: open PRs against the appropriate `REL/v*.*.*` branch.

---

### Release branches — `REL/v<major>.<minor>.<patch>`

Created when preparing a release. The version number follows [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`.

**Examples:** `REL/v1.0.0`, `REL/v1.2.3`, `REL/v2.0.0`

Source: branch off `master` (or the previous release branch if stacking).
Target: merge into `master` via PR after all requirements below are met.

---

## Branch Flow

```
master
  └── REL/v*.*.*
        ├── DEV/<name>/<description>   (feature work → PR → REL)
        └── BUG/<name>/<description>   (issue fixes  → PR → REL)
              ↓ PR (after full testing)
           master
```

---

## Direct Push Rules

### `master` — no direct pushes, ever
All changes to `master` must arrive via a `REL/v*.*.*` → `master` PR with CI passing and required reviews approved.

### `REL/v*.*.*` — limited direct commits allowed
Direct commits to a release branch are permitted **only** for:
- Minor fixes surfaced during testing (small, localized changes)
- Documentation updates
- Version number bumps made via the build script

If a required change is substantial, open a `BUG/<name>/<description>` branch off the release branch and merge it back via PR instead.

---

## PR Requirements

| PR type | Requirements |
|---|---|
| `DEV/**` → `REL/**` | CI passing, code review approved |
| `BUG/**` → `REL/**` | CI passing, code review approved |
| `REL/**` → `master` | CI passing, required reviews approved, **full test suite must pass on that exact commit**, verification report attached |

> Full testing on the release commit means: after any last direct commits to the release branch (minor fixes, version bump, docs), re-run the complete test suite and confirm it passes before requesting the merge to `master`. Do not merge on a stale test run.

---

## Versioning

**`VERSION.txt` is the definitive source of truth for the software version.** It must be updated on the release branch before opening the `REL/v*.*.*` -> `master` PR, and kept in sync with `.claude-plugin/plugin.json`'s `version` field (`tests/test_version_sync.py` and `ci-release.yml` both enforce this).

When a `REL/v*.*.*` branch is merged to `master`, the `release.yml` workflow reads `VERSION.txt`, derives the tag `v<content>`, and publishes a GitHub Release if that tag doesn't already exist. Do not create version tags manually.

Version increments are determined by changes to this repo's public interface: **the MCP tool set exposed by `arena_mcp_server.py`, and each skill's `SKILL.md` contract** (its inputs, the sequence of tools it calls, its outputs).

- **MAJOR** - a breaking change. A skill's documented inputs/outputs change incompatibly, or an MCP tool a skill depends on is removed or renamed.
- **MINOR** - a backward-compatible addition. A new skill is added, or a new MCP tool is added, without changing any existing skill's contract.
- **PATCH** - a bug fix. No skill's contract changes; no tools are added or removed. A bug caught by the test suite (e.g. a fix to `arena_mcp_server.py`'s request/response handling) is a PATCH as long as no skill's documented behavior changes.

**Decision razor:** imagine another skill already written against the current tool set and this repo's current skills. Ask:
- Would this release require *rewriting* that skill to keep working? -> **MAJOR**
- Would this release let a new skill *add* capabilities, while existing skills work unchanged? -> **MINOR**
- Would this release require *no changes* to any existing skill at all? -> **PATCH**
