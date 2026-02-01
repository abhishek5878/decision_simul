# Decision Attribution Module

Game-theoretic attribution of decision forces using Shapley values.

## Overview

This module answers: **"Which internal forces caused this specific decision?"**

It uses **cooperative game theory** (Shapley values) to quantify the contribution of each force (effort, risk, value, trust, intent) to a decision outcome.

## Key Principles

- ✅ **Local attribution only** - No global model, no training dataset
- ✅ **Deterministic** - Same inputs → same attribution
- ✅ **Game-theoretic** - Shapley values (fair contribution)
- ✅ **Decision-first** - "Which forces caused this decision?" not "feature importance"

## Architecture

```
Behavioral Engine
   ↓
Decision Trace (state_before, decision, state_after)
   ↓
Decision Attribution Layer  ← (THIS MODULE)
   ↓
Context Graph / DIS
```

## Components

### 1. `attribution_types.py`
- `DecisionAttribution` dataclass
- Immutable attribution records

### 2. `attribution_model.py`
- `LocalDecisionFunction` - Mirrors behavioral engine logic
- Deterministic function: `f(features) → P(CONTINUE)`

### 3. `shap_attributor.py`
- `compute_shapley_values` - Exact Shapley value computation
- `compute_decision_attribution` - Main attribution function

### 4. `attribution_utils.py`
- Decision-first aggregation utilities
- Step-conditioned, decision-conditioned summaries

## Usage

Attribution is automatically computed during simulation and attached to each `DecisionTrace`.

### Access Attribution

```python
from decision_graph.decision_trace import DecisionTrace

# Attribution is attached to each trace
trace: DecisionTrace = ...
if trace.attribution:
    print(f"Dominant forces: {trace.attribution.dominant_forces}")
    print(f"SHAP values: {trace.attribution.shap_values}")
```

### Aggregate Attribution

```python
from decision_attribution.attribution_utils import (
    aggregate_step_attribution,
    get_dominant_forces_by_step
)

# Get dominant forces for Step 4 (DROP decisions)
dominant = get_dominant_forces_by_step(traces, decision="DROP")
step_4_forces = dominant.get("step_4", [])

# Format as human-readable
from decision_attribution.attribution_utils import format_attribution_summary
summary = format_attribution_summary(step_4_forces)
# "At Step 4, effort explains 62% of rejection pressure, risk 21%, intent 6%."
```

## Features

Each decision is explained using these forces:

1. **Persona State Features:**
   - `cognitive_energy`
   - `intent_strength`
   - `effort_tolerance`
   - `risk_tolerance`
   - `trust_baseline`
   - `value_expectation`

2. **Step Force Features:**
   - `step_effort`
   - `step_risk`
   - `step_value`
   - `step_trust`
   - `intent_mismatch`

## Output Format

Attribution is included in `DecisionTrace` objects:

```json
{
  "attribution": {
    "step_id": "step_4",
    "decision": "DROP",
    "baseline_probability": 0.60,
    "final_probability": 0.35,
    "shap_values": {
      "effort": 0.62,
      "risk": 0.21,
      "intent_mismatch": 0.06,
      "value": 0.05,
      "trust": 0.05
    },
    "dominant_forces": [
      ["effort", 0.62],
      ["risk", 0.21],
      ["intent_mismatch", 0.06]
    ]
  }
}
```

## Design Constraints

✅ **What This Module Does:**
- Explains past simulated decisions only
- Fully traceable back to DecisionTrace IDs
- Deterministic and reproducible
- Uses game theory (Shapley values), not ML inference

❌ **What This Module Does NOT Do:**
- Black-box ML explanations
- Optimization suggestions
- Prediction claims
- Modify decision logic
- Global feature importance

## Methodology

1. **Local Decision Function:** Mirrors behavioral engine logic deterministically
2. **Shapley Value Computation:** Exact computation for small feature sets
3. **Baseline:** Neutral state (all features at midpoint)
4. **Attribution:** Fair contribution of each feature to decision outcome

## Integration

Attribution is computed **at decision time** in `behavioral_engine_intent_aware.py`:

```python
# Attribution is computed and attached to each trace
trace.attribution = compute_decision_attribution(...)
```

This ensures attribution is:
- First-class (not post-hoc)
- Deterministic
- Traceable
- Included in ledger/DIS outputs

## Example Output

**Founder-facing summary:**

> "At Step 4, effort explains 62% of rejection pressure, risk 21%, intent 6%."

**Ledger format:**

```json
{
  "decision_boundaries": [
    {
      "step_id": "step_4",
      "force_attribution": {
        "effort": 0.62,
        "risk": 0.21,
        "intent_mismatch": 0.06
      },
      "dominant_force": "effort"
    }
  ]
}
```

## Future Enhancements

- Counterfactual games ("If effort were reduced, would trust still matter?")
- Coalition analysis ("Which forces must combine to cause a drop?")
- Dominant strategy detection ("Which features dominate regardless of others?")

