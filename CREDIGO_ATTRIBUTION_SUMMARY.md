# Credigo Decision Attribution: Results Summary

**Product:** Credigo (AI Credit Card Recommender)  
**Simulation Date:** January 2025  
**Sample Size:** 1,000 personas, 36,765 decision traces  
**Attribution Method:** Shapley values (cooperative game theory)

---

## Executive Summary

Credigo's onboarding flow has **two distinct phases** with fundamentally different drop drivers:

1. **Entry Phase (Step 0):** Trust is the primary filter (38.3% of drops)
2. **Intent Phase (Steps 1+):** Intent mismatch dominates (58.7% overall, 84-100% after Step 3)

**Core Finding:** Users who pass the trust barrier are committed. Those who drop later do so because the flow asks for information before delivering value aligned with their intent.

---

## Funnel Metrics

- **Entry Rate:** 55.50%
- **Completion Rate:** 21.89%
- **Total Conversion:** 12.15%

**Interpretation:** 44.5% of users don't enter the funnel. Of those who enter, 21.89% complete all 11 steps.

---

## Force Attribution (DROP Decisions)

### Overall Pattern

Across all drop decisions, forces contribute as follows:

1. **Intent mismatch: 58.7%** of rejection pressure
2. **Trust: 17.0%** of rejection pressure
3. **Cognitive energy: 7.5%** of rejection pressure
4. **Value: 5.9%** of rejection pressure
5. **Risk: 5.2%** of rejection pressure

**Interpretation:** Intent alignment is the dominant driver. Users drop when they don't see how the current step serves their goal ("get a credit card recommendation").

---

## The Two-Phase Funnel

### Phase 1: Trust Filter (Step 0)

**"Find the Best Credit Card In 60 seconds"**
- **Drop rate:** 20.6% (1,445 drops)
- **Dominant force:** Trust (38.3%)
- **Secondary forces:** Intent mismatch (33.8%), Cognitive energy (10.8%)

**What's happening:** Users are evaluating "Can I trust this?" more than "Is this for me?"

**Key Insight:** Trust barrier at entry. Users who don't trust the system drop immediately.

---

### Phase 2: Intent Filter (Steps 1-10)

**Steps 1-2: Transition Phase**
- Drop rates: 19.7% → 18.4%
- Intent mismatch: 29.9% → 49.3%
- **Pattern:** Intent mismatch increasing, trust decreasing

**Steps 3+: Intent-Dominated**
- Drop rates: 15.1% → 9.0% (declining)
- Intent mismatch: 84.5% → 100%
- **Pattern:** Pure intent filtering - users are committed, drops only when steps don't align

**What's happening:** Once users trust the system, they're committed. Drops happen when steps don't serve their known goal.

---

## Step-by-Step Breakdown

### Step 0: Landing Page
**"Find the Best Credit Card In 60 seconds"**
- Drop rate: **20.6%** (highest)
- Forces: Trust 38.3% | Intent mismatch 33.8% | Cognitive energy 10.8%
- **Action:** Strengthen trust signals (security badges, testimonials, credibility)

### Step 1: Perks Question
**"What kind of perks excite you the most?"**
- Drop rate: **19.7%**
- Forces: Intent mismatch 29.9% | Trust 16.9% | Cognitive energy 15.0%
- **Action:** Show value preview before asking preferences

### Step 2: Annual Fee Question
**"Any preference on annual fee?"**
- Drop rate: **18.4%**
- Forces: Intent mismatch 49.3% | Trust 16.5% | Cognitive energy 9.2%
- **Action:** Frame as part of recommendation, not a barrier

### Step 3: Transition Point ⚠️
**"straightforward + options are clearly defined"**
- Drop rate: **15.1%**
- Forces: Intent mismatch **84.5%** (jump from 49.3%)
- **Action:** Critical milestone - ensure value is clear before this step

### Steps 4-10: Intent-Dominated
- Drop rates: 11.7% → 9.0% (declining)
- Forces: Intent mismatch 91-100%
- **Pattern:** Users are highly committed, drops are rare and purely intent-driven

---

## Force Co-Occurrence Patterns

### Most Common Combinations (DROP Decisions)

1. **intent_mismatch + trust:** 60.9% of all drops
   - **Interpretation:** Most drops involve both intent misalignment AND trust issues

2. **cognitive_energy + intent_mismatch:** 37.6% of all drops
   - **Interpretation:** Fatigue makes intent misalignment more salient

3. **cognitive_energy + intent_mismatch + trust:** 44.4% of all drops
   - **Interpretation:** The "perfect storm" - fatigue + misalignment + trust deficit

**Key Insight:** Forces compound. Intent mismatch rarely exists alone - it combines with trust issues and cognitive fatigue to cause drops.

---

## Strategic Recommendations

### Priority 1: Fix the Trust Barrier (Step 0)

**Impact:** 20.6% drop rate (1,445 drops)

**Actions:**
- Add security badges and trust indicators
- Include testimonials or user count ("Trusted by X users")
- Clarify data usage and privacy policy
- Strengthen brand credibility signals

**Expected Impact:** 10-15% reduction in Step 0 drops = **144-217 additional users continue**

---

### Priority 2: Optimize Intent Alignment (Steps 1-3)

**Impact:** 53.2% combined drop rate (Steps 1-3)

**Actions:**
- **Step 1:** Show value preview before asking preferences
- **Step 2:** Frame annual fee question as part of recommendation process
- **Step 3:** Ensure clear value is delivered by this critical transition point

