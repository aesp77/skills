# SKILL: Database Conventions

## Trigger
Read before writing any database code. All projects share a common schema.

---

## Strategy

| Project | DB | Purpose |
|---------|-----|---------|
| vol_pipeline | SQLite | Calibration results |
| coco_model | SQLite | Pricing cache |
| rl-deep-hedging | PostgreSQL (psycopg) | Experiment tracking |
| All | SQLite shared | Cross-project backtest comparison |

New projects: use SQLite unless concurrent writes or PostgreSQL already in use.

---

## Shared SQLite Schema

```python
# db/schema.py — copy into every project
import sqlite3, json, subprocess
from pathlib import Path

LOCAL_DB = Path("results") / "experiments.db"

DDL = """
CREATE TABLE IF NOT EXISTS experiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    project         TEXT    NOT NULL,
    experiment_type TEXT    NOT NULL,
    simulator       TEXT,
    model           TEXT,
    epoch           INTEGER,
    loss            REAL,
    val_loss        REAL,
    mean_pnl        REAL,
    std_pnl         REAL,
    sharpe          REAL,
    cvar_50         REAL,
    ratio_vs_bs     REAL,
    delta_corr      REAL,
    rmse            REAL,
    hyperparams     TEXT,
    market_params   TEXT,
    notes           TEXT,
    git_hash        TEXT
);

CREATE TABLE IF NOT EXISTS calibrations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    project     TEXT NOT NULL,
    model       TEXT NOT NULL,
    date        TEXT,
    symbol      TEXT,
    params      TEXT NOT NULL,
    rmse        REAL,
    git_hash    TEXT
);
"""

def get_connection(db_path: Path = LOCAL_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.commit()
    return conn
```

---

## Logging

```python
def log_experiment(project, experiment_type, metrics, hyperparams,
                   market_params=None, notes=""):
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        git_hash = "unknown"

    conn = get_connection()
    conn.execute(
        """INSERT INTO experiments
           (project, experiment_type, hyperparams, market_params, git_hash, notes,
            loss, val_loss, mean_pnl, std_pnl, sharpe, cvar_50,
            ratio_vs_bs, delta_corr, rmse, epoch, simulator, model)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (project, experiment_type,
         json.dumps(hyperparams), json.dumps(market_params or {}),
         git_hash, notes,
         metrics.get("loss"), metrics.get("val_loss"),
         metrics.get("mean_pnl"), metrics.get("std_pnl"),
         metrics.get("sharpe"), metrics.get("cvar_50"),
         metrics.get("ratio_vs_bs"), metrics.get("delta_corr"),
         metrics.get("rmse"), metrics.get("epoch"),
         metrics.get("simulator"), metrics.get("model"))
    )
    conn.commit()
    conn.close()
```

---

## Querying

```python
import pandas as pd
from db.schema import get_connection

def load_experiments(project=None):
    conn = get_connection()
    q = "SELECT * FROM experiments"
    if project:
        q += f" WHERE project = '{project}'"
    df = pd.read_sql_query(q + " ORDER BY timestamp DESC", conn)
    conn.close()
    return df
```
