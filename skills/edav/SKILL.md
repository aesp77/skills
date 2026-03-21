# SKILL: Exploratory Data Analysis and Visualization (EDAV)

<!--
name: edav
trigger: Exploring a dataset, checking data quality, detecting outliers, visualizing distributions, or building data dashboards
depends-on: [market-data]
applies-to: [all]
-->

## When to Apply

Read before exploring any dataset, checking data quality, detecting outliers,
or building visualizations. This skill ensures data is properly understood
and validated before any modelling work begins.

## Dependencies

- **market-data** — data is loaded from the standard schema.

## Rules

1. Always run EDAV before modelling — never train on data you haven't explored.
2. Use Plotly for interactive charts (Streamlit dashboards). Matplotlib/seaborn for static (notebooks, reports).
3. Always check: missing values, duplicates, outliers, distributions, and temporal gaps.
4. Color-code data quality: green (>= 95%), yellow (80-95%), red (< 80%).
5. Outlier detection uses both Z-score and IQR methods — flag but don't auto-remove.
6. Every EDAV notebook or dashboard answers: "Is this data ready for modelling?"
7. Save EDAV outputs (summary stats, quality reports) so they can be referenced later.

## Patterns

### Quick Dataset Overview

The first thing to run on any dataset. Answers: what do we have, what's missing,
what looks wrong?

```python
import pandas as pd
import numpy as np

def dataset_overview(df: pd.DataFrame, name: str = "dataset") -> dict:
    """Quick summary of a DataFrame — run this first on any dataset."""
    summary = {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "dtypes": df.dtypes.value_counts().to_dict(),
        "missing": df.isnull().sum().to_dict(),
        "missing_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "duplicates": df.duplicated().sum(),
        "memory_mb": df.memory_usage(deep=True).sum() / 1e6,
    }

    print(f"\n{'='*60}")
    print(f"  {name}: {summary['rows']:,} rows x {summary['columns']} columns")
    print(f"  Memory: {summary['memory_mb']:.1f} MB")
    print(f"  Duplicates: {summary['duplicates']}")
    print(f"{'='*60}")

    # Missing data
    missing = {k: v for k, v in summary["missing_pct"].items() if v > 0}
    if missing:
        print(f"\n  Missing data:")
        for col, pct in sorted(missing.items(), key=lambda x: -x[1]):
            status = "RED" if pct > 20 else "YELLOW" if pct > 5 else "ok"
            print(f"    {col:30s}: {pct:5.1f}%  [{status}]")
    else:
        print(f"\n  No missing data [GREEN]")

    # Numeric column stats
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        print(f"\n  Numeric columns summary:")
        print(numeric.describe().round(4).to_string())

    return summary
```

### Data Quality Report

```python
def data_quality_report(df: pd.DataFrame, date_col: str = "date") -> dict:
    """Full data quality assessment — missing values, gaps, outliers."""
    report = {"status": "GREEN", "issues": []}

    # 1. Missing values
    missing_pct = (df.isnull().sum() / len(df) * 100)
    worst_missing = missing_pct.max()
    if worst_missing > 20:
        report["status"] = "RED"
        report["issues"].append(f"Column '{missing_pct.idxmax()}' has {worst_missing:.1f}% missing")
    elif worst_missing > 5:
        report["status"] = "YELLOW"
        report["issues"].append(f"Column '{missing_pct.idxmax()}' has {worst_missing:.1f}% missing")

    # 2. Duplicates
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        report["issues"].append(f"{n_dupes} duplicate rows")

    # 3. Temporal gaps (if date column exists)
    if date_col in df.columns:
        dates = pd.to_datetime(df[date_col]).sort_values()
        gaps = dates.diff().dt.days
        large_gaps = gaps[gaps > 5]  # more than a weekend + 1
        if len(large_gaps) > 0:
            report["issues"].append(
                f"{len(large_gaps)} temporal gaps > 5 days "
                f"(largest: {large_gaps.max():.0f} days on {dates[large_gaps.idxmax()].date()})"
            )

    # 4. Constant columns
    constant_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                     if df[c].nunique() <= 1]
    if constant_cols:
        report["issues"].append(f"Constant columns: {constant_cols}")

    # 5. Summary
    print(f"\n  Data Quality: [{report['status']}]")
    if report["issues"]:
        for issue in report["issues"]:
            print(f"    - {issue}")
    else:
        print(f"    All checks passed")

    return report
```

### Outlier Detection

Two methods — use both, compare results. Flag outliers but don't auto-remove.

