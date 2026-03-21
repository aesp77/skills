# CLAUDE.md

## Shared Skills

Before starting any work, read the relevant skills from `~/skills/skills/`.

### Always read
- ~/skills/skills/project-scaffold/SKILL.md
- ~/skills/skills/env-setup/SKILL.md
- ~/skills/skills/git-workflow/SKILL.md

### Read for data work
- ~/skills/skills/market-data/SKILL.md
- ~/skills/skills/edav/SKILL.md
- ~/skills/skills/experiment-logging/SKILL.md

### Read for ML/model work
- ~/skills/skills/keras3-pytorch/SKILL.md
- ~/skills/skills/notebook-workflow/SKILL.md
- ~/skills/skills/experiment-workflow/SKILL.md
- ~/skills/skills/paper-replication/SKILL.md

### Read for quant/finance work
- ~/skills/skills/vol-and-curves/SKILL.md
- ~/skills/skills/pricing/SKILL.md
- ~/skills/skills/quant-patterns/SKILL.md
- ~/skills/skills/backtesting/SKILL.md

### Read for testing
- ~/skills/skills/testing-conventions/SKILL.md

### Read for CI/CD (optional — add when project is mature)
- ~/skills/skills/ci-cd/SKILL.md

## Commands

- **"init"** — This is a new project. Read project-scaffold and env-setup skills.
  Check if we're inside an existing Poetry environment (walk up for pyproject.toml).
  Scaffold the directory structure, then work on `main` until the project has a
  working foundation. Ask what the project does and scaffold accordingly.

- **"upgrade"** — This is an existing project with working code. Read upgrade-repo
  and git-workflow skills. Create a feature branch (e.g. `refactor/csv-to-db`).
  Make changes step by step, test after each step, ensure existing code still
  produces the same output. Only merge to main when everything passes.
  Infrastructure changes must be transparent — same interfaces, no retraining needed.

## Keeping this file up to date

This file is the source of truth for project configuration. When the user asks
to change the project (add features, remove components, change architecture),
update this file to reflect the new state. Specifically:

- Add new project rules under **Project Rules** when decisions are made
- Add constraints under **Do NOT** when the user says to avoid something
- Update **Architecture** when the project structure changes
- Update **Current State** when branches, active work, or known issues change

The user should never need to edit this file by hand. If they want to change
something, they tell Claude and Claude updates both the code and this file.

## Project Rules

<!-- Rules will be added here as the project evolves -->

## Architecture

<!-- Will be filled in after init or upgrade -->

## Current State

<!-- Will be updated as work progresses -->

## Do NOT

<!-- Constraints will be added here as decisions are made -->
