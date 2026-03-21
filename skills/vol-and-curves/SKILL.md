# SKILL: Volatility and Curves

<!--
name: vol-and-curves
trigger: Vol surface interpolation, rate curve building, volatility estimation, or time/day-count conventions
depends-on: [market-data]
applies-to: [all]
-->

## When to Apply

Read before interpolating vol surfaces, building yield curves, estimating
realized volatility, or handling time conventions. This skill standardises
how market surfaces and curves are constructed and queried.

## Dependencies

- **market-data** — raw data comes from the standard market data schema.

## Rules

1. Vol surfaces are interpolated in **log-moneyness x time** space — never raw strike x date.
2. Rate curves use **natural cubic spline** with flat extrapolation beyond range.
3. Time conventions: **252 trading days** for volatility, **365 days** for interest rates.
4. Always specify which volatility estimator you're using and why.
5. Vol surface interpolation method must be documented in the project's CLAUDE.md.
6. Discount factors use continuous compounding: `exp(-r * T)`.
7. Forward rates derived from: `(r_end * T_end - r_start * T_start) / (T_end - T_start)`.

## Patterns

### Time Conventions

```python
# Standard conventions — use these consistently across all projects
TRADING_DAYS_PER_YEAR = 252     # for volatility annualisation
CALENDAR_DAYS_PER_YEAR = 365    # for interest rates (ACT/365)

def trading_days_to_years(days: int) -> float:
    return days / TRADING_DAYS_PER_YEAR

def calendar_days_to_years(days: int) -> float:
    return days / CALENDAR_DAYS_PER_YEAR

# Tenor string to years
TENOR_MAP = {
    "1d": 1/365, "1w": 7/365,
    "1m": 1/12, "2m": 2/12, "3m": 3/12, "6m": 6/12,
    "9m": 9/12, "1y": 1.0, "18m": 1.5, "2y": 2.0,
    "3y": 3.0, "4y": 4.0, "5y": 5.0, "7y": 7.0,
    "10y": 10.0, "20y": 20.0, "30y": 30.0,
}

def tenor_to_years(tenor: str) -> float:
    tenor = tenor.lower().strip()
    if tenor in TENOR_MAP:
        return TENOR_MAP[tenor]
    raise ValueError(f"Unknown tenor: {tenor}")
```

### Vol Surface Interpolation

Always work in **log-moneyness** (ln(K/S)) for stability. Choose method
based on data density.

```python
import numpy as np
from scipy.interpolate import RectBivariateSpline, RBFInterpolator, RegularGridInterpolator

class VolSurfaceInterpolator:
    """Interpolate implied vol from a strike x expiry grid.

    Methods:
        'cubic'   — RectBivariateSpline (default, good for regular grids)
        'rbf'     — RBF with thin-plate spline (irregular grids, sparse data)
        'linear'  — RegularGridInterpolator (fast, simple)
    """

    def __init__(self, strikes, expiries, ivs, spot, method="cubic"):
        """
        Args:
            strikes: array of strikes
            expiries: array of expiry times (years)
            ivs: 2D array of implied vols (strikes x expiries)
            spot: current spot price
            method: interpolation method
        """
        self.spot = spot
        self.method = method

        # Convert to log-moneyness for stability
        self.log_moneyness = np.log(strikes / spot)
        self.expiries = np.array(expiries)
        self.ivs = np.array(ivs)

        if method == "cubic":
            self._interp = RectBivariateSpline(
                self.log_moneyness, self.expiries, self.ivs, kx=3, ky=3
            )
        elif method == "rbf":
            # Flatten for RBF (handles irregular grids)
            lm_grid, exp_grid = np.meshgrid(self.log_moneyness, self.expiries, indexing="ij")
            points = np.column_stack([lm_grid.ravel(), exp_grid.ravel()])
            self._interp = RBFInterpolator(points, self.ivs.ravel(), kernel="thin_plate_spline")
        elif method == "linear":
            self._interp = RegularGridInterpolator(
                (self.log_moneyness, self.expiries), self.ivs,
                method="linear", bounds_error=False, fill_value=None
            )

    def get_vol(self, strike: float, expiry: float) -> float:
        """Get interpolated implied vol for a strike and expiry."""
        lm = np.log(strike / self.spot)

        # Clamp to grid boundaries (flat extrapolation)
        lm = np.clip(lm, self.log_moneyness.min(), self.log_moneyness.max())
        expiry = np.clip(expiry, self.expiries.min(), self.expiries.max())

        if self.method == "cubic":
            return float(self._interp(lm, expiry)[0, 0])
        elif self.method == "rbf":
            return float(self._interp(np.array([[lm, expiry]]))[0])
        elif self.method == "linear":
            return float(self._interp(np.array([[lm, expiry]]))[0])

    def get_smile(self, expiry: float) -> tuple[np.ndarray, np.ndarray]:
        """Vol smile (IV vs strike) for a fixed expiry."""
        strikes = self.spot * np.exp(self.log_moneyness)
        ivs = np.array([self.get_vol(k, expiry) for k in strikes])
        return strikes, ivs

    def get_term_structure(self, strike: float) -> tuple[np.ndarray, np.ndarray]:
        """Term structure (IV vs expiry) for a fixed strike."""
        ivs = np.array([self.get_vol(strike, t) for t in self.expiries])
        return self.expiries, ivs
```

