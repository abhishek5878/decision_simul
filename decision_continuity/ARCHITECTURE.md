# Decision Continuity & Precedent Engine - Architecture

## Overview

Extends DropSim from a decision autopsy engine into a decision continuity system that:
- Captures decision traces DURING execution (not just post-simulation)
- Maintains persistent belief state per entity (product/user/account)
- Converts past decision traces into reusable precedents
- Enables compounding learning across runs

## Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ContinuityEngine                          │
│  (Orchestrates recording, querying, persistence)            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ DecisionEvent│   │ContinuityState│   │PrecedentGraph│
│  (Primitive) │   │ (Per Entity)  │   │ (Aggregates)│
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Integration │
                    │  (Traces,    │
                    │   Graph,     │
                    │   Autopsy)   │
                    └──────────────┘
```

## Components

### 1. DecisionEvent

**Purpose**: Immutable record of a decision made during execution.

**Key Fields**:
- `belief_state_before` / `belief_state_after`: Belief state transition
- `action_considered` / `action_taken`: What was considered vs. what was done
- `alternatives_rejected`: What was considered but not taken
- `outcome_observed`: What actually happened
- `confidence_level`: Confidence in the decision

**Invariants**:
- Immutable once created
- Captured DURING execution (not post-hoc)
- Contains full context

### 2. ContinuityState

**Purpose**: Persistent belief state per entity that accumulates across runs.

**Key Fields**:
- `cumulative_trust` / `cumulative_value` / `cumulative_commitment`: Weighted averages
- `commitment_history` / `value_realization_history` / `trust_change_history`: Event logs
- `irreversible_events`: Events that permanently affect future decisions
- `active_hypotheses`: Hypotheses being tested

**Invariants**:
- Append-only: Historical records never mutated
- Incremental updates: New events update cumulative metrics
- Entity-scoped: One ContinuityState per entity

### 3. PrecedentGraph

**Purpose**: Aggregates historical DecisionEvents into reusable precedents.

**Structure**:
- **Nodes**: Condition signatures (patterns of conditions)
- **Edges**: Transitions between condition signatures
- **Node Data**: Action → outcome distributions

**Key Operations**:
- `add_event()`: Add event to graph (creates/updates precedents)
- `query_precedents()`: Find precedents matching conditions
- `query_what_usually_works()`: High-level query for recommendations

**Invariants**:
- Precedents derived from historical events, never mutated
- New events create new or update existing precedents incrementally

### 4. ContinuityEngine

**Purpose**: Main orchestrator for the system.

**Key Operations**:
- `record_event()`: Record DecisionEvent during execution
- `record_event_from_trace()`: Convert DecisionTrace to DecisionEvent
- `get_continuity_state()`: Get persistent state for entity
- `query_precedents()`: Query what has worked historically
- `query_what_usually_works()`: High-level recommendation query

**Persistence**:
- Saves to JSON files: `continuity_states.json`, `precedent_graph.json`, `event_history.json`
- Loads on initialization

## Data Flow

### During Simulation

```
1. DecisionTrace created (existing system)
   ↓
2. DecisionTrace → DecisionEvent conversion
   ↓
3. ContinuityEngine.record_event()
   ↓
4. ContinuityState updated (cumulative metrics)
   ↓
5. PrecedentGraph updated (new precedent or update existing)
   ↓
6. State persisted to disk
```

### Query Time

```
1. Query: "What usually works when [condition]?"
   ↓
2. ContinuityEngine.query_what_usually_works()
   ↓
3. PrecedentGraph searches for matching condition signatures
   ↓
4. Returns actions with highest success rates
   ↓
5. Results inform future simulations
```

## Integration Points

### With DecisionTrace

- `create_decision_event_from_trace()`: Converts DecisionTrace to DecisionEvent
- `record_event_from_trace()`: Records event from trace

### With ContextGraph

- Precedents can inform context graph construction
- Historical patterns can guide graph queries

### With DecisionAutopsy

- `get_continuity_context_for_autopsy()`: Provides historical context
- `enrich_autopsy_with_precedents()`: Adds precedent insights to autopsy output

## Example Queries

### Query 1: "What usually works when belief collapses due to delayed value?"

```python
results = engine.query_what_usually_works(
    condition_description="belief collapses due to delayed value",
    step_id="Step 3"
)

# Returns:
# [
#   {
#     'action': 'Show value before asking for commitment',
#     'success_rate': 0.85,
#     'total_occurrences': 42,
#     'average_confidence': 0.78
#   },
#   ...
# ]
```

### Query 2: Precedents for specific conditions

```python
precedents = engine.query_precedents(
    step_id="Step 3",
    trust=0.5,
    value=0.2,
    commitment=0.3,
    risk=0.6,
    intent=0.7,
    factors={"value_delay", "risk_spike"}
)

# Returns matching precedents with action distributions
```

## Design Principles

1. **Deterministic**: Same inputs → same outputs
2. **Immutable Historical Records**: Past events never mutated
3. **Append-Only**: New events added, history preserved
4. **Incremental Learning**: Precedents built incrementally
5. **Entity-Scoped**: State tracked per entity (product/user/account)
6. **Queryable**: Historical patterns accessible via queries

## File Structure

```
decision_continuity/
├── __init__.py              # Module exports
├── decision_event.py        # DecisionEvent primitive
├── continuity_state.py      # ContinuityState per entity
├── precedent_graph.py       # PrecedentGraph aggregation
├── continuity_engine.py      # Main orchestrator
├── integration.py           # Integration with existing systems
├── examples.py              # Usage examples
├── README.md                # Usage documentation
└── ARCHITECTURE.md          # This file
```

## Next Steps

1. **Integration**: Wire into simulation pipeline to record events during execution
2. **Query Interface**: Build UI/API for querying precedents
3. **Learning Loop**: Use precedents to inform future simulations
4. **Validation**: Test with historical data to validate precedent accuracy

