# SKILL: Experiment Workflow

<!--
name: experiment-workflow
trigger: Hyperparameter tuning, algorithm comparison, model selection, or systematic experimentation
depends-on: [keras3-pytorch, experiment-logging]
applies-to: [all]
-->

## When to Apply

Read before running hyperparameter searches, comparing model architectures,
or making model selection decisions. This skill turns ad-hoc experimentation
into a systematic, reproducible process.

## Reference

- Optuna: https://optuna.readthedocs.io/
- Keras Tuner: https://keras.io/api/keras_tuner/

## Dependencies

- **keras3-pytorch** — models and training follow that skill's patterns.
- **experiment-logging** — all experiment results are logged to the shared DB.

## Rules

1. Never tune by hand — always use a structured search (Optuna, Keras Tuner, or at minimum a config grid).
2. Every experiment run must be logged to the DB with its full config, metrics, and git hash.
3. Always use the same train/val/test split across all runs in a comparison — never resplit.
4. Evaluate on the test set only once, after selecting the best model — never use test set during tuning.
5. Set a compute budget (max trials or max time) before starting a search.
6. Compare models on the same metric — define it upfront before running experiments.
7. Document the final selection decision: what was chosen, what was rejected, and why.

## Patterns

### Experiment Config — Define Before Running

```python
from dataclasses import dataclass, field

@dataclass
class ExperimentConfig:
    """Define the full experiment before running anything."""
    name: str                           # e.g. "encoder_architecture_search"
    objective_metric: str               # e.g. "val_loss", "val_rmse", "sharpe"
    direction: str = "minimize"         # "minimize" or "maximize"
    max_trials: int = 50               # compute budget
    max_hours: float = 4.0             # time budget (whichever hits first)
    fixed_seed: int = 42               # reproducibility
    notes: str = ""                    # why are we running this?
```

### Option A: Optuna (Recommended for Most Cases)

Optuna is the default choice — it uses Bayesian optimisation, prunes bad trials
early, and works with any training framework.

```python
import optuna
import torch
import keras
from db.schema import log_experiment

def create_objective(data, experiment_config):
    """Create an Optuna objective that trains and evaluates a model."""

    def objective(trial):
        # Define search space
        lr = trial.suggest_float("lr", 1e-5, 1e-2, log=True)
        hidden_units = trial.suggest_categorical("hidden_units", [32, 64, 128, 256])
        dropout = trial.suggest_float("dropout", 0.0, 0.5)
        batch_size = trial.suggest_categorical("batch_size", [32, 64, 128, 256])
        optimizer_name = trial.suggest_categorical("optimizer", ["adam", "adamw"])
        weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True)

        # Build model
        model = build_model(hidden_units=hidden_units, dropout=dropout)

        # Compile
        if optimizer_name == "adam":
            optimizer = keras.optimizers.Adam(learning_rate=lr)
        else:
            optimizer = keras.optimizers.AdamW(
                learning_rate=lr, weight_decay=weight_decay
            )

        model.compile(optimizer=optimizer, loss="mse", metrics=["mae"])

        # Train with pruning callback
        pruning_cb = optuna.integration.KerasPruningCallback(trial, "val_loss")

        history = model.fit(
            data["train"],
            validation_data=data["val"],
            epochs=100,
            callbacks=[
                pruning_cb,
                keras.callbacks.EarlyStopping(
                    patience=10, restore_best_weights=True
                ),
            ],
            verbose=0,
        )

        val_loss = min(history.history["val_loss"])

        # Log every trial to the DB
        log_experiment(
            project=experiment_config.name,
            experiment_type="hparam_search",
            metrics={
                "val_loss": val_loss,
                "val_mae": min(history.history["val_mae"]),
                "epochs_trained": len(history.history["loss"]),
            },
            hyperparams={
                "lr": lr,
                "hidden_units": hidden_units,
                "dropout": dropout,
                "batch_size": batch_size,
                "optimizer": optimizer_name,
                "weight_decay": weight_decay,
                "trial_number": trial.number,
            },
        )

        return val_loss

    return objective


def run_search(data, experiment_config: ExperimentConfig):
    """Run the full hyperparameter search."""
    import time

    study = optuna.create_study(
        study_name=experiment_config.name,
        direction=experiment_config.direction,
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5),
    )

    timeout = experiment_config.max_hours * 3600

    study.optimize(
        create_objective(data, experiment_config),
        n_trials=experiment_config.max_trials,
        timeout=timeout,
        show_progress_bar=True,
    )

    return study
```

### Option B: Keras Tuner (Simpler, Keras-Native)

Use when the search space is simpler and you want to stay fully within Keras.

```python
import keras_tuner as kt

def build_tunable_model(hp):
    """Define model with tunable hyperparameters."""
    hidden_units = hp.Choice("hidden_units", [32, 64, 128, 256])
    dropout = hp.Float("dropout", 0.0, 0.5, step=0.1)
    lr = hp.Float("lr", 1e-5, 1e-2, sampling="log")
    n_layers = hp.Int("n_layers", 1, 4)

    model = keras.Sequential()
    for _ in range(n_layers):
        model.add(keras.layers.Dense(hidden_units))
        model.add(keras.layers.BatchNormalization())
        model.add(keras.layers.Activation("relu"))
        model.add(keras.layers.Dropout(dropout))
    model.add(keras.layers.Dense(output_dim))

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr),
        loss="mse",
        metrics=["mae"],
    )
    return model


tuner = kt.BayesianOptimization(
    build_tunable_model,
    objective="val_loss",
    max_trials=50,
    directory="tuner_results",
    project_name="encoder_search",
)

tuner.search(
    data["train"],
    validation_data=data["val"],
    epochs=100,
    callbacks=[keras.callbacks.EarlyStopping(patience=10)],
)

# Best hyperparameters
best_hp = tuner.get_best_hyperparameters()[0]
print(best_hp.values)
```

