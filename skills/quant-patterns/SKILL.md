# SKILL: Quant Finance Patterns

<!--
name: quant-patterns
trigger: Calibrating models to market data, normalising features for ML, or diagnosing training convergence
depends-on: [pricing, experiment-logging]
applies-to: [all]
-->

## When to Apply

Read before calibrating a model to market data, preparing market features
for neural networks, or diagnosing convergence issues in deep learning
models applied to finance.

## Dependencies

- **pricing** — calibration targets prices/IVs produced by pricing models.
- **experiment-logging** — calibration results are logged.

## Rules

1. Calibration uses `scipy.optimize` and always returns `CalibrationResult`.
2. Use `minimize_scalar` for 1D, `minimize` with L-BFGS-B for multi-parameter.
3. Always log calibration results via `log_experiment()`.
4. Neural network features must be normalised to O(1).
5. Follow convergence diagnostic order before tuning hyperparameters.

## Patterns

### Calibration — Standard Interface

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from scipy.optimize import minimize, minimize_scalar

@dataclass
class CalibrationResult:
    params: dict
    rmse: float
    converged: bool
    method: str = ""
    n_iterations: int = 0


class Calibratable(ABC):
    """Base class for any model that can be calibrated to market data."""

    @abstractmethod
    def price(self, S, K, T, r, **params) -> np.ndarray: ...

    @abstractmethod
    def calibrate(self, market_prices, strikes, expiries, S, r) -> CalibrationResult: ...

    def rmse(self, market, model):
        return float(np.sqrt(np.mean((market - model) ** 2)))
```

### 1D Calibration (e.g. constant vol)

```python
def calibrate_constant_vol(market_prices, S, K, T, r, q, option_type="C"):
    from pricing import bs_price
    result = minimize_scalar(
        lambda sigma: np.sum((bs_price(S, K, r, q, sigma, T, option_type) - market_prices) ** 2),
        bounds=(0.01, 2.0),
        method="bounded",
    )
    return CalibrationResult(
        params={"sigma": result.x},
        rmse=np.sqrt(result.fun / len(market_prices)),
        converged=result.success,
        method="minimize_scalar (bounded)",
    )
```

### Multi-Parameter Calibration (e.g. Heston)

```python
def calibrate_heston(market_prices, S, K, T, r, q):
    bounds = [
        (0.1, 10.0),     # kappa
        (0.01, 1.0),     # theta
        (0.01, 2.0),     # sigma_v
        (-0.99, 0.99),   # rho
        (0.01, 1.0),     # v0
    ]

    def objective(params):
        kappa, theta, sigma_v, rho, v0 = params
        model_prices = heston_price(S, K, r, q, T, kappa, theta, sigma_v, rho, v0)
        return np.sum((market_prices - model_prices) ** 2)

    x0 = [2.0, 0.04, 0.3, -0.7, 0.04]
    result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)

    params = dict(zip(["kappa", "theta", "sigma_v", "rho", "v0"], result.x))
    return CalibrationResult(
        params=params,
        rmse=np.sqrt(result.fun / len(market_prices)),
        converged=result.success,
        method="L-BFGS-B",
    )
```

### Always Log Calibration Results

```python
def calibrate_and_log(calibrator, market_data, project_name):
    """Calibrate and log the result in one step."""
    result = calibrator.calibrate(**market_data)

    from db.schema import log_experiment
    log_experiment(
        project=project_name,
        experiment_type="calibration",
        metrics={"rmse": result.rmse, "converged": int(result.converged)},
        hyperparams=result.params,
        notes=result.method,
    )

    return result
```

### State Normalisation (for ML/RL)

All features must be O(1) before feeding to neural networks.

```python
import torch

def normalise_state(S, K, tau, T, sigma, running_pnl, delta, S0):
    """Normalise market features to O(1) for neural network input."""
    return torch.stack([
        torch.log(S / K),           # log-moneyness
        tau / T,                    # normalised time to maturity [0,1]
        running_pnl / (S0 * 0.1),  # PnL normalised by 10% of spot
        delta,                      # already [0,1]
        S / S0 - 1.0,              # return from initial spot
        torch.full_like(S, sigma), # vol feature
    ], dim=-1)
```

### Convergence Diagnostics

Check in this order before adjusting hyperparameters:

1. **Delta variability** < 0.01 — network collapsed — reduce LR, use LayerNorm
2. **Grad norms** > 100 — explosion — clip gradients
3. **Grad norms** < 1e-6 — vanishing — check loss function
4. **State values** >> O(1) — fix normalisation
5. Only then: adjust LR or architecture

```python
def check_gradient_health(model):
    """Run during training to diagnose issues."""
    norms = {n: p.grad.norm().item()
             for n, p in model.named_parameters() if p.grad is not None}
    total = sum(norms.values())

    status = "ok"
    advice = ""
    if total > 100:
        status = "EXPLODING"
        advice = "Enable gradient clipping (clipnorm=1.0)"
    elif total < 1e-6:
        status = "VANISHING"
        advice = "Check loss function, increase LR, or add skip connections"
    elif total < 0.01:
        status = "LOW"
        advice = "Network may be collapsing — try LayerNorm, reduce LR"

    return {"total_norm": total, "status": status, "advice": advice, "per_layer": norms}


def check_delta_health(deltas: torch.Tensor):
    """Check if hedging network output is collapsing to a constant."""
    variability = deltas.std().item()
    if variability < 0.01:
        return {"status": "COLLAPSED", "variability": variability,
                "advice": "Delta output is nearly constant — reduce LR, add LayerNorm, check entropy bonus"}
    return {"status": "ok", "variability": variability}
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Ad-hoc calibration output | Always return `CalibrationResult` |
| Calibrate without logging | Always `log_experiment()` |
| Raw market features into neural networks | Normalise to O(1) via `normalise_state()` |
| Tune hyperparams before checking gradients | Follow convergence diagnostic order |
| Use gradient descent for 1D calibration | `minimize_scalar` with bounds |

## Checklist

- [ ] Calibration returns `CalibrationResult` dataclass
- [ ] Calibration uses `scipy.optimize` (minimize_scalar / minimize with L-BFGS-B)
- [ ] Calibration result logged via `log_experiment()`
- [ ] Neural network features normalised to O(1)
- [ ] Convergence diagnostics checked in order before tuning
