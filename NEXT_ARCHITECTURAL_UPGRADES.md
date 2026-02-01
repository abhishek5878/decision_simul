# Next Architectural Upgrades: DropSim as Decision Infrastructure

## Context

DropSim has transitioned from behavioral simulation to decision system of record. DecisionTraces are captured at decision time, aggregated into DecisionSequences, and compiled into ContextGraphs. The system can answer "which user types does this product accept/reject."

This document proposes the next architectural upgrades that strengthen DropSim as **long-lived decision infrastructure**, not optimization tooling.

---

## Core Principles (Immutable)

1. **Decision traces are ground truth** — immutable, append-only
2. **No ML inference** — all patterns derived from traces, not learned
3. **Policy-versioned decisions** — every trace linked to explicit policy version
4. **Deterministic equivalence** — grouping by rule, not similarity
5. **Counterfactuals create new traces** — never mutate history

---

## Priority 1: Policy Versioning System

### Problem

When behavioral logic, intent rules, or parameter bounds change, past DecisionTraces become uninterpretable. Without versioning, you cannot answer "why did this persona drop at step X" if the policy that generated that trace no longer exists.

### Solution

**Policy Version Registry**

- **Policy Definition**: Immutable snapshot of behavioral equations, intent logic, parameter bounds, and engine code path
- **Policy Version**: Hash-derived identifier (e.g., `policy_v2_3f8a1b2c`)
- **Trace-Policy Linkage**: Every DecisionTrace carries `policy_version` (already present, must be enforced)
- **Policy Storage**: Append-only registry of policy definitions

**Implementation Points:**

```
policy_registry/
├── policies/
│   ├── v1_3f8a1b2c.json  # Policy definition snapshot
│   ├── v2_7d9e4f5a.json
│   └── ...
├── policy_resolver.py     # Resolve version -> definition
└── policy_auditor.py      # Validate trace-policy consistency
```

**Where It Fits:**

- Between `behavioral_engine_intent_aware.py` and trace creation
- Policy version injected at DecisionTrace creation time
- Policy registry queried when interpreting historical traces

**Why It Strengthens Decision Persistence:**

- Past decisions remain interpretable indefinitely
- Enables audit: "What policy generated this decision?"
- Enables replay: "Re-run this trace under policy v3"
- Prevents drift through accidental policy changes

---

## Priority 2: Trace Immutability & Lineage

### Problem

Decision traces must be immutable ground truth, but the system needs to track:
- Which traces belong to which simulation run
- How traces relate to policy versions
- Which traces were generated vs replayed (counterfactuals)

### Solution

**Trace Storage Layer**

- **Immutable Storage**: Append-only trace store (write once, never modify)
- **Trace IDs**: Deterministic IDs derived from (persona_id, step_id, policy_version, timestamp_hash)
- **Lineage Metadata**: Each trace records simulation_run_id, policy_version, generation_type (original | replayed)
- **Trace Index**: Index by policy_version, simulation_run_id, persona_id, step_id (for queries)

**Implementation Points:**

```
trace_store/
├── traces/
│   ├── {trace_id}.json    # Immutable trace file
│   └── ...
├── lineage/
│   ├── simulation_runs.json  # Run metadata
│   └── policy_versions.json  # Policy version registry link
├── index/
│   ├── by_policy_version.json
│   ├── by_simulation_run.json
│   └── by_persona_step.json
└── trace_reader.py        # Read-only access layer
```

**Where It Fits:**

- After DecisionTrace creation in behavioral engine
- Before context graph building
- Replaces in-memory trace aggregation with persistent storage

**Why It Strengthens Decision Persistence:**

- Guarantees trace immutability at storage layer
- Enables long-term trace accumulation (years of decisions)
- Provides audit trail: which run generated which traces
- Separates generation from storage (enables replay)

---

## Priority 3: Deterministic Precedent Grouping

### Problem

To answer "which personas drop for similar reasons," we need to group similar DecisionTraces. ML-based clustering violates the "no inference" principle. We need deterministic equivalence classes.

### Solution

**Precedent Equivalence Classes**

- **Equivalence Rule**: Two traces are equivalent if they share:
  - Same step_id
  - Same decision outcome (CONTINUE | DROP)
  - Same cognitive state bucket (energy/risk/effort/value/control binned into 5 levels each)
  - Same intent_id
  - Same dominant_factors set
- **Precedent Hash**: Deterministic hash of equivalence attributes
- **Precedent Registry**: Map precedent_hash → list of trace_ids
- **Query Interface**: "Find all traces matching precedent X"

**Implementation Points:**

```
precedents/
├── equivalence_rules.py   # Defines equivalence criteria
├── precedent_hasher.py    # Generate precedent hash
├── precedent_registry.py  # Hash -> trace_ids mapping
└── precedent_queries.py   # Query by precedent
```

**Where It Fits:**

- After trace storage
- Input to context graph building (group by precedent)
- Enables precedent-based queries

**Why It Strengthens Decision Persistence:**

- Enables pattern discovery without inference
- Deterministic: same inputs → same precedent
- Interpretable: equivalence rule is explicit
- Enables "show me all personas that dropped like this"

---

## Priority 4: Counterfactual Replay Framework

### Problem

To answer "what would have happened if we used policy v3 instead of v2," we need to replay past decisions under new policies. But we must never mutate historical traces.

### Solution

**Counterfactual Replay Engine**

- **Input**: Original trace + new policy version
- **Process**: Re-run decision logic with new policy (using saved cognitive state snapshot as input)
- **Output**: New trace with `generation_type: "replayed"` and `original_trace_id` linkage
- **Storage**: Replayed traces stored separately (never overwrite originals)
- **Lineage**: Track counterfactual chains (original → replayed → replayed again)

