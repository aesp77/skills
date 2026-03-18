# SKILL: Project Scaffold

## Trigger
Read before creating any new Python project, restructuring an existing one,
or adding Poetry, pre-commit, or CI.

---

## Directory Structure

```
project-name/
├── CLAUDE.md                  # Project behaviour rules
├── PATTERNS.md                # Project domain knowledge
├── pyproject.toml
├── .env                       # Never committed
├── .env.example               # Template (committed)
├── .pre-commit-config.yaml
├── .gitignore
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

---

## pyproject.toml Template

```toml
[tool.poetry]
name = "project-name"
version = "0.1.0"
description = ""
authors = ["Ale <ale@portmansquarecapital.com>"]
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

---

## Pre-commit Config

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

---

## .gitignore

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

---

## Setup Commands

```bash
poetry new project-name --src && cd project-name
poetry env use python3.11
poetry install
echo "KERAS_BACKEND=torch" >> .env
pre-commit install
git init && git add . && git commit -m "chore: initial scaffold"
```
