# SKILL: Git Workflow

<!--
name: git-workflow
trigger: Branching, committing, opening PRs, versioning, or release work
depends-on: [project-scaffold]
applies-to: [all]
-->

## When to Apply

Read before creating branches, writing commit messages, opening pull requests,
or bumping versions. Ensures all repos follow the same git conventions.

## Dependencies

- **project-scaffold** — repos must already follow the standard directory structure.

## Rules

1. **New projects**: work on `main` until the project is ready for production.
2. **Existing projects**: always use a feature branch — never commit directly to `main`.
3. Branch names follow the format: `<type>/<short-description>`.
4. Commit messages follow Conventional Commits: `<type>: <description>`.
5. One logical change per commit — do not bundle unrelated changes.
6. Infrastructure changes (e.g. CSV -> DB) must be transparent — existing code should not need to change its interface.
7. Version bumps use `poetry version <rule>` — never edit `pyproject.toml` by hand.

## Patterns

### Two Modes — New vs Existing

#### New Project (init mode)

Work on `main` until the project has a working foundation. No branches needed
yet — you're building from scratch, there's nothing to protect.

```
main
  ├── commit: chore: initial scaffold
  ├── commit: feat: add data pipeline
  ├── commit: feat: add core model
  ├── commit: test: add unit tests
  ├── commit: feat: add basic notebook
  └── ... (keep going until it works end-to-end)
```

**When to switch to branching**: once the project has working code that you
rely on — a model that's been trained, notebooks with results, a pipeline
that produces output you trust. At that point, `main` becomes protected.

#### Existing Project (update mode)

Production code exists. Always branch, test, merge.

```
main (protected — working code lives here)
  └── feat/csv-to-db-migration
        ├── commit: refactor: add database loader alongside CSV
        ├── commit: test: verify DB loader matches CSV output
        ├── commit: refactor: switch default to DB, keep CSV fallback
        ├── commit: test: run all notebooks with DB source
        └── PR -> main (squash merge after all tests pass)
```

### Infrastructure Changes — The Transparency Rule

When changing infrastructure (data source, storage format, API, etc.),
the code that consumes the data should not need to change. The interface
stays the same.

**Example: vol_pipeline CSV -> DB migration**

```python
# BEFORE: CSV loader
def load_spot_data(symbol: str, start_date: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/raw/{symbol}_spot.csv")
    return df[df["date"] >= start_date]

# AFTER: DB loader with same interface — notebooks don't change
def load_spot_data(symbol: str, start_date: str) -> pd.DataFrame:
    conn = get_project_db(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM time_series WHERE symbol = ? AND field = 'spot' AND date >= ?",
        conn, params=(symbol, start_date),
    )
    conn.close()
    return df
```

**The migration process:**

```
Step 1: Add DB loader alongside CSV (both work)
        → commit: feat: add DB data loader
        → test: existing notebooks still work with CSV

Step 2: Verify DB output matches CSV output exactly
        → commit: test: verify DB matches CSV for all datasets
        → run comparison: assert db_df.equals(csv_df)

Step 3: Switch default to DB, keep CSV as fallback
        → commit: refactor: default to DB, CSV fallback
        → test: all notebooks produce same results

Step 4: Remove CSV fallback (only after confidence)
        → commit: refactor: remove CSV loader
        → test: full test suite passes

Key: NO retraining needed. Models, notebooks, and modules
call the same function — only the implementation changes.
```

### Branch Naming

```
feat/vol-surface-encoder       # new feature
fix/calibration-nan            # bug fix
refactor/csv-to-db             # infrastructure change, no behaviour change
exp/nb22-heston-calibration    # experiment / notebook exploration
chore/update-dependencies      # tooling, deps, CI
docs/readme-update             # documentation only
migrate/csv-to-db              # data migration
```

### Commit Messages (Conventional Commits)

```
feat: add Heston model calibration
fix: handle NaN in vol surface interpolation
refactor: extract training loop into separate module
test: add hypothesis tests for GBM simulation
chore: bump keras to 3.1
docs: update PATTERNS.md with new normalisation
migrate: switch vol_pipeline from CSV to DB
```

Multi-line for context when needed:

```
refactor: switch data source from CSV to DB

CSV loader kept as fallback during transition.
All notebooks verified to produce identical output.
No model retraining required — interface unchanged.
```

### Pull Request Template

```markdown
## Summary
- [1-3 bullet points: what and why]

## Changes
- [list of files/modules changed]

## Testing
- [ ] Unit tests pass (`poetry run pytest`)
- [ ] Notebook validation (if model/data change)
- [ ] Output matches before and after (if infrastructure change)
- [ ] No retraining required (if data source change)

## Migration Notes
- [any migration steps needed]
- [fallback strategy if something breaks]
- [data to verify: list]
```

### Version Bumping

```bash
# Patch: bug fixes (0.1.0 -> 0.1.1)
poetry version patch

# Minor: new features, backward compatible (0.1.0 -> 0.2.0)
poetry version minor

# Major: breaking changes (0.1.0 -> 1.0.0)
poetry version major

# Then commit and tag
git add pyproject.toml
git commit -m "chore: bump version to $(poetry version -s)"
git tag "v$(poetry version -s)"
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Branch on a new project with no working code yet | Work on `main` until it's stable |
| Commit directly to `main` on an existing project | Feature branch + PR |
| Random branch names (`my-branch`, `test123`) | `<type>/<description>` format |
| Vague commits (`fix stuff`, `update`) | Conventional Commits with clear description |
| Infrastructure change that breaks existing interface | Keep the same function signatures |
| Data migration that requires retraining | Verify output matches before switching |
| Manual version edits in `pyproject.toml` | `poetry version <rule>` |
| Force-pushing to shared branches | Only force-push your own feature branches |
| Merge commits | Squash merge PRs into main |

## Checklist

### New project (init mode)
- [ ] Working on `main` until project has stable foundation
- [ ] All commits use Conventional Commits format
- [ ] Switch to branching once code is relied upon

### Existing project (update mode)
- [ ] Branch name follows `<type>/<description>` format
- [ ] All commits use Conventional Commits format
- [ ] Infrastructure changes keep same interface
- [ ] Existing notebooks/models produce same output after change
- [ ] No retraining required for data source changes
- [ ] PR has summary, changes, testing, and migration notes
- [ ] Version bumped if releasing (`poetry version`)
