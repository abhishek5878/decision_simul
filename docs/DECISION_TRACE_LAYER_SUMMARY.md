# Decision Trace Layer - Implementation Summary

## 🎯 What Was Added

A **Decision Trace Layer** that transforms the system from:
- **Before:** "A behavioral simulation engine" 
- **After:** "A system of record for how products decide which users they accept or reject"

## 🔑 Core Concept

**DecisionTrace** - A first-class primitive that captures WHY a persona continued or dropped at a specific step. This is captured AT DECISION TIME, not post-hoc.

This enables answering:
- "Which user types does this product work for?"
- "Which user types does it reject?"
- "What decisions caused that outcome?"

## 📦 New Module: `decision_graph/`

### Components

1. **`decision_trace.py`**
   - `DecisionTrace` - System of record primitive
   - `DecisionSequence` - Sequence of decisions for one persona
   - `CognitiveStateSnapshot` - State at decision time
   - `IntentSnapshot` - Intent state at decision time
   - `create_decision_trace()` - Factory function

2. **`decision_event.py`**
   - `DecisionEvent` - Reframes step as event, not computation
   - Queries: continuation rate, drop rate, dominant factors, rejection patterns

3. **`context_graph.py`**
   - `ContextGraph` - Graph built FROM traces (not inferred by ML)
   - `build_context_graph_from_traces()` - Core building function
   - Nodes: Personas, Steps, Intents, Failure modes
   - Edges: Decision outcomes, Repeated precedents, Dominant causal paths

4. **`graph_queries.py`**
   - Query functions for answering key questions:
     - `get_persona_acceptance_map()` - Which personas accepted/rejected
     - `get_step_rejection_map()` - Which steps reject which personas
     - `get_product_user_contract()` - Implicit user contract
     - `query_which_user_types_accepted()` - Accepted user types
     - `query_which_user_types_rejected()` - Rejected user types

## 🔧 Integration Points

### 1. Behavioral Engine (`behavioral_engine_intent_aware.py`)

**Modified:** `simulate_persona_trajectory_intent_aware()`

**Changes:**
- Captures decision traces AT DECISION TIME (before random sampling)
- Each step creates a `DecisionTrace` object
- Traces include: cognitive state, intent, dominant factors, probability
- Returns traces in result dictionary

**Key Code:**
```python
# Capture trace before sampling
trace = create_decision_trace(
    persona_id=persona_id,
    step_id=step_name,
    step_index=step_index,
    decision=decision,
    probability_before_sampling=final_prob,
    sampled_outcome=sampled_outcome,
    cognitive_state=cognitive_state_dict,
    intent_info=intent_info_dict,
    dominant_factors=dominant_factors,
    policy_version="v1.0"
)
decision_traces.append(trace)
```

### 2. Pipeline (`simulation_pipeline.py`)

**Modified:**
- `PipelineResult` - Now decision-first (includes traces and context graph)
- `_run_canonical_engine()` - Collects traces and builds context graph
- `run_simulation()` - Includes decision data in output

**PipelineResult Changes:**
```python
@dataclass
class PipelineResult:
    # ... existing fields ...
    decision_traces: Optional[List[Dict]] = None  # NEW
    context_graph_summary: Optional[Dict] = None  # NEW
```

### 3. Output Structure

**Before (metrics-first):**
```python
{
    'entry': {...},
    'behavioral': {...},
    'final_metrics': {...}
}
```

**After (decision-first):**
```python
{
    'entry': {...},
    'behavioral': {...},
    'final_metrics': {...},
    'decision_traces': [...],  # NEW
    'context_graph_summary': {  # NEW
        'dominant_failure_paths': [...],
        'persona_step_rejection_map': {...},
        'repeated_precedents': [...]
    }
}
```

## 🎯 What This Unlocks

### Answers to Key Questions

1. **"Which user types does this product work for?"**
   ```python
   result = run_simulation(...)
   accepted = query_which_user_types_accepted(
       sequences, graph
   )
   ```

2. **"Which user types does it reject?"**
   ```python
   rejected = query_which_user_types_rejected(
       sequences, graph
   )
   ```

3. **"What decisions caused that outcome?"**
   ```python
   for trace in decision_traces:
       if trace.decision == DecisionOutcome.DROP:
           print(f"Persona {trace.persona_id} dropped at {trace.step_id}")
           print(f"  Reasons: {trace.dominant_factors}")
   ```

4. **"Your product implicitly selects for these behaviors"**
   ```python
   contract = get_product_user_contract(graph, sequences)
   # Returns: acceptance patterns, rejection patterns, dominant rejection steps
   ```

## 🚀 Strategic Impact

### Before
- System answers: "What is likely to happen, and why, for this persona distribution?"
- Metrics-focused outputs
- Explanations but no system of record

### After
- System answers: "Which user types does this product actually work for, which ones does it reject, and what decisions caused that outcome?"
- Decision-first outputs
- System of record for product-user fit decisions

### Value Prop Alignment

**Value Prop:** "We show which user types actually make it through your product and which ones don't — and why."

**Before:** Narratively true (explains why)  
**After:** Architecturally true (system of record)

## 📊 Context Graph Insights

The context graph provides:

1. **Dominant Failure Paths**
   - Which steps cause which rejections
   - Frequency and patterns

2. **Persona-Step Rejection Map**
   - Which personas rejected at which steps
   - Systematic rejection patterns

3. **Repeated Precedents**
   - Behavioral patterns that repeat
   - Predictable decision outcomes

4. **Causal Paths**
   - Step → Failure mode → Persona type
   - Clear causal chains

## 🔄 Migration Notes

### No Breaking Changes

- Existing metrics still available
- Decision data is additive
- Backward compatible

### New Capabilities

- Query decision traces directly
- Build context graphs
- Analyze acceptance/rejection patterns
- Understand implicit user contracts

## 🎯 Next Steps (Future Enhancements)

1. **Decision Drift Monitoring** (not yet implemented)
   - Track changes in decision patterns over time
   - Detect when product's implicit contract changes

2. **Query Interface**
   - High-level API for common queries
   - "Which personas are rejected at step X?"
   - "What's the acceptance rate for user type Y?"

3. **Visualization**
   - Graph visualization
   - Decision flow diagrams
   - Rejection pattern heatmaps

## ✅ Success Criteria

After this upgrade, the system can:

✅ Capture decisions as first-class records  
✅ Build context graphs from traces  
✅ Answer "which user types accepted/rejected"  
✅ Understand implicit user contracts  
✅ Provide system of record for product-user fit  

**The system is now architecturally aligned with its value proposition.**

