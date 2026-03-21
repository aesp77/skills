# CLAUDE.md — coco_model

## Identity

- **Project**: coco_model
- **Owner**: Ale (aesp77)
- **Stack**: Python 3.11+, Keras 3 (PyTorch backend), Poetry
- **Purpose**: Contingent convertible bond (CoCo) pricing model

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

1. All pricing results are cached to SQLite via `log_experiment()` with `project="coco_model"`.
2. CoCo trigger conditions must be explicitly parameterised — never hardcoded.
3. Always price against a benchmark (e.g. equity derivative decomposition).
4. Credit spread and equity vol are co-dependent — never calibrate independently.
5. Conversion ratios and trigger levels are part of `market_params` in DB logging.

## Architecture

```
src/coco_model/
├── models/          # CoCo pricing models (structural, reduced-form, neural)
├── data/            # Bond data, credit spreads, equity data
├── pricing/         # Pricing engine
├── calibration/     # Joint equity-credit calibration
└── utils/           # Payoff calculations, barrier checks
```

## Key Files

| File | Purpose |
|------|---------|
| `src/coco_model/models/structural.py` | Structural CoCo model |
| `src/coco_model/pricing/engine.py` | Pricing orchestrator |
| `src/coco_model/calibration/joint.py` | Joint equity-credit calibration |
| `db/schema.py` | Shared experiment DB |

## Current State

- **Active branch**: main
- **Known issues**: none

## Project-Specific Patterns

### CoCo instrument definition
```python
@dataclass
class CoCoSpec:
    notional: float
    coupon: float
    maturity: float           # years
    trigger_level: float      # as fraction of initial (e.g. 0.75)
    conversion_ratio: float   # shares per unit notional
    trigger_type: str         # "accounting" | "market"
```

## Do NOT

- Do not price CoCos without specifying the trigger type — accounting vs market triggers have different dynamics.
- Do not assume constant credit spreads — always allow term structure.
- Do not cache prices without the full instrument spec in `hyperparams`.
