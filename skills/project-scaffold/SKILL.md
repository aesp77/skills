# SKILL: Project Scaffold

<!--
name: project-scaffold
trigger: Creating a new Python project, restructuring, or adding Poetry/pre-commit/CI
depends-on: []
applies-to: [all]
-->

## When to Apply

Read before creating any new Python project, restructuring an existing one,
or adding Poetry, pre-commit, or CI configuration.

## Dependencies

None.

## Rules

1. All projects use Poetry with `src/` layout.
2. Python >= 3.11 always.
3. Every project has `CLAUDE.md` at root — project-specific behaviour rules.
4. Every project has `PATTERNS.md` at root — domain knowledge for that project.
5. `.env` is never committed. `.env.example` is committed as a template.
6. Pre-commit is mandatory: ruff + ruff-format + mypy + standard hooks.
7. No commits directly to `main` — use feature branches.

## Patterns

### Directory Structure

```
project-name/
├── CLAUDE.md                  # Project behaviour rules
├── PATTERNS.md                # Project domain knowledge
├── pyproject.toml
├── .env                       # Never committed
├── .env.example               # Template (committed)
├── .pre-commit-config.yaml
├── .gitignore
├── .vscode/
│   └── launch.json            # Run & Debug configs (committed)
├── README.md
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── models/
│       ├── data/
│       ├── training/
│       └── utils/
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_validation.ipynb
│   └── 03_production_prep.ipynb
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
├── output/
└── data/
```

### pyproject.toml

```toml
[tool.poetry]
name = "project-name"
version = "0.1.0"
description = ""
authors = ["Ale <ale@example.com>"]
readme = "README.md"
packages = [{include = "project_name", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
keras = ">=3.0"
torch = ">=2.0"
numpy = ">=2.0"
pandas = ">=2.0"
scipy = ">=1.11"
matplotlib = ">=3.8"
pydantic = ">=2.0"

[tool.poetry.group.dev.dependencies]
pytest = ">=7.4"
pytest-cov = ">=4.0"
hypothesis = ">=6.0"
ruff = ">=0.3"
mypy = ">=1.8"
pre-commit = ">=3.0"
ipykernel = ">=6.0"
jupyter = ">=1.0"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Pre-commit Config

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: no-commit-to-branch
        args: ['--branch', 'main']
```

### .gitignore

```
__pycache__/
*.py[cod]
.venv/
dist/
build/
.env
data/raw/
output/
*.db
*.sqlite
.ipynb_checkpoints/
.vscode/settings.json
saved_models/
checkpoints/
```

### VS Code Run & Debug (.vscode/launch.json)

Every project should have Run & Debug configs. **Before creating the file,
detect where it should go** using the same Poetry root detection from env-setup.

#### Step 1 — Detect where launch.json belongs

Use `find_poetry_root()` from the env-setup skill to walk up the directory tree.

- **Parent Poetry root found** (e.g. `ale/`) → this is a monorepo. The user
  opens `ale/` in VS Code, so `launch.json` must go at `ale/.vscode/launch.json`.
- **No parent found** → standalone project. Put it at `<project>/.vscode/launch.json`.

#### Case A — Standalone Project

```jsonc
// <project>/.vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit App",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "justMyCode": true,
            "args": [
                "run",
                "app/streamlit_app.py",
                "--server.runOnSave",
                "true"
            ]
        },
        {
            "name": "Run Script",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["tests", "-v"]
        },
        {
            "name": "Debug Script",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

#### Case B — Monorepo Subdirectory

The launch.json goes at the **Poetry root** (e.g. `ale/.vscode/launch.json`).
Prefix every config name with the project name so configs from different
projects don't clash. Set `cwd` and `PYTHONPATH` to point at the subdirectory.

```jsonc
// ale/.vscode/launch.json — configs for reddit-top-stocks project
{
    "name": "Reddit: Streamlit App",
    "type": "python",
    "request": "launch",
    "module": "streamlit",
    "justMyCode": true,
    "cwd": "${workspaceFolder}/reddit-top-stocks",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/reddit-top-stocks/src"
    },
    "args": [
        "run",
        "app/streamlit_app.py",
        "--server.runOnSave",
        "true"
    ]
},
{
    "name": "Reddit: Run Tests",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "justMyCode": false,
    "cwd": "${workspaceFolder}/reddit-top-stocks",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/reddit-top-stocks/src"
    },
    "args": ["tests", "-v"]
},
{
    "name": "Reddit: Update Data",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/reddit-top-stocks/scripts/update_data.py",
    "args": ["update"],
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}/reddit-top-stocks",
    "justMyCode": true
}
```

**If `launch.json` already exists** at the Poetry root (from another project),
**merge** the new configs into the existing `configurations` array — do not
overwrite the file.

#### Adding project-specific entries

For either case, add entries for common project tasks:

```jsonc
{
    "name": "Train Model",
    "type": "python",
    "request": "launch",
    "program": "scripts/train.py",
    "console": "integratedTerminal",
    "justMyCode": true
},
{
    "name": "Update Market Data",
    "type": "python",
    "request": "launch",
    "program": "scripts/update_data.py",
    "args": ["update"],
    "console": "integratedTerminal",
    "justMyCode": true
}
```

### .gitignore

Note: `launch.json` is NOT gitignored — it should be committed so the
Run & Debug buttons work for anyone opening the project.
`settings.json` IS gitignored (personal preferences).

```
__pycache__/
*.py[cod]
.venv/
dist/
build/
.env
data/raw/
output/
*.db
*.sqlite
.ipynb_checkpoints/
.vscode/settings.json
saved_models/
checkpoints/
results/
```

## Banned Patterns

| Do NOT use | Use instead |
|---|---|
| `pip install` / `requirements.txt` | `poetry add` / `pyproject.toml` |
| Flat layout (`project_name/` at root) | `src/` layout |
| Hardcoded config values | Dataclasses or pydantic models |
| `print()` for logging | `logging` module |
| Committing `.env` | `.env.example` + `.gitignore` |
| `launch.json` inside a subdirectory when workspace root is the parent | Detect Poetry root, place `launch.json` there |

## Checklist

- [ ] `src/` layout with `packages = [{include = "...", from = "src"}]`
- [ ] `CLAUDE.md` exists at project root
- [ ] `.env.example` committed, `.env` in `.gitignore`
- [ ] Pre-commit installed and configured
- [ ] `ruff`, `mypy`, `pytest` in dev dependencies
- [ ] Python version `^3.11`
- [ ] `.vscode/launch.json` placed at correct level (Poetry root for monorepo, project root for standalone)
- [ ] Monorepo configs prefixed with project name (e.g. "Reddit: Streamlit App")
- [ ] Monorepo configs have `cwd` and `PYTHONPATH` set to project subdirectory
