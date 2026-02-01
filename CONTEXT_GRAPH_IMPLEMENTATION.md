# Context Graph Implementation

## Overview

The Context Graph layer records event-level behavioral traces during simulation runs, enabling:
- **Causal inspection**: Understand why users drop at specific steps
- **Path-based reasoning**: See which paths users take through the product
- **"Why did this happen?" explanations**: Trace back from outcomes to causes
- **Future extensibility**: Foundation for counterfactual simulation

This is **structured logging + reasoning** over the existing engine, not a new model.

## Architecture

### 1. Event Abstraction (`Event`)

Each behavioral transition is captured as an `Event`:

```python
@dataclass
class Event:
    step_id: str
    persona_id: str
    variant_id: str
    state_before: Dict[str, float]  # cognitive_energy, perceived_risk, etc.
    state_after: Dict[str, float]
    applied_costs: Dict[str, float]  # cognitive_cost, effort_cost, risk_cost, etc.
    decision: Literal["continue", "drop"]
    dominant_factor: str  # e.g., "fatigue", "risk", "effort", "multi-factor"
    timestamp: int  # monotonic step index (0-based)
```

**Generated at every step evaluation** inside the simulation loop.

### 2. Event Trace (`EventTrace`)

Each persona × state-variant produces exactly one `EventTrace`:

```python
@dataclass
class EventTrace:
    persona_id: str
    variant_id: str
    events: List[Event]
    final_outcome: Literal["completed", "dropped"]
```

**Not persisted globally** — exists per simulation run.

### 3. Context Graph (`ContextGraph`)

Aggregated graph from all event traces:

```python
@dataclass
class ContextGraph:
    nodes: Dict[str, StepNode]  # step_id -> StepNode
    edges: Dict[Tuple[str, str], EdgeStats]  # (from_step, to_step) -> EdgeStats
```

**Nodes** = product steps with:
- Total entries/exits/drops
- Average state values (cognitive_energy, perceived_risk, etc.)
- Dominant failure factor

**Edges** = transitions between steps with:
- Traversal count
- Average state deltas (energy loss, risk increase, etc.)
- Dominant failure factor

## Integration

### Simulation Loop Modification

In `dropsim_simulation_runner.py`, the simulation loop now:

1. **Captures state_before** before `update_state()`
2. **Captures state_after** after `update_state()`
3. **Creates Event** with decision and dominant factor
4. **Appends to EventTrace**
5. **Builds ContextGraph** after all simulations complete

**No logic or math altered** — only added event recording.

### Output Extension

The context graph is added to result metadata:

```python
result_df.attrs['context_graph'] = context_graph.to_dict()
result_df.attrs['context_graph_summary'] = context_graph_summary
```

Accessible via:
- `result_df.attrs['context_graph']` — Full graph structure
- `result_df.attrs['context_graph_summary']` — Pre-computed insights

## Query Functions

### 1. `query_paths_to_failure()`

Find paths that most often lead to failure:

```python
failure_paths = query_paths_to_failure(context_graph, min_failures=10)
# Returns: [{'path': [step1, step2], 'failure_count': N, 'dominant_factor': '...'}, ...]
```

### 2. `query_high_energy_loss_transitions()`

Find transitions with highest cognitive energy loss:

```python
energy_loss = query_high_energy_loss_transitions(context_graph, top_n=10)
# Returns: [{'from_step': '...', 'to_step': '...', 'avg_energy_delta': -0.5, ...}, ...]
```

### 3. `query_fragile_transitions()`

Find fragile steps (high drop rate):

```python
fragile = query_fragile_transitions(context_graph, min_traversals=5)
# Returns: [{'step_id': '...', 'drop_rate': 0.3, 'total_drops': N, ...}, ...]
```

### 4. `query_successful_paths_despite_risk()`

Find paths that succeed despite high risk/effort:

```python
successful = query_successful_paths_despite_risk(context_graph, min_traversals=10)
# Returns: [{'from_step': '...', 'to_step': '...', 'success_rate': 0.8, ...}, ...]
```

### 5. `query_dominant_paths()`

Find the most common paths through the product:

```python
paths = query_dominant_paths(context_graph, min_traversals=50)
# Returns: [{'path': [step1, step2], 'traversal_count': N, ...}, ...]
```

## Usage Example

```python
from dropsim_simulation_runner import run_simulation_with_database_personas
from dropsim_context_graph import (
    query_paths_to_failure,
    query_high_energy_loss_transitions,
    query_fragile_transitions
)

# Run simulation
result_df = run_simulation_with_database_personas(
    product_steps=product_steps,
    n_personas=1000
)

# Access context graph
context_graph_dict = result_df.attrs.get('context_graph')
context_graph_summary = result_df.attrs.get('context_graph_summary')

# Query insights
if context_graph_dict:
    from dropsim_context_graph import ContextGraph
    # Reconstruct graph (or use summary directly)
    summary = context_graph_summary
    
    print("Top failure paths:", summary['failure_paths'])
    print("High energy loss:", summary['high_energy_loss_transitions'])
    print("Fragile steps:", summary['fragile_steps'])
```

## Output Format

The context graph is included in the wizard output:

```python
result = run_fintech_wizard(...)
scenario_result = result['scenario_result']

# Access context graph
context_graph = scenario_result.get('context_graph')
context_graph_summary = scenario_result.get('context_graph_summary')
```

## Key Design Principles

1. **No ML models**: Deterministic aggregation only
2. **No embeddings**: Structured data only
3. **No clustering**: Explicit graph structure
4. **No probabilistic sampling**: Deterministic behavior
5. **No re-training**: Pure computation from events

## Future Extensibility

The Context Graph enables:

1. **Counterfactual simulation**: "What if we reduced cognitive_demand at step X?"
2. **Path optimization**: "Which path has lowest energy loss?"
3. **Persona segmentation**: "Which persona types fail on same transitions?"
4. **A/B testing**: Compare graphs from different product configurations

## Files Modified

1. **`dropsim_context_graph.py`** (NEW): Core context graph implementation
2. **`dropsim_simulation_runner.py`**: Added event capture and graph building
3. **`dropsim_wizard.py`**: Added context graph to output

## Testing

Run a simulation and check for context graph:

```python
result_df = run_simulation_with_database_personas(...)
assert 'context_graph' in result_df.attrs
assert 'context_graph_summary' in result_df.attrs
```

The context graph summary includes:
- Total nodes and edges
- Top 5 failure paths
- Top 5 high energy loss transitions
- Top 5 fragile steps
- Top 5 successful paths despite risk
- Top 5 dominant paths

