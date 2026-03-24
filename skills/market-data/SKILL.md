# SKILL: Market Data

<!--
name: market-data
trigger: Sourcing, storing, updating, or reusing market data
depends-on: [project-scaffold]
applies-to: [all]
-->

## When to Apply

Read before downloading, storing, or querying any market data. This skill
ensures data is stored in a standard schema, updated incrementally, and
can be copied between projects to avoid re-downloading.

## Dependencies

- **project-scaffold** — projects follow the standard directory structure.

## Rules

1. Each project has its own DB at `data/db/<project>.db` — but all use the same schema.
2. Always update incrementally — only download dates newer than the last stored date.
3. Define a source priority per data type — cheapest/fastest first, expensive last.
4. Before downloading, check if another project already has the data — copy it.
5. Schema is instrument-agnostic — same tables work for any symbol.
6. Credentials go in `.env` — never in code, never committed.
7. All queries use parameterised placeholders (`?`) — never f-strings.

## Patterns

### Credentials — Always in .env

```bash
# .env (never committed — add keys for your data sources)
# FirstRate Data
FIRSTRATE_BASE_URL=https://firstratedata.com/api/data_file
FIRSTRATE_LAST_UPDATE_URL=https://firstratedata.com/api/last_update
FIRSTRATE_USER_ID=QQgoG4i9pUS2KxmPmLWvGw
# BBG_HOST=localhost
# BBG_PORT=8194
# MARQUEE_CLIENT_ID=...
# MARQUEE_CLIENT_SECRET=...
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

def get_credential(key: str) -> str:
    """Get a credential from .env. Fail loudly if missing."""
    val = os.environ.get(key)
    if not val:
        raise EnvironmentError(f"Missing credential: {key}. Add it to .env")
    return val
```

### Standard Schema

All projects use the same table definitions. This means you can copy tables
between project databases directly.

```python
import sqlite3
from pathlib import Path

MARKET_DDL = """
-- Daily time series (spot, close, div yield, volume, etc.)
CREATE TABLE IF NOT EXISTS time_series (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    field       TEXT NOT NULL,
    value       REAL NOT NULL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date, field)
);

-- Term structures (yield curves, forward curves, VIX futures, etc.)
CREATE TABLE IF NOT EXISTS term_structures (
    curve_id    TEXT NOT NULL,       -- e.g. 'USD_OIS', 'EUR_YIELD', 'VIX_FUTURES'
    date        TEXT NOT NULL,
    tenor       TEXT NOT NULL,
    value       REAL NOT NULL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (curve_id, date, tenor)
);

-- Vol surfaces (strike x expiry grid per symbol per date)
CREATE TABLE IF NOT EXISTS vol_surfaces (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    expiry      TEXT NOT NULL,
    strike      REAL NOT NULL,
    iv          REAL NOT NULL,
    delta       REAL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date, expiry, strike)
);

-- Option chains (individual contracts)
CREATE TABLE IF NOT EXISTS option_chains (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    expiry      TEXT NOT NULL,
    strike      REAL NOT NULL,
    option_type TEXT NOT NULL,       -- 'C' or 'P'
    bid         REAL,
    ask         REAL,
    mid         REAL,
    volume      INTEGER,
    open_interest INTEGER,
    iv          REAL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date, expiry, strike, option_type)
);

-- Intraday data (for projects that need it)
CREATE TABLE IF NOT EXISTS intraday (
    symbol      TEXT NOT NULL,
    datetime    TEXT NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, datetime)
);

-- Tracks what has been downloaded to avoid re-fetching
CREATE TABLE IF NOT EXISTS fetch_log (
    source      TEXT NOT NULL,
    dataset     TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    last_date   TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source, dataset, symbol)
);

CREATE INDEX IF NOT EXISTS idx_ts_symbol_date ON time_series(symbol, date);
CREATE INDEX IF NOT EXISTS idx_vol_symbol_date ON vol_surfaces(symbol, date);
CREATE INDEX IF NOT EXISTS idx_opt_symbol_date ON option_chains(symbol, date);
CREATE INDEX IF NOT EXISTS idx_term_curve_date ON term_structures(curve_id, date);
CREATE INDEX IF NOT EXISTS idx_intraday_symbol ON intraday(symbol, datetime);
"""


def get_project_db(db_path: Path, extra_ddl: str = "") -> sqlite3.Connection:
    """Open (or create) a project database with the standard schema.

    Args:
        extra_ddl: Additional CREATE TABLE statements for project-specific tables.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(MARKET_DDL)
    if extra_ddl:
        conn.executescript(extra_ddl)
    conn.commit()
    return conn
```

