# SKILL: Pricing

<!--
name: pricing
trigger: Pricing options, computing Greeks, Monte Carlo simulation, PDE solving, or implied vol calculation
depends-on: [vol-and-curves]
applies-to: [all]
-->

## When to Apply

Read before writing any option pricing, Greeks computation, Monte Carlo
simulation, PDE solver, or implied vol calculation code.

## Dependencies

- **vol-and-curves** — vol surfaces and rate curves feed into pricing.

## Rules

1. All pricing is custom-coded using `scipy.stats.norm` — no QuantLib or py_vollib.
2. Greeks use analytical formulas where available, bump-and-reprice otherwise.
3. Standard bump sizes: **1% spot**, **1% vol**, **1bp rate**, **1 day time**.
4. Monte Carlo minimum **100,000 paths** with antithetic variates for pricing.
5. Use the decision framework to choose analytical vs MC vs PDE.

## Patterns

### Decision Framework — When to Use What

| Situation | Method | Why |
|-----------|--------|-----|
| European vanilla (BS assumptions) | **Analytical** (Black-Scholes) | Exact, instant |
| European vanilla (stochastic vol) | **MC** or **FFT** | No closed-form |
| Path-dependent (lookback, barrier, Asian) | **Monte Carlo** | Handles any payoff |
| American / early exercise | **PDE finite difference** | Backward induction |
| Greeks for analytical models | **Analytical formulas** | Exact, fast |
| Greeks for exotic / custom models | **Bump-and-reprice** | Works for anything |

### Standard Packages

```
scipy.stats.norm    — BS pricing (CDF, PDF)
scipy.optimize      — implied vol (brentq)
scipy.sparse        — PDE tridiagonal solve
numpy               — path generation, array operations
torch               — differentiable simulation (deep learning)
```

No external pricing libraries. All pricing from scratch.

### Black-Scholes — Full Suite

```python
from scipy.stats import norm
import numpy as np

def bs_price(S, K, r, q, sigma, T, option_type="C"):
    """Black-Scholes price for European options."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "C":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def bs_delta(S, K, r, q, sigma, T, option_type="C"):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return np.exp(-q * T) * norm.cdf(d1) if option_type == "C" else np.exp(-q * T) * (norm.cdf(d1) - 1)


def bs_gamma(S, K, r, q, sigma, T):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))


def bs_vega(S, K, r, q, sigma, T):
    """Per 1% vol move."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) * 0.01


def bs_theta(S, K, r, q, sigma, T, option_type="C"):
    """Per calendar day."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    term1 = -S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
    if option_type == "C":
        term2 = q * S * np.exp(-q * T) * norm.cdf(d1) - r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        term2 = -q * S * np.exp(-q * T) * norm.cdf(-d1) + r * K * np.exp(-r * T) * norm.cdf(-d2)
    return (term1 + term2) / 365


def bs_implied_vol(price, S, K, r, q, T, option_type="C"):
    """Implied vol via Brent root finding."""
    from scipy.optimize import brentq
    try:
        return brentq(lambda sigma: bs_price(S, K, r, q, sigma, T, option_type) - price, 0.001, 5.0)
    except ValueError:
        return np.nan
```

### Greeks — Bump-and-Reprice

For exotics, custom models, or anything without closed-form Greeks.

```python
BUMP_SPOT = 0.01       # 1% relative
BUMP_VOL = 0.01        # 1% absolute (100 bps)
BUMP_RATE = 0.0001     # 1 bp absolute
BUMP_TIME = 1 / 365    # 1 calendar day


def numerical_greeks(pricer_fn, S, K, r, q, sigma, T, option_type="C"):
    """Central difference Greeks. Works with any pricer."""
    base = pricer_fn(S, K, r, q, sigma, T, option_type)
    dS = S * BUMP_SPOT

    delta = (pricer_fn(S + dS, K, r, q, sigma, T, option_type)
             - pricer_fn(S - dS, K, r, q, sigma, T, option_type)) / (2 * dS)

    gamma = (pricer_fn(S + dS, K, r, q, sigma, T, option_type)
             - 2 * base
             + pricer_fn(S - dS, K, r, q, sigma, T, option_type)) / (dS ** 2)

    vega = (pricer_fn(S, K, r, q, sigma + BUMP_VOL, T, option_type)
            - pricer_fn(S, K, r, q, sigma - BUMP_VOL, T, option_type)) / 2

    theta = (pricer_fn(S, K, r, q, sigma, T - BUMP_TIME, option_type) - base) if T > BUMP_TIME else 0.0

    rho = (pricer_fn(S, K, r + BUMP_RATE, q, sigma, T, option_type)
           - pricer_fn(S, K, r - BUMP_RATE, q, sigma, T, option_type)) / 2

    return {"price": base, "delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}
```

### Payoff Definitions

