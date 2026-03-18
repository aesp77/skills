# SKILL: Quant Finance Patterns

## Trigger
Read before any quant finance code — pricing, calibration, backtesting, path simulation.

---

## Differentiable GBM Simulation

```python
import torch

def simulate_gbm(S0, mu, sigma, T, n_steps, n_paths, device="cpu"):
    """
    Reparameterised GBM. Noise outside graph — gradients flow through S.
    Returns (n_paths, n_steps+1).
    """
    dt = T / n_steps
    eps = torch.randn(n_paths, n_steps, device=device)   # outside graph
    log_inc = (mu - 0.5*sigma**2)*dt + sigma*dt**0.5*eps
    log_paths = torch.cat([
        torch.zeros(n_paths, 1, device=device),
        torch.cumsum(log_inc, dim=1)
    ], dim=1)
    return S0 * torch.exp(log_paths)
```

---

## State Normalisation

```python
def build_hedging_state(S, K, tau, T, sigma, running_pnl, delta, S0):
    """All features O(1) after normalisation."""
    return torch.stack([
        torch.log(S / K),           # log-moneyness
        tau / T,                    # normalised ttm [0,1]
        running_pnl / (S0 * 0.1),  # PnL normalised by 10% of spot
        delta,                      # already [0,1]
        S / S0 - 1.0,              # return from initial spot
        torch.full_like(S, sigma), # vol feature
    ], dim=-1)
```

---

## Risk Measures

```python
def cvar_loss(pnl: torch.Tensor, alpha: float = 0.5) -> torch.Tensor:
    """CVaR_alpha. Minimise expected loss in worst alpha-fraction."""
    sorted_pnl = torch.sort(pnl)[0]
    cutoff = max(1, int(alpha * pnl.shape[0]))
    return -sorted_pnl[:cutoff].mean()

def exponential_utility_loss(pnl: torch.Tensor, lam: float = 0.1) -> torch.Tensor:
    """CARA utility. Smoother gradients. Use lam=0.1 to start."""
    return -torch.mean(-torch.exp(-lam * pnl))
```

---

## Black-Scholes Reference

```python
from scipy.stats import norm
import numpy as np

def bs_call_price(S, K, r, q, sigma, T):
    d1 = (np.log(S/K) + (r - q + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return S*np.exp(-q*T)*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)

def bs_delta(S, K, r, q, sigma, T):
    """The benchmark all deep hedging must beat (with TC enabled)."""
    d1 = (np.log(S/K) + (r - q + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return np.exp(-q*T) * norm.cdf(d1)
```

---

## Calibration Pattern

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

@dataclass
class CalibrationResult:
    params: dict
    rmse: float
    converged: bool

class VolModel(ABC):
    @abstractmethod
    def price(self, S, K, T, r) -> np.ndarray: ...
    @abstractmethod
    def calibrate(self, market_ivs, strikes, expiries) -> CalibrationResult: ...

    def rmse(self, market_ivs, model_ivs):
        return float(np.sqrt(np.mean((market_ivs - model_ivs)**2)))
```

---

## Backtesting Pattern

```python
from dataclasses import dataclass, field
import pandas as pd

@dataclass
class BacktestConfig:
    start_date: str
    end_date: str
    instrument: str
    transaction_cost: float = 0.001

@dataclass
class BacktestResult:
    pnl_series: pd.Series
    sharpe: float
    max_drawdown: float

def run_backtest(strategy, config: BacktestConfig) -> BacktestResult:
    result = BacktestResult(...)
    from db.schema import log_experiment
    log_experiment("backtest", config.instrument,
                   {"sharpe": result.sharpe}, {"tc": config.transaction_cost})
    return result
```

---

## Convergence Diagnostics (check in this order)

1. `delta_variability` < 0.01 → collapsed → reduce LR, use LayerNorm
2. Grad norms > 100 → explosion → clip already in trainer
3. Grad norms < 1e-6 → vanishing → check loss function
4. State values >> O(1) → fix normalisation
5. Only then: adjust LR

```python
def check_gradient_health(model):
    norms = {n: p.grad.norm().item()
             for n, p in model.named_parameters() if p.grad is not None}
    total = sum(norms.values())
    return {"total": total, "status": "ok" if 0.01 < total < 100 else "WARNING"}
```
