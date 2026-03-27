# SKILL: Keras 3 with PyTorch Backend

<!--
name: keras3-pytorch
trigger: Any ML/deep-learning model code — training, inference, saving, or loss functions
depends-on: []
applies-to: [all]
-->

## When to Apply

Read before writing any Keras or PyTorch model, training loop, custom loss, or
inference code. This is the ML foundation for all projects.

## Reference

The authoritative API reference is https://keras.io/api/ — always check it for
correct signatures, available layers, callbacks, and ops.

## Dependencies

None.

## Rules

1. Set `KERAS_BACKEND=torch` **before** `import keras` — always, everywhere.
2. Never install or import TensorFlow. Keras 3 with PyTorch backend does not need it.
3. Use `keras.ops.*` for all math inside model code — never `torch.*` or `np.*` inside a `keras.Model`.
4. Use `model(x, training=False)` for inference — never `model.predict(x)`.
5. Save models as `.keras` — never `.h5`.
6. Override `compute_loss()` for custom losses — never use `GradientTape`.
7. Use `torch.utils.data.DataLoader` for data loading — never `tf.data.Dataset`.
8. Always split data into **train / validation / test** sets before training.
9. Always use the standard callback stack: ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, and a logger.
10. Always track and log metrics — never train blind.
11. Convert data to tensors early (from DB, CSV, DataFrame) — let Keras handle CPU/GPU placement.
12. Never manually call `.to("cuda")` or `.to("cpu")` — Keras 3 manages device placement automatically.

## Patterns

### Setup

```python
import os
os.environ["KERAS_BACKEND"] = "torch"
import keras
assert keras.backend.backend() == "torch"
```

```bash
poetry add keras torch torchvision
```

### Model Definition

```python
import keras
from keras import layers, ops

class VolSurfaceEncoder(keras.Model):
    def __init__(self, latent_dim: int, hidden_units: int = 64, dropout: float = 0.1):
        super().__init__()
        self.encoder = keras.Sequential([
            layers.Dense(hidden_units),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(dropout),
            layers.Dense(hidden_units),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(dropout),
            layers.Dense(latent_dim),
        ])

    def call(self, x: keras.KerasTensor, training: bool = False) -> keras.KerasTensor:
        return self.encoder(x, training=training)
```

### Data Pipeline — Source to Tensor to Device

Keras 3 with PyTorch backend handles CPU/GPU placement automatically.
Your job is to get data into tensors — Keras decides where to run the computation.

```python
import torch
import pandas as pd
import numpy as np

def dataframe_to_tensors(df: pd.DataFrame, target_col: str, dtype=torch.float32):
    """Convert a DataFrame (from DB, CSV, or any source) into tensors.

    Keras 3 handles device placement — do NOT manually call .to(device).
    Just convert to tensors and let Keras move them as needed.
    """
    y = torch.tensor(df[target_col].values, dtype=dtype)
    X = torch.tensor(df.drop(columns=[target_col]).values, dtype=dtype)
    return X, y


def db_to_tensors(query: str, db_path: str, target_col: str):
    """Load from SQLite/PostgreSQL directly into tensors."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return dataframe_to_tensors(df, target_col)


def csv_to_tensors(path: str, target_col: str):
    """Load from CSV directly into tensors."""
    df = pd.read_csv(path)
    return dataframe_to_tensors(df, target_col)
```

**Key point:** Do NOT manually manage device placement with `.to("cuda")` or
`.to("cpu")`. Keras 3 handles this automatically — it decides what runs on
CPU vs GPU based on the operation. Just provide tensors and Keras does the rest.

If you need to check what Keras is using:
```python
print(keras.distribution.list_devices())  # shows available devices
```

### Data Splitting — Always Train / Validation / Test

```python
from torch.utils.data import DataLoader, TensorDataset, random_split

def prepare_data(X, y, train_ratio=0.7, val_ratio=0.15, batch_size=64, seed=42):
    """Split into train/val/test and return DataLoaders."""
    dataset = TensorDataset(X, y)
    n = len(dataset)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val

    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds, test_ds = random_split(
        dataset, [n_train, n_val, n_test], generator=generator
    )

    return {
        "train": DataLoader(train_ds, batch_size=batch_size, shuffle=True),
        "val": DataLoader(val_ds, batch_size=batch_size, shuffle=False),
        "test": DataLoader(test_ds, batch_size=batch_size, shuffle=False),
    }
```

### Standard Callback Stack

