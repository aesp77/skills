# SKILL: Experiment Logging

<!--
name: experiment-logging
trigger: Recording results, comparing models, managing trained model versions, or analysing why one approach outperforms another
depends-on: [project-scaffold]
applies-to: [all]
-->

## When to Apply

Read before running any experiment where you'll want to remember what you did,
compare approaches, or reload a trained model later.

## Dependencies

- **project-scaffold** — projects follow the standard directory structure.

## What This Does

Three things:
1. **Experiment log** — records every run (settings + results) so you can compare later
2. **Model registry** — saves trained models with version numbers so nothing gets overwritten
3. **Analysis tools** — helps you understand WHY something worked, not just that it did

## Rules

1. Call `log_experiment()` after every meaningful run.
2. Save trained models to `saved_models/<name>/<version>/` — never overwrite.
3. Always save the config alongside the model — a model without its config is useless.
4. When comparing models, compare on the **same data** with the **same metrics**.
5. Don't just compare numbers — analyse what's different (architecture, data, loss function).
6. Database files and saved models are gitignored — they stay local.

## Patterns

### Directory Structure

```
project-root/
├── results/
│   └── experiments.db              # experiment log (auto-created)
├── saved_models/
│   ├── encoder/
│   │   ├── v001/
│   │   │   ├── model.keras         # trained weights
│   │   │   ├── config.json         # architecture + training config
│   │   │   └── metrics.json        # final metrics
│   │   ├── v002/
│   │   │   ├── model.keras
│   │   │   ├── config.json
│   │   │   └── metrics.json
│   │   └── best -> v002/           # symlink to best version
│   └── hedging_agent/
│       ├── v001/
│       └── ...
└── .gitignore                      # includes: results/, saved_models/
```

### Part 1 — Experiment Logging

#### Log an experiment — one function call

```python
from experiment_log import log_experiment

# After a training run
log_experiment(
    project="rl_hedging",
    experiment_type="training",
    metrics={"loss": 0.023, "val_loss": 0.031, "sharpe": 1.5, "epochs_trained": 142},
    hyperparams={"lr": 0.001, "layers": 3, "dropout": 0.1, "loss_fn": "cvar", "alpha": 0.05},
    notes="CVaR loss with lower alpha — better tail risk",
)

# After a calibration
log_experiment(
    project="vol_pipeline",
    experiment_type="calibration",
    metrics={"rmse": 0.0034, "converged": True},
    hyperparams={"model": "heston", "method": "L-BFGS-B", "symbol": "SPX"},
)

# After a backtest
log_experiment(
    project="rl_hedging",
    experiment_type="backtest",
    metrics={"sharpe": 1.2, "cvar_5": 0.018, "max_drawdown": 0.05, "improvement_vs_bs": 19.2},
    hyperparams={"train_window": 252, "tc_rate": 0.0005},
)
```

#### Query past results

```python
from experiment_log import load_experiments

# All experiments for a project
df = load_experiments("rl_hedging")

# Filter by type
training_runs = load_experiments("rl_hedging", experiment_type="training")

# Best run by a metric
best = training_runs.sort_values("sharpe", ascending=False).head(1)

# All experiments across all projects
everything = load_experiments()
```

### Part 2 — Model Registry

#### Saving a trained model

```python
from model_registry import save_model, load_model, list_versions, get_best

# After training — saves model + config + metrics together
version = save_model(
    name="encoder",
    model=trained_model,                    # keras model or torch state_dict
    config={                                # everything needed to rebuild
        "input_dim": 715,
        "latent_dim": 3,
        "hidden_units": 64,
        "dropout": 0.1,
    },
    metrics={                               # final performance
        "val_loss": 0.023,
        "test_loss": 0.026,
        "test_rmse": 0.031,
    },
    notes="Best so far — 3-layer with dropout",
)
# Prints: Saved encoder v003 to saved_models/encoder/v003/
```

#### Loading a model

```python
# Load a specific version
model, config, metrics = load_model("encoder", version="v002")

# Load the latest version
model, config, metrics = load_model("encoder")

# Load the best version (by a metric)
model, config, metrics = load_model("encoder", best_by="val_loss")
```

#### Listing and comparing versions

```python
# What versions exist?
list_versions("encoder")
#   v001: val_loss=0.045, test_loss=0.052 (2026-03-15)
#   v002: val_loss=0.031, test_loss=0.035 (2026-03-18)
#   v003: val_loss=0.023, test_loss=0.026 (2026-03-21) ← best

# Compare all versions
compare_versions("encoder", sort_by="val_loss")
```

#### Implementation

