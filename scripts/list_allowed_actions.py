#!/usr/bin/env python3

"""
Purpose
-------
Generate allowlists of third-party GitHub Actions used by this repository's reusable workflows
and composite actions, grouped by platform (iOS and Android). Useful to create the latest 
allowlist for workflow release notes.

What it scans
-------------
- Reusable workflows in `.github/workflows/**` that declare `on: workflow_call`.
  - From these, it collects remote actions referenced via `uses: owner/repo[@ref]`.
- Composite actions under `.github/actions/**`.
  - It inspects the composite action steps and collects remote actions they use.

What it excludes
----------------
- GitHub official actions (`actions/*`) — assumed allowed by default.
- Reusable workflow references (`owner/repo/.github/workflows/...@ref`).
- Local composite action references; these are not versioned (ex: `./.github/actions/ios-setup-dependencies-action`).

Refs handling
-------------
- Preserves the ref exactly as written (commit SHA or semver tag).

Platform grouping
-----------------
- iOS vs Android is inferred from filenames/content of reusable workflows.
- Composite actions are grouped by their directory prefix: `ios-` -> iOS, `android-` -> Android.
- A generic `versions.yml` reusable workflow is counted for both platforms.

Output
------
Two lists are printed to stdout:
- iOS: one line per action, formatted as `owner/repo[@ref],`
- Android: one line per action, formatted as `owner/repo[@ref],`

Usage
-----
Run from the repo root:

    python3 scripts/list_allowed_actions.py

"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB_DIR = REPO_ROOT / ".github"
WORKFLOWS_DIR = GITHUB_DIR / "workflows"
LOCAL_ACTIONS_DIR = GITHUB_DIR / "actions"


# Capture the first non-whitespace token after 'uses:'; allow trailing comments or params
USES_LINE_RE = re.compile(r"^\s*uses:\s*[\"']?([^\"'\s]+)[\"']?")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def is_workflow_file(path: Path) -> bool:
    return path.suffix.lower() in {".yml", ".yaml"}


def detect_platforms_for_workflow(path: Path, content: str) -> Set[str]:
    filename = path.name.lower()
    platforms: Set[str] = set()

    has_ios = "ios" in filename
    has_android = "android" in filename

    if has_ios and not has_android:
        platforms.add("ios")
    elif has_android and not has_ios:
        platforms.add("android")
    else:
        # Generic reusable workflow: include in both lists
        platforms.update({"ios", "android"})

    return platforms


def is_reusable_workflow(content: str) -> bool:
    # Heuristic: ensure 'workflow_call:' appears and is not commented out
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if stripped.startswith('workflow_call:'):
            return True
    # Fallback: simple multiline detection under 'on:' block
    if re.search(r"^\s*on:\s*(?:\n|\r\n).*?^\s*workflow_call:\s*$", content, re.MULTILINE | re.DOTALL):
        return True
    return False


def extract_uses_targets(content: str) -> List[str]:
    targets: List[str] = []
    for line in content.splitlines():
        m = USES_LINE_RE.match(line)
        if not m:
            continue
        value = m.group(1).strip()
        # Ignore Docker-style uses entries, ex:
        #   uses: docker://image@tag
        if value.startswith("docker://"):
            continue
        targets.append(value)
    return targets


def normalize_remote_use(value: str) -> Tuple[str, str]:
    """Return (repo_path, ref) if remote action, else ("", "").

    Accepts formats like 'owner/repo@ref' or 'owner/repo/path@ref'.
    """
    if value.startswith("./") or value.startswith(".github/") or value.startswith("/"):
        return ("", "")
    if "@" not in value:
        return ("", "")
    # Split on the last '@' to be safe if repo path somehow contains '@'
    repo_part, ref = value.rsplit("@", 1)
    return (repo_part, ref)


def is_github_official_action(repo_path: str) -> bool:
    # 'actions/*' should be omitted
    # repo_path could include a subdir like 'owner/repo/path'
    parts = repo_path.split("/")
    if not parts:
        return False
    owner = parts[0]
    return owner == "actions"


def is_reusable_workflow_path(repo_path: str) -> bool:
    # Reusable workflow reference like 'owner/repo/.github/workflows/file.yml@ref'
    return "/.github/workflows/" in repo_path


def is_repo_composite_action_path(repo_path: str) -> bool:
    # Composite action reference like 'owner/repo/.github/actions/name@ref'
    return "/.github/actions/" in repo_path


def classify_local_action_from_path(local_path: str) -> Tuple[str, str]:
    """Given a local uses path like './.github/actions/ios-setup-dependencies-action',
    return (action_dir_name, platform) if determinable. Platform is 'ios' or 'android' or ''.
    """
    # Normalize
    normalized = local_path
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")

    # Expect it to start with '.github/actions/'
    if not normalized.startswith(".github/actions/"):
        return ("", "")
    rel = normalized[len(".github/actions/") :]
    # The first path segment is the action directory name
    action_dir = rel.split("/", 1)[0]
    platform = ""
    if action_dir.startswith("ios-"):
        platform = "ios"
    elif action_dir.startswith("android-"):
        platform = "android"
    return (action_dir, platform)


def gather_local_action_dirs() -> Dict[str, Set[str]]:
    """Scan .github/actions immediate subdirectories and classify by prefix.

    Returns a mapping platform -> set of 'name (platform)' entries.
    """
    results: Dict[str, Set[str]] = {"ios": set(), "android": set()}
    if not LOCAL_ACTIONS_DIR.exists():
        return results
    for entry in LOCAL_ACTIONS_DIR.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if name.startswith("ios-"):
            results["ios"].add(f"{name} (ios)")
        elif name.startswith("android-"):
            results["android"].add(f"{name} (android)")
    return results


def main() -> int:
    if not GITHUB_DIR.exists():
        print(".github directory not found.", file=sys.stderr)
        return 1

    actions_by_platform: Dict[str, Set[str]] = {"ios": set(), "android": set()}

    # Walk workflow files (only reusable workflows)
    if WORKFLOWS_DIR.exists():
        for path in WORKFLOWS_DIR.rglob("*"):
            if not path.is_file() or not is_workflow_file(path):
                continue
            content = read_text(path)
            if not is_reusable_workflow(content):
                continue
            platforms = detect_platforms_for_workflow(path, content)
            # If no platform detected, only include for 'versions.yml' (already handled); otherwise skip
            if not platforms:
                continue

            for value in extract_uses_targets(content):
                # First, try remote actions
                repo_path, ref = normalize_remote_use(value)
                if (
                    repo_path
                    and ref
                    and not is_github_official_action(repo_path)
                    and not is_reusable_workflow_path(repo_path)
                    and not is_repo_composite_action_path(repo_path)
                ):
                    entry = f"{repo_path}@{ref}"
                    for p in platforms:
                        actions_by_platform[p].add(entry)
                    continue

                # Ignore local composite actions in allowlist
                # (but we will scan inside composite definitions below)

    # Scan composite action definitions to include third-party actions they use
    if LOCAL_ACTIONS_DIR.exists():
        for action_dir in LOCAL_ACTIONS_DIR.iterdir():
            if not action_dir.is_dir():
                continue
            platform = ""
            if action_dir.name.startswith("ios-"):
                platform = "ios"
            elif action_dir.name.startswith("android-"):
                platform = "android"
            if not platform:
                continue

            for candidate in [action_dir / "action.yml", action_dir / "action.yaml"]:
                if not candidate.exists():
                    continue
                content = read_text(candidate)
                for value in extract_uses_targets(content):
                    repo_path, ref = normalize_remote_use(value)
                    if (
                        repo_path
                        and ref
                        and not is_github_official_action(repo_path)
                        and not is_reusable_workflow_path(repo_path)
                        and not is_repo_composite_action_path(repo_path)
                    ):
                        actions_by_platform[platform].add(f"{repo_path}@{ref}")

    # Print results
    def print_list(title: str, items: Set[str]) -> None:
        print(title)
        for item in sorted(items):
            print(f"{item},")
        print()

    print_list("iOS:", actions_by_platform["ios"])
    print_list("Android:", actions_by_platform["android"])

    return 0


if __name__ == "__main__":
    sys.exit(main())


