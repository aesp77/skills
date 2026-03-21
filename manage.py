#!/usr/bin/env python3
"""Skills manager CLI — install, validate, and sync skills across projects.

Usage:
    python manage.py install <project-dir> [--template <name>]
    python manage.py validate <project-dir>
    python manage.py sync <project-dir> [--fix]
    python manage.py list
    python manage.py check-all [--fix]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent
SKILLS_DIR = SKILLS_ROOT / "skills"
TEMPLATES_DIR = SKILLS_ROOT / "templates"

# All available skills (auto-discovered from skills/ subdirectories)
def discover_skills() -> list[str]:
    """Return sorted list of skill names from skills/ directory."""
    return sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )


def parse_skill_frontmatter(skill_name: str) -> dict:
    """Parse the HTML comment frontmatter from a SKILL.md."""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        return {}

    content = skill_path.read_text(encoding="utf-8")
    match = re.search(r"<!--\s*\n(.*?)\n\s*-->", content, re.DOTALL)
    if not match:
        return {}

    meta = {}
    for line in match.group(1).strip().splitlines():
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            meta[key.strip()] = value
    return meta


def extract_skill_refs(claude_md: Path) -> list[str]:
    """Extract skill names referenced in a CLAUDE.md file."""
    if not claude_md.exists():
        return []

    content = claude_md.read_text(encoding="utf-8")
    # Match patterns like ~/skills/skills/<name>/SKILL.md
    refs = re.findall(r"~/skills/skills/([^/]+)/SKILL\.md", content)
    return refs


# --- Commands ---

def cmd_list(args: argparse.Namespace) -> int:
    """List all available skills with their triggers."""
    skills = discover_skills()
    print(f"\n{'Skill':<25} {'Trigger':<50} {'Depends On'}")
    print("-" * 100)
    for name in skills:
        meta = parse_skill_frontmatter(name)
        trigger = meta.get("trigger", "—")
        deps = meta.get("depends-on", [])
        deps_str = ", ".join(deps) if isinstance(deps, list) else str(deps)
        print(f"{name:<25} {trigger:<50} {deps_str}")
    print(f"\n{len(skills)} skills available.")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """Install a CLAUDE.md template into a project directory."""
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        print(f"Error: {project_dir} is not a directory.")
        return 1

    target = project_dir / "CLAUDE.md"

    # Determine which template to use
    template_name = args.template
    if template_name:
        template_file = TEMPLATES_DIR / f"CLAUDE-{template_name}.md"
        if not template_file.exists():
            template_file = TEMPLATES_DIR / f"{template_name}.md"
    else:
        # Try to match by directory name
        project_name = project_dir.name
        template_file = TEMPLATES_DIR / f"CLAUDE-{project_name}.md"
        if not template_file.exists():
            template_file = TEMPLATES_DIR / "CLAUDE.md"

    if not template_file.exists():
        print(f"Error: template not found: {template_file}")
        return 1

    if target.exists() and not args.force:
        print(f"CLAUDE.md already exists at {target}")
        print("Use --force to overwrite.")
        return 1

    shutil.copy2(template_file, target)
    print(f"Installed {template_file.name} -> {target}")

    # Validate immediately after install
    return cmd_validate(argparse.Namespace(project_dir=args.project_dir))


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate that a project's CLAUDE.md references valid skills."""
    project_dir = Path(args.project_dir).resolve()
    claude_md = project_dir / "CLAUDE.md"

    if not claude_md.exists():
        print(f"Error: no CLAUDE.md found at {project_dir}")
        print(f"Run: python manage.py install {project_dir}")
        return 1

    available = set(discover_skills())
    referenced = extract_skill_refs(claude_md)
    referenced_set = set(referenced)

    errors = 0

    # Check for references to non-existent skills
    invalid = referenced_set - available
    if invalid:
        for name in sorted(invalid):
            print(f"  ERROR: references unknown skill '{name}'")
        errors += len(invalid)

    # Check for missing dependency chains
    for name in referenced:
        if name not in available:
            continue
        meta = parse_skill_frontmatter(name)
        deps = meta.get("depends-on", [])
        if isinstance(deps, list):
            for dep in deps:
                if dep and dep not in referenced_set:
                    print(f"  WARN:  '{name}' depends on '{dep}' which is not referenced")

    # Check for skills not referenced
    missing = available - referenced_set
    if missing:
        print(f"\n  INFO:  Skills not referenced (may be intentional):")
        for name in sorted(missing):
            meta = parse_skill_frontmatter(name)
            trigger = meta.get("trigger", "")
            print(f"         - {name} ({trigger})")

    if errors == 0:
        print(f"\n  OK: {claude_md} references {len(referenced)} valid skills.")
        return 0
    else:
        print(f"\n  FAILED: {errors} error(s) found.")
        return 1