**Implementation Points:**

```
replay/
├── replay_engine.py       # Replay trace under new policy
├── counterfactual_builder.py  # Build counterfactual scenarios
└── replay_storage.py      # Store replayed traces separately
```

**Where It Fits:**

- Separate from trace generation (reads from trace store)
- Can replay any stored trace under any policy version
- Outputs feed back into trace store (as new traces)

**Why It Strengthens Decision Persistence:**

- Enables "what if" analysis without mutating history
- Preserves original traces as ground truth
- Enables policy comparison: "Policy v2 vs v3 on same personas"
- Maintains auditability: every trace links to its generation method

---

## Priority 5: Decision-Pattern Drift Detection

### Problem

Current drift monitoring is metric-based (completion rates, parameter values). We need drift at the decision level: "Has the product's implicit user contract changed?"

### Solution

**Decision Pattern Drift**

- **Baseline Pattern Distribution**: Distribution of precedent hashes from baseline simulation
- **Current Pattern Distribution**: Distribution of precedent hashes from current simulation
- **Drift Metric**: Statistical distance between distributions (e.g., JS divergence, chi-square)
- **Drift Severity**: Thresholds for stable/warning/critical
- **Drift Explanation**: Which precedents increased/decreased in frequency

**Implementation Points:**

```
drift/
├── pattern_drift.py       # Compare precedent distributions
├── drift_explainer.py     # Explain which patterns changed
└── drift_monitor.py       # Integrate with existing drift system
```

**Where It Fits:**

- Extends existing `calibration/model_health_monitor.py`
- Uses precedent registry to compute distributions
- Compares across policy versions (or time windows)

**Why It Strengthens Decision Persistence:**

- Detects when product's user contract changes (not just metrics)
- Answers: "Are we rejecting different user types now?"
- Enables proactive recalibration when patterns shift
- Complements metric-based drift (decision-level insight)

---

## What We Must Never Build

### ❌ Optimization Engines

- No conversion rate optimization
- No A/B testing frameworks
- No "suggest improvements to increase completion"
- Rationale: DropSim explains decisions, it doesn't optimize outcomes.

### ❌ Predictive Models

- No ML models that predict future decisions
- No learned embeddings or similarity functions
- No neural networks or gradient-based optimization
- Rationale: Decisions are deterministic under explicit policies. Prediction requires inference, which violates ground truth principle.

### ❌ Autonomous Decision Systems

- No systems that modify policies automatically
- No reinforcement learning or policy gradients
- No "auto-calibration" that changes behavioral logic
- Rationale: Policies are human-defined contracts. Automation breaks auditability.

### ❌ Analytics Dashboards

- No "funnel optimization" views
- No conversion rate tracking over time
- No user segmentation for marketing
- Rationale: DropSim is infrastructure, not analytics. Analytics tools consume DropSim outputs, they are not DropSim itself.

### ❌ Real-Time Decision APIs

- No APIs that make decisions in production user flows
- No "should this user continue?" endpoints
- No live decision engines
- Rationale: DropSim simulates and records decisions. It does not make live decisions. That separation preserves system-of-record integrity.

---

## Architectural Invariants (Must Never Violate)

1. **Decision traces are immutable**
   - Once written, never modified
   - Counterfactuals create new traces, never overwrite

2. **Every trace links to a policy version**
   - No trace exists without explicit policy_version
   - Policy registry must exist before trace creation

3. **Equivalence is deterministic**
   - Same inputs → same precedent hash
   - No learned similarity or inference

4. **Storage is append-only**
   - Traces: append-only
   - Policies: append-only (new versions, never modify old)
   - Lineage: append-only

5. **Replay never mutates**
   - Counterfactuals generate new traces
   - Original traces remain unchanged
   - Replay lineage tracked explicitly

6. **No inference in core paths**
   - All grouping, equivalence, drift detection is rule-based
   - ML/statistical inference only in optional analysis layers (consumers of DropSim)

---

## Reframing: What DropSim Becomes

After these upgrades, DropSim becomes:

**"A versioned, immutable system of record for product-user fit decisions, with deterministic precedent grouping and counterfactual replay capabilities, that enables long-term auditability and policy comparison without inference or optimization."**

In shorter terms:

**"Decision infrastructure with versioned policies, immutable traces, deterministic precedents, and counterfactual replay."**

---

## Implementation Order

1. **Policy Versioning** (Foundation)
   - Required before any other upgrade
   - Enables trace interpretability

2. **Trace Immutability & Lineage** (Storage Layer)
   - Enables long-term accumulation
   - Required before replay

3. **Deterministic Precedent Grouping** (Query Layer)
   - Enables pattern discovery
   - Feeds into drift detection

4. **Counterfactual Replay** (Analysis Layer)
   - Depends on policy versioning + immutable storage
   - Enables policy comparison

5. **Decision-Pattern Drift** (Monitoring Layer)
   - Depends on precedents
   - Extends existing drift system

---

## Summary

These five upgrades transform DropSim from "decision capture system" to "decision infrastructure system." They prioritize:

- **Auditability**: Every decision linked to explicit policy
- **Immutability**: Ground truth preserved indefinitely
- **Determinism**: No inference, all patterns rule-based
- **Replayability**: Counterfactuals without mutation
- **Longevity**: System compounds over years, not months

The system remains focused on **explaining and recording decisions**, not optimizing outcomes. It becomes infrastructure that other systems (analytics, optimization, experimentation) consume, not a tool that competes with them.