```python
# model_registry.py
import json
import shutil
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path("saved_models")


def _next_version(model_dir: Path) -> str:
    """Get next version number (v001, v002, ...)."""
    existing = sorted(model_dir.glob("v*"))
    if not existing:
        return "v001"
    last_num = int(existing[-1].name[1:])
    return f"v{last_num + 1:03d}"


def save_model(name: str, model, config: dict, metrics: dict,
               notes: str = "", models_dir: Path = MODELS_DIR) -> str:
    """Save a trained model with its config and metrics. Never overwrites."""
    model_dir = models_dir / name
    version = _next_version(model_dir)
    version_dir = model_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    import keras
    model.save(version_dir / "model.keras")

    # Save config
    config["saved_at"] = datetime.now().isoformat()
    config["notes"] = notes
    (version_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Save metrics
    (version_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Update 'best' symlink based on val_loss (or first metric)
    _update_best_link(model_dir, sort_metric="val_loss")

    print(f"  Saved {name} {version} to {version_dir}")
    return version


def load_model(name: str, version: str = None, best_by: str = None,
               models_dir: Path = MODELS_DIR):
    """Load a saved model with its config and metrics.

    Args:
        name: model name
        version: specific version (e.g. 'v002'). None = latest.
        best_by: load the version with best value for this metric (e.g. 'val_loss')
    """
    import keras

    model_dir = models_dir / name
    if not model_dir.exists():
        raise FileNotFoundError(f"No saved models for '{name}'")

    if best_by:
        version = _find_best_version(model_dir, best_by)
    elif version is None:
        versions = sorted(model_dir.glob("v*"))
        version = versions[-1].name if versions else None

    if version is None:
        raise FileNotFoundError(f"No versions found for '{name}'")

    version_dir = model_dir / version
    model = keras.saving.load_model(version_dir / "model.keras")
    config = json.loads((version_dir / "config.json").read_text())
    metrics = json.loads((version_dir / "metrics.json").read_text())

    print(f"  Loaded {name} {version}")
    return model, config, metrics


def list_versions(name: str, models_dir: Path = MODELS_DIR):
    """List all saved versions of a model."""
    model_dir = models_dir / name
    if not model_dir.exists():
        print(f"  No saved models for '{name}'")
        return

    print(f"\n  {name} versions:")
    for v_dir in sorted(model_dir.glob("v*")):
        if not v_dir.is_dir():
            continue
        metrics_file = v_dir / "metrics.json"
        config_file = v_dir / "config.json"

        metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else {}
        config = json.loads(config_file.read_text()) if config_file.exists() else {}

        saved_at = config.get("saved_at", "?")[:10]
        metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items() if isinstance(v, (int, float)))
        print(f"    {v_dir.name}: {metrics_str} ({saved_at})")


def compare_versions(name: str, sort_by: str = "val_loss", models_dir: Path = MODELS_DIR):
    """Compare all versions of a model side by side."""
    import pandas as pd

    model_dir = models_dir / name
    rows = []
    for v_dir in sorted(model_dir.glob("v*")):
        if not v_dir.is_dir():
            continue
        metrics = json.loads((v_dir / "metrics.json").read_text()) if (v_dir / "metrics.json").exists() else {}
        config = json.loads((v_dir / "config.json").read_text()) if (v_dir / "config.json").exists() else {}
        row = {"version": v_dir.name, "saved_at": config.get("saved_at", "")[:10]}
        row.update(metrics)
        row.update({k: v for k, v in config.items() if k not in ("saved_at", "notes") and not isinstance(v, (dict, list))})
        rows.append(row)

    df = pd.DataFrame(rows)
    ascending = sort_by in ("loss", "val_loss", "rmse", "test_loss", "cvar_5", "max_drawdown")
    df = df.sort_values(sort_by, ascending=ascending)
    print(f"\n  {name} — sorted by {sort_by}:")
    print(df.to_string(index=False))
    return df


def _find_best_version(model_dir: Path, metric: str) -> str:
    best_version = None
    best_value = float("inf") if metric in ("loss", "val_loss", "rmse", "test_loss") else float("-inf")
    ascending = metric in ("loss", "val_loss", "rmse", "test_loss", "cvar_5", "max_drawdown")

    for v_dir in model_dir.glob("v*"):
        if not v_dir.is_dir():
            continue
        metrics_file = v_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        metrics = json.loads(metrics_file.read_text())
        if metric in metrics:
            val = metrics[metric]
            if (ascending and val < best_value) or (not ascending and val > best_value):
                best_value = val
                best_version = v_dir.name

    return best_version


def _update_best_link(model_dir: Path, sort_metric: str):
    best = _find_best_version(model_dir, sort_metric)
    if best:
        link = model_dir / "best"
        if link.exists():
            if link.is_symlink():
                link.unlink()
            elif link.is_dir():
                shutil.rmtree(link)
        try:
            link.symlink_to(best)
        except OSError:
            pass  # symlinks may not work on Windows without admin
```

### Part 3 — Analysis: Understanding WHY

Don't just compare numbers. When one model beats another, ask why.

