# Decision Autopsy: Module Mapping

This document maps which engine modules feed which sections of the Decision Autopsy output.

## Architecture Overview

```
Simulation Pipeline
    ↓
Decision Traces (decision_graph/decision_trace.py)
    ↓
Attribution Layer (decision_attribution/)
    ↓
Context Graph (decision_graph/context_graph.py)
    ↓
Decision Autopsy Generator (decision_autopsy_generator.py)
    ↓
Decision Autopsy Document (Markdown/JSON)
```

## Section-by-Section Mapping

### Section 0: Header (Identity & Legitimacy)

**Source Modules:**
- `simulation_pipeline.py` → `PipelineResult.execution_mode`
- `simulation_pipeline.py` → `PipelineResult.decision_traces` (count)
- `decision_autopsy_generator.py` → `compute_simulation_hash()` (from product_steps + config)
- `decision_autopsy_generator.py` → `compute_confidence_level()` (from trace variance)

**Data Flow:**
```
PipelineResult
    → product_id (from config)
    → execution_mode
    → decision_traces (count)
    → compute_simulation_hash(product_steps, config)
    → compute_confidence_level(traces)
```

### Section 1: One-Line Verdict

**Source Modules:**
- `decision_attribution/attribution_types.py` → `DecisionAttribution.shap_values` (aggregated)
- `decision_graph/decision_trace.py` → `DecisionTrace.attribution` (for drops at irreversible step)
- `decision_autopsy_generator.py` → `generate_one_line_verdict()` (aggregates SHAP values)

**Data Flow:**
```
DecisionTrace (drops at irreversible step)
    → trace.attribution.shap_values
    → aggregate force contributions
    → identify dominant force
    → generate verdict sentence (deterministic pattern matching)
```

### Section 2: Irreversible Moment Detection

**Source Modules:**
- `decision_graph/decision_trace.py` → `DecisionTrace.step_id`, `DecisionTrace.decision`, `DecisionTrace.probability_before_sampling`
- `product_steps` (from product config) → `irreversibility` flag, `delay_to_value`
- `decision_autopsy_generator.py` → `detect_irreversible_moment()` (algorithmic detection)

**Data Flow:**
```
DecisionTrace (all traces)
    → group by step_id
    → compute drop_rate, commitment_delta, exit_probability_gradient
    → product_steps[step_id].irreversibility
    → compute irreversible_score
    → select step with max score
```

### Section 3: Belief State Transition (Before vs After)

**Source Modules:**
- `decision_graph/decision_trace.py` → `DecisionTrace.cognitive_state_snapshot` (energy, risk, effort, value, control)
- `product_steps` → `delay_to_value`, `explicit_value`
- `decision_autopsy_generator.py` → `reconstruct_belief_states()` (maps cognitive state to belief vector)

**Data Flow:**
```
DecisionTrace (at irreversible step)
    → trace.cognitive_state_snapshot
    → aggregate before_state (all traces reaching step)
    → aggregate after_state (traces that dropped)
    → map to belief components:
        - task_framing (from delay_to_value)
        - commitment_level (from perceived_control)
        - expected_value_timing (from delay_to_value)
        - perceived_risk (from cognitive_state.risk)
```

### Section 4: Recovery Impossibility Proof

**Source Modules:**
- `decision_graph/decision_trace.py` → `DecisionTrace.persona_id`, `DecisionTrace.step_index`, `DecisionTrace.decision`
- `decision_autopsy_generator.py` → `compute_recovery_impossibility()` (analyzes persona journeys)

**Data Flow:**
```
DecisionTrace (all traces)
    → group by persona_id
    → sort by step_index
    → detect retries (drops followed by continues)
    → detect backtracking (step_index decreases)
    → compute rates
```

### Section 5: Single Highest-Leverage Counterfactual

**Source Modules:**
- `product_steps` → `delay_to_value`, `irreversibility`, `explicit_value`
- `decision_attribution/` → Attribution sensitivity analysis (implicit)
- `decision_autopsy_generator.py` → `identify_counterfactual()` (deterministic sequencing analysis)