Always use this set of callbacks. Adjust parameters, but never skip any.

```python
def get_callbacks(checkpoint_path="best.keras", patience_stop=15, patience_lr=5):
    """Standard callback stack for all training runs."""
    return [
        # Save the best model based on validation loss
        keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        # Stop early if validation loss plateaus
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience_stop,
            restore_best_weights=True,
            verbose=1,
        ),
        # Reduce learning rate when validation loss plateaus
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=patience_lr,
            min_lr=1e-6,
            verbose=1,
        ),
        # Log training progress
        keras.callbacks.CSVLogger("training_log.csv"),
    ]
```

### Training — Standard (compile + fit)

```python
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss=keras.losses.MeanSquaredError(),
    metrics=[
        keras.metrics.MeanAbsoluteError(name="mae"),
        keras.metrics.RootMeanSquaredError(name="rmse"),
    ],
)

history = model.fit(
    data["train"],
    validation_data=data["val"],
    epochs=200,
    callbacks=get_callbacks(),
)

# Always evaluate on test set AFTER training is complete
test_results = model.evaluate(data["test"], return_dict=True)
print(f"Test loss: {test_results['loss']:.4f}, Test RMSE: {test_results['rmse']:.4f}")
```

### Training — Custom Training Loop

For full control (e.g. deep hedging, multi-loss, GAN). Override `train_step`
and `test_step` — see https://keras.io/api/models/model_training_apis/

```python
class CustomModel(keras.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loss_tracker = keras.metrics.Mean(name="loss")
        self.val_loss_tracker = keras.metrics.Mean(name="val_loss")

    @property
    def metrics(self):
        return [self.loss_tracker, self.val_loss_tracker]

    def train_step(self, data):
        x, y = data

        # Forward pass with gradient tracking
        with torch.enable_grad():
            y_pred = self(x, training=True)
            loss = self.compute_loss(x=x, y=y, y_pred=y_pred)

        # Backward pass — Keras handles this
        self.zero_grad()
        loss.backward()
        trainable_weights = [v for v in self.trainable_weights]
        gradients = [v.value.grad for v in trainable_weights]
        with torch.no_grad():
            self.optimizer.apply(gradients, trainable_weights)

        self.loss_tracker.update_state(loss)
        return {"loss": self.loss_tracker.result()}

    def test_step(self, data):
        x, y = data
        y_pred = self(x, training=False)
        loss = self.compute_loss(x=x, y=y, y_pred=y_pred)
        self.val_loss_tracker.update_state(loss)
        return {"val_loss": self.val_loss_tracker.result()}

    def compute_loss(self, x=None, y=None, y_pred=None, sample_weight=None):
        """Override this for custom loss functions."""
        pnl = y_pred - y
        return cvar_loss(pnl, alpha=0.5)
```

### Checkpointing in Custom Loops

When using fully custom training loops (not `keras.Model.fit`), you MUST
implement checkpoint saving manually. The standard callback stack does not
apply — you are responsible for equivalent behaviour.

```python
# Inside your custom train() method:
import os

checkpoint_dir = "checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)

for epoch in range(max_epochs):
    metrics = self.train_epoch(...)

    if epoch % val_freq == 0:
        val = self.validate(...)

        # Equivalent of ModelCheckpoint(save_best_only=True)
        if val['loss'] < best_loss:
            best_loss = val['loss']
            torch.save(model.state_dict(), f"{checkpoint_dir}/best.pt")

        # Periodic checkpoint for crash recovery
        if epoch % 500 == 0:
            torch.save({
                'epoch': epoch,
                'model_state': model.state_dict(),
                'optimizer_state': optimizer.state_dict(),
                'best_loss': best_loss,
            }, f"{checkpoint_dir}/checkpoint_epoch_{epoch}.pt")
```

### Learning Rate Scheduling

```python
# Option A: ReduceLROnPlateau (included in standard callbacks above)

# Option B: Cosine decay for known epoch count
lr_schedule = keras.optimizers.schedules.CosineDecay(
    initial_learning_rate=1e-3,
    decay_steps=n_train_samples * epochs // batch_size,
    alpha=1e-6,  # minimum lr
)
optimizer = keras.optimizers.Adam(learning_rate=lr_schedule)

# Option C: Warmup + decay
lr_schedule = keras.optimizers.schedules.PiecewiseConstantDecay(
    boundaries=[1000, 5000],
    values=[1e-4, 1e-3, 1e-4],  # warmup -> peak -> decay
)
```