### Extending the Schema for Different Data Types

The standard tables above cover common market data. When your project needs
different data types, add project-specific tables alongside the standard ones.
The rules for custom tables:

1. **Always include** `date TEXT`, `source TEXT`, and `updated_at TEXT DEFAULT (datetime('now'))`
2. **Always include** a `PRIMARY KEY` that prevents duplicates
3. **Register in `fetch_log`** so incremental updates work
4. **Keep standard tables untouched** — add new tables, don't modify existing ones

```python
# Example: credit_macro project needs CDS spreads
CREDIT_DDL = """
CREATE TABLE IF NOT EXISTS cds_spreads (
    index_name  TEXT NOT NULL,       -- 'EU_IG', 'US_HY', etc.
    date        TEXT NOT NULL,
    tenor       TEXT NOT NULL,       -- '3Y', '5Y', '7Y', '10Y'
    spread_bps  REAL NOT NULL,
    series      INTEGER,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (index_name, date, tenor)
);

CREATE TABLE IF NOT EXISTS total_return_series (
    index_name  TEXT NOT NULL,
    tenor       TEXT NOT NULL,
    date        TEXT NOT NULL,
    long_tr     REAL,
    short_tr    REAL,
    daily_pnl   REAL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (index_name, tenor, date)
);
"""

# Open DB with standard + custom tables
conn = get_project_db(PROJECT_DB, extra_ddl=CREDIT_DDL)
```

```python
# Example: market_instability_gae needs correlation matrices and model outputs
GAE_DDL = """
CREATE TABLE IF NOT EXISTS realized_volatility (
    symbol      TEXT NOT NULL,
    date        TEXT NOT NULL,
    rv_daily    REAL,
    parkinson   REAL,
    garman_klass REAL,
    yang_zhang  REAL,
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS correlation_matrices (
    date        TEXT NOT NULL UNIQUE,
    window_size INTEGER,
    matrix_data BLOB,                -- serialised numpy array
    threshold   REAL,
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS model_outputs (
    date        TEXT NOT NULL,
    model_name  TEXT NOT NULL,
    metric_name TEXT NOT NULL,       -- 'reconstruction_error', 'auroc', etc.
    value       REAL NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (date, model_name, metric_name)
);
"""

conn = get_project_db(PROJECT_DB, extra_ddl=GAE_DDL)
```

```python
# Example: a non-financial project (Reddit sentiment, macro indicators, etc.)
ALTERNATIVE_DDL = """
CREATE TABLE IF NOT EXISTS text_data (
    source_name TEXT NOT NULL,       -- 'reddit', 'twitter', 'news', etc.
    date        TEXT NOT NULL,
    symbol      TEXT,                -- optional: ticker if relevant
    content     TEXT NOT NULL,
    sentiment   REAL,                -- optional: pre-computed sentiment score
    metadata    TEXT,                -- JSON for extra fields
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source_name, date, content)
);

CREATE TABLE IF NOT EXISTS macro_indicators (
    indicator   TEXT NOT NULL,       -- 'CPI', 'UNEMPLOYMENT', 'PMI', etc.
    date        TEXT NOT NULL,
    value       REAL NOT NULL,
    country     TEXT NOT NULL,       -- 'US', 'EU', 'UK', etc.
    source      TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (indicator, date, country)
);
"""

conn = get_project_db(PROJECT_DB, extra_ddl=ALTERNATIVE_DDL)
```

