# skills

Shared Claude skill library — rules, patterns, and checklists that tell
Claude Code how to write code consistently across all projects.

## Quick Start

### 1. Drop a CLAUDE.md into your project

```bash
cp ~/skills/templates/CLAUDE.md ~/my-project/CLAUDE.md
```

### 2. Open Claude Code in your project

```bash
cd ~/my-project
claude
```

### 3. Tell Claude what to do

- **New project?** Say `init` — Claude scaffolds everything, works on main
- **Existing project?** Say `upgrade` — Claude creates a branch, makes changes step by step, tests, merges

That's it. The CLAUDE.md tells Claude to read the skills, and the skills
tell Claude how to do everything.

## How It Works

```
This repo (~/skills/)          Your project (~/my-project/)
┌─────────────────────┐        ┌──────────────────────────┐
│ skills/              │        │ CLAUDE.md                │
│   18 skill files    │◄───────│   "read ~/skills/..."    │
│                     │        │                          │
│ templates/          │        │ src/                     │
│   CLAUDE.md         │        │ tests/                   │
└─────────────────────┘        └──────────────────────────┘
```

1. CLAUDE.md in your project points to skill files in this repo
2. Claude reads the relevant skills before starting work
3. Skills tell Claude the rules, patterns, and checklists to follow
4. Claude updates CLAUDE.md as the project evolves — you never edit it by hand

## Init vs Upgrade

| | **Init** (new project) | **Upgrade** (existing project) |
|---|---|---|
| **When** | Empty or new directory | Working code already exists |
| **Branch** | Work on `main` | Create a feature branch |
| **Goal** | Scaffold from scratch | Change without breaking anything |
| **Testing** | Add as you go | Verify existing output is unchanged |
| **Merge** | Already on main | Merge after all tests pass |
| **Key rule** | Build fast, switch to branching when stable | Infrastructure changes must be transparent |

## Skills Index (18 skills)

### Foundation
| Skill | What it does |
|-------|-------------|
| [project-scaffold](skills/project-scaffold/SKILL.md) | Directory structure, pyproject.toml, pre-commit |
| [env-setup](skills/env-setup/SKILL.md) | Environment detection (shared vs standalone), .env, Poetry |
| [git-workflow](skills/git-workflow/SKILL.md) | Init vs upgrade modes, branching, commits, PRs |
| [keras3-pytorch](skills/keras3-pytorch/SKILL.md) | Keras 3 + PyTorch backend, model patterns, data pipeline |

### Data
| Skill | What it does |
|-------|-------------|
| [market-data](skills/market-data/SKILL.md) | Standard DB schema, incremental updates, copy between projects |
| [edav](skills/edav/SKILL.md) | Data quality, outlier detection, distributions, visualisation |

### Quant Finance
| Skill | What it does |
|-------|-------------|
| [vol-and-curves](skills/vol-and-curves/SKILL.md) | Vol surface interpolation, rate curves, vol estimators, time conventions |
| [pricing](skills/pricing/SKILL.md) | Black-Scholes, Greeks, Monte Carlo, PDE, payoff definitions |
| [quant-patterns](skills/quant-patterns/SKILL.md) | Calibration interface, state normalisation, convergence diagnostics |
| [backtesting](skills/backtesting/SKILL.md) | Walk-forward testing, risk metrics, transaction costs, hedging comparison |

### ML Workflow
| Skill | What it does |
|-------|-------------|
| [experiment-logging](skills/experiment-logging/SKILL.md) | Log runs, model registry (versioned), compare and analyse models |
| [experiment-workflow](skills/experiment-workflow/SKILL.md) | Hyperparameter tuning (Optuna/Keras Tuner), systematic model selection |
| [notebook-workflow](skills/notebook-workflow/SKILL.md) | Notebook → module → Streamlit pipeline |
| [paper-replication](skills/paper-replication/SKILL.md) | Read paper → replicate → validate → adapt (simple to complex notebooks) |

### Testing & CI
| Skill | What it does |
|-------|-------------|
| [testing-conventions](skills/testing-conventions/SKILL.md) | Staged testing (smoke → full), pytest, hypothesis, file discipline |
| [ci-cd](skills/ci-cd/SKILL.md) | GitHub Actions (optional — add when project is mature) |

### Orchestration
| Skill | What it does |
|-------|-------------|
| [upgrade-repo](skills/upgrade-repo/SKILL.md) | Step-by-step repo upgrade on a branch |
| [skills-manager](skills/skills-manager/SKILL.md) | Adding new skills, syncing across projects |

## Template

One generic template — the `init` conversation customises it for your project:

| Template | Use for |
|----------|---------|
| [CLAUDE.md](templates/CLAUDE.md) | Any project — drop in, say `init` or `upgrade` |

## Adding a New Skill

```bash
# 1. Create the directory
mkdir skills/my-new-skill

# 2. Copy the template
cp SKILL_TEMPLATE.md skills/my-new-skill/SKILL.md

# 3. Edit, then verify
python manage.py list

# 4. Check what projects need updating
python manage.py check-all
```

## Utilities

`manage.py` is an optional helper for bulk operations:

```bash
python manage.py list                        # list all skills
python manage.py validate <project-dir>      # check a project's CLAUDE.md
python manage.py sync <project-dir> [--fix]  # check if in sync
python manage.py check-all [--fix]           # check all projects
```

## Skill Template

All skills follow [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md):

```
# SKILL: Name
<!-- frontmatter: name, trigger, depends-on, applies-to -->
## When to Apply
## Dependencies
## Rules
## Patterns
## Banned Patterns
## Checklist
```