### Regularisation

```python
# Dropout — use in all hidden layers, typical range 0.1-0.3
layers.Dropout(0.1)

# BatchNormalization — use before activation, helps convergence
layers.BatchNormalization()

# LayerNormalization — alternative when batch size is small
layers.LayerNormalization()

# Weight decay via optimizer (L2 regularisation)
optimizer = keras.optimizers.AdamW(
    learning_rate=1e-3,
    weight_decay=1e-4,
)

# Gradient clipping
optimizer = keras.optimizers.Adam(
    learning_rate=1e-3,
    clipnorm=1.0,  # clip by global norm
)
```

### Inference

```python
# Always training=False
output = model(x, training=False)
```

### Saving / Loading

```python
model.save("saved_models/encoder.keras")   # .keras format only
model = keras.saving.load_model("saved_models/encoder.keras",
                                 custom_objects={"MyLayer": MyLayer})
```

### Backend-Agnostic Math

```python
from keras import ops
x = ops.log(x)
x = ops.exp(x)
x = ops.sort(x, axis=-1)
x = ops.mean(x, axis=0)
x = ops.cumsum(x, axis=1)
x = ops.clip(x, 0.0, 1.0)
```

### Training Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

def plot_training_history(history_or_csv="training_log.csv"):
    """Plot loss and metrics curves for train and validation."""
    if isinstance(history_or_csv, str):
        df = pd.read_csv(history_or_csv)
    else:
        df = pd.DataFrame(history_or_csv.history)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Loss
    axes[0].plot(df["loss"], label="train")
    if "val_loss" in df:
        axes[0].plot(df["val_loss"], label="validation")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[0].set_xlabel("Epoch")

    # Check for overfitting: val_loss diverging from train_loss
    if "val_loss" in df:
        final_gap = df["val_loss"].iloc[-1] - df["loss"].iloc[-1]
        if final_gap > df["loss"].iloc[-1] * 0.5:
            axes[0].set_title("Loss (WARNING: possible overfitting)")

    # Metrics
    metric_cols = [c for c in df.columns if c not in ["epoch", "loss", "val_loss", "lr"]]
    for col in metric_cols:
        axes[1].plot(df[col], label=col)
    axes[1].set_title("Metrics")
    axes[1].legend()
    axes[1].set_xlabel("Epoch")

    plt.tight_layout()
    return fig
```

## Banned Patterns

| Do NOT use | Use instead |
|---|---|
| `tf.GradientTape()` | Override `compute_loss()` or `train_step()` |
| `@tf.function` | `torch.compile()` if needed |
| `tf.data.Dataset` | `torch.utils.data.DataLoader` |
| `model.predict(x)` | `model(x, training=False)` |
| `from tensorflow import keras` | `import keras` |
| `tf.keras.*` | `keras.*` |
| `K.mean(x)` | `ops.mean(x)` |
| `tf.random.*` | `keras.random.*` |
| `.numpy()` inside model code | Stay in tensor space |
| `import tensorflow as tf` | Never — not needed with Keras 3 |
| Training without validation data | Always pass `validation_data` to `fit()` |
| Training without callbacks | Always use the standard callback stack |
| No metrics during training | Always track loss + relevant metrics |
| Single train/test split | Always train / validation / test |
| `.to("cuda")` / `.to("cpu")` | Let Keras 3 handle device placement |
| Training on raw DataFrames/dicts | Convert to tensors first via `dataframe_to_tensors()` |
| Custom training loop without checkpoints | Save best + periodic checkpoints |

## Checklist

- [ ] `KERAS_BACKEND=torch` set before any keras import
- [ ] No tensorflow in `pyproject.toml` or imports
- [ ] All model math uses `keras.ops`, not `torch.*` or `np.*`
- [ ] Data split into train / validation / test
- [ ] Standard callback stack: ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, CSVLogger
- [ ] Metrics tracked during training (MAE, RMSE, or domain-specific)
- [ ] Regularisation applied (dropout, batch norm, weight decay as appropriate)
- [ ] Model evaluated on test set after training completes
- [ ] Training curves reviewed for overfitting
- [ ] Models saved as `.keras`, not `.h5`
- [ ] Inference uses `model(x, training=False)`, not `predict()`
- [ ] Data converted from source (DB/CSV/DataFrame) to tensors before training
- [ ] No manual `.to("cuda")` or `.to("cpu")` calls — Keras handles device placement
