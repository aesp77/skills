# SKILL: Backtesting

<!--
name: backtesting
trigger: Strategy evaluation, walk-forward testing, risk measurement, hedging comparison, or P&L analysis
depends-on: [quant-patterns, experiment-logging]
applies-to: [all]
-->

## When to Apply

Read before evaluating any strategy, running a backtest, computing risk
metrics, or comparing hedging approaches. This skill standardises how
strategies are tested, measured, and compared.

## Dependencies

- **quant-patterns** — pricing and Greeks used within strategies.
- **experiment-logging** — all backtest results are logged.

## Rules

1. Always use **walk-forward** testing — never in-sample evaluation.
2. Always compare against a **benchmark** (BS delta, buy-and-hold, etc.).
3. Always report the **standard risk metrics**: Sharpe, CVaR, max drawdown.
4. Transaction costs are **always included** — default 5 bps proportional.
5. Log every backtest result via `log_experiment()`.
6. Use the same data split for strategy and benchmark — fair comparison.
7. Never optimise on the test set — parameter tuning uses the training window only.

## Patterns

### Walk-Forward Framework

```
Data timeline:
|----train----|---test---|  step  |----train----|---test---|
|    252 days  |  63 days |  21d  |    252 days  |  63 days |  ...

Default windows:
  train:  252 trading days (~1 year)
  test:    63 trading days (~3 months)
  step:    21 trading days (~1 month)
```

```python
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

@dataclass
class BacktestConfig:
    train_window: int = 252     # trading days
    test_window: int = 63       # trading days
    step_size: int = 21         # trading days
    tc_rate: float = 0.0005     # 5 bps proportional
    benchmark_name: str = ""    # name of benchmark strategy


@dataclass
class BacktestResult:
    strategy_pnl: np.ndarray
    benchmark_pnl: np.ndarray
    strategy_metrics: dict
    benchmark_metrics: dict
    config: BacktestConfig
    n_windows: int = 0


def walk_forward(strategy_fn, benchmark_fn, data, config: BacktestConfig) -> BacktestResult:
    """Walk-forward backtest with rolling train/test windows.

    Args:
        strategy_fn(train_data) -> callable that takes test_data and returns pnl array
        benchmark_fn(test_data) -> pnl array (no training needed)
        data: full dataset (DataFrame or array)
        config: backtest configuration
    """
    all_strategy_pnl = []
    all_benchmark_pnl = []
    n = len(data)
    n_windows = 0

    start = 0
    while start + config.train_window + config.test_window <= n:
        train_end = start + config.train_window
        test_end = train_end + config.test_window

        train_data = data[start:train_end]
        test_data = data[train_end:test_end]

        # Train strategy on training window, evaluate on test window
        trained = strategy_fn(train_data)
        strategy_pnl = trained(test_data, tc_rate=config.tc_rate)
        benchmark_pnl = benchmark_fn(test_data, tc_rate=config.tc_rate)

        all_strategy_pnl.extend(strategy_pnl)
        all_benchmark_pnl.extend(benchmark_pnl)
        n_windows += 1

        start += config.step_size

    s_pnl = np.array(all_strategy_pnl)
    b_pnl = np.array(all_benchmark_pnl)

    result = BacktestResult(
        strategy_pnl=s_pnl,
        benchmark_pnl=b_pnl,
        strategy_metrics=risk_report(s_pnl),
        benchmark_metrics=risk_report(b_pnl),
        config=config,
        n_windows=n_windows,
    )

    # Log to experiment DB
    from db.schema import log_experiment
    log_experiment(
        project="backtest",
        experiment_type="walk_forward",
        metrics=result.strategy_metrics,
        hyperparams={
            "train_window": config.train_window,
            "test_window": config.test_window,
            "step_size": config.step_size,
            "tc_rate": config.tc_rate,
            "benchmark": config.benchmark_name,
            "n_windows": n_windows,
        },
    )

    return result
```

### Risk Metrics — Standard Report

Always compute all of these. Never pick and choose.