```python
def detect_outliers(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    z_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """Detect outliers using Z-score and IQR methods.

    Returns a DataFrame with boolean columns marking outliers.
    """
    columns = columns or df.select_dtypes(include=[np.number]).columns.tolist()
    results = {}

    for col in columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        # Z-score method
        z_scores = np.abs((series - series.mean()) / series.std())
        z_outliers = z_scores > z_threshold

        # IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        iqr_outliers = (series < q1 - iqr_multiplier * iqr) | (series > q3 + iqr_multiplier * iqr)

        n_z = z_outliers.sum()
        n_iqr = iqr_outliers.sum()

        results[col] = {
            "z_score_outliers": int(n_z),
            "z_score_pct": round(n_z / len(series) * 100, 2),
            "iqr_outliers": int(n_iqr),
            "iqr_pct": round(n_iqr / len(series) * 100, 2),
            "min": series.min(),
            "max": series.max(),
            "mean": series.mean(),
            "std": series.std(),
        }

        if n_z > 0 or n_iqr > 0:
            print(f"  {col}: Z-score={n_z} ({results[col]['z_score_pct']}%), "
                  f"IQR={n_iqr} ({results[col]['iqr_pct']}%)")

    return pd.DataFrame(results).T
```

### Distribution Plots — Static (Notebooks)

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_distributions(df: pd.DataFrame, columns: list[str] | None = None, figsize=(14, 4)):
    """Histogram + boxplot for each numeric column."""
    columns = columns or df.select_dtypes(include=[np.number]).columns.tolist()

    for col in columns:
        fig, axes = plt.subplots(1, 3, figsize=figsize)

        # Histogram
        axes[0].hist(df[col].dropna(), bins=50, edgecolor="black", alpha=0.7)
        axes[0].set_title(f"{col} — Distribution")
        axes[0].axvline(df[col].mean(), color="red", linestyle="--", label="mean")
        axes[0].legend()

        # Boxplot
        axes[1].boxplot(df[col].dropna(), vert=True)
        axes[1].set_title(f"{col} — Boxplot")

        # Time series (if index is datetime)
        if isinstance(df.index, pd.DatetimeIndex):
            axes[2].plot(df.index, df[col], linewidth=0.5)
            axes[2].set_title(f"{col} — Time Series")
        else:
            axes[2].plot(df[col].values, linewidth=0.5)
            axes[2].set_title(f"{col} — Sequence")

        plt.tight_layout()
        plt.show()


def plot_correlation_matrix(df: pd.DataFrame, method: str = "pearson", figsize=(10, 8)):
    """Correlation heatmap for numeric columns."""
    numeric = df.select_dtypes(include=[np.number])
    corr = numeric.corr(method=method)

    fig, ax = plt.subplots(figsize=figsize)
    mask = np.triu(np.ones_like(corr, dtype=bool))  # upper triangle only
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, vmin=-1, vmax=1, ax=ax)
    ax.set_title(f"Correlation Matrix ({method})")
    plt.tight_layout()
    return fig
```

### Interactive Charts — Plotly (Streamlit Dashboards)

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_time_series_interactive(
    df: pd.DataFrame,
    columns: list[str],
    date_col: str = "date",
    title: str = "Time Series",
):
    """Interactive time series with Plotly — use in Streamlit."""
    fig = make_subplots(
        rows=len(columns), cols=1,
        shared_xaxes=True,
        subplot_titles=columns,
        vertical_spacing=0.05,
    )

    for i, col in enumerate(columns, 1):
        fig.add_trace(
            go.Scatter(x=df[date_col], y=df[col], name=col, mode="lines"),
            row=i, col=1,
        )

    fig.update_layout(height=300 * len(columns), title_text=title, showlegend=False)
    return fig


def plot_missing_data_heatmap(df: pd.DataFrame, date_col: str = "date"):
    """Heatmap showing where data is missing — gaps are immediately visible."""
    missing = df.set_index(date_col).isnull().astype(int)

    fig = go.Figure(data=go.Heatmap(
        z=missing.values.T,
        x=missing.index,
        y=missing.columns,
        colorscale=[[0, "green"], [1, "red"]],
        showscale=False,
    ))
    fig.update_layout(
        title="Missing Data Heatmap (red = missing)",
        height=max(300, len(missing.columns) * 25),
    )
    return fig


def plot_outlier_scatter(
    df: pd.DataFrame,
    col: str,
    date_col: str = "date",
    z_threshold: float = 3.0,
):
    """Scatter plot highlighting outliers in a time series."""
    series = df[col].dropna()
    z_scores = np.abs((series - series.mean()) / series.std())
    is_outlier = z_scores > z_threshold

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[date_col][~is_outlier], y=series[~is_outlier],
        mode="markers", name="Normal", marker=dict(size=3, color="blue"),
    ))
    fig.add_trace(go.Scatter(
        x=df[date_col][is_outlier], y=series[is_outlier],
        mode="markers", name=f"Outlier (|z| > {z_threshold})",
        marker=dict(size=8, color="red", symbol="x"),
    ))
    fig.update_layout(title=f"{col} — Outlier Detection")
    return fig
```

### Data Completeness Check (From Database)

