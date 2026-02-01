# Long-term Calibration Layer

This module provides a data-grounded calibration system for the behavioral simulation engine. It transforms the system from a hand-tuned simulator into a continuously learning, empirically grounded behavioral model.

## 🎯 Purpose

**Do NOT modify behavioral logic** - only calibrate scaling parameters to match observed real-world outcomes.

## 📁 Structure

```
calibration/
├── parameter_space.py    # Define learnable parameters with bounds
├── loss_functions.py     # Compare simulation vs observed metrics
├── optimizer.py          # Optimization algorithms (random search, Bayesian)
├── calibrator.py         # Main calibration runner
├── validation.py         # Guardrails and validation checks
└── __init__.py           # Module exports
```

## 🔧 Key Parameters

Calibratable parameters (with defaults):

- **BASE_COMPLETION_RATE** (default: 0.60): Base completion probability floor
- **PERSISTENCE_BONUS_START** (default: 0.18): Persistence bonus at journey start
- **PERSISTENCE_BONUS_RATE** (default: 0.22): Rate persistence bonus increases with progress
- **INTENT_PENALTY_WEIGHT** (default: 0.025): Weight for intent mismatch penalties
- **FRICTION_PENALTY_WEIGHT** (default: 1.0): Global multiplier for friction penalties
- **VALUE_SENSITIVITY** (default: 1.0): Multiplier for value signal impact
- **COGNITIVE_PENALTY_WEIGHT** (default: 1.0): Weight for cognitive/fatigue penalties
- **EFFORT_PENALTY_WEIGHT** (default: 1.0): Weight for effort penalties
- **RISK_PENALTY_WEIGHT** (default: 1.0): Weight for risk/loss-aversion penalties

## 📊 Observables

Calibration compares:

1. **Completion rate**: Overall completion rate (0-1)
2. **Drop-off distribution**: Drop rate per step
3. **Average steps completed**: Mean steps before exit/completion

## 🚀 Usage

### Basic Example

```python
from calibration import (
    CalibrationConfig,
    calibrate_parameters,
    export_calibration_result
)
from behavioral_engine_improved import run_behavioral_simulation_improved
from load_dataset import load_and_sample
from derive_features import derive_all_features

# Load data
df, _ = load_and_sample(n=1000, seed=42)
df = derive_all_features(df)

# Define observed metrics (from real-world data)
observed_metrics = {
    'completion_rate': 0.23,  # 23% observed completion
    'dropoff_by_step': {
        'Step 1': 0.15,
        'Step 2': 0.20,
        'Step 3': 0.25,
        # ... etc
    },
    'avg_steps_completed': 3.8
}

# Configure calibration
config = CalibrationConfig(
    max_iterations=100,
    early_stopping_patience=20,
    verbose=True
)

# Run calibration
result = calibrate_parameters(
    simulation_function=run_behavioral_simulation_improved,
    simulation_args={
        'df': df,
        'verbose': False,
        'product_steps': product_steps,
        'seed': 42
    },
    observed_metrics=observed_metrics,
    product_steps=product_steps,
    config=config,
    engine_module='behavioral_engine_improved'
)

# Export results
export_calibration_result(result, 'calibration_results.json')

# Use calibrated parameters
print(f"Fit score: {result.fit_score:.4f}")
print(f"Calibrated parameters: {result.calibrated_parameters}")
```

### With Intent-Aware Engine

```python
from behavioral_engine_intent_aware import run_intent_aware_simulation

result = calibrate_parameters(
    simulation_function=run_intent_aware_simulation,
    simulation_args={
        'df': df,
        'product_steps': product_steps,
        'fixed_intent': CREDIGO_GLOBAL_INTENT,
        'verbose': False,
        'seed': 42
    },
    observed_metrics=observed_metrics,
    product_steps=product_steps,
    config=config,
    engine_module='behavioral_engine_intent_aware'
)
```

## ✅ Validation & Guardrails

The calibration system enforces:

1. **Probability bounds**: All probabilities remain in [0.05, 0.95]
2. **Monotonicity**: More friction → lower completion
3. **Overfitting detection**: Penalizes suspiciously perfect matches
4. **Parameter dominance**: Warns if parameters change too dramatically from defaults

## 📈 Output Artifacts

After calibration, you get:

```json
{
  "calibrated_parameters": {
    "BASE_COMPLETION_RATE": 0.65,
    "PERSISTENCE_BONUS_START": 0.20,
    ...
  },
  "fit_score": 0.87,
  "loss": 0.13,
  "confidence_intervals": {
    "BASE_COMPLETION_RATE": [0.60, 0.70],
    ...
  },
  "recommended_defaults": {...},
  "validation_results": {...}
}
```

## 🎯 Success Criteria

- Model outputs match observed data within ±5-10%
- No single parameter dominates outcome
- Behavior remains interpretable
- Small input changes → smooth output changes

## ⚠️ Important Notes

1. **No behavioral logic changes** - only parameter scaling
2. **Explainable** - every parameter has clear meaning
3. **Interpretable** - model structure unchanged
4. **Production-ready** - defensible, scalable, continuously learning