```python
import numpy as np

def sharpe_ratio(pnl: np.ndarray) -> float:
    """Sharpe ratio of P&L series."""
    return pnl.mean() / pnl.std() if pnl.std() > 0 else 0.0


def max_drawdown(cumulative_pnl: np.ndarray) -> float:
    """Maximum drawdown from peak."""
    running_max = np.maximum.accumulate(cumulative_pnl)
    drawdown = running_max - cumulative_pnl
    return float(drawdown.max())


def cvar(pnl: np.ndarray, alpha: float = 0.05) -> float:
    """Conditional Value at Risk — expected loss in worst alpha fraction."""
    sorted_pnl = np.sort(pnl)
    cutoff = max(1, int(alpha * len(pnl)))
    return float(-sorted_pnl[:cutoff].mean())


def var(pnl: np.ndarray, alpha: float = 0.05) -> float:
    """Value at Risk at alpha confidence level."""
    return float(-np.percentile(pnl, alpha * 100))


def risk_report(pnl: np.ndarray) -> dict:
    """Standard risk report — run on every backtest."""
    cum_pnl = np.cumsum(pnl)
    report = {
        "mean_pnl": float(pnl.mean()),
        "std_pnl": float(pnl.std()),
        "sharpe": sharpe_ratio(pnl),
        "max_drawdown": max_drawdown(cum_pnl),
        "var_5": var(pnl, 0.05),
        "cvar_5": cvar(pnl, 0.05),
        "min_pnl": float(pnl.min()),
        "max_pnl": float(pnl.max()),
        "total_pnl": float(cum_pnl[-1]),
        "n_observations": len(pnl),
    }

    print(f"\n  Risk Report:")
    for k, v in report.items():
        if isinstance(v, float):
            print(f"    {k:20s}: {v:>12.4f}")
        else:
            print(f"    {k:20s}: {v:>12}")
    return report
```

### Transaction Costs

```python
DEFAULT_TC_RATE = 0.0005  # 5 bps proportional

def transaction_cost(delta_old: float, delta_new: float, spot: float,
                     notional: float = 1.0, tc_rate: float = DEFAULT_TC_RATE) -> float:
    """Proportional transaction cost on delta rebalancing."""
    return tc_rate * abs(delta_new - delta_old) * spot * notional


def apply_tc_to_pnl(pnl_gross: np.ndarray, deltas: np.ndarray,
                     spots: np.ndarray, tc_rate: float = DEFAULT_TC_RATE) -> np.ndarray:
    """Subtract transaction costs from gross P&L series."""
    delta_changes = np.abs(np.diff(deltas, prepend=0))
    costs = tc_rate * delta_changes * spots
    return pnl_gross - costs
```

### Option Strategy Evaluation — Point-to-Point

For evaluating option strategies (spreads, straddles, etc.):

```python
@dataclass
class OptionTrade:
    entry_date: str
    exit_date: str
    option_type: str            # 'C' or 'P'
    strike: float
    expiry: str
    direction: int              # +1 long, -1 short
    entry_price: float = 0.0
    exit_price: float = 0.0
    notional: float = 1.0


def evaluate_option_strategy(trades: list[OptionTrade], tc_rate: float = DEFAULT_TC_RATE) -> dict:
    """Evaluate an option strategy by comparing entry to exit.

    P&L = direction * (exit_price - entry_price) * notional - transaction_costs
    """
    total_pnl = 0.0
    total_tc = 0.0
    trade_results = []

    for trade in trades:
        gross_pnl = trade.direction * (trade.exit_price - trade.entry_price) * trade.notional
        tc = tc_rate * (trade.entry_price + trade.exit_price) * trade.notional
        net_pnl = gross_pnl - tc

        trade_results.append({
            "strike": trade.strike,
            "type": trade.option_type,
            "direction": "long" if trade.direction > 0 else "short",
            "gross_pnl": gross_pnl,
            "tc": tc,
            "net_pnl": net_pnl,
        })
        total_pnl += net_pnl
        total_tc += tc

    return {
        "total_pnl": total_pnl,
        "total_tc": total_tc,
        "n_trades": len(trades),
        "trades": trade_results,
    }
```

### Hedging Strategy Comparison

```python
def compare_hedging(strategy_deltas, benchmark_deltas, paths, option_payoffs,
                    option_premium, tc_rate=DEFAULT_TC_RATE):
    """Compare two hedging strategies on the same paths.

    P&L = premium + sum(delta_t * dS_t) - payoff - transaction_costs

    Args:
        strategy_deltas: (n_paths, n_steps) strategy hedge ratios
        benchmark_deltas: (n_paths, n_steps) benchmark hedge ratios (e.g. BS delta)
        paths: (n_paths, n_steps+1) spot price paths
        option_payoffs: (n_paths,) option payoff at maturity
        option_premium: float, option premium received
    """
    dS = np.diff(paths, axis=1)  # price changes

    def compute_pnl(deltas):
        hedge_pnl = np.sum(deltas * dS, axis=1)
        tc = tc_rate * np.sum(np.abs(np.diff(deltas, axis=1, prepend=0)) * paths[:, :-1], axis=1)
        return option_premium + hedge_pnl - option_payoffs - tc

    strategy_pnl = compute_pnl(strategy_deltas)
    benchmark_pnl = compute_pnl(benchmark_deltas)

    print(f"\n{'':30s} {'Strategy':>12s} {'Benchmark':>12s}")
    print(f"  {'='*54}")

    s_metrics = risk_report(strategy_pnl)
    b_metrics = risk_report(benchmark_pnl)

    # Improvement ratio
    if b_metrics["std_pnl"] > 0:
        improvement = 1 - s_metrics["std_pnl"] / b_metrics["std_pnl"]
        print(f"\n  Hedging cost reduction vs benchmark: {improvement*100:.1f}%")

    return {
        "strategy": s_metrics,
        "benchmark": b_metrics,
        "improvement_pct": improvement * 100 if b_metrics["std_pnl"] > 0 else 0,
    }
```

