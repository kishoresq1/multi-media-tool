#!/usr/bin/env python3
"""
Render the sponsors block in README.md from sponsors.json.

Usage:
    python scripts/render_sponsors.py           # update README.md in-place
    python scripts/render_sponsors.py --check   # exit 1 if README is out of sync

Markers (created automatically if absent):
    <!-- SPONSORS:START -->
    <!-- SPONSORS:END -->

Running this script is idempotent: re-running it produces the same output.
Wire it to CI or pre-commit to keep README in sync:

    pre-commit: python scripts/render_sponsors.py --check
    CI step:    python scripts/render_sponsors.py && git diff --exit-code README.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_README = _REPO_ROOT / "README.md"
_SPONSORS_FILE = _REPO_ROOT / "sponsors.json"

START_MARKER = "<!-- SPONSORS:START -->"
END_MARKER = "<!-- SPONSORS:END -->"

VALID_TIERS = {"featured", "integration", "supporter"}
REQUIRED_FIELDS = {"name", "tagline", "url", "logo", "tier"}


# ---------------------------------------------------------------------------
# Validation (stdlib-only, no openosint import so the script is self-contained)
# ---------------------------------------------------------------------------


def _load_and_validate(path: Path) -> list[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"[render_sponsors] ERROR: {path} not found")
    except json.JSONDecodeError as exc:
        sys.exit(f"[render_sponsors] ERROR: {path} is not valid JSON: {exc}")

    if not isinstance(raw, list):
        sys.exit("[render_sponsors] ERROR: sponsors.json must be a JSON array")

    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            sys.exit(f"[render_sponsors] ERROR: entry {i} is not an object")
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            sys.exit(f"[render_sponsors] ERROR: entry {i} missing fields: {sorted(missing)}")
        if entry["tier"] not in VALID_TIERS:
            sys.exit(
                f"[render_sponsors] ERROR: entry {i} ({entry['name']!r}) "
                f"has unknown tier {entry['tier']!r}"
            )
    return raw


# ---------------------------------------------------------------------------
# Block renderer
# ---------------------------------------------------------------------------


def _render_block(sponsors: list[dict]) -> str:
    lines: list[str] = [START_MARKER, ""]

    featured = [s for s in sponsors if s["tier"] == "featured"]
    integration = [s for s in sponsors if s["tier"] == "integration"]
    supporter = [s for s in sponsors if s["tier"] == "supporter"]

    if featured:
        lines.append("### Featured Integrations")
        lines.append("")
        for s in featured:
            tool_note = f" — powers `{s['tool']}`" if s.get("tool") else ""
            lines.append(f"**[{s['name']}]({s['url']})**{tool_note}")
            lines.append("")
            lines.append(f"> {s['tagline']}")
            lines.append("")

    if integration:
        lines.append("### Integrations")
        lines.append("")
        for s in integration:
            lines.append(
                f"| [![{s['name']}]({s['logo']})]({s['url']}) "
                f"| **[{s['name']}]({s['url']})** | {s['tagline']} |"
            )
        lines.append("")

    if supporter:
        lines.append("### Supporters")
        lines.append("")
        for s in supporter:
            lines.append(f"[![{s['name']}]({s['logo']})]({s['url']})")
        lines.append("")

    lines.append(
        "_Want to sponsor OpenOSINT? See [SPONSORSHIP.md](SPONSORSHIP.md) for tiers and rates._"
    )
    lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# README updater
# ---------------------------------------------------------------------------


def _inject(readme_text: str, block: str) -> str:
    """Replace content between START and END markers (inclusive)."""
    if START_MARKER not in readme_text:
        return readme_text.rstrip("\n") + "\n\n## Sponsors\n\n" + block + "\n"

    start_idx = readme_text.index(START_MARKER)
    end_idx = readme_text.index(END_MARKER, start_idx) + len(END_MARKER)
    return readme_text[:start_idx] + block + readme_text[end_idx:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if README.md is out of sync (do not write).",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=_README,
        help="Path to README.md (default: repo root README.md).",
    )
    parser.add_argument(
        "--sponsors",
        type=Path,
        default=_SPONSORS_FILE,
        help="Path to sponsors.json (default: repo root sponsors.json).",
    )
    args = parser.parse_args()

    sponsors = _load_and_validate(args.sponsors)
    block = _render_block(sponsors)

    readme_text = args.readme.read_text(encoding="utf-8")
    updated = _inject(readme_text, block)

    if args.check:
        if updated != readme_text:
            print("[render_sponsors] README.md sponsors block is out of sync.")
            print("Run:  python scripts/render_sponsors.py")
            sys.exit(1)
        print("[render_sponsors] README.md sponsors block is up to date.")
        return

    if updated != readme_text:
        args.readme.write_text(updated, encoding="utf-8")
        print(f"[render_sponsors] Updated {args.readme}")
    else:
        print(f"[render_sponsors] {args.readme} already up to date.")


if __name__ == "__main__":
    main()
