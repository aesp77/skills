# CLAUDE.md — rl-deep-hedging

## Identity

- **Project**: rl-deep-hedging
- **Owner**: Ale (aesp77)
- **Stack**: Python 3.11+, Keras 3 (PyTorch backend), Poetry
- **Purpose**: Deep hedging via reinforcement learning for options portfolios

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

1. All experiment results logged to PostgreSQL via `log_experiment()` with `project="rl-deep-hedging"`.
2. Every hedging model must be compared against BS delta benchmark — report `ratio_vs_bs` and `delta_corr`.
3. Use CVaR (alpha=0.5) as the default loss. Document if switching to exponential utility.
4. State features must be normalised to O(1) via `build_hedging_state()`.
5. Path simulation must be differentiable (reparameterisation trick).
6. Follow convergence diagnostic order before tuning hyperparameters.
7. Notebook numbering continues from NB21 — next is NB22.

## Architecture

```
src/rl_deep_hedging/
├── models/          # Hedging networks (actor, critic)
├── simulation/      # Path simulators (GBM, Heston, local vol)
├── training/        # Training loops, PPO/A2C, custom losses
├── evaluation/      # Backtesting, BS comparison, metrics
├── data/            # Market data, option chains
└── utils/           # State building, normalisation, gradient checks
```

## Key Files

| File | Purpose |
|------|---------|
| `src/rl_deep_hedging/models/hedging_network.py` | Main hedging actor network |
| `src/rl_deep_hedging/simulation/gbm.py` | Differentiable GBM simulator |
| `src/rl_deep_hedging/training/trainer.py` | Training loop with CVaR loss |
| `src/rl_deep_hedging/evaluation/benchmark.py` | BS delta comparison |
| `src/rl_deep_hedging/utils/state.py` | `build_hedging_state()` |
| `db/schema.py` | Shared experiment DB |

## Current State

- **Active branch**: main
- **Next notebook**: NB22
- **Known issues**: none

## Project-Specific Patterns

### Training config
```python
@dataclass
class TrainingConfig:
    n_paths: int = 100_000
    n_steps: int = 50
    T: float = 1.0
    lr: float = 1e-3
    epochs: int = 200
    batch_size: int = 4096
    cvar_alpha: float = 0.5
    grad_clip: float = 1.0
    transaction_cost: float = 0.001
```

### Evaluation metrics (always report all)
```python
metrics = {
    "mean_pnl": float,
    "std_pnl": float,
    "sharpe": float,
    "cvar_50": float,
    "ratio_vs_bs": float,    # hedging cost vs BS delta hedging
    "delta_corr": float,     # correlation with BS delta
}
```

### Convergence diagnostic order
1. Check `delta_variability` — if < 0.01, network collapsed
2. Check grad norms — if > 100, exploding; if < 1e-6, vanishing
3. Check state feature magnitudes — must be O(1)
4. Only then adjust learning rate or architecture

## Do NOT

- Do not train without comparing against BS delta — every experiment logs `ratio_vs_bs`.
- Do not use raw (unnormalised) features as network input.
- Do not skip gradient health checks during training.
- Do not use non-differentiable path simulators for training (eval-only is fine).
- Do not start a new notebook without checking the current NB number in this file.
