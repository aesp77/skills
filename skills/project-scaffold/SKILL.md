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
4. Every project has `PROGRESS.md` at root — tracks what's done, in progress, and next.
5. `.env` is never committed. `.env.example` is committed as a template.
6. Pre-commit is mandatory: ruff + ruff-format + mypy + standard hooks.
7. No commits directly to `main` — use feature branches.

## Patterns

### Directory Structure

```
project-name/
├── CLAUDE.md                  # Project behaviour rules
├── PROGRESS.md                # What's done, in progress, and next
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

### Streamlit App with `src/` Layout

When a project has a Streamlit dashboard alongside `src/` library code,
**every page file must explicitly add both the project root and `src/` to
`sys.path`**. Do NOT rely on `PYTHONPATH` — Streamlit runs pages as
subprocesses that don't reliably inherit environment variables on Windows.

#### Directory structure

```
project-name/
├── src/
│   └── project_name/          # Library code
│       ├── models/
│       └── data/
├── streamlit_app/             # Dashboard (NOT inside src/)
│   ├── app.py                 # Main entry point
│   ├── utils/                 # App-specific helpers
│   │   ├── config.py
│   │   ├── database.py
│   │   └── sidebar_config.py
│   └── pages/
│       ├── 1_Page_One.py
│       └── 2_Page_Two.py
└── data/                      # Data files (gitignored)
```

#### sys.path pattern for pages

**IMPORTANT:** Do NOT import `from streamlit_app.utils...` — Streamlit
manages `streamlit_app/` as a special directory and importing it as a
package causes intermittent `KeyError: 'streamlit_app'`. Instead, add
`streamlit_app/` to sys.path and import `from utils...` directly.

Each page file (`streamlit_app/pages/*.py`) needs:

```python
import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, str(Path(_project_root) / "src"))             # for project_name.*
sys.path.insert(0, str(Path(_project_root) / "streamlit_app"))   # for utils.*
```

Then import as:
```python
from utils.database import query_data        # NOT from streamlit_app.utils.database
from utils.sidebar_config import render_sidebar
from project_name.models.foo import Bar      # library code from src/
```

The main `app.py` (`streamlit_app/app.py`) needs:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))   # src/
sys.path.insert(0, str(Path(__file__).parent))                  # streamlit_app/ (for utils.*)
```

#### Launch command

The app should launch with just `streamlit run streamlit_app/app.py` from
the project root — no `PYTHONPATH` needed because the sys.path inserts
handle it.

#### Monorepo launch.json config

```jsonc
{
    "name": "ProjectName: Streamlit App",
    "type": "debugpy",
    "request": "launch",
    "module": "streamlit",
    "justMyCode": true,
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}/project-name",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/project-name/src;${workspaceFolder}/project-name",
        "KERAS_BACKEND": "torch"
    },
    "args": [
        "run",
        "streamlit_app/app.py",
        "--server.runOnSave",
        "true"
    ]
}
```

Note: `PYTHONPATH` in launch.json is a belt-and-suspenders backup — the
sys.path inserts in the code are the primary mechanism.

#### Data defaults

When defaulting date ranges from the database, use the analysis window
(e.g. 2015-present) not the full DB range. Most tickers don't exist going
back to 2000, creating huge sparse matrices filled with zeros.

```python
if 'start_date' not in st.session_state:
    st.session_state.start_date = max(db_min_date, "2015-01-01")
```

#### Post-restructure testing

After any restructure that changes imports or paths, test every page's
actual functionality — not just that it loads without error:

1. Data Explorer: refresh DB info, fetch data, check data quality
2. Each analysis page: load data, run analysis, verify output is non-zero
3. Training pages: load data, start training, verify metrics appear

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
| Relying on `PYTHONPATH` for Streamlit imports | Explicit `sys.path.insert()` in every page file |
| `from streamlit_app.utils...` in page files | `from utils...` (add `streamlit_app/` to sys.path) |
| Defaulting date ranges to full DB range | Default to analysis window (e.g. 2015+) |
| Testing only imports after restructure | Test every page button and verify output |

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
- [ ] Streamlit pages have explicit `sys.path` inserts for both project root and `src/`
- [ ] Streamlit app launches with just `streamlit run streamlit_app/app.py` (no env vars needed)
- [ ] After restructure: every page button/function tested, not just imports