```python
def check_completeness(
    db_path,
    table: str,
    symbol: str,
    date_col: str = "date",
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Check how complete the data is relative to business days."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    query = f"SELECT DISTINCT {date_col} FROM {table} WHERE symbol = ?"
    params = [symbol]
    if start_date:
        query += f" AND {date_col} >= ?"
        params.append(start_date)
    if end_date:
        query += f" AND {date_col} <= ?"
        params.append(end_date)

    dates = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if dates.empty:
        return {"completeness": 0, "actual_days": 0, "expected_days": 0}

    dates[date_col] = pd.to_datetime(dates[date_col])
    actual = len(dates)

    # Expected business days in the range
    date_range = pd.bdate_range(dates[date_col].min(), dates[date_col].max())
    expected = len(date_range)

    completeness = actual / expected * 100 if expected > 0 else 0

    status = "GREEN" if completeness >= 95 else "YELLOW" if completeness >= 80 else "RED"

    print(f"  {symbol}/{table}: {actual}/{expected} days = {completeness:.1f}% [{status}]")

    return {
        "completeness": round(completeness, 2),
        "actual_days": actual,
        "expected_days": expected,
        "status": status,
        "first_date": str(dates[date_col].min().date()),
        "last_date": str(dates[date_col].max().date()),
    }
```

### Vol Surface Exploration

```python
def plot_vol_surface(df: pd.DataFrame, title: str = "Volatility Surface"):
    """3D vol surface plot — strikes x expiries x IV."""
    surface = df.pivot(index="strike", columns="expiry", values="iv")

    fig = go.Figure(data=[go.Surface(
        z=surface.values,
        x=list(range(len(surface.columns))),
        y=surface.index,
        colorscale="Viridis",
    )])
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="Expiry",
            yaxis_title="Strike",
            zaxis_title="Implied Vol",
        ),
        height=600,
    )
    return fig


def plot_vol_smile(df: pd.DataFrame, date: str, expiry: str):
    """Vol smile for a specific date and expiry."""
    mask = (df["date"] == date) & (df["expiry"] == expiry)
    slice_df = df[mask].sort_values("strike")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=slice_df["strike"], y=slice_df["iv"],
        mode="lines+markers", name=f"{expiry}",
    ))
    fig.update_layout(
        title=f"Vol Smile — {date}, Expiry: {expiry}",
        xaxis_title="Strike",
        yaxis_title="Implied Vol",
    )
    return fig
```

### Standard EDAV Notebook Template

Every project should have a `notebooks/01_edav.ipynb` following this structure:

```python
# Cell 1: Setup
import os
os.environ["KERAS_BACKEND"] = "torch"
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid")

# Cell 2: Load data
# from data.market_data import ...
# df = load_data(...)

# Cell 3: Overview
# dataset_overview(df, "my_dataset")

# Cell 4: Data quality
# data_quality_report(df)

# Cell 5: Distributions
# plot_distributions(df)

# Cell 6: Outliers
# detect_outliers(df)

# Cell 7: Correlations
# plot_correlation_matrix(df)

# Cell 8: Time series patterns
# plot_time_series_interactive(df, columns=[...])

# Cell 9: Missing data
# plot_missing_data_heatmap(df)

# Last cell: Findings
"""
FINDINGS:
- [data quality summary]
- [outlier findings]
- [key patterns observed]
- [data readiness for modelling: YES/NO]

ISSUES TO ADDRESS:
- [list any data problems to fix before modelling]
"""
```

### Streamlit Data Explorer Page

Standard page to add to any project's Streamlit app:

```python
# app/pages/01_data_explorer.py
import os
os.environ["KERAS_BACKEND"] = "torch"

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Data Explorer", layout="wide")
st.title("Data Explorer")

# Tabs
tab_overview, tab_quality, tab_distributions, tab_outliers, tab_completeness = st.tabs([
    "Overview", "Data Quality", "Distributions", "Outliers", "Completeness"
])

with tab_overview:
    # dataset_overview() output
    st.subheader("Dataset Overview")
    # ... load and display

with tab_quality:
    st.subheader("Data Quality Report")
    # data_quality_report() with color-coded indicators
    # plot_missing_data_heatmap()

with tab_distributions:
    st.subheader("Distributions")
    # column selector + plot_distributions equivalent in Plotly

with tab_outliers:
    st.subheader("Outlier Detection")
    # column selector + z_threshold slider
    # plot_outlier_scatter()
    # detect_outliers() table

with tab_completeness:
    st.subheader("Data Completeness")
    # check_completeness() per symbol/table
    # color-coded: green >= 95%, yellow >= 80%, red < 80%
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Start modelling without exploring the data | Always run EDAV first |
| Use only one outlier detection method | Use both Z-score and IQR, compare |
| Auto-remove outliers without inspection | Flag, visualize, then decide |
| Use matplotlib in Streamlit | Plotly for interactive dashboards |
| Ignore temporal gaps in time series | Check with `data_quality_report()` |
| Skip data completeness checks | Always run `check_completeness()` |
| Print raw DataFrames as quality checks | Use color-coded status (green/yellow/red) |

## Checklist

- [ ] `dataset_overview()` run — rows, columns, missing, duplicates documented
- [ ] `data_quality_report()` passed — no RED status items unresolved
- [ ] Outlier detection run — outliers flagged and reviewed
- [ ] Distributions plotted — no unexpected shapes or spikes
- [ ] Correlation matrix reviewed — no surprising correlations
- [ ] Temporal gaps checked — no unexplained missing periods
- [ ] Data completeness >= 95% for all required tables/symbols
- [ ] EDAV notebook has final cell with FINDINGS and data readiness verdict
