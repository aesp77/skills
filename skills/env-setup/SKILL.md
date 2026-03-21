# SKILL: Environment Setup

<!--
name: env-setup
trigger: Setting up a dev environment, managing .env files, configuring secrets, or onboarding to a project
depends-on: [project-scaffold]
applies-to: [all]
-->

## When to Apply

Read before setting up a development environment, managing environment
variables, or configuring secrets.

## Dependencies

- **project-scaffold** — assumes standard directory structure.

## Rules

1. `KERAS_BACKEND=torch` must be set before any Python process that imports keras.
2. `.env` is never committed — use `.env.example` as the committed template.
3. Secrets (API keys, DB credentials) go in `.env` only — never in code.
4. **Always check for an existing Poetry environment first** — walk up the directory tree looking for `pyproject.toml`. If found, use it. If not, create one.
5. Never create a duplicate environment inside a project that already inherits one from a parent.

## Patterns

### Step 1 — Detect the Environment

Before doing anything, check if the current directory is inside an existing
Poetry project.

```python
from pathlib import Path

def find_poetry_root(start_dir: Path = None) -> Path | None:
    """Walk up the directory tree looking for pyproject.toml with [tool.poetry].

    Returns the directory containing the Poetry config, or None if standalone.
    """
    current = (start_dir or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.poetry]" in content:
                return parent
    return None
```

```bash
# Quick check from the command line
# If this returns a path, you're inside a Poetry project — use that environment
python -c "
from pathlib import Path
current = Path.cwd().resolve()
for p in [current] + list(current.parents):
    if (p / 'pyproject.toml').exists():
        print(f'Poetry root: {p}')
        break
else:
    print('No Poetry project found — standalone directory')
"
```

### Step 2 — Act Based on What You Found

#### Case A: Parent Poetry environment exists (e.g. `ale/`)

You're inside a monorepo. **Do NOT create a new environment.**

```
ale/                              # Poetry root — pyproject.toml lives here
├── pyproject.toml                # shared Poetry config
├── poetry.lock                   # locked dependencies
├── .env                          # secrets (never committed)
├── vol_pipeline/                 # project — uses parent env
├── rl_hedging_comparison/        # project — uses parent env
├── credit_macro/                 # project — uses parent env
└── ...
```

```bash
# Adding a dependency — do it at the Poetry root
cd ~/ale
poetry add <package>

# Running code — from anywhere, Poetry resolves the environment
poetry run python vol_pipeline/scripts/train.py

# Or activate the shell once
poetry shell
python vol_pipeline/scripts/train.py
```

New projects just create a directory:
```bash
cd ~/ale
mkdir new_project
# Start coding — environment is already there
```

#### Case B: No parent environment — standalone directory

This is an independent project. Create a Poetry environment here.

```bash
cd ~/standalone-project

# Initialise Poetry
poetry init --no-interaction --name my-project --python "^3.11"

# Add dependencies
poetry add keras torch numpy pandas scipy matplotlib

# Install
poetry install

# Set up .env
echo "KERAS_BACKEND=torch" > .env
cp .env .env.example
```

#### Case C: No Poetry at all — pip fallback

If Poetry is not available (e.g. someone else's machine, CI without Poetry):

```bash
cd ~/project

# Create a venv
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install from requirements if available
pip install -r requirements.txt

# Or install manually
pip install keras torch numpy pandas scipy
```

### Decision Flowchart

```
Start: Where am I?
  │
  ├── Walk up directories looking for pyproject.toml with [tool.poetry]
  │
  ├── FOUND → Use that environment. Do NOT create a new one.
  │            Add dependencies at that level.
  │
  └── NOT FOUND
       │
       ├── Poetry available? → poetry init, poetry install
       │
       └── Poetry not available? → python -m venv, pip install
```

### .env.example Template

```bash
# .env.example — committed to repo
KERAS_BACKEND=torch

# Bloomberg
# BBG_HOST=localhost
# BBG_PORT=8194

# Marquee (Goldman Sachs)
# MARQUEE_CLIENT_ID=...
# MARQUEE_CLIENT_SECRET=...

# FirstRate Data
# FIRSTRATE_API_KEY=...

# Optional: GPU
# CUDA_VISIBLE_DEVICES=0
```

### Loading Environment Variables

```python
# In scripts and modules
from dotenv import load_dotenv
load_dotenv()  # loads from nearest .env (walks up to parent)

# In notebooks (cell 1, always)
import os
os.environ["KERAS_BACKEND"] = "torch"
```

### Running Commands

Always from the parent directory, or use `poetry run` from anywhere.

```bash
# From parent directory
cd ~/ale
poetry run python vol_pipeline/scripts/train.py
poetry run pytest rl_hedging_comparison/tests/

# Or activate the shell once
poetry shell
python vol_pipeline/scripts/train.py
```

### GPU Configuration

```bash
# .env
CUDA_VISIBLE_DEVICES=0

# Verify in Python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device count: {torch.cuda.device_count()}")
```

### IDE Setup (VS Code)

Point VS Code to the shared Poetry environment.

```jsonc
// .vscode/settings.json (in .gitignore)
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python",
    "python.terminal.activateEnvironment": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true
    },
    "python.testing.pytestEnabled": true
}
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Create a new virtualenv without checking for an existing one | Run `find_poetry_root()` first |
| `poetry install` inside a project that inherits from parent | Add dependencies at the Poetry root |
| Hardcode credentials in code | `.env` + `python-dotenv` |
| Commit `.env` | `.env.example` + `.gitignore` |
| Missing `KERAS_BACKEND` | Set in `.env` and notebook cell 1 |
| Assume Poetry is available | Check, and fall back to pip + venv if not |

## Checklist

- [ ] Checked for existing Poetry environment (walked up directory tree)
- [ ] Using the correct environment (parent if exists, new if standalone)
- [ ] Dependencies added at the right level (Poetry root, not subdirectory)
- [ ] `.env.example` exists and lists all required variables
- [ ] `.env` is in `.gitignore`
- [ ] `KERAS_BACKEND=torch` is set
- [ ] No secrets in committed files