**The key point:** standard tables give you copyable market data across projects.
Custom tables extend the schema for project-specific needs. Both coexist in
the same DB and use the same `fetch_log` / incremental update infrastructure.

### Copying Data From Another Project

When starting a new project, copy the tables you need from an existing DB
instead of re-downloading. The shared schema makes this a direct table copy.

```python
def copy_tables(
    source_db: Path,
    target_db: Path,
    tables: list[str] | None = None,
    symbols: list[str] | None = None,
    date_from: str | None = None,
):
    """Copy market data tables from one project's DB to another.

    Args:
        source_db: Path to the existing project's database
        target_db: Path to the new project's database
        tables: Which tables to copy (None = all standard tables)
        symbols: Filter to specific symbols (None = all)
        date_from: Only copy data from this date onwards (None = all)
    """
    all_tables = [
        "time_series", "term_structures", "vol_surfaces",
        "option_chains", "intraday", "fetch_log",
    ]
    tables = tables or all_tables

    src = sqlite3.connect(source_db)
    tgt = get_project_db(target_db)

    for table in tables:
        # Check table exists in source
        exists = src.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if not exists:
            print(f"  {table}: not in source, skipping")
            continue

        # Build query with optional filters
        query = f"SELECT * FROM {table} WHERE 1=1"
        params = []

        if symbols and table not in ("term_structures", "fetch_log"):
            placeholders = ",".join("?" * len(symbols))
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbols)

        if date_from:
            date_col = "datetime" if table == "intraday" else "date"
            query += f" AND {date_col} >= ?"
            params.append(date_from)

        rows = src.execute(query, params).fetchall()
        if not rows:
            print(f"  {table}: no matching data")
            continue

        # Get column names
        cols = [desc[0] for desc in src.execute(f"SELECT * FROM {table} LIMIT 1").description]
        placeholders = ",".join("?" * len(cols))

        tgt.executemany(
            f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})",
            rows,
        )
        tgt.commit()
        print(f"  {table}: copied {len(rows)} rows")

    # Also copy fetch_log so incremental updates know where to start
    if "fetch_log" in tables:
        fetch_rows = src.execute("SELECT * FROM fetch_log").fetchall()
        if fetch_rows:
            cols = [desc[0] for desc in src.execute("SELECT * FROM fetch_log LIMIT 1").description]
            placeholders = ",".join("?" * len(cols))
            tgt.executemany(
                f"INSERT OR IGNORE INTO fetch_log VALUES ({placeholders})",
                fetch_rows,
            )
            tgt.commit()

    src.close()
    tgt.close()
    print(f"\nDone. Copied from {source_db.name} -> {target_db.name}")
```

#### Usage Examples

```python
from pathlib import Path

# Copy everything from rl_hedging to a new project
copy_tables(
    source_db=Path("~/rl_hedging_comparison/data/db/rl_hedging_data.db").expanduser(),
    target_db=Path("~/new_project/data/db/new_project.db").expanduser(),
)

# Copy only SPX data from 2023 onwards
copy_tables(
    source_db=Path("~/rl_hedging_comparison/data/db/rl_hedging_data.db").expanduser(),
    target_db=Path("~/new_project/data/db/new_project.db").expanduser(),
    symbols=["SPX"],
    date_from="2023-01-01",
)

# Copy only term structures (shared across instruments anyway)
copy_tables(
    source_db=Path("~/spx_lookback_pricer/spx_lookback_data.db").expanduser(),
    target_db=Path("~/new_project/data/db/new_project.db").expanduser(),
    tables=["term_structures"],
)
```

### Incremental Updates