### When to Use Which Interpolation Method

| Method | Use when | Strengths | Weaknesses |
|--------|----------|-----------|------------|
| `cubic` (RectBivariateSpline) | Regular grid, dense data | Smooth, fast, well-behaved | Needs structured grid |
| `rbf` (RBFInterpolator) | Irregular/sparse data | Handles any point layout | Slower, can overshoot |
| `linear` (RegularGridInterpolator) | Quick lookups, simple needs | Fast, no surprises | Not smooth at grid edges |
| `ssvi` (parametric) | Arbitrage-free surfaces | Guaranteed no-arb | Needs calibration |

### Rate Curve Interpolation

```python
from scipy.interpolate import CubicSpline

class RateCurveInterpolator:
    """Interpolate risk-free rates from tenor points.

    Uses natural cubic spline with flat extrapolation.
    """

    def __init__(self, tenors_years: list[float], rates: list[float]):
        self.tenors = np.array(tenors_years)
        self.rates = np.array(rates)
        self._spline = CubicSpline(self.tenors, self.rates, bc_type="natural")

    def get_rate(self, T: float) -> float:
        """Interpolated rate for maturity T (years). Flat extrapolation."""
        T = np.clip(T, self.tenors.min(), self.tenors.max())
        return float(self._spline(T))

    def discount_factor(self, T: float) -> float:
        """Continuous compounding discount factor."""
        return np.exp(-self.get_rate(T) * T)

    def forward_rate(self, T1: float, T2: float) -> float:
        """Forward rate between T1 and T2."""
        r1, r2 = self.get_rate(T1), self.get_rate(T2)
        return (r2 * T2 - r1 * T1) / (T2 - T1)

    def get_curve(self, tenors: list[float] = None) -> tuple[np.ndarray, np.ndarray]:
        """Full rate curve at specified tenors."""
        if tenors is None:
            tenors = np.linspace(self.tenors.min(), self.tenors.max(), 100)
        rates = np.array([self.get_rate(t) for t in tenors])
        return np.array(tenors), rates
```

### Volatility Estimators

Five standard estimators. Choose based on data availability.

