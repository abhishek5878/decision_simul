# Decision Attribution Layer: Architecture & Integration Plan

**Status:** Foundation exists, integration needed  
**Priority:** Medium-High (after testing & hardening)  
**Purpose:** Formalize causality through game-theoretic force attribution

---

## PHILOSOPHICAL FRAMING

### What SHAP Is NOT in DropSim

- ❌ A model explanation tool
- ❌ A prediction explainer  
- ❌ A UX insight generator
- ❌ A feature importance calculator

### What SHAP IS in DropSim

> **A decision force attribution mechanism**
> 
> "Which internal forces *caused* this decision to flip?"

This aligns with:
- Decision traces (what happened)
- Perturbation engine (what-if analysis)
- Sensitivity analysis (which forces matter)

---

## ARCHITECTURAL POSITION

### Current Architecture

```
Behavioral Engine
   ↓
Decision Trace (state_before, decision, state_after)
   ↓
Context Graph / DIS
```

### With Decision Attribution

```
Behavioral Engine
   ↓
Decision Trace (state_before, decision, state_after)
   ↓
Decision Attribution Layer  ← (NEW - explains decisions)
   ↓
Context Graph / DIS
```

**Key Point:** This is **not** a replacement for anything. It *explains* what already happened.

---

## THE "MODEL" (Important)

### You Do NOT Explain the Behavioral Engine Directly

Instead, for each decision you create a **local surrogate decision function**:

```
f(state, step_features) → decision_probability
```

**Inputs (features):**
- `cognitive_energy`
- `intent_strength`
- `effort_tolerance`
- `risk_tolerance`
- `trust_baseline`
- `value_expectation`
- `step_effort`
- `step_risk`
- `step_value`
- `intent_mismatch`

**Output:**
- `probability of CONTINUE vs DROP`

This function already exists implicitly in your engine. You are just **making it explicit for attribution**.

---

## SHAP = GAME THEORY, NOT ML

### Positioning

SHAP is based on **Shapley values** (cooperative game theory), which means:

- Each feature is a "player"
- The decision outcome is the "payout"
- SHAP computes *fair contribution* of each feature

**You can honestly say:**

> "We use cooperative game theory to attribute decisions."

That's strong and defensible.

**Key Principles:**
- ✅ Deterministic (no randomness)
- ✅ No training dataset needed
- ✅ No black-box learning
- ✅ Mathematically rigorous

---

## IMPLEMENTATION PLAN

### Phase 1: Extend DecisionTrace Schema

**Add `DecisionAttribution` to every `DecisionTrace`:**

```python
@dataclass
class DecisionAttribution:
    """Game-theoretic attribution of decision forces."""
    step_id: str
    decision: DecisionOutcome
    baseline_probability: float  # Probability with all features at baseline
    
    # Shapley values (force contributions)
    shap_values: Dict[str, float]  # {force_name: contribution}
    
    # Dominant forces (ranked by absolute contribution)
    dominant_forces: List[Tuple[str, float]]  # [(force_name, contribution), ...]
    
    # Attribution metadata
    attribution_method: str = "shapley_values"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Integration Point:**
- Attach to `DecisionTrace` at creation time
- Store in `DecisionTrace.attribution` field
- Include in `DecisionTrace.to_dict()`

---

### Phase 2: Local Attribution Computation

**For each decision:**

1. **Extract state vector:**
   ```python
   state_vector = [
       cognitive_energy,
       intent_strength,
       effort_tolerance,
       risk_tolerance,
       trust_baseline,
       value_expectation,
       step_effort,
       step_risk,
       step_value,
       intent_mismatch
   ]
   ```

2. **Define baseline (neutral state):**
   ```python
   baseline = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0]
   ```

3. **Compute SHAP values:**
   - Use existing `decision_explainability/shap_model.py`
   - Local computation only (no global model)
   - Deterministic (same inputs → same outputs)

4. **Store attribution:**
   - Attach to `DecisionTrace`
   - Include in ledger generation

---

### Phase 3: Decision-First Aggregation

**Never say:**
- ❌ "Feature importance overall"
- ❌ "Global feature rankings"
- ❌ "Most important factors"

**Always say:**
- ✅ "At Step 4, effort explains 63% of drops"
- ✅ "Intent stops mattering after Step 2"
- ✅ "Trust only matters at entry, never later"
- ✅ "At Step 4, 62% of rejection pressure comes from effort intolerance, 21% from risk sensitivity, and only 6% from intent"

These are **decision truths**, not metrics.

---

### Phase 4: Ledger Integration

**Add to Decision Ledger:**

```json
{
  "decision_boundaries": [
    {
      "step_id": "step_4",
      "persona_class": "...",
      "decision": "REJECT",
      "force_attribution": {
        "effort": 0.63,
        "risk": 0.21,
        "intent_mismatch": 0.06,
        "value": 0.05,
        "trust": 0.05
      },
      "dominant_force": "effort",
      "supporting_trace_count": 86
    }
  ]
}
```

**Key Rule:** Attribution is **assertion**, not interpretation.

---

### Phase 5: DIS Integration

**Add "Decision Mechanics" section to DIS:**

```markdown
## Decision Mechanics by Step