```python
import pandas as pd

def get_last_fetched_date(conn, source: str, dataset: str, symbol: str) -> str | None:
    row = conn.execute(
        "SELECT last_date FROM fetch_log WHERE source = ? AND dataset = ? AND symbol = ?",
        (source, dataset, symbol),
    ).fetchone()
    return row[0] if row else None


def update_fetch_log(conn, source: str, dataset: str, symbol: str, last_date: str):
    conn.execute(
        """INSERT OR REPLACE INTO fetch_log (source, dataset, symbol, last_date)
           VALUES (?, ?, ?, ?)""",
        (source, dataset, symbol, last_date),
    )
    conn.commit()


def fetch_incremental(conn, symbol: str, dataset: str, source: str, fetcher_fn):
    """Only download data newer than what we already have.

    fetcher_fn(symbol, start_date) -> pd.DataFrame
    """
    last_date = get_last_fetched_date(conn, source, dataset, symbol)

    if last_date:
        print(f"  {symbol}/{dataset}: have up to {last_date}, fetching new...")
    else:
        print(f"  {symbol}/{dataset}: no data, full download...")

    df = fetcher_fn(symbol, last_date)

    if df is not None and not df.empty:
        _insert_data(conn, dataset, df, source)
        update_fetch_log(conn, source, dataset, symbol, df["date"].max())
        print(f"  Added {len(df)} rows")
    else:
        print(f"  Already up to date")
```

### Source Priority — Try Cheapest First

```python
from dataclasses import dataclass, field

@dataclass
class SourceConfig:
    name: str
    priority: int                       # lower = try first (cheapest)
    provides: list[str]                 # e.g. ['spot', 'option_chains']
    credential_keys: list[str] = field(default_factory=list)


def fetch_with_fallback(conn, symbol: str, dataset: str, sources: list[SourceConfig], fetchers: dict):
    """Try sources in priority order. First one that works wins.

    Once a source is found for a symbol+dataset, it's recorded in fetch_log.
    Future updates go straight to that source.
    """
    # Already have a source? Just update incrementally
    existing = conn.execute(
        "SELECT source, last_date FROM fetch_log WHERE dataset = ? AND symbol = ?",
        (dataset, symbol),
    ).fetchone()

    if existing:
        source_name, last_date = existing
        print(f"  {symbol}/{dataset}: updating from {source_name}")
        fetch_incremental(conn, symbol, dataset, source_name, fetchers[source_name])
        return

    # First time — try sources in priority order
    for src in sorted(sources, key=lambda s: s.priority):
        if dataset not in src.provides:
            continue
        fetcher = fetchers.get(src.name)
        if not fetcher:
            continue

        print(f"  {symbol}/{dataset}: trying {src.name}...")
        try:
            fetch_incremental(conn, symbol, dataset, src.name, fetcher)
            return  # success — fetch_log now records this source
        except Exception as e:
            print(f"  {src.name} failed: {e}")
            continue

    print(f"  WARNING: {symbol}/{dataset} not found in any source")
```

### Standard Update Script

Every project should have a `scripts/update_data.py` that follows this pattern.
It handles init, incremental updates, copying from another project, and status checks.