**Data Flow:**
```
IrreversibleMoment
    → step position_in_flow
    → product_steps[step_id].delay_to_value
    → product_steps[step_id].irreversibility
    → product_steps[step_id].explicit_value
    → deterministic counterfactual generation (pattern matching)
```

### Section 6: Falsifiability Conditions

**Source Modules:**
- `decision_autopsy_generator.py` → `compute_recovery_impossibility()` (retry_rate)
- `decision_autopsy_generator.py` → `compute_variant_sensitivity()` (variant drop rates)
- `decision_autopsy_generator.py` → `IrreversibleMoment.commitment_delta`
- `decision_autopsy_generator.py` → `generate_falsifiability_conditions()` (deterministic conditions)

**Data Flow:**
```
Autopsy data
    → retry_rate (from recovery analysis)
    → variant_sensitivity (from variant analysis)
    → commitment_delta (from irreversible moment)
    → generate 2-3 falsifiability conditions (deterministic)
```

### Section 7: Variant Sensitivity Snapshot

**Source Modules:**
- `decision_graph/decision_trace.py` → `DecisionTrace.persona_id` (contains variant), `DecisionTrace.decision`
- `decision_autopsy_generator.py` → `compute_variant_sensitivity()` (groups by variant, computes drop rates)

**Data Flow:**
```
DecisionTrace (all traces)
    → extract variant from persona_id
    → group by variant
    → compute drop_rate per variant
    → select most_sensitive (max drop_rate)
    → select least_sensitive (min drop_rate)
```

### Section 8: Explicit Non-Claims

**Source Modules:**
- `decision_autopsy_generator.py` → `generate_non_claims()` (static, deterministic list)

**Data Flow:**
```
Static generation (no input dependencies)
    → predefined list of non-claims
    → predefined list of non-intended uses
```

### Section 9: Closing Identity Line

**Source Modules:**
- `decision_autopsy_generator.py` → Fixed string constant

**Data Flow:**
```
Static string: "This analysis explains why belief collapsed, not how to redesign the product."
```

## Determinism Guarantees

### Same Inputs → Same Output

All sections are deterministic:
- **Section 0**: Hash is deterministic, confidence computed from variance (deterministic)
- **Section 1**: Verdict generated from aggregated SHAP values (deterministic aggregation)
- **Section 2**: Irreversible moment selected by max score (deterministic selection)
- **Section 3**: Belief states aggregated from traces (deterministic aggregation)
- **Section 4**: Recovery rates computed from trace patterns (deterministic computation)
- **Section 5**: Counterfactual generated from step properties (deterministic pattern matching)
- **Section 6**: Falsifiability conditions generated deterministically
- **Section 7**: Variant sensitivity computed from drop rates (deterministic)
- **Section 8**: Static list (deterministic)
- **Section 9**: Static string (deterministic)

### No LLM Creativity

All text generation uses:
- Pattern matching (e.g., verdict generation based on dominant force + step context)
- Deterministic aggregation (e.g., belief state reconstruction)
- Static templates (e.g., non-claims, closing line)

### Traceability

Every sentence maps to:
- **DecisionTrace objects** (sections 1, 2, 3, 4, 7)
- **SHAP attribution values** (section 1)
- **Product step definitions** (sections 2, 3, 5)
- **Computed metrics** (sections 0, 2, 4, 7)

## Integration Points

### Input: PipelineResult

```python
from simulation_pipeline import PipelineResult
from decision_autopsy_generator import DecisionAutopsyGenerator

# Load product steps
product_steps = load_product_steps(product_id)

# Initialize generator
generator = DecisionAutopsyGenerator(product_steps)

# Generate autopsy
autopsy = generator.generate(
    product_id=result.product_id,
    traces=[DecisionTrace.from_dict(t) for t in result.decision_traces],
    run_mode=result.execution_mode,
    config={...}
)

# Export
markdown = generator.to_markdown(autopsy)
json_output = generator.to_json(autopsy)
```

### Output Formats

- **Markdown**: Human-readable, deterministic formatting
- **JSON**: Machine-readable, same structure as schema

