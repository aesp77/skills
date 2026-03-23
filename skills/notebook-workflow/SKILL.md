# SKILL: Notebook to Module to Streamlit Workflow

<!--
name: notebook-workflow
trigger: Creating or modifying notebooks, extracting code to modules, or building Streamlit apps
depends-on: [keras3-pytorch, project-scaffold]
applies-to: [all]
-->

## When to Apply

Read before creating any notebook, extracting notebook code into modules, or
building a Streamlit app. Enforces the three-stage pipeline from exploration
to production.

## Dependencies

- **keras3-pytorch** — notebooks must set `KERAS_BACKEND=torch` in cell 1.
- **project-scaffold** — notebooks and apps live in the standard directory structure.

## Rules

1. All production logic lives in `src/` — never in notebooks.
2. Never skip stages: Notebook -> Module -> Streamlit.
3. Every notebook cell 1 sets `KERAS_BACKEND=torch` before any keras import.
4. Every notebook last cell documents findings and what to extract.
5. Notebooks are numbered sequentially: `01_`, `02_`, etc.
6. Streamlit apps import from `src/` — never re-implement logic.
7. Use `@st.cache_resource` for model loading in Streamlit.
8. For rl-deep-hedging: continue numbering from NB21 (next is NB22).

## Patterns

### The Three Stages

```
Stage 1: Exploration Notebook     (notebooks/01_*.ipynb)  — throwaway
    |  extract and test
Stage 2: Validated Module         (src/project_name/...)  — tested, typed
    |  wrap in interface
Stage 3: Streamlit App            (app/streamlit_app.py)  — production
```

### Stage 1 — Exploration Notebook

```python
# Cell 1: always set backend before keras
import os
os.environ["KERAS_BACKEND"] = "torch"

# Last cell: document what to extract
"""
FINDINGS: [summary]
TO EXTRACT TO src/: [list of functions/classes]
"""
```

#### Notebook naming

```
notebooks/
├── 01_data_exploration.ipynb
├── 02_model_architecture.ipynb
├── 03_training_experiments.ipynb
├── 04_validation.ipynb
└── 05_production_prep.ipynb
```

### Stage 2 — Validated Module

1. Every function: type signature + Google-style docstring
2. Every module: unit tests in `tests/`
3. Config via dataclass, not hardcoded values
4. No `print()` — use `logging`
5. Validate output matches notebook before deleting cells

```python
from dataclasses import dataclass
import keras

@dataclass
class EncoderConfig:
    input_dim: int = 715
    latent_dim: int = 3
    hidden_units: int = 64

class VolSurfaceEncoder(keras.Model):
    """VAE encoder. Extracted from notebooks/02_model_architecture.ipynb."""
    def __init__(self, config: EncoderConfig): ...
```

### Stage 3 — Streamlit App

```python
# app/streamlit_app.py
import os
os.environ["KERAS_BACKEND"] = "torch"  # always first

import streamlit as st
from src.models.encoder import VolSurfaceEncoder  # import from src/, never reimplement

@st.cache_resource
def load_model():
    return VolSurfaceEncoder(EncoderConfig())

st.set_page_config(page_title="App", layout="wide")
```

#### App structure

```
app/
├── streamlit_app.py
├── pages/
│   ├── 01_training.py
│   └── 02_validation.py
└── components/
    └── charts.py
```

#### README.md — Two Phases

The README lives at the project root and evolves in two phases:

**Phase 1 — Scientific background (created early)**
If the project is based on a paper, the README starts as the scientific
story — generated via NotebookLM (see paper-replication skill). This
gives the project context on GitHub and helps Claude Code understand
what to build. For projects without a paper, create a short README
explaining what the project does and why.

**Phase 2 — Add practical sections (when app is ready)**
Once Stage 3 is working, update the README with setup, run instructions,
directory structure, and pages overview. Don't replace the scientific
content — add to it.

Sections to add in Phase 2:

```markdown
## Setup

```bash
poetry install
cp .env.example .env
# Edit .env with your credentials
```

## Project Structure

```
├── src/project_name/       # Core logic (models, data, training)
├── app/                    # Streamlit app (entry point: streamlit_app.py)
├── notebooks/              # Exploration and study notebooks
├── papers/                 # Academic papers and replications
├── tests/                  # Unit and integration tests
├── scripts/                # Utility scripts (update_data.py, train.py)
├── data/                   # Market data and databases
├── saved_models/           # Trained model versions
├── results/                # Experiment logs
├── CLAUDE.md               # Project config (read by Claude Code)
└── PROGRESS.md             # What's done, in progress, and next
```

## Run the App

```bash
poetry run streamlit run app/streamlit_app.py
```

Or use the VS Code Run & Debug button: **"Project: Streamlit App"**

## Pages

| Page | What it does |
|------|-------------|
| Main | [description] |
| Training | [description] |
| Validation | [description] |

## Key Modules

| Module | What it does |
|--------|-------------|
| `src/project_name/models/` | [description] |
| `src/project_name/data/` | [description] |

## Data

[Where the data comes from, how to update it]

```bash
poetry run python scripts/update_data.py update
```
```

## Banned Patterns

| Do NOT use | Use instead |
|---|---|
| Production logic in notebooks | Extract to `src/`, import back |
| Skipping Stage 2 (notebook -> Streamlit directly) | Always go through validated module |
| Re-implementing logic in Streamlit | Import from `src/` |
| `print()` in modules | `logging` |
| Hardcoded config in modules | `dataclass` or pydantic config |
| Un-numbered notebooks | Sequential `01_`, `02_`, ... naming |

## Checklist

- [ ] Notebook cell 1 sets `KERAS_BACKEND=torch`
- [ ] Notebook last cell has `FINDINGS` and `TO EXTRACT` summary
- [ ] Extracted modules have type signatures and docstrings
- [ ] Unit tests exist for extracted modules
- [ ] Streamlit app imports from `src/`, not re-implemented
- [ ] `@st.cache_resource` used for model loading
- [ ] `README.md` Phase 1: scientific background (created early, from paper or project description)
- [ ] `README.md` Phase 2: setup/run/structure added when Streamlit app is ready
