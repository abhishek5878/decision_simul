# Decision Continuity & Precedent Engine

Extends DropSim from a decision autopsy engine into a decision continuity system.

## Architecture

### Core Components

1. **DecisionEvent** - Immutable record of a decision made during execution
2. **ContinuityState** - Persistent belief state per entity (product/user/account)
3. **PrecedentGraph** - Aggregates historical DecisionEvents into reusable precedents
4. **ContinuityEngine** - Orchestrates recording and querying

### Key Invariants

- **Deterministic**: Same inputs → same outputs
- **Immutable Historical Records**: Past events are never mutated
- **Append-Only**: New events are added, but historical records remain unchanged
- **Incremental Learning**: Precedents are built incrementally from events

## Usage

### Recording Events During Simulation

```python
from decision_continuity import ContinuityEngine, DecisionEvent, BeliefState, DecisionEventType

# Initialize engine
engine = ContinuityEngine(storage_path="./continuity_data")

# During simulation, record a decision event
event = DecisionEvent(
    event_id="evt_123",
    entity_id="product_credigo",
    entity_type="product",
    step_id="Step 3",
    step_index=2,
    event_type=DecisionEventType.CONTINUATION,
    belief_state_before=BeliefState(
        trust_level=0.6,
        value_perception=0.3,
        commitment_level=0.2,
        cognitive_energy=0.7,
        risk_perception=0.4,
        intent_strength=0.8
    ),
    belief_state_after=BeliefState(
        trust_level=0.65,
        value_perception=0.3,
        commitment_level=0.4,
        cognitive_energy=0.6,
        risk_perception=0.4,
        intent_strength=0.8
    ),
    action_considered="Continue to next step",
    action_taken="Continue to next step",
    alternatives_rejected=["Drop", "Skip step"],
    outcome_observed="User continued",
    confidence_level=0.75
)

# Record the event
engine.record_event(event)
```

### Recording from DecisionTrace

```python
from decision_continuity import ContinuityEngine
from decision_graph.decision_trace import DecisionTrace

engine = ContinuityEngine()

# Convert existing DecisionTrace to DecisionEvent
event = engine.record_event_from_trace(
    trace=decision_trace,
    entity_id="product_credigo",
    entity_type="product",
    action_considered="Continue",
    action_taken="Continue",
    alternatives_rejected=["Drop"],
    outcome_observed="User continued",
    confidence_level=0.8
)
```

### Querying Precedents

```python
# Query: "What usually works when belief collapses due to delayed value?"
results = engine.query_what_usually_works(
    condition_description="belief collapses due to delayed value",
    step_id="Step 3"
)

# Results show actions with highest success rates
for result in results:
    print(f"Action: {result['action']}")
    print(f"Success Rate: {result['success_rate']}")
    print(f"Occurrences: {result['total_occurrences']}")
```

### Getting Entity Belief State

```python
# Get current belief state for a product
belief_state = engine.get_entity_belief_state(
    entity_id="product_credigo",
    entity_type="product"
)

print(f"Trust: {belief_state['trust']}")
print(f"Value: {belief_state['value']}")
print(f"Commitment: {belief_state['commitment']}")
```

## Integration Points

### With DecisionTrace

The `create_decision_event_from_trace()` function bridges DecisionTrace and DecisionEvent systems.

### With ContextGraph

Precedents can be queried to inform context graph construction.

### With DecisionAutopsy

ContinuityState can provide historical context for autopsy generation.

## Data Persistence

State is persisted to JSON files:
- `continuity_states.json` - Entity continuity states
- `precedent_graph.json` - Precedent graph structure
- `event_history.json` - Recent event log (last 10k events)

## Example Flow

1. **During Simulation**: DecisionTrace is created
2. **Event Recording**: DecisionTrace → DecisionEvent conversion
3. **Continuity Update**: ContinuityState updated for entity
4. **Precedent Building**: PrecedentGraph updated with new event
5. **Query Time**: Future simulations query precedents for guidance

## Example Query

```python
# "What usually works when belief collapses due to delayed value?"
results = engine.query_what_usually_works(
    "belief collapses due to delayed value",
    step_id="Step 3"
)

# Returns actions like:
# - "Show value before asking for commitment" (success_rate: 0.85)
# - "Reduce effort demand" (success_rate: 0.72)
# - "Add reassurance signals" (success_rate: 0.68)
```

