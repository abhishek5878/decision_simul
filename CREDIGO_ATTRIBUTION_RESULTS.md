# Credigo Decision Attribution Results

**Generated:** After implementing Decision Attribution Layer  
**Simulation:** Credigo, 1000 personas, Production mode  
**Total Decision Traces:** 36,765  
**Traces with Attribution:** 36,765/36,765 (100%)

---

## Key Findings

### Overall Attribution Patterns (DROP Decisions)

Across all drop decisions, the dominant forces are:

1. **Intent mismatch: 55.6%** of rejection pressure
2. **Trust: 20.7%** of rejection pressure  
3. **Cognitive energy: 7.4%** of rejection pressure
4. **Value: 5.3%** of rejection pressure
5. **Risk: 5.2%** of rejection pressure

**Interpretation:** Intent alignment is the primary driver of drop decisions in Credigo's onboarding flow.

---

## Attribution by Step (DROP Decisions)

### Landing Page: "Find the Best Credit Card In 60 seconds"
- **Trust: 49%** of rejection pressure
- **Intent mismatch: 29%** of rejection pressure
- **Cognitive energy: 9%** of rejection pressure

**Interpretation:** At entry, users who drop are primarily driven by trust concerns, not intent alignment.

---

### Step: "Any preference on annual fee?"
- **Intent mismatch: 43%** of rejection pressure
- **Trust: 21%** of rejection pressure
- **Cognitive energy: 10%** of rejection pressure

---

### Step: "Your top 2 spend categories?"
- **Intent mismatch: 91%** of rejection pressure
- **Trust: 4%** of rejection pressure
- **Effort: 1%** of rejection pressure

**Interpretation:** By this step, intent alignment dominates. Users who have reached this point are committed, but the question itself creates intent mismatch.

---

### Step: "What kind of perks excite you the most?"
- **Intent mismatch: 26%** of rejection pressure
- **Trust: 18%** of rejection pressure
- **Cognitive energy: 16%** of rejection pressure

**Interpretation:** More balanced attribution, suggesting multi-factor decision-making.

---

### Steps with 100% Intent Mismatch Attribution

These steps show pure intent mismatch as the drop driver:
- "Do you have any existing credit cards?"
- "Do you track your monthly spending?"
- "How much do you spend monthly?"
- "Help us personalise your card matches"
- "Best Deals for You – Apply Now"
- "Step 1 of 11"
- "straightforward + options are clearly defined"

**Interpretation:** These steps create clear intent conflicts - users who drop here are doing so because the step doesn't align with their goal.

---

## Methodology Notes

### Attribution Computation

- **Method:** Shapley values (cooperative game theory)
- **Local attribution only:** No global model, no training
- **Deterministic:** Same inputs → same attribution
- **Baseline:** Neutral state (all features at midpoint)

### Features Attributed

1. **Persona State:**
   - Cognitive energy
   - Intent strength
   - Effort tolerance
   - Risk tolerance
   - Trust baseline
   - Value expectation

2. **Step Forces:**
   - Step effort
   - Step risk
   - Step value
   - Step trust
   - Intent mismatch

### Limitations

- Attribution values are normalized to percentages for readability
- Shapley value computation uses exact enumeration (computationally expensive for large feature sets)
- Attribution reflects simulated decisions, not real user behavior

---

## Decision-First Insights

### What This Tells Us

1. **Intent alignment is the dominant filter** - 55.6% of drops are driven by intent mismatch
2. **Trust matters most at entry** - Landing page drops are 49% trust-driven
3. **Intent mismatch accumulates** - Steps that demand information before value show high intent mismatch attribution
4. **Multi-factor decisions exist** - Some steps show balanced attribution (e.g., "What kind of perks excite you the most?")

### Product Implications

- **Early steps:** Focus on trust signals and intent alignment
- **Mid-funnel steps:** Intent mismatch dominates - ensure steps serve user's known goal
- **Late steps:** Users are committed - intent mismatch less critical, but still present

---

## Example Attribution Output

```json
{
  "step_id": "Find the Best Credit Card In 60 seconds",
  "decision": "CONTINUE",
  "attribution": {
    "step_id": "Find the Best Credit Card In 60 seconds",
    "decision": "CONTINUE",
    "baseline_probability": 0.891,
    "final_probability": 0.873,
    "shap_values": {
      "trust": 1.0,
      "cognitive_energy": 0.0,
      "intent": 0.0,
      ...
    },
    "dominant_forces": [
      ["trust", 1.0],
      ["cognitive_energy", 0.0],
      ...
    ]
  }
}
```

---

## Next Steps

1. **Integrate attribution into Decision Ledger** - Include force attribution in ledger assertions
2. **Add to DIS (Decision Intelligence Summary)** - Include "Decision Mechanics" section
3. **Create founder-facing report** - "Why Users Drop: Decision Mechanics Analysis"
4. **Refine Shapley computation** - Optimize for production use (consider approximate methods for large feature sets)

---

**This is the first implementation of decision attribution in DropSim.**
The system now answers: "Which internal forces caused this specific decision?"

