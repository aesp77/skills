# SKILL: Notebook → Module → Streamlit Workflow

## Trigger
Read before creating any notebook or Streamlit app.

---

## The Three Stages

```
Stage 1: Exploration Notebook     (notebooks/01_*.ipynb)  — throwaway
    ↓  extract and test
Stage 2: Validated Module         (src/project_name/...)  — tested, typed
    ↓  wrap in interface
Stage 3: Streamlit App            (app/streamlit_app.py)  — production
```

Never skip stages. Do not put production logic in notebooks.

---

## Stage 1 Rules

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

### Notebook naming
```
notebooks/
├── 01_data_exploration.ipynb
├── 02_model_architecture.ipynb
├── 03_training_experiments.ipynb
├── 04_validation.ipynb
└── 05_production_prep.ipynb
```

For rl-deep-hedging: continue from NB21, next is NB22.

---

## Stage 2 Rules

1. Every function: type signature + Google-style docstring
2. Every module: unit tests in tests/
3. Config → dataclass, not hardcoded
4. No print() → use logging
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
    """
    VAE encoder. Extracted from notebooks/02_model_architecture.ipynb.
    """
    def __init__(self, config: EncoderConfig): ...
```

---

## Stage 3 Rules

```python
# app/streamlit_app.py
import os
os.environ["KERAS_BACKEND"] = "torch"  # always first

import streamlit as st
from src.models.encoder import VolSurfaceEncoder  # import from src/, never reimplement

@st.cache_resource
def load_model():
    return VolSurfaceEncoder(EncoderConfig())

st.set_page_config(page_title="PSC App", layout="wide")
```

### App structure
```
app/
├── streamlit_app.py
├── pages/
│   ├── 01_training.py
│   └── 02_validation.py
└── components/
    └── charts.py
```
