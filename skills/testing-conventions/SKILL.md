# SKILL: Testing Conventions

<!--
name: testing-conventions
trigger: Writing tests, adding test infrastructure, or validating code
depends-on: [project-scaffold, keras3-pytorch]
applies-to: [all]
-->

## When to Apply

Read before writing any tests. This skill defines where tests go, how they're
written, and how much testing is appropriate at each stage of development.

## Dependencies

- **project-scaffold** — tests live in the standard `tests/` directory.
- **keras3-pytorch** — model tests need the correct backend setup.

## Rules

1. **All test files go in `tests/`** — never create test files anywhere else (not in `src/`, not in project root, not next to the code).
2. Use `pytest` — never `unittest.TestCase`. Plain functions with `assert`.
3. Match testing intensity to the development stage (see stages below).
4. `conftest.py` at `tests/` root for shared fixtures.
5. Set `KERAS_BACKEND=torch` in `conftest.py` before any keras import.
6. Never mock the database — use a real temporary SQLite via `tmp_path`.
7. Clean up after yourself — no temp files left behind after tests run.

## Patterns

### Testing Stages — Match Intensity to Development Phase

#### Stage 1: Notebook Exploration
**No formal tests.** The notebook is the test. You're experimenting.
Don't write test files for notebook code.

#### Stage 2: Extracted Module (Prototype)
**Smoke tests only.** Verify it runs and produces sensible output.
One test file, a few quick checks. This is the minimum before using
the module in other code.

```python
# tests/test_encoder.py — smoke test for a prototype module
def test_encoder_runs():
    """Does it run without crashing?"""
    from src.project_name.models.encoder import VolSurfaceEncoder, EncoderConfig
    config = EncoderConfig(input_dim=10, latent_dim=3)
    model = VolSurfaceEncoder(config)
    x = torch.randn(8, 10)
    out = model(x, training=False)
    assert out.shape == (8, 3)


def test_encoder_output_finite():
    """No NaN or Inf in output?"""
    ...
    assert torch.isfinite(out).all()
```

#### Stage 3: Production Code
**Full test suite.** Unit tests, integration tests, property-based tests.
This is required before the code is relied upon. Target: **80%+ coverage**.

```
tests/
├── conftest.py              # shared fixtures, backend setup
├── unit/
│   ├── test_models.py       # model architecture, output shapes
│   ├── test_pricing.py      # BS, MC, Greeks correctness
│   ├── test_data.py         # data loading, transformations
│   └── test_utils.py        # utility functions
└── integration/
    ├── test_db.py            # database round-trip
    ├── test_pipeline.py      # end-to-end data pipeline
    └── test_training.py      # training loop runs and converges
```

### Where Tests Go — Never Outside `tests/`

```
project-root/
├── src/
│   └── project_name/
│       ├── models/
│       │   └── encoder.py          # code lives here
│       └── data/
│           └── loader.py           # code lives here
├── tests/                          # ALL tests live here
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_encoder.py         # tests for encoder.py
│   │   └── test_loader.py          # tests for loader.py
│   └── integration/
│       └── test_pipeline.py
└── notebooks/                      # NO test files here
```

**Naming convention:** `test_<module_name>.py` — mirrors the module it tests.

### conftest.py — Shared Fixtures

```python
import os
os.environ["KERAS_BACKEND"] = "torch"

import pytest
import sqlite3
import torch
from pathlib import Path


@pytest.fixture
def device():
    """Use GPU if available, else CPU."""
    return "cuda" if torch.cuda.is_available() else "cpu"


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary SQLite database with standard schema.
    Automatically cleaned up after the test — no temp files left."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    # Add your schema here
    yield db_path
    conn.close()
```

### Writing Tests — pytest Basics

pytest is simpler than unittest. No classes needed. Just functions with `assert`.

```python
# unittest style (DON'T USE)
import unittest
class TestEncoder(unittest.TestCase):
    def setUp(self):
        self.model = ...
    def test_output_shape(self):
        self.assertEqual(out.shape, (8, 3))

# pytest style (USE THIS)
def test_encoder_output_shape():
    model = ...
    out = model(x, training=False)
    assert out.shape == (8, 3)
```

**Why pytest:**
- Less boilerplate — no classes, no `self`, no `setUp`/`tearDown`
- Better error messages — shows the actual values on failure
- `tmp_path` fixture — automatic temp directory, cleaned up after each test
- Plugins: `hypothesis`, `pytest-cov`, `pytest-xdist` for parallel runs
- Runs unittest tests too if you have legacy ones

### Unit Tests — Fast, Isolated

Test individual functions and classes. Should run in seconds.