```python
def analyse_difference(name: str, version_a: str, version_b: str,
                       models_dir: Path = MODELS_DIR):
    """Compare two model versions — config differences and metric differences."""
    dir_a = models_dir / name / version_a
    dir_b = models_dir / name / version_b

    config_a = json.loads((dir_a / "config.json").read_text())
    config_b = json.loads((dir_b / "config.json").read_text())
    metrics_a = json.loads((dir_a / "metrics.json").read_text())
    metrics_b = json.loads((dir_b / "metrics.json").read_text())

    # What changed in the config?
    print(f"\n  Config differences ({version_a} vs {version_b}):")
    all_keys = set(config_a) | set(config_b)
    for key in sorted(all_keys):
        if key in ("saved_at", "notes"):
            continue
        val_a = config_a.get(key, "—")
        val_b = config_b.get(key, "—")
        if val_a != val_b:
            print(f"    {key}: {val_a} → {val_b}")

    # What changed in the metrics?
    print(f"\n  Metric differences ({version_a} vs {version_b}):")
    all_metrics = set(metrics_a) | set(metrics_b)
    for key in sorted(all_metrics):
        val_a = metrics_a.get(key)
        val_b = metrics_b.get(key)
        if val_a is not None and val_b is not None and isinstance(val_a, (int, float)):
            diff = val_b - val_a
            pct = (diff / abs(val_a) * 100) if val_a != 0 else 0
            direction = "better" if (key in ("sharpe",) and diff > 0) or (key in ("loss", "val_loss", "rmse") and diff < 0) else "worse" if diff != 0 else "same"
            print(f"    {key}: {val_a:.4f} → {val_b:.4f} ({diff:+.4f}, {pct:+.1f}%) [{direction}]")
```

#### Usage

```python
# What changed between v001 and v003 of the encoder?
analyse_difference("encoder", "v001", "v003")

# Output:
#   Config differences (v001 vs v003):
#     dropout: 0.0 → 0.1
#     hidden_units: 32 → 64
#     lr: 0.01 → 0.001
#
#   Metric differences (v001 vs v003):
#     val_loss: 0.0450 → 0.0230 (-0.0220, -48.9%) [better]
#     test_loss: 0.0520 → 0.0260 (-0.0260, -50.0%) [better]
#
# Conclusion: adding dropout and increasing width while reducing LR
# cut the loss in half. The dropout was the key change.
```

### The Experiment Log Implementation

```python
# experiment_log.py
import sqlite3
import json
import subprocess
from pathlib import Path
import pandas as pd

RESULTS_DB = Path("results") / "experiments.db"

DDL = """
CREATE TABLE IF NOT EXISTS experiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    project         TEXT    NOT NULL,
    experiment_type TEXT    NOT NULL,
    metrics         TEXT    NOT NULL,
    hyperparams     TEXT    NOT NULL,
    notes           TEXT    DEFAULT '',
    git_hash        TEXT
);
"""

def _get_git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def _get_conn(db_path: Path = RESULTS_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.commit()
    return conn


def log_experiment(project: str, experiment_type: str, metrics: dict,
                   hyperparams: dict, notes: str = "", db_path: Path = RESULTS_DB):
    conn = _get_conn(db_path)
    conn.execute(
        "INSERT INTO experiments (project, experiment_type, metrics, hyperparams, notes, git_hash) VALUES (?,?,?,?,?,?)",
        (project, experiment_type, json.dumps(metrics), json.dumps(hyperparams), notes, _get_git_hash()),
    )
    conn.commit()
    conn.close()


def load_experiments(project: str = None, experiment_type: str = None,
                     db_path: Path = RESULTS_DB) -> pd.DataFrame:
    conn = _get_conn(db_path)
    query = "SELECT * FROM experiments WHERE 1=1"
    params = []
    if project:
        query += " AND project = ?"
        params.append(project)
    if experiment_type:
        query += " AND experiment_type = ?"
        params.append(experiment_type)
    query += " ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # Expand metrics JSON into columns
    if not df.empty and "metrics" in df.columns:
        metrics_df = df["metrics"].apply(json.loads).apply(pd.Series)
        for col in metrics_df.columns:
            df[col] = metrics_df[col]
    return df
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Run experiments without logging | Always call `log_experiment()` |
| Overwrite a trained model | Save as a new version in `saved_models/<name>/v00X/` |
| Save a model without its config | Always save config.json alongside model.keras |
| Compare models on different data | Same data, same metrics, fair comparison |
| Just compare numbers | Use `analyse_difference()` to understand what changed |
| Commit model files or experiment DBs | `saved_models/` and `results/` in `.gitignore` |

## Checklist

- [ ] `log_experiment()` called after every run
- [ ] `metrics` dict includes all measured values
- [ ] `hyperparams` dict includes all settings
- [ ] Trained models saved via `save_model()` with config + metrics
- [ ] Models never overwritten — each version gets its own directory
- [ ] `saved_models/` and `results/` in `.gitignore`
- [ ] Can compare versions with `compare_versions()` and `analyse_difference()`