### Step 4: "Your top 2 spend categories?"

**Force Attribution (for REJECT decisions):**
- Effort intolerance: 63% of rejection pressure
- Risk sensitivity: 21% of rejection pressure
- Intent mismatch: 6% of rejection pressure
- Value deficit: 5% of rejection pressure
- Trust deficit: 5% of rejection pressure

**Interpretation (Non-binding):**
At this step, users who reject are primarily driven by effort intolerance.
Intent alignment is not the dominant factor, suggesting the question itself
is the barrier, not the product's alignment with user intent.
```

**Language Rules:**
- Use "explains X% of rejection pressure" (not "importance")
- Use "driven by" (not "caused by")
- Include disclaimer: "Attribution based on Shapley values (cooperative game theory)"

---

## MODULE STRUCTURE

```
decision_attribution/
├── __init__.py
├── attribution_model.py      # Local surrogate decision function
├── shapley_computer.py        # Shapley value computation
├── force_attribution.py      # Force contribution extraction
├── attribution_aggregator.py  # Decision-first aggregation
└── README.md                  # Documentation
```

**Integration Points:**
- `behavioral_engine_intent_aware.py` - Attach attribution at trace creation
- `decision_graph/decision_trace.py` - Extend DecisionTrace schema
- `decision_graph/decision_ledger.py` - Include attribution in ledger
- `decision_intelligence/dis_generator.py` - Add "Decision Mechanics" section

---

## FOUNDER-FACING OUTPUT

### What You Show

**Not:**
- ❌ SHAP charts
- ❌ Feature importance plots
- ❌ Global rankings

**Instead:**
- ✅ "At Step 4, 62% of rejection pressure comes from effort intolerance"
- ✅ "Trust explains 48% of the landing page decision, but 0% beyond Step 2"
- ✅ "Intent stops mattering after Step 2 - by Step 4, effort dominates"

### Example: Decision Mechanics Report

```markdown
# Decision Mechanics: Why Users Drop

## Step 0: Landing Page

**For REJECT decisions:**
- Trust deficit: 48% of rejection pressure
- Intent uncertainty: 32% of rejection pressure
- Risk sensitivity: 20% of rejection pressure

**Interpretation:** Users who drop at landing page are primarily
driven by trust concerns, not intent alignment.

## Step 4: Spending Categories

**For REJECT decisions:**
- Effort intolerance: 63% of rejection pressure
- Risk sensitivity: 21% of rejection pressure
- Intent mismatch: 6% of rejection pressure

**Interpretation:** By Step 4, effort dominates. Users who have
reached this point are committed (intent is aligned), but the
question itself creates too much effort for them to continue.

---

