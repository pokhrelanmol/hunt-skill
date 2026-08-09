#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "hunt-skill"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


required = [
    ROOT / "README.md",
    ROOT / "docs" / "SETUP.md",
    ROOT / "scripts" / "install.sh",
    SKILL / "SKILL.md",
    SKILL / "agents" / "openai.yaml",
    SKILL / "scripts" / "auditctl.py",
]

for path in required:
    if not path.exists():
        fail(f"required path missing: {path.relative_to(ROOT)}")

if (SKILL / "README.md").exists():
    fail("README.md belongs at repository root, not inside the skill payload")

skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
lines = skill_text.splitlines()
if len(lines) > 500:
    fail(f"SKILL.md exceeds 500 lines: {len(lines)}")
if not skill_text.startswith("---\n"):
    fail("SKILL.md YAML frontmatter is missing")

frontmatter_end = skill_text.find("\n---\n", 4)
if frontmatter_end == -1:
    fail("SKILL.md YAML frontmatter is not closed")
frontmatter = skill_text[4:frontmatter_end]
keys = re.findall(r"(?m)^([a-zA-Z0-9_-]+):", frontmatter)
if set(keys) != {"name", "description"}:
    fail(f"SKILL.md frontmatter keys must be name and description; found {keys}")
if not re.search(r"(?m)^name:\s*hunt-skill\s*$", frontmatter):
    fail("SKILL.md name must be hunt-skill")

markdown_files = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md")), *sorted((SKILL / "workflows").glob("*.md"))]
link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
for markdown in markdown_files:
    text = markdown.read_text(encoding="utf-8")
    for match in link_pattern.finditer(text):
        target = match.group(1)
        if "://" in target or target.startswith("mailto:"):
            continue
        resolved = (markdown.parent / target).resolve()
        if not resolved.exists():
            fail(f"broken link in {markdown.relative_to(ROOT)}: {target}")

print("Repository and skill structure are valid.")