```python
# tests/unit/test_pricing.py
import numpy as np

def test_bs_call_put_parity():
    """Call - Put = S*exp(-qT) - K*exp(-rT)"""
    from src.project_name.pricing import bs_price
    S, K, r, q, sigma, T = 100, 100, 0.05, 0.02, 0.2, 1.0
    call = bs_price(S, K, r, q, sigma, T, "C")
    put = bs_price(S, K, r, q, sigma, T, "P")
    parity = S * np.exp(-q * T) - K * np.exp(-r * T)
    assert abs(call - put - parity) < 1e-10


def test_bs_delta_bounded():
    """Call delta must be in [0, 1]."""
    from src.project_name.pricing import bs_delta
    delta = bs_delta(100, 100, 0.05, 0.02, 0.2, 1.0, "C")
    assert 0 <= delta <= 1
```

### Integration Tests — Slower, Real Dependencies

Test components working together. Use real databases (not mocks).

```python
# tests/integration/test_db.py
def test_log_and_retrieve(tmp_db):
    """Round-trip: log an experiment, read it back."""
    from src.project_name.db import log_experiment, load_experiments

    log_experiment(
        project="test",
        experiment_type="unit_test",
        metrics={"sharpe": 1.5},
        hyperparams={"lr": 1e-3},
        db_path=tmp_db,
    )

    df = load_experiments(project="test", db_path=tmp_db)
    assert len(df) == 1
    assert df.iloc[0]["project"] == "test"
```

### Property-Based Tests — Hypothesis

For numerical/quant code. Define properties that must always hold,
hypothesis generates random inputs to find violations.

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(S0=st.floats(min_value=50, max_value=200),
       sigma=st.floats(min_value=0.05, max_value=1.0))
@settings(max_examples=50)
def test_gbm_paths_always_positive(S0, sigma):
    """GBM paths must always be positive."""
    from src.project_name.simulation import simulate_gbm
    paths = simulate_gbm(S0=S0, mu=0.05, sigma=sigma, T=1.0, n_steps=50, n_paths=100)
    assert (paths > 0).all()


@given(alpha=st.floats(min_value=0.01, max_value=0.99))
@settings(max_examples=20)
def test_cvar_worse_than_var(alpha):
    """CVaR should always be >= VaR (more conservative)."""
    from src.project_name.risk import cvar, var
    pnl = np.random.randn(1000)
    assert cvar(pnl, alpha) >= var(pnl, alpha) - 1e-6
```

### Running Tests

```bash
# All tests
poetry run pytest

# Unit only (fast feedback)
poetry run pytest tests/unit/ -v

# Single file
poetry run pytest tests/unit/test_pricing.py -v

# With coverage
poetry run pytest --cov=src --cov-report=term-missing

# Stop on first failure
poetry run pytest -x

# Run in parallel (if pytest-xdist installed)
poetry run pytest -n auto
```

### When to Write Tests

| You just did... | Write tests? | What kind? |
|----------------|-------------|------------|
| Explored in a notebook | No | Notebook is the test |
| Extracted a function to `src/` | Yes — smoke test | `test_it_runs()`, `test_output_shape()` |
| Built a data pipeline | Yes — integration | Round-trip: write then read back |
| Wrote pricing code | Yes — unit + property | Parity checks, boundary conditions, hypothesis |
| Fixed a bug | Yes — regression test | Test that reproduces the bug, verify it's fixed |
| Preparing for production | Yes — full suite | Unit + integration + property, 80%+ coverage |
| Refactoring | Run existing tests | They should all still pass |

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Create `test_*.py` outside of `tests/` | All test files in `tests/` directory |
| Leave temp files after tests | Use `tmp_path` fixture (auto-cleanup) |
| `unittest.TestCase` | Plain pytest functions with `assert` |
| Mock the database | Real temporary SQLite via `tmp_db` fixture |
| Skip `KERAS_BACKEND` in test setup | Set in `conftest.py` before imports |
| Write full test suite for a prototype | Smoke tests are enough at prototype stage |
| Ship to production without tests | 80%+ coverage for production code |
| `print()` in tests | `assert` statements or `pytest.fail()` |
| Test files named without `test_` prefix | Always `test_<module_name>.py` |

## Checklist

### Prototype stage
- [ ] Test files are in `tests/`, not scattered elsewhere
- [ ] Smoke tests: does it run, is output the right shape, no NaN

### Production stage
- [ ] `conftest.py` sets `KERAS_BACKEND=torch`
- [ ] `tmp_db` fixture for database tests
- [ ] Tests split into `unit/` and `integration/`
- [ ] Hypothesis used for numerical properties
- [ ] `poetry run pytest` passes with no failures
- [ ] Coverage > 80% on `src/`
- [ ] No temp files left behind after test run
