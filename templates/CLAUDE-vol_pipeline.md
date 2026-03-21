# CLAUDE.md — vol_pipeline

## Identity

- **Project**: vol_pipeline
- **Owner**: Ale (aesp77)
- **Stack**: Python 3.11+, Keras 3 (PyTorch backend), Poetry
- **Purpose**: Volatility surface calibration and interpolation pipeline

## Shared Skills

Before starting any work, read the relevant skills from the shared library.

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

### Read for quant/finance work
- ~/skills/skills/vol-and-curves/SKILL.md
- ~/skills/skills/pricing/SKILL.md
- ~/skills/skills/quant-patterns/SKILL.md
- ~/skills/skills/backtesting/SKILL.md

### Read for testing
- ~/skills/skills/testing-conventions/SKILL.md

## Project Rules

1. All calibration results must be logged to SQLite via `log_experiment()` with `project="vol_pipeline"`.
2. Vol surface models must implement the `VolModel` ABC from quant-patterns.
3. Calibration output is always a `CalibrationResult` dataclass.
4. Market data inputs are never modified in place — always copy first.
5. RMSE against market IVs is the primary calibration metric.

## Architecture

```
src/vol_pipeline/
├── models/          # Vol surface models (SVI, SABR, neural)
├── data/            # Market data loading, IV parsing
├── calibration/     # Calibration engine, optimisers
├── interpolation/   # Surface interpolation methods
└── utils/           # Plotting, date handling
```

## Key Files

| File | Purpose |
|------|---------|
| `src/vol_pipeline/models/svi.py` | SVI parameterisation |
| `src/vol_pipeline/models/sabr.py` | SABR model |
| `src/vol_pipeline/calibration/engine.py` | Calibration orchestrator |
| `db/schema.py` | Shared experiment DB |

## Current State

- **Active branch**: main
- **Known issues**: none

## Project-Specific Patterns

### Vol surface representation
```python
# Surfaces are always (strikes x expiries) DataFrames with IV values
# Index = strikes (float), Columns = expiries (str dates)
surface: pd.DataFrame  # shape: (n_strikes, n_expiries)
```

### Calibration workflow
```
1. Load market IVs from data source
2. Select model (SVI, SABR, or neural)
3. Run calibration -> CalibrationResult
4. Log to DB via log_experiment()
5. Compare RMSE across models
```

## Do NOT

- Do not store raw market data in the repo — it goes in `data/raw/` which is gitignored.
- Do not use `scipy.optimize` directly — wrap it in the calibration engine.
- Do not interpolate without calibrating first — always fit a model.