```python
import numpy as np
import pandas as pd

def realized_vol(returns: np.ndarray, annualise: int = 252) -> float:
    """Realized volatility from intraday or daily returns."""
    return np.sqrt(np.sum(returns**2)) * np.sqrt(annualise / len(returns))


def parkinson_vol(high: np.ndarray, low: np.ndarray, annualise: int = 252) -> float:
    """Parkinson (1980) — uses high-low range. ~2x more efficient than close-to-close.
    Best when: you have high/low data but no open."""
    n = len(high)
    return np.sqrt(annualise / (4 * n * np.log(2)) * np.sum(np.log(high / low)**2))


def garman_klass_vol(open: np.ndarray, high: np.ndarray, low: np.ndarray,
                     close: np.ndarray, annualise: int = 252) -> float:
    """Garman-Klass (1980) — uses OHLC. ~7.4x more efficient than close-to-close.
    Best when: you have full OHLC data, no overnight gaps."""
    n = len(close)
    hl = np.log(high / low)**2
    co = np.log(close / open)**2
    return np.sqrt(annualise / n * np.sum(0.5 * hl - (2 * np.log(2) - 1) * co))


def rogers_satchell_vol(open: np.ndarray, high: np.ndarray, low: np.ndarray,
                        close: np.ndarray, annualise: int = 252) -> float:
    """Rogers-Satchell (1991) — drift-independent. Works for trending markets.
    Best when: asset has significant drift/trend."""
    n = len(close)
    rs = np.log(high / close) * np.log(high / open) + np.log(low / close) * np.log(low / open)
    return np.sqrt(annualise / n * np.sum(rs))


def yang_zhang_vol(open: np.ndarray, high: np.ndarray, low: np.ndarray,
                   close: np.ndarray, window: int = 20, annualise: int = 252) -> float:
    """Yang-Zhang (2000) — accounts for overnight gaps. Most accurate overall.
    Best when: market has trading breaks (equities, futures)."""
    n = len(close)
    k = 0.34 / (1.34 + (window + 1) / (window - 1))

    # Overnight variance
    log_oc = np.log(open[1:] / close[:-1])
    overnight_var = np.var(log_oc, ddof=1)

    # Open-to-close variance
    log_co = np.log(close / open)
    open_var = np.var(log_co, ddof=1)

    # Rogers-Satchell variance
    rs = np.log(high / close) * np.log(high / open) + np.log(low / close) * np.log(low / open)
    rs_var = np.mean(rs)

    variance = overnight_var + k * open_var + (1 - k) * rs_var
    return np.sqrt(variance * annualise)
```

### When to Use Which Estimator

| Estimator | Data needed | Best for | Efficiency vs close-to-close |
|-----------|-------------|----------|------------------------------|
| **Realized vol** | Intraday returns | High-frequency data available | Gold standard |
| **Parkinson** | High, Low | No open price available | ~2x |
| **Garman-Klass** | OHLC | Full daily bars, no gaps | ~7.4x |
| **Rogers-Satchell** | OHLC | Trending/drifting markets | Good with drift |
| **Yang-Zhang** | OHLC + prev close | Markets with overnight gaps (equities) | Most accurate overall |

### SSVI Parametric Vol Surface

For arbitrage-free surfaces when calibrated parameters are available.

```python
def ssvi_implied_vol(log_moneyness: float, theta: float, rho: float, beta: float) -> float:
    """SSVI (Gatheral & Jacquier) — parametric arbitrage-free vol surface.

    Args:
        log_moneyness: ln(K/F) where F is forward price
        theta: ATM total variance
        rho: correlation parameter (-1, 1)
        beta: power-law parameter (>0)
    """
    phi = beta / theta  # mixing function
    w = 0.5 * theta * (1 + rho * phi * log_moneyness
                        + np.sqrt((phi * log_moneyness + rho)**2 + (1 - rho**2)))
    return np.sqrt(w)  # total implied vol
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Interpolate in raw strike space | Use log-moneyness: `ln(K/S)` |
| Use 365 days for vol annualisation | 252 trading days for vol |
| Use 252 days for rate conventions | 365 days (ACT/365) for rates |
| Linear interpolation for rate curves | Natural cubic spline with flat extrapolation |
| Mix up estimators without documenting | Always state which estimator and why |
| Extrapolate beyond grid without clamping | Flat extrapolation (clamp to boundary) |
| Hardcode tenor-to-years conversions | Use `TENOR_MAP` / `tenor_to_years()` |

## Checklist

- [ ] Vol surface interpolated in log-moneyness x time space
- [ ] Interpolation method documented in CLAUDE.md
- [ ] Rate curve uses natural cubic spline
- [ ] Time conventions correct: 252 for vol, 365 for rates
- [ ] Volatility estimator chosen and documented
- [ ] Flat extrapolation at surface/curve boundaries
- [ ] Discount factors use continuous compounding
- [ ] Tenor conversions use standard `TENOR_MAP`
