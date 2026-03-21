# SKILL: Upgrade Repo

<!--
name: upgrade-repo
trigger: Bringing an existing project into compliance with the skills library
depends-on: [skills-manager, project-scaffold, git-workflow]
applies-to: [all]
-->

## When to Apply

Read before upgrading an existing project to comply with the full skills library.
This skill orchestrates a safe, step-by-step upgrade on a feature branch —
nothing touches `main` until everything passes.

## Dependencies

- **skills-manager** — uses `manage.py` to install and validate CLAUDE.md.
- **project-scaffold** — the target structure the repo is upgraded towards.
- **git-workflow** — branch naming and commit conventions during the upgrade.

## Rules

1. All upgrade work happens on a `chore/skills-upgrade` branch — never on main.
2. Each step is a separate commit with a clear Conventional Commit message.
3. After each step, run the relevant check (lint, type-check, tests) before continuing.
4. If any step fails, fix it on the branch before moving to the next step.
5. Only merge to main after ALL checks pass and the full checklist is green.
6. Never delete existing code that is still in use — only restructure or add.
7. Back up any files being moved or restructured before modifying them.

## Patterns

### Full Upgrade Sequence

Run these steps in order. Each step is one commit on the upgrade branch.

```bash
# ──────────────────────────────────────────────
# STEP 0: Prepare
# ──────────────────────────────────────────────
cd ~/your-project
git checkout main
git pull origin main
git checkout -b chore/skills-upgrade

# ──────────────────────────────────────────────
# STEP 1: Install CLAUDE.md
# ──────────────────────────────────────────────
python ~/skills/manage.py install . --template <project-name> --force
# Review and customise the installed CLAUDE.md
git add CLAUDE.md
git commit -m "chore: install skills-managed CLAUDE.md"

# ──────────────────────────────────────────────
# STEP 2: Fix directory structure (project-scaffold)
# ──────────────────────────────────────────────
# Ensure src/ layout exists
# Move any flat-layout code into src/<package_name>/
# Create missing directories: tests/unit/, tests/integration/, scripts/, output/
# Add .env.example if missing
git add -A
git commit -m "refactor: align directory structure with project-scaffold skill"

# ──────────────────────────────────────────────
# STEP 3: Fix pyproject.toml (project-scaffold)
# ──────────────────────────────────────────────
# Ensure packages = [{include = "...", from = "src"}]
# Add missing dev dependencies: ruff, mypy, pytest, hypothesis, pre-commit
# Set [tool.ruff] and [tool.mypy] sections
# Set [tool.pytest.ini_options]
poetry install
git add pyproject.toml poetry.lock
git commit -m "chore: align pyproject.toml with project-scaffold skill"

# CHECKPOINT: does it install cleanly?
poetry install && echo "OK"

# ──────────────────────────────────────────────
# STEP 4: Add pre-commit and linting (project-scaffold)
# ──────────────────────────────────────────────
# Add .pre-commit-config.yaml if missing
# Run ruff to auto-fix existing code
poetry run ruff check src/ --fix
poetry run ruff format src/ tests/
poetry run pre-commit install
git add -A
git commit -m "chore: add pre-commit config and auto-fix lint issues"

# CHECKPOINT: does lint pass?
poetry run ruff check src/ tests/ && echo "OK"

# ──────────────────────────────────────────────
# STEP 5: Fix Keras/PyTorch patterns (keras3-pytorch)
# ──────────────────────────────────────────────
# Search for banned patterns:
#   grep -r "import tensorflow" src/
#   grep -r "tf\." src/
#   grep -r "model\.predict(" src/
#   grep -r "\.h5" src/
# Fix each occurrence per the skill's banned patterns table
git add -A
git commit -m "refactor: align ML code with keras3-pytorch skill"

# CHECKPOINT: do imports work?
poetry run python -c "import os; os.environ['KERAS_BACKEND']='torch'; import keras; print('OK')"

# ──────────────────────────────────────────────
# STEP 6: Fix database code (experiment-logging)
# ──────────────────────────────────────────────
# Ensure db/schema.py uses the shared DDL
# Fix any SQL injection (f-strings → parameterised queries)
# Ensure log_experiment() captures git_hash
git add -A
git commit -m "refactor: align database code with experiment-logging skill"

# ──────────────────────────────────────────────
# STEP 7: Add/fix tests (testing-conventions)
# ──────────────────────────────────────────────
# Ensure conftest.py sets KERAS_BACKEND=torch
# Add tmp_db fixture
# Add hypothesis tests for numerical code
# Fill gaps to reach 80% coverage
git add -A
git commit -m "test: align test suite with testing-conventions skill"

# CHECKPOINT: do tests pass?
poetry run pytest --cov=src --cov-report=term-missing && echo "OK"

# ──────────────────────────────────────────────
# STEP 8: Fix notebooks (notebook-workflow)
# ──────────────────────────────────────────────
# Ensure cell 1 sets KERAS_BACKEND=torch
# Ensure last cell has FINDINGS/TO EXTRACT summary
# Rename to sequential numbering if needed
git add -A
git commit -m "chore: align notebooks with notebook-workflow skill"

# ──────────────────────────────────────────────
# STEP 9: Add CI (ci-cd)
# ──────────────────────────────────────────────
# Create .github/workflows/ci.yml from the ci-cd skill template
mkdir -p .github/workflows
# Copy the workflow from the ci-cd skill
git add .github/
git commit -m "ci: add GitHub Actions workflow from ci-cd skill"

# ──────────────────────────────────────────────
# STEP 10: Update .gitignore and .env (env-setup)
# ──────────────────────────────────────────────
# Merge skill's .gitignore entries with existing
# Ensure .env has KERAS_BACKEND=torch
# Ensure .env.example is committed
git add -A
git commit -m "chore: align .gitignore and .env with env-setup skill"

# ──────────────────────────────────────────────
# STEP 11: Final validation
# ──────────────────────────────────────────────
python ~/skills/manage.py validate .
poetry run ruff check src/ tests/
poetry run mypy src/
poetry run pytest --cov=src --cov-fail-under=80

# All green? Merge.
git checkout main
git merge chore/skills-upgrade
git push origin main
git branch -d chore/skills-upgrade
```