def cmd_sync(args: argparse.Namespace) -> int:
    """Check if a project's CLAUDE.md is in sync with the skills library.
    With --fix, update the skills references block."""
    project_dir = Path(args.project_dir).resolve()
    claude_md = project_dir / "CLAUDE.md"

    if not claude_md.exists():
        print(f"Error: no CLAUDE.md found at {project_dir}")
        return 1

    available = set(discover_skills())
    referenced = set(extract_skill_refs(claude_md))

    # New skills added to the library but not referenced
    new_skills = available - referenced
    if not new_skills:
        print(f"  OK: {claude_md.name} is up to date with all {len(available)} skills.")
        return 0

    print(f"\n  New skills not yet in {claude_md.name}:")
    for name in sorted(new_skills):
        meta = parse_skill_frontmatter(name)
        trigger = meta.get("trigger", "")
        print(f"    + {name} ({trigger})")

    if args.fix:
        content = claude_md.read_text(encoding="utf-8")
        # Build lines to add
        additions = []
        for name in sorted(new_skills):
            line = f"- ~/skills/skills/{name}/SKILL.md"
            additions.append(line)

        # Find the last skill reference line and append after it
        lines = content.splitlines()
        last_ref_idx = -1
        for i, line in enumerate(lines):
            if "~/skills/skills/" in line and "SKILL.md" in line:
                last_ref_idx = i

        if last_ref_idx >= 0:
            for j, addition in enumerate(additions):
                lines.insert(last_ref_idx + 1 + j, addition)
            claude_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"\n  FIXED: added {len(new_skills)} skill reference(s) to {claude_md.name}.")
            print("  Review the placement and categorise under the right heading.")
        else:
            print(f"\n  Could not find skill references block in {claude_md.name}.")
            print("  Add these lines manually under '## Shared Skills':")
            for a in additions:
                print(f"    {a}")
            return 1
    else:
        print(f"\n  Run with --fix to add them automatically.")

    return 0


def cmd_check_all(args: argparse.Namespace) -> int:
    """Validate and sync all known project directories."""
    # Auto-discover sibling directories that contain a CLAUDE.md
    parent = SKILLS_ROOT.parent
    project_dirs = sorted(
        d for d in parent.iterdir()
        if d.is_dir() and d != SKILLS_ROOT and (d / "CLAUDE.md").exists()
    )

    if not project_dirs:
        print(f"No projects with CLAUDE.md found in {parent}")
        return 0

    errors = 0
    for project_dir in project_dirs:
        project_name = project_dir.name
        if not project_dir.is_dir():
            continue

        print(f"\n--- {project_name} ---")
        claude_md = project_dir / "CLAUDE.md"
        if not claude_md.exists():
            print(f"  No CLAUDE.md found. Run: python manage.py install {project_dir}")
            errors += 1
            continue

        ns = argparse.Namespace(project_dir=str(project_dir))
        result = cmd_validate(ns)
        errors += result

        ns_sync = argparse.Namespace(project_dir=str(project_dir), fix=args.fix)
        cmd_sync(ns_sync)

    print(f"\n{'=' * 40}")
    if errors == 0:
        print("All projects OK.")
    else:
        print(f"{errors} project(s) with issues.")
    return min(errors, 1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage skills library across projects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List all available skills")

    # install
    p_install = sub.add_parser("install", help="Install CLAUDE.md into a project")
    p_install.add_argument("project_dir", help="Path to the project directory")
    p_install.add_argument("--template", help="Template name (e.g. vol_pipeline, coco_model)")
    p_install.add_argument("--force", action="store_true", help="Overwrite existing CLAUDE.md")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a project's CLAUDE.md")
    p_validate.add_argument("project_dir", help="Path to the project directory")

    # sync
    p_sync = sub.add_parser("sync", help="Check if CLAUDE.md is in sync with skills library")
    p_sync.add_argument("project_dir", help="Path to the project directory")
    p_sync.add_argument("--fix", action="store_true", help="Auto-add missing skill references")

    # check-all
    p_all = sub.add_parser("check-all", help="Validate and sync all known projects")
    p_all.add_argument("--fix", action="store_true", help="Auto-fix missing references")

    args = parser.parse_args()
    commands = {
        "list": cmd_list,
        "install": cmd_install,
        "validate": cmd_validate,
        "sync": cmd_sync,
        "check-all": cmd_check_all,
    }
    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()
