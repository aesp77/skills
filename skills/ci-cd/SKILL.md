# SKILL: CI/CD

<!--
name: ci-cd
trigger: Setting up or modifying GitHub Actions, CI pipelines, or automated checks
depends-on: [project-scaffold, testing-conventions]
applies-to: [all]
-->

## When to Apply

Read before setting up or modifying GitHub Actions workflows, adding automated
checks, or configuring branch protection rules.

## Dependencies

- **project-scaffold** — CI assumes Poetry, `src/` layout, and standard `pyproject.toml`.
- **testing-conventions** — CI runs the test suite defined by that skill.

## Rules

1. Every repo has a `.github/workflows/ci.yml` that runs on every push and PR.
2. CI pipeline runs three stages in order: lint -> type-check -> test.
3. Use the same Python version as `pyproject.toml` (`3.11`).
4. Cache Poetry virtualenv for speed.
5. Set `KERAS_BACKEND=torch` in CI environment.
6. Never skip CI checks — no `[skip ci]` for PRs to main.
7. Branch protection on `main`: require CI pass + 1 approval (when team > 1).

## Patterns

### Standard CI Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  KERAS_BACKEND: torch
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        run: pipx install poetry

      - name: Cache Poetry venv
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-${{ runner.os }}-${{ hashFiles('poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Lint
        run: poetry run ruff check src/ tests/

      - name: Format check
        run: poetry run ruff format --check src/ tests/

  type-check:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        run: pipx install poetry

      - name: Cache Poetry venv
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-${{ runner.os }}-${{ hashFiles('poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Type check
        run: poetry run mypy src/

  test:
    runs-on: ubuntu-latest
    needs: type-check
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        run: pipx install poetry

      - name: Cache Poetry venv
        uses: actions/cache@v4
        with:
          path: ~/.cache/pypoetry
          key: poetry-${{ runner.os }}-${{ hashFiles('poetry.lock') }}

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run tests
        run: poetry run pytest --cov=src --cov-report=term-missing

      - name: Check coverage threshold
        run: poetry run pytest --cov=src --cov-fail-under=80 -q
```

### Branch Protection (set via GitHub UI or CLI)

```bash
# Enable branch protection on main
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  -F required_status_checks='{"strict":true,"contexts":["lint","type-check","test"]}' \
  -F enforce_admins=true \
  -F required_pull_request_reviews='{"required_approving_review_count":0}' \
  -F restrictions=null
```

### Optional: Notebook Validation Job

```yaml
  notebook-check:
    runs-on: ubuntu-latest
    needs: test
    if: contains(github.event.pull_request.labels.*.name, 'notebook')
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        run: pipx install poetry

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Validate notebooks execute
        run: |
          poetry run jupyter nbconvert --execute --to notebook \
            --output-dir=/tmp/nb-output notebooks/*.ipynb
```

### Release Workflow (manual trigger)

```yaml
# .github/workflows/release.yml
name: Release

on:
  workflow_dispatch:
    inputs:
      bump:
        description: "Version bump type"
        required: true
        type: choice
        options: [patch, minor, major]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        run: pipx install poetry

      - name: Bump version
        run: poetry version ${{ inputs.bump }}

      - name: Commit and tag
        run: |
          VERSION=$(poetry version -s)
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add pyproject.toml
          git commit -m "chore: bump version to ${VERSION}"
          git tag "v${VERSION}"
          git push origin main --tags
```

## Banned Patterns

| Do NOT use | Use instead |
|---|---|
| `[skip ci]` on PRs to main | Always run CI on main PRs |
| `pip install` in CI | `poetry install` |
| Missing `KERAS_BACKEND` env var | Set `KERAS_BACKEND: torch` in workflow env |
| Hardcoded Python version in multiple places | Use `env.PYTHON_VERSION` variable |
| Running all jobs in a single step | Separate lint / type-check / test jobs |

## Checklist

- [ ] `.github/workflows/ci.yml` exists with lint, type-check, test jobs
- [ ] `KERAS_BACKEND=torch` set in workflow environment
- [ ] Poetry venv cached via `actions/cache`
- [ ] Coverage threshold enforced (`--cov-fail-under=80`)
- [ ] Branch protection enabled on `main`
- [ ] Release workflow uses `poetry version` for bumps