**Methodology:** Attribution based on Shapley values (cooperative
game theory). Each force's contribution is computed as its fair
share of the decision outcome, given all other forces.
```

---

## EXTENSIONS (Future)

### Counterfactual Games

**Question:** "If effort were reduced, would trust still matter?"

**Method:** Recompute SHAP values with effort set to baseline, see how other forces redistribute.

### Coalition Analysis

**Question:** "Which forces must combine to cause a drop?"

**Method:** Analyze force combinations that lead to rejection.

### Dominant Strategy Detection

**Question:** "Which features dominate regardless of others?"

**Method:** Identify forces that have high SHAP values across all scenarios.

---

## ARCHITECTURAL BENEFITS

### Before Attribution

- ✅ You know *what* decisions happened
- ✅ You know *where* users dropped
- ✅ You infer *why* via rules and perturbations

### After Attribution

- ✅ You can **quantify causality**
- ✅ You can **rank forces mathematically**
- ✅ You can **compare decisions across products**
- ✅ You can **answer "why" with numbers**

**This unlocks:**
- Sensitivity surfaces
- Fragility maps
- Decision equations per step
- Founder-facing "Decision Mechanics" outputs

---

## RISK ASSESSMENT

### Complexity: Medium

- SHAP computation is well-understood
- Local attribution is simpler than global
- Integration is straightforward

### Performance: Low Impact

- Attribution computed per decision (already have decision)
- No additional simulation runs needed
- Can be computed lazily (on-demand)

### Maintenance: Low

- Isolated module
- Clear interfaces
- Well-documented algorithm

---

## POSITIONING

### How to Describe This

**Not:**
- ❌ "We use SHAP to explain our model"
- ❌ "Feature importance analysis"
- ❌ "ML explainability"

**Instead:**
- ✅ "We use cooperative game theory (Shapley values) to attribute decision forces"
- ✅ "Decision mechanics analysis"
- ✅ "Mathematical causality attribution"
- ✅ "Game-theoretic decision explanation"

### Marketing Language

**"Decision Mechanics™"**

> DropSim doesn't just record decisions—it explains the mechanics.
> Using cooperative game theory, we quantify which internal forces
> (effort, risk, value, trust, intent) caused each decision.
> 
> This is not analytics. This is decision mechanics.

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Schema Extension
- [ ] Add `DecisionAttribution` dataclass
- [ ] Extend `DecisionTrace` to include `attribution` field
- [ ] Update `DecisionTrace.to_dict()` to include attribution

### Phase 2: Attribution Computation
- [ ] Create local surrogate decision function
- [ ] Implement Shapley value computation
- [ ] Attach attribution at trace creation time
- [ ] Test attribution computation

### Phase 3: Ledger Integration
- [ ] Include attribution in decision boundary assertions
- [ ] Add force attribution to ledger JSON schema
- [ ] Update ledger formatter to display attribution

### Phase 4: DIS Integration
- [ ] Add "Decision Mechanics" section to DIS
- [ ] Generate force attribution summaries
- [ ] Include methodology notes

### Phase 5: Founder-Facing Output
- [ ] Create "Decision Mechanics" report generator
- [ ] Add attribution to founder summaries
- [ ] Test with Credigo/Blink Money

---

## SUCCESS CRITERIA

**This is successful when:**

1. ✅ Every `DecisionTrace` includes `DecisionAttribution`
2. ✅ Ledger includes force attribution for each boundary
3. ✅ DIS includes "Decision Mechanics" section
4. ✅ Founder reports include "Why this decision happened"
5. ✅ Attribution is deterministic and reproducible
6. ✅ No ML inference in core paths
7. ✅ Positioning is "game theory" not "ML explainability"

---

## CONCLUSION

**This is not feature creep.**

This is the **missing mathematical spine** that connects:
- Behavioral theory
- Perturbations
- Decision traces
- Founder-level truth

**You are not "adding SHAP".**

**You are formalizing causality.**

---

**Next Steps:**
1. Review this architecture plan
2. Decide on implementation priority
3. Start with Phase 1 (schema extension)
4. Iterate based on feedback

**Estimated Effort:**
- Phase 1: 1-2 days
- Phase 2: 3-5 days
- Phase 3: 2-3 days
- Phase 4: 2-3 days
- Phase 5: 2-3 days
- **Total: 2-3 weeks**

---

**This transforms DropSim from "decision recorder" to "decision mechanics engine."**

