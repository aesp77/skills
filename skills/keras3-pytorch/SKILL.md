# SKILL: Keras 3 with PyTorch Backend

## Trigger
Read before any ML/deep learning work. Read before writing any Keras or PyTorch model code.

---

## Setup

```bash
poetry add keras torch torchvision
# Do NOT add tensorflow — Keras 3 with PyTorch backend does not need it
```

```python
# Set backend BEFORE importing keras — always
import os
os.environ["KERAS_BACKEND"] = "torch"
import keras
assert keras.backend.backend() == "torch"
```

---

## Model Definition

```python
import keras
from keras import layers, ops

class VolSurfaceEncoder(keras.Model):
    def __init__(self, latent_dim: int, hidden_units: int = 64):
        super().__init__()
        self.encoder = keras.Sequential([
            layers.Dense(hidden_units, activation="relu"),
            layers.Dense(hidden_units, activation="relu"),
            layers.Dense(latent_dim),
        ])

    def call(self, x: keras.KerasTensor, training: bool = False) -> keras.KerasTensor:
        return self.encoder(x, training=training)
```

---

## Training

```python
# Keras 3 handles backward pass — do NOT use GradientTape
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss=keras.losses.MeanSquaredError(),
)
model.fit(dataset, epochs=100, callbacks=[
    keras.callbacks.ModelCheckpoint("best.keras", save_best_only=True),
    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
])
```

### Custom loss
```python
class DeepHedgingModel(keras.Model):
    def compute_loss(self, x=None, y=None, y_pred=None, sample_weight=None):
        pnl = y_pred - y
        return cvar_loss(pnl, alpha=0.5)
```

---

## Inference

```python
# Always training=False — never model.predict() for custom models
output = model(x, training=False)
```

---

## Saving

```python
model.save("saved_models/encoder.keras")   # .keras format, not .h5
model = keras.saving.load_model("saved_models/encoder.keras",
                                 custom_objects={"MyLayer": MyLayer})
```

---

## Backend-Agnostic Math — Always keras.ops

```python
from keras import ops
# Use ops.* inside model code — never torch.* or np.*
x = ops.log(x)
x = ops.exp(x)
x = ops.sort(x, axis=-1)
x = ops.mean(x, axis=0)
x = ops.cumsum(x, axis=1)
x = ops.clip(x, 0.0, 1.0)
```

---

## Banned Patterns

| ❌ DO NOT USE | ✅ USE INSTEAD |
|---|---|
| `tf.GradientTape()` | Override `compute_loss()` |
| `@tf.function` | `torch.compile()` if needed |
| `tf.data.Dataset` | `torch.utils.data.DataLoader` |
| `keras.backend.GradientTape` | Does not exist in Keras 3 |
| `model.predict(x)` | `model(x, training=False)` |
| `from tensorflow import keras` | `import keras` |
| `tf.keras.*` | `keras.*` |
| `K.mean(x)` | `ops.mean(x)` |
| `tf.random.*` | `keras.random.*` |
| `.numpy()` inside model code | Stay in tensor space |
| `import tensorflow as tf` | Never in PSC code |
