# skills

Shared Claude skill library for aesp77 Python projects.

These skill files are read by Claude Code (VS Code) and Claude.ai to enforce
consistent patterns across all repositories:
- vol_pipeline
- coco_model
- rl-deep-hedging
- Any future PSC quant project

## How to use

### In Claude Code (VS Code)
In each project's CLAUDE.md, add:
```
## Shared Skills
Before starting work, read:
- ~/skills/skills/keras3-pytorch/SKILL.md
- ~/skills/skills/project-scaffold/SKILL.md
- ~/skills/skills/db-conventions/SKILL.md
- ~/skills/skills/notebook-workflow/SKILL.md
- ~/skills/skills/quant-patterns/SKILL.md
```

### In Claude.ai chat
Upload the relevant SKILL.md files or paste their contents at the start of a session.

## Skills Index

| Skill | Covers | Trigger |
|-------|--------|---------|
| keras3-pytorch | Keras 3 + PyTorch backend, model patterns, banned TF patterns | Any ML/DL work |
| project-scaffold | Poetry setup, directory structure, pyproject.toml, pre-commit | New project or restructure |
| db-conventions | Shared SQLite/PostgreSQL schema, cross-project log_experiment() | Any DB work |
| notebook-workflow | Exploration → module → Streamlit pipeline | Any notebook work |
| quant-patterns | Calibration, backtesting, path simulation, normalisation | Any quant finance code |