```python
#!/usr/bin/env python3
"""Update market data for this project.

Usage:
    poetry run python scripts/update_data.py status          # what do we have?
    poetry run python scripts/update_data.py update          # fetch new data
    poetry run python scripts/update_data.py copy <source>   # copy from another project's DB
    poetry run python scripts/update_data.py init <source>   # copy + update to today
"""
import argparse
import sys
from pathlib import Path

# Project-specific config — edit these for your project
PROJECT_DB = Path(__file__).parent.parent / "data" / "db" / "my_project.db"
SYMBOLS = ["SPX"]                       # symbols this project needs
DATASETS = ["spot", "vol_surfaces", "term_structures", "option_chains"]


def cmd_status(args):
    check_data_coverage(PROJECT_DB)


def cmd_update(args):
    conn = get_project_db(PROJECT_DB)
    for symbol in SYMBOLS:
        for dataset in DATASETS:
            fetch_with_fallback(conn, symbol, dataset, SOURCES, FETCHERS)
    conn.close()
    check_data_coverage(PROJECT_DB)


def cmd_copy(args):
    source_db = Path(args.source).expanduser()
    if not source_db.exists():
        print(f"Source DB not found: {source_db}")
        sys.exit(1)
    copy_tables(source_db, PROJECT_DB, symbols=SYMBOLS)
    check_data_coverage(PROJECT_DB)


def cmd_init(args):
    """Copy from another project, then update to fill any gaps."""
    cmd_copy(args)
    cmd_update(args)


def main():
    parser = argparse.ArgumentParser(description="Update market data")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show data coverage")
    sub.add_parser("update", help="Fetch new data incrementally")

    p_copy = sub.add_parser("copy", help="Copy data from another project's DB")
    p_copy.add_argument("source", help="Path to source database")

    p_init = sub.add_parser("init", help="Copy from source DB then update")
    p_init.add_argument("source", help="Path to source database")

    args = parser.parse_args()
    {"status": cmd_status, "update": cmd_update, "copy": cmd_copy, "init": cmd_init}[args.command](args)


if __name__ == "__main__":
    main()
```

#### Usage

```bash
# Check what data you have
poetry run python scripts/update_data.py status

# Copy SPX data from rl_hedging as a starting point
poetry run python scripts/update_data.py copy ~/rl_hedging_comparison/data/db/rl_hedging_data.db

# Or copy + update in one step
poetry run python scripts/update_data.py init ~/rl_hedging_comparison/data/db/rl_hedging_data.db

# Daily incremental update
poetry run python scripts/update_data.py update
```

### Data Coverage Check

```python
def check_data_coverage(db_path: Path, symbol: str = None) -> dict:
    conn = get_project_db(db_path)
    coverage = {}

    tables_with_symbol = ["time_series", "vol_surfaces", "option_chains", "intraday"]
    for table in tables_with_symbol:
        if symbol:
            row = conn.execute(
                f"SELECT MIN(date), MAX(date), COUNT(*) FROM {table} WHERE symbol = ?",
                (symbol,),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT MIN(date), MAX(date), COUNT(*) FROM {table}",
            ).fetchone()
        coverage[table] = {"from": row[0], "to": row[1], "rows": row[2]}

    # Term structures (shared, not per-symbol)
    row = conn.execute(
        "SELECT MIN(date), MAX(date), COUNT(*) FROM term_structures"
    ).fetchone()
    coverage["term_structures"] = {"from": row[0], "to": row[1], "rows": row[2]}

    conn.close()

    label = f" for {symbol}" if symbol else ""
    print(f"\nData coverage{label} ({db_path.name}):")
    for table, info in coverage.items():
        if info["from"]:
            print(f"  {table:20s}: {info['from']} to {info['to']} ({info['rows']} rows)")
        else:
            print(f"  {table:20s}: empty")

    return coverage
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Re-download data that exists in another project DB | `copy_tables()` from the existing DB |
| Re-download full history each time | Check `fetch_log`, only fetch new dates |
| Jump to expensive source first | Try cheapest source first, fallback if missing |
| Hardcode credentials in code | `.env` file + `get_credential()` |
| Use different table schemas per project | Standard schema so data is copyable |
| f-strings in SQL | Always `?` placeholders |
| Download term structures per symbol | Term structures are shared — copy once |

## Checklist

- [ ] Database at `data/db/<project>.db` using standard schema
- [ ] Credentials in `.env`, listed in `.env.example`
- [ ] Checked if another project already has the data before downloading
- [ ] Source priority defined (cheapest first)
- [ ] Incremental updates via `fetch_log`
- [ ] All queries parameterised
- [ ] `check_data_coverage()` run before starting analysis