### Partial Upgrade (single skill)

If you only need to apply one skill:

```bash
cd ~/your-project
git checkout -b chore/upgrade-<skill-name>

# Apply changes for that one skill
# ...

# Validate
poetry run ruff check src/
poetry run pytest

# Merge
git checkout main
git merge chore/upgrade-<skill-name>
git branch -d chore/upgrade-<skill-name>
```

### Dry Run (check what needs changing without modifying)

```bash
cd ~/your-project

echo "=== Directory structure ==="
# Check for src/ layout
ls src/ 2>/dev/null || echo "MISSING: src/ layout"

echo "=== Banned imports ==="
grep -rn "import tensorflow" src/ || echo "OK: no tensorflow"
grep -rn "model\.predict(" src/ || echo "OK: no model.predict()"

echo "=== SQL injection ==="
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*WHERE" src/ db/ || echo "OK: no f-string SQL"

echo "=== CLAUDE.md ==="
python ~/skills/manage.py validate . 2>&1

echo "=== Tests ==="
poetry run pytest --co -q 2>/dev/null | tail -1 || echo "No tests found"

echo "=== CI ==="
ls .github/workflows/ci.yml 2>/dev/null || echo "MISSING: CI workflow"
```

### Recovery (if something goes wrong)

```bash
# Abort the upgrade and go back to main
git checkout main
git branch -D chore/skills-upgrade

# Or reset just the last commit on the upgrade branch
git checkout chore/skills-upgrade
git reset --soft HEAD~1
# Fix the issue, then re-commit
```

## Step-by-Step Checkpoints

| Step | What to check | Command |
|------|--------------|---------|
| 3 | Poetry installs cleanly | `poetry install` |
| 4 | No lint errors | `poetry run ruff check src/ tests/` |
| 5 | Keras imports work | `python -c "import os; os.environ['KERAS_BACKEND']='torch'; import keras"` |
| 7 | Tests pass, coverage >= 80% | `poetry run pytest --cov=src --cov-fail-under=80` |
| 9 | CI workflow is valid YAML | `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` |
| 11 | Full validation | `python ~/skills/manage.py validate .` |

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Upgrade directly on main | Always use `chore/skills-upgrade` branch |
| Apply all changes in one commit | One commit per step |
| Skip checkpoints | Run the check after each step |
| Delete code you don't understand | Investigate first, restructure if needed |
| Force-merge with failing checks | Fix all issues on the branch first |
| Upgrade without reading CLAUDE.md first | Install CLAUDE.md as Step 1 |

## Checklist

Before merging `chore/skills-upgrade` into main, verify ALL of these:

- [ ] CLAUDE.md installed and validated (`manage.py validate .`)
- [ ] `src/` layout with correct `pyproject.toml` packages entry
- [ ] `pyproject.toml` has all required dev dependencies
- [ ] `.pre-commit-config.yaml` present and hooks installed
- [ ] No banned Keras/TF patterns in code
- [ ] Database code uses parameterised queries
- [ ] `conftest.py` sets `KERAS_BACKEND=torch`
- [ ] Tests pass with >= 80% coverage
- [ ] Notebooks have backend set in cell 1 and findings in last cell
- [ ] `.github/workflows/ci.yml` present
- [ ] `.env.example` committed, `.env` gitignored
- [ ] Every commit follows Conventional Commits format
- [ ] `python ~/skills/manage.py validate .` passes with no errors