### Option C: Manual Config Grid (Small Search Spaces Only)

For comparing a handful of known configurations (e.g. 3 model architectures).

```python
from dataclasses import asdict

configs = [
    {"name": "small", "hidden_units": 32, "n_layers": 2, "dropout": 0.1},
    {"name": "medium", "hidden_units": 64, "n_layers": 3, "dropout": 0.2},
    {"name": "large", "hidden_units": 128, "n_layers": 4, "dropout": 0.3},
]

results = []
for config in configs:
    model = build_model(**{k: v for k, v in config.items() if k != "name"})
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])

    history = model.fit(
        data["train"],
        validation_data=data["val"],
        epochs=100,
        callbacks=get_callbacks(f"best_{config['name']}.keras"),
        verbose=0,
    )

    val_loss = min(history.history["val_loss"])
    results.append({"config": config["name"], "val_loss": val_loss})

    log_experiment(
        project="model_comparison",
        experiment_type="architecture_search",
        metrics={"val_loss": val_loss},
        hyperparams=config,
    )

# Compare
results_df = pd.DataFrame(results).sort_values("val_loss")
print(results_df)
```

### Algorithm Comparison — Different Model Types

When comparing fundamentally different approaches (not just hyperparameters).

```python
from abc import ABC, abstractmethod

class ModelCandidate(ABC):
    """Base class for comparing different model types on equal footing."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def build(self, input_shape): ...

    @abstractmethod
    def train(self, data) -> dict:
        """Train and return metrics dict."""
        ...

    @abstractmethod
    def evaluate(self, test_data) -> dict:
        """Evaluate on test set and return metrics dict."""
        ...


def compare_candidates(candidates: list[ModelCandidate], data, test_data):
    """Run all candidates on the same data and compare."""
    results = []
    for candidate in candidates:
        print(f"\n--- {candidate.name()} ---")
        train_metrics = candidate.train(data)
        # DO NOT evaluate on test set here — only after selection

        results.append({
            "name": candidate.name(),
            **train_metrics,
        })

        log_experiment(
            project="algorithm_comparison",
            experiment_type="model_selection",
            metrics=train_metrics,
            hyperparams={"model_type": candidate.name()},
        )

    results_df = pd.DataFrame(results).sort_values("val_loss")
    print("\n=== Results (ranked by val_loss) ===")
    print(results_df.to_string(index=False))

    # Select best based on validation performance
    best = results_df.iloc[0]
    print(f"\nBest: {best['name']} (val_loss: {best['val_loss']:.4f})")

    # NOW evaluate the winner on the test set
    winner = next(c for c in candidates if c.name() == best["name"])
    test_metrics = winner.evaluate(test_data)
    print(f"Test performance: {test_metrics}")

    return results_df, test_metrics
```

### Analysing Search Results

```python
def analyse_search(study):
    """Summarise an Optuna study."""
    print(f"Best trial: #{study.best_trial.number}")
    print(f"Best value: {study.best_value:.4f}")
    print(f"Best params: {study.best_params}")
    print(f"Total trials: {len(study.trials)}")
    print(f"Pruned trials: {len(study.get_trials(states=[optuna.trial.TrialState.PRUNED]))}")

    # Parameter importance
    importance = optuna.importance.get_param_importances(study)
    print("\nParameter importance:")
    for param, imp in importance.items():
        print(f"  {param}: {imp:.3f}")

    # Visualisation
    fig1 = optuna.visualization.plot_optimization_history(study)
    fig2 = optuna.visualization.plot_param_importances(study)
    fig3 = optuna.visualization.plot_parallel_coordinate(study)

    return importance


def load_past_experiments(project: str):
    """Load past experiment results from the DB for comparison."""
    from db.schema import get_connection
    import pandas as pd

    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM experiments WHERE project = ? ORDER BY timestamp DESC",
        conn,
        params=(project,),
    )
    conn.close()
    return df
```

### Documenting the Decision

After selecting a model, record the decision in the project's CLAUDE.md
or a dedicated `EXPERIMENTS.md`:

```markdown
## Model Selection: encoder_architecture_search (2026-03-21)

**Objective:** Find the best encoder architecture for vol surface compression.

**Search:** Optuna, 50 trials, 4h budget, minimising val_loss.

**Result:**
- Best: 3-layer, 128 units, dropout=0.15, AdamW (wd=3e-4), lr=2e-3
- Val loss: 0.0023 (vs baseline 0.0089)
- Test loss: 0.0026

**Rejected:**
- 2-layer small (val_loss 0.0067) — underfitting
- 4-layer large (val_loss 0.0025) — marginal gain, 3x slower training

**Key finding:** Dropout > 0.3 consistently hurt performance. AdamW with
weight decay outperformed plain Adam in all trials.
```

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Tune hyperparameters by hand | Optuna, Keras Tuner, or config grid |
| Change train/val/test split between experiments | Fix the split, compare fairly |
| Evaluate on test set during tuning | Test set only once, after final selection |
| Run experiments without logging | Every run logged via `log_experiment()` |
| Start a search without a budget | Set `max_trials` and `max_hours` upfront |
| Pick a model without documenting why | Record decision with what was rejected and why |
| Compare models on different metrics | Define the objective metric before starting |

## Checklist

- [ ] Objective metric and direction defined before starting
- [ ] Compute budget set (max trials and/or max hours)
- [ ] Train/val/test split fixed across all runs
- [ ] Every trial logged to DB with full config and metrics
- [ ] Test set evaluated only once, on the selected model
- [ ] Search results analysed (parameter importance, pruned trials)
- [ ] Decision documented: what was chosen, what was rejected, why
