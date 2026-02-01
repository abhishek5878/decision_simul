# Deprecated Components

**⚠️ IMPORTANT: Use `simulation_pipeline.run_simulation()` as the ONLY entry point.**

This document lists deprecated components that should NOT be used directly.

---

## 🚫 Deprecated Behavioral Engines

The following behavioral engines are **DEPRECATED** and should not be used:

### 1. `behavioral_engine.py`
- **Status:** ❌ DEPRECATED
- **Reason:** Replaced by canonical engine
- **Use Instead:** `simulation_pipeline.run_simulation()`
- **Removal Date:** TBD

### 2. `behavioral_engine_improved.py`
- **Status:** ❌ DEPRECATED
- **Reason:** Replaced by canonical engine
- **Use Instead:** `simulation_pipeline.run_simulation()`
- **Removal Date:** TBD

### 3. `behavioral_engine_semantic_aware.py`
- **Status:** ❌ DEPRECATED
- **Reason:** Replaced by canonical engine
- **Use Instead:** `simulation_pipeline.run_simulation()`
- **Removal Date:** TBD

### 4. `behavioral_engine_stabilized.py`
- **Status:** ❌ DEPRECATED
- **Reason:** Replaced by canonical engine
- **Use Instead:** `simulation_pipeline.run_simulation()`
- **Removal Date:** TBD

---

## ✅ Canonical Engine

**ONLY USE THIS:**

- **`behavioral_engine_intent_aware.py`** - ✅ CANONICAL
  - This is the ONLY engine used by `simulation_pipeline`
  - Do not import directly - use `simulation_pipeline.run_simulation()` instead

---

## 🚫 Deprecated Run Scripts

The following run scripts are **DEPRECATED**:

- `run_behavioral_simulation.py` - ❌ Use `simulation_pipeline.run_simulation()`
- `run_credigo_original.py` - ❌ Use `simulation_pipeline.run_simulation(product_config="credigo")`
- `run_credigo_improved.py` - ❌ Use `simulation_pipeline.run_simulation(product_config="credigo")`
- `run_blink_money_improved.py` - ❌ Use `simulation_pipeline.run_simulation(product_config="blink_money")`
- Any script that imports deprecated engines directly

---

## ✅ Correct Usage

### ✅ DO THIS:

```python
from simulation_pipeline import run_simulation

# Run simulation
result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000
)

# Access results
print(f"Total conversion: {result.final_metrics['total_conversion']:.2%}")
print(f"Drift status: {result.drift['overall_status']}")

# Export
result.export('my_result.json')
```

### ❌ DON'T DO THIS:

```python
# DON'T import deprecated engines directly
from behavioral_engine_improved import run_behavioral_simulation_improved  # ❌ DEPRECATED

# DON'T use old run scripts
# python run_credigo_improved.py  # ❌ DEPRECATED

# DON'T bypass the pipeline
from behavioral_engine_intent_aware import run_intent_aware_simulation  # ⚠️ Use pipeline instead
```

---

## 🔄 Migration Guide

### Old Way (DEPRECATED):

```python
from behavioral_engine_improved import run_behavioral_simulation_improved
from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
from load_dataset import load_and_sample

df, _ = load_and_sample(n=1000, seed=42)
result_df = run_behavioral_simulation_improved(df, product_steps=CREDIGO_SS_11_STEPS)
```

### New Way (CANONICAL):

```python
from simulation_pipeline import run_simulation

result = run_simulation(
    product_config="credigo",
    mode="production",
    n_personas=1000,
    seed=42
)

# Result includes everything:
# - Entry model results
# - Behavioral results
# - Intent analysis
# - Calibration (if available)
# - Evaluation (if mode allows)
# - Drift monitoring (if production mode)
```

---

## 📋 What Gets Included in Pipeline

The canonical pipeline automatically includes:

1. ✅ **Entry Model** - Always runs
2. ✅ **Behavioral Engine** - Uses canonical engine only
3. ✅ **Intent Layer** - Built into canonical engine
4. ✅ **Calibration** - Applied if available (evaluation/production modes)
5. ✅ **Evaluation** - Runs in evaluation/production modes
6. ✅ **Drift Monitoring** - Runs in production mode only

---

## 🎯 Execution Modes

The pipeline supports three modes:

### `mode="research"`
- Entry model: ✅
- Behavioral engine: ✅
- Calibration: ❌ (skipped)
- Evaluation: ❌ (skipped)
- Drift monitoring: ❌ (skipped)

**Use for:** Quick experiments, development

### `mode="evaluation"`
- Entry model: ✅
- Behavioral engine: ✅
- Calibration: ✅ (applied if available)
- Evaluation: ✅
- Drift monitoring: ❌ (skipped)

**Use for:** Comprehensive analysis, validation

### `mode="production"`
- Entry model: ✅
- Behavioral engine: ✅
- Calibration: ✅ (applied if available)
- Evaluation: ✅
- Drift monitoring: ✅

**Use for:** Production deployments, monitoring

---

## ⚠️ Breaking Changes

If you're migrating from old scripts:

1. **Import changes:** Use `simulation_pipeline` instead of direct engine imports
2. **Output format:** Unified output object instead of scattered JSONs
3. **Execution flow:** Fixed pipeline stages, no customization
4. **Engine choice:** Only canonical engine used

---

## 📝 Notes

- Deprecated components are kept for backward compatibility but will be removed in future versions
- All new code should use `simulation_pipeline.run_simulation()`
- If you need functionality not in the pipeline, please file an issue

---

**Last Updated:** January 2026

