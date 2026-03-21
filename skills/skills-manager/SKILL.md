# SKILL: Skills Manager

<!--
name: skills-manager
trigger: Adding a new skill, onboarding a project, or checking skills are in sync across repos
depends-on: []
applies-to: [all]
-->

## When to Apply

Read before adding a new skill to the library, onboarding a new project, or
checking that all repos are up to date with the latest skills.

## Dependencies

None.

## Rules

1. Every new skill must follow `SKILL_TEMPLATE.md` — same sections, same frontmatter.
2. After adding a skill, run `python manage.py check-all` to flag repos that need updating.
3. After adding a project-specific template, add it to the `templates/` index in README.
4. Skills are auto-discovered from `skills/*/SKILL.md` — no manual registration needed.
5. The `manage.py` script is the single source of truth for validation.

## Patterns

### Adding a New Skill

```bash
# 1. Create the skill directory and file
mkdir skills/my-new-skill
cp SKILL_TEMPLATE.md skills/my-new-skill/SKILL.md

# 2. Edit the SKILL.md — fill in all sections

# 3. Verify it's discovered
python manage.py list

# 4. Check which repos need updating
python manage.py check-all

# 5. Auto-fix references (then review placement)
python manage.py check-all --fix
```

### Onboarding a New Project

```bash
# 1. Install CLAUDE.md from generic template
python manage.py install ~/new-project

# 2. Or use a specific template
python manage.py install ~/new-project --template vol_pipeline

# 3. Validate the installation
python manage.py validate ~/new-project
```

### Keeping Repos in Sync

```bash
# Check all known projects
python manage.py check-all

# Auto-add missing skill references
python manage.py check-all --fix

# Check a single project
python manage.py sync ~/vol_pipeline
python manage.py sync ~/vol_pipeline --fix
```

### Creating a Project-Specific Template

1. Copy the generic template: `cp templates/CLAUDE.md templates/CLAUDE-<name>.md`
2. Fill in all `{{placeholders}}`
3. Add project-specific rules, architecture, and patterns
4. Add to the README templates table

## Banned Patterns

| Do NOT use | Use instead |
|---|---|
| Manual skill registration | Auto-discovery from `skills/*/SKILL.md` |
| Copying CLAUDE.md by hand without validating | `python manage.py install` + `validate` |
| Skill without `SKILL_TEMPLATE.md` structure | Always follow the template |
| Adding skills without running `check-all` | Always verify cross-repo impact |

## Checklist

- [ ] New skill follows `SKILL_TEMPLATE.md` structure
- [ ] `python manage.py list` shows the new skill
- [ ] `python manage.py check-all` reports no errors
- [ ] README skills index updated
- [ ] README dependency graph updated (if new dependencies)