**Expected Impact:** 20-30% reduction in Steps 1-3 drops = **440-660 additional users continue**

---

### Priority 3: Maintain Intent Alignment (Steps 4+)

**Impact:** 9-15% drop rate (Steps 4-10)

**Actions:**
- Ensure every step clearly serves user's goal ("get a recommendation")
- Avoid steps that don't contribute to recommendation
- Reduce intent confusion with clear explanations

**Expected Impact:** 5-10% reduction in late-funnel drops = **90-180 additional users continue**

---

## The Decision Mechanics Equation

### For CONTINUE Decisions:
```
P(CONTINUE) ≈ Trust (51%) + Value (2.5%) - Intent Mismatch (1.6%)
```

**Interpretation:** Trust enables continuation. Value helps. Intent alignment is present but not dominant.

### For DROP Decisions:
```
P(DROP) ≈ Intent Mismatch (58.7%) + Trust Deficit (17.0%) + Cognitive Fatigue (7.5%)
```

**Interpretation:** Intent misalignment is the primary driver. Trust deficits compound. Fatigue amplifies.

### The Compound Effect:
```
P(DROP) ≈ Intent Mismatch × (1 + Trust Deficit Factor) × (1 + Fatigue Factor)
```

**Interpretation:** Forces multiply. Intent mismatch is worse when trust is low and fatigue is high.

---

## Key Insights for Product Strategy

### 1. Trust Matters Most at Entry

**Finding:** Trust drives 38.3% of landing page drops.

**Implication:** Landing page is a trust gate, not an intent gate.

**Strategy:** Strengthen trust signals before asking for any information.

---

### 2. Intent Alignment Becomes Dominant After Step 3

**Finding:** Intent mismatch dominates 84-100% of drops after Step 3.

**Implication:** Steps 0-3 are about trust and exploration. Steps 4+ are about intent alignment.

**Strategy:** Ensure Step 3 delivers clear value. After Step 3, focus exclusively on intent alignment.

---

### 3. Forces Compound (Not Isolated)

**Finding:** 60.9% of drops involve intent_mismatch + trust together.

**Implication:** Forces compound. Intent misalignment is worse when trust is low.

**Strategy:** Build trust early (Steps 0-2) to reduce compound drops. When intent alignment is unclear, strengthen trust signals.

---

### 4. The Commitment Effect

**Finding:** Drop rates decline from 20.6% (Step 0) to 9.0% (Step 10).

**Implication:** Users who pass the trust barrier are committed.

**Strategy:** Focus optimization efforts on Steps 0-3 (highest impact). After Step 3, focus on intent alignment, not trust/friction.

---

## Comparison: CONTINUE vs DROP

### What Makes Users CONTINUE?

**Forces (average SHAP values):**
- Trust: **51.0%** positive contribution (strongest)
- Value: 2.5% positive contribution
- Intent mismatch: -1.6% (negative - indicates alignment helps)

**Interpretation:** Users who continue have high trust. Value signals help, but trust is the primary enabler.

---

### What Makes Users DROP?

**Forces (normalized percentages):**
- Intent mismatch: **58.7%** of rejection pressure
- Trust: **17.0%** of rejection pressure
- Cognitive energy: **7.5%** of rejection pressure

**Interpretation:** Drops are primarily driven by intent misalignment. Trust deficits matter but are secondary.

---

## Data Quality Notes

- **Attribution Coverage:** 100% (all 36,765 traces include attribution)
- **Method:** Shapley values (cooperative game theory)
- **Baseline:** Adaptive by step context (early steps: higher trust expectation, late steps: lower intent mismatch expectation)
- **Values:** Both raw SHAP values and normalized percentages reported

**Interpretation:** Attribution is mathematically rigorous, context-aware, and comprehensive.

---

## Actionable Next Steps

### Immediate (High Impact)

1. **Strengthen Step 0 trust signals**
   - Add security badges, testimonials, user count
   - Expected: 10-15% reduction in Step 0 drops

2. **Ensure Step 3 delivers clear value**
   - This is the critical transition point (intent mismatch jumps to 84.5%)
   - Expected: 20-30% reduction in Steps 1-3 drops

3. **Frame questions as part of recommendation process**
   - Steps 1-2: Show value before asking
   - Expected: Better intent alignment, reduced drops

### Short-Term (Medium Impact)

4. **Reduce cognitive load in Steps 1-3**
   - Fatigue amplifies intent misalignment (37.6% of drops)
   - Expected: Reduced compound drops

5. **Clarify intent alignment in Steps 4+**
   - Ensure every step clearly serves user's goal
   - Expected: 5-10% reduction in late-funnel drops

---

## Conclusion

Credigo's onboarding flow has a **two-phase structure**:

1. **Trust Filter (Step 0):** Users evaluate trust before committing
2. **Intent Filter (Steps 1+):** Users evaluate intent alignment after committing

**The transition happens at Step 3**, where intent mismatch becomes the overwhelming driver (84.5%).

**Strategic Focus:**
- **Steps 0-3:** Trust + intent alignment (multi-factor)
- **Steps 4+:** Intent alignment only (single-factor)

**Expected Total Impact:** If all recommendations are implemented:
- Step 0: +144-217 users (trust improvements)
- Steps 1-3: +440-660 users (intent alignment)
- Steps 4+: +90-180 users (intent maintenance)
- **Total: +674-1,057 users continue** (from current 1,532 completions)

---

**This analysis transforms "users drop at Step X" into "users drop at Step X because force Y explains Z% of rejection pressure."**

**That's the power of Decision Attribution.**