### Deep Hedging Loss Functions

For training neural network hedging policies.

```python
import torch

def exponential_utility_loss(pnl: torch.Tensor, lam: float = 0.1) -> torch.Tensor:
    """CARA utility — risk-averse, unbounded gradient on large losses.
    Default starting point for deep hedging. Adjust lam for risk aversion."""
    return -torch.mean(-torch.exp(-lam * pnl))


def cvar_loss(pnl: torch.Tensor, alpha: float = 0.05) -> torch.Tensor:
    """CVaR loss — focuses on worst alpha fraction of outcomes.
    Use for tail-risk optimisation."""
    sorted_pnl = torch.sort(pnl)[0]
    cutoff = max(1, int(alpha * pnl.shape[0]))
    return -sorted_pnl[:cutoff].mean()


def combined_loss(pnl: torch.Tensor, lam: float = 0.1, alpha: float = 0.05,
                  weight_utility: float = 0.7) -> torch.Tensor:
    """Combined exponential utility + CVaR — balances average vs tail risk."""
    return weight_utility * exponential_utility_loss(pnl, lam) + (1 - weight_utility) * cvar_loss(pnl, alpha)
```

### Backtest Visualization

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_backtest_results(result: BacktestResult, title: str = "Backtest Results"):
    """Standard backtest visualization — cumulative P&L and drawdown."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Cumulative P&L", "Drawdown"],
                        vertical_spacing=0.1)

    cum_strat = np.cumsum(result.strategy_pnl)
    cum_bench = np.cumsum(result.benchmark_pnl)

    # Cumulative P&L
    fig.add_trace(go.Scatter(y=cum_strat, name="Strategy", mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(y=cum_bench, name="Benchmark", mode="lines",
                             line=dict(dash="dash")), row=1, col=1)

    # Drawdown
    running_max = np.maximum.accumulate(cum_strat)
    dd = running_max - cum_strat
    fig.add_trace(go.Scatter(y=-dd, name="Drawdown", fill="tozeroy",
                             line=dict(color="red")), row=2, col=1)

    fig.update_layout(height=600, title_text=title)
    return fig


def plot_pnl_distribution(result: BacktestResult, title: str = "P&L Distribution"):
    """P&L histogram with VaR and CVaR markers."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=result.strategy_pnl, name="Strategy", opacity=0.7, nbinsx=50))
    fig.add_trace(go.Histogram(x=result.benchmark_pnl, name="Benchmark", opacity=0.5, nbinsx=50))

    # VaR and CVaR lines
    var5 = -result.strategy_metrics["var_5"]
    cvar5 = -result.strategy_metrics["cvar_5"]
    fig.add_vline(x=var5, line_dash="dash", line_color="orange",
                  annotation_text=f"VaR 5%: {var5:.4f}")
    fig.add_vline(x=cvar5, line_dash="dash", line_color="red",
                  annotation_text=f"CVaR 5%: {cvar5:.4f}")

    fig.update_layout(barmode="overlay", title=title)
    return fig
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| In-sample evaluation | Walk-forward with train/test split |
| Backtest without benchmark | Always compare against a baseline |
| Report only Sharpe | Full `risk_report()`: Sharpe, CVaR, VaR, max drawdown |
| Ignore transaction costs | Always apply TC (default 5 bps) |
| Optimise on test set | Parameter tuning in training window only |
| Skip logging results | `log_experiment()` for every backtest |
| P&L without confidence intervals | Report mean +/- std, or percentiles |
| Compare strategies on different data | Same paths, same split, fair comparison |

## Checklist

- [ ] Walk-forward testing with rolling windows (not in-sample)
- [ ] Benchmark strategy evaluated on same data
- [ ] Transaction costs applied (default 5 bps)
- [ ] Full risk report: Sharpe, CVaR, VaR, max drawdown, total P&L
- [ ] Results logged via `log_experiment()`
- [ ] P&L distribution visualised
- [ ] Cumulative P&L and drawdown plotted
- [ ] Improvement vs benchmark quantified
