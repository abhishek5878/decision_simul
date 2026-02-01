# Decision-First Context Graph Queries

## Overview

The context graph query layer exposes **decision boundaries, precedents, and acceptance surfaces** — not analytics metrics.

## Why Context Graph Queries Are Not Analytics

Analytics answers: "What happened?" (drop rates, completion percentages, top failure points)  
Decision queries answer: "Which personas were accepted/rejected, and what precedents explain it?"

### Key Differences

| Analytics Approach | Decision-First Approach |
|-------------------|------------------------|
| Global drop rates | Decision boundaries per persona class |
| Top failure points | Stable precedents with occurrence counts |
| Monocausal explanations | Multi-factor explanations with counterexamples |
| Funnel percentages | Acceptance surfaces per persona class |
| Aggregate summaries | Precedent-based patterns |

## Query Primitives

### 1. Decision Boundaries

**Function:** `query_decision_boundaries(sequences, step_id)`

**Answers:** "At step X, which persona classes are ACCEPTED vs REJECTED?"  
"What cognitive thresholds separate them?"

**Returns:** List of `DecisionBoundary` objects with:
- Persona class definition
- Accepted/rejected counts
- Cognitive thresholds (energy, risk, effort, value, control ranges)
- Counterexamples (to prevent monocausal claims)

**Example:**
```python
boundaries = query_decision_boundaries(sequences, "Find the Best Credit Card In 60 seconds")
for boundary in boundaries:
    print(f"Persona class: {boundary.persona_class}")
    print(f"Accepted: {boundary.accepted_count}, Rejected: {boundary.rejected_count}")
    print(f"Thresholds: {boundary.cognitive_thresholds}")
```

### 2. Persona Differentiation

**Function:** `query_persona_differentiation(sequences, step_x_id, step_x_plus_one_id)`

**Answers:** "Which personas fail at step X but succeed at step X+1 under similar entry conditions?"  
"What differentiating decision factors explain the divergence?"

**Returns:** List of `PersonaDifferentiation` objects showing divergent behavior patterns.

### 3. Stable Precedents

**Function:** `query_stable_precedents(sequences, minimum_occurrence=3)`

**Answers:** "Which (step, persona_class, dominant_factors) combinations recur frequently?"

**Returns:** List of `StablePrecedent` objects with:
- Step ID
- Persona class
- Dominant factors (immutable tuple)
- Occurrence count
- Outcome (CONTINUE/DROP)
- Example traces

**Example:**
```python
precedents = query_stable_precedents(sequences, minimum_occurrence=10)
for precedent in precedents:
    print(f"Pattern: {precedent.persona_class} at {precedent.step_id}")
    print(f"Factors: {precedent.dominant_factors}")
    print(f"Occurrences: {precedent.occurrence_count}")
```

### 4. Competing Explanations

**Function:** `query_competing_explanations(sequences, primary_factor="intent_alignment")`

**Answers:**
- "Where do drops occur despite high intent alignment?"
- "Where do continuations occur despite low intent alignment?"

**Forces multi-factor explanations** by finding counterexamples to monocausal claims.

**Returns:** List of `CompetingExplanation` objects with:
- Step ID
- Outcome
- Primary factor and value
- Competing factors
- Example trace

**Example:**
```python
competing = query_competing_explanations(sequences, "intent_alignment")
for explanation in competing:
    print(f"Step: {explanation.step_id}")
    print(f"Outcome: {explanation.outcome.value}")
    print(f"High {explanation.primary_factor} but {explanation.outcome.value}")
    print(f"Explained by: {explanation.competing_factors}")
```

### 5. Acceptance Surface

**Function:** `query_acceptance_surface(sequences, product_steps)`

**Answers:** "For each persona class, what is the deepest step reliably reached?"  
"Where does continuation probability collapse sharply?"

**Returns:** List of `AcceptanceSurface` objects showing decision boundary surfaces per persona class.

## Design Principles

1. **No Global Aggregations** - All queries condition on persona classes
2. **No Monocausal Explanations** - Counterexamples always included
3. **No Percentages Without Conditioning** - All counts are conditioned on persona classes
4. **Precedent-Based** - All insights derived from recurring patterns
5. **Audit-Safe** - Every insight can be traced back to DecisionTrace objects

## Usage

```python
from decision_graph.graph_queries import (
    query_decision_boundaries,
    query_stable_precedents,
    query_competing_explanations,
    query_acceptance_surface
)

# Load sequences from simulation result
sequences = load_sequences_from_result('credigo_pipeline_result.json')

# Query decision boundaries
boundaries = query_decision_boundaries(sequences, "step_id")

# Query stable precedents
precedents = query_stable_precedents(sequences, minimum_occurrence=10)

# Query competing explanations
competing = query_competing_explanations(sequences, "intent_alignment")

# Query acceptance surface
product_steps = {...}  # Step definitions
surfaces = query_acceptance_surface(sequences, product_steps)
```

## What NOT to Do

❌ **Don't compute global drop rates:**
```python
# WRONG - Analytics style
total_drops = sum(1 for s in sequences if s.final_outcome == DROP)
drop_rate = total_drops / len(sequences)  # Global percentage
```

✅ **Do query decision boundaries per persona class:**
```python
# CORRECT - Decision-first
boundaries = query_decision_boundaries(sequences, step_id)
for boundary in boundaries:
    # Conditioned on persona class
    print(f"{boundary.persona_class}: {boundary.accepted_count} accepted, {boundary.rejected_count} rejected")
```

❌ **Don't claim monocausal explanations:**
```python
# WRONG - Monocausal
if all(trace.dominant_factors == ['intent_mismatch'] for trace in dropped_traces):
    print("All drops caused by intent_mismatch")  # Monocausal claim
```

✅ **Do include counterexamples:**
```python
# CORRECT - Multi-factor with counterexamples
boundaries = query_decision_boundaries(sequences, step_id)
for boundary in boundaries:
    if boundary.counterexample_accepted:
        print("Found accepted trace that violates thresholds")  # Counterexample
```

## Testing

Run the test script to see decision-first queries in action:

```bash
python3 test_decision_first_queries.py
```

This demonstrates all 5 query primitives with real Credigo simulation data.