```python
# Standard European
def call_payoff(paths, K):
    return np.maximum(paths[:, -1] - K, 0)

def put_payoff(paths, K):
    return np.maximum(K - paths[:, -1], 0)

# Path-dependent
def lookback_call_payoff(paths):
    return paths[:, -1] - paths.min(axis=1)

def lookback_put_payoff(paths):
    return paths.max(axis=1) - paths[:, -1]

def asian_call_payoff(paths, K):
    return np.maximum(paths.mean(axis=1) - K, 0)

def barrier_call_payoff(paths, K, barrier, barrier_type="up-and-out"):
    """Barrier option payoff."""
    terminal = np.maximum(paths[:, -1] - K, 0)
    if barrier_type == "up-and-out":
        knocked = paths.max(axis=1) >= barrier
    elif barrier_type == "down-and-out":
        knocked = paths.min(axis=1) <= barrier
    else:
        raise ValueError(f"Unknown barrier type: {barrier_type}")
    return terminal * (~knocked)
```

### Monte Carlo — NumPy (Pricing)

```python
def simulate_gbm(S0, r, q, sigma, T, n_steps, n_paths, antithetic=True, seed=None):
    """GBM paths with antithetic variates. Returns (n_paths, n_steps+1)."""
    if seed is not None:
        np.random.seed(seed)
    dt = T / n_steps
    half = n_paths // 2 if antithetic else n_paths
    Z = np.random.standard_normal((half, n_steps))
    if antithetic:
        Z = np.concatenate([Z, -Z], axis=0)
    log_inc = (r - q - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    log_paths = np.zeros((len(Z), n_steps + 1))
    log_paths[:, 1:] = np.cumsum(log_inc, axis=1)
    return S0 * np.exp(log_paths)


def mc_price(payoff_fn, S0, r, q, sigma, T, n_steps=252, n_paths=100_000, seed=42):
    """MC pricing with confidence interval."""
    paths = simulate_gbm(S0, r, q, sigma, T, n_steps, n_paths, seed=seed)
    payoffs = payoff_fn(paths)
    disc = np.exp(-r * T) * payoffs
    se = disc.std() / np.sqrt(n_paths)
    return {"price": float(disc.mean()), "se": float(se),
            "ci_95": (float(disc.mean() - 1.96 * se), float(disc.mean() + 1.96 * se))}
```

### Monte Carlo — PyTorch (Differentiable)

Use when gradients need to flow through simulation (deep hedging, RL).

```python
import torch

def simulate_gbm_torch(S0, r, q, sigma, T, n_steps, n_paths, device="cpu"):
    """Reparameterised GBM — noise outside graph, gradients flow through S."""
    dt = T / n_steps
    eps = torch.randn(n_paths, n_steps, device=device)
    log_inc = (r - q - 0.5 * sigma**2) * dt + sigma * dt**0.5 * eps
    log_paths = torch.cat([
        torch.zeros(n_paths, 1, device=device),
        torch.cumsum(log_inc, dim=1)
    ], dim=1)
    return S0 * torch.exp(log_paths)
```

### PDE Finite Difference — Crank-Nicolson

```python
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve

def pde_price(S0, K, r, q, sigma, T, option_type="C", n_space=200, n_time=200):
    """Crank-Nicolson for European options. Extend for American exercise."""
    S_max = 3 * S0
    dS = S_max / n_space
    dt = T / n_time
    S = np.linspace(0, S_max, n_space + 1)
    V = np.maximum(S - K, 0) if option_type == "C" else np.maximum(K - S, 0)

    for t in range(n_time):
        j = np.arange(1, n_space)
        alpha = 0.25 * dt * (sigma**2 * j**2 - (r - q) * j)
        beta = -0.5 * dt * (sigma**2 * j**2 + r)
        gamma = 0.25 * dt * (sigma**2 * j**2 + (r - q) * j)

        A = diags([-alpha[1:], 1 - beta, -gamma[:-1]], [-1, 0, 1],
                  shape=(n_space - 1, n_space - 1), format="csc")
        B = diags([alpha[1:], 1 + beta, gamma[:-1]], [-1, 0, 1],
                  shape=(n_space - 1, n_space - 1), format="csc")

        rhs = B @ V[1:-1]
        if option_type == "C":
            rhs[-1] += gamma[-1] * (S_max - K * np.exp(-r * (T - t * dt)))
        else:
            rhs[0] += alpha[0] * (K * np.exp(-r * (T - t * dt)))

        V[1:-1] = spsolve(A, rhs)

    return float(np.interp(S0, S, V))
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Use QuantLib or py_vollib | Custom BS with `scipy.stats.norm` |
| Inconsistent bump sizes | 1% spot, 1% vol, 1bp rate, 1 day |
| MC with < 100k paths (pricing) | Minimum 100,000 with antithetic variates |
| MC without confidence interval | Always report price + SE + CI |
| PDE with pure explicit scheme | Use Crank-Nicolson (semi-implicit) |
| Hardcode payoffs inline | Use standard payoff functions |

## Checklist

- [ ] Decision framework followed (analytical vs MC vs PDE)
- [ ] BS uses `scipy.stats.norm`, includes dividend yield
- [ ] Greeks bump sizes match standard
- [ ] MC uses antithetic variates, >= 100k paths, reports CI
- [ ] PDE uses Crank-Nicolson
- [ ] Payoffs defined as reusable functions
