# Credigo Deep Attribution Insights

**Analysis Date:** After Decision Attribution Layer Implementation  
**Total Decision Traces:** 36,765  
**CONTINUE Decisions:** 31,297 (85.1%)  
**DROP Decisions:** 5,468 (14.9%)

---

## Executive Summary

**The Core Truth:** Credigo's onboarding flow has **two distinct phases** with fundamentally different drop drivers:

1. **Entry Phase (Step 0):** Trust is the primary filter (49% of drops)
2. **Intent Phase (Steps 1+):** Intent mismatch dominates (55.6% overall, 84-100% after Step 3)

**Key Insight:** Users who pass the trust barrier are committed. Those who drop later do so because the flow asks for information before delivering value aligned with their intent.

---

## 1. CONTINUE vs DROP: The Success/Failure Divide

### What Makes Users CONTINUE?

**CONTINUE decisions are driven by:**
- **Trust: 51.0%** positive contribution (strongest force)
- **Value: 2.5%** positive contribution
- **Intent mismatch: -1.6%** (negative - indicates alignment helps)

**Interpretation:** Users who continue have high trust in the system. Value signals help, but trust is the primary enabler. Intent alignment (low mismatch) is present but not the dominant factor for continuation.

### What Makes Users DROP?

**DROP decisions are driven by:**
1. **Intent mismatch: 55.6%** of rejection pressure
2. **Trust: 20.7%** of rejection pressure
3. **Cognitive energy: 7.4%** of rejection pressure
4. **Value: 5.3%** of rejection pressure
5. **Risk: 5.2%** of rejection pressure

**Interpretation:** Drops are primarily driven by intent misalignment. Users who drop don't see how the current step serves their goal ("get a credit card recommendation"). Trust deficits matter but are secondary.

---

## 2. The Trust-to-Intent Transition

### Critical Finding: Funnel Has Two Phases

**Phase 1: Trust Filter (Step 0 - Landing Page)**
- **Drop rate:** 20.6% (1,445 drops)
- **Dominant force:** Trust (49.0% of drops)
- **Secondary force:** Intent mismatch (28.8%)
- **Interpretation:** At entry, users are evaluating "Can I trust this?" more than "Is this for me?"

**Phase 2: Intent Filter (Steps 1+)**
- **Drop rate:** Decreasing (from 19.7% to 9.0%)
- **Dominant force:** Intent mismatch (84-100% after Step 3)
- **Interpretation:** Once users trust the system, they're committed. Drops happen when steps don't serve their known goal.

### The Transition Point: Step 3

**Step 3: "straightforward + options are clearly defined"**
- **Drop rate:** 15.1% (549 drops)
- **Dominant force:** Intent mismatch (84.5%)
- **Transition marker:** This is where intent mismatch becomes the overwhelming driver (84.5%, up from 42.8% at Step 2)

**After Step 3:** Intent mismatch dominates 91-100% of drops. Users are committed; they drop only when steps clearly don't align with their goal.

---

## 3. Step Fragility Ranking

### Most Fragile Steps (Highest Drop Rates)

1. **Step 0: "Find the Best Credit Card In 60 seconds"**
   - Drop rate: **20.6%** (1,445 drops)
   - Driver: Trust (49%) + Intent mismatch (29%)
   - **Action:** Strengthen trust signals at landing page

2. **Step 1: "What kind of perks excite you the most?"**
   - Drop rate: **19.7%** (1,096 drops)
   - Driver: Intent mismatch (26%) + Trust (18%) + Cognitive energy (16%)
   - **Action:** Show value before asking preferences

3. **Step 2: "Any preference on annual fee?"**
   - Drop rate: **18.4%** (820 drops)
   - Driver: Intent mismatch (43%) + Trust (21%)
   - **Action:** Frame as part of recommendation, not a barrier

4. **Step 3: "straightforward + options are clearly defined"**
   - Drop rate: **15.1%** (549 drops)
   - Driver: Intent mismatch (84.5%)
   - **Action:** Critical transition point - ensure value is clear before this step

### Least Fragile Steps (Lowest Drop Rates)

**Steps 5-10:** Drop rates decline from 10.0% to 9.0%
- **Driver:** Intent mismatch (100%)
- **Interpretation:** Users who reach Step 5+ are highly committed. Drops are rare and driven purely by intent misalignment.

---

## 4. Force Co-Occurrence Patterns

### Top Force Pairs in DROP Decisions

1. **intent_mismatch + trust:** 3,326 occurrences (60.9% of all drops)
   - **Insight:** Most drops involve both intent misalignment AND trust issues

2. **cognitive_energy + intent_mismatch:** 2,055 occurrences (37.6% of all drops)
   - **Insight:** When users are fatigued, intent misalignment becomes more salient

### Top Force Triplets

1. **cognitive_energy + intent_mismatch + trust:** 2,430 occurrences (44.4% of all drops)
   - **Insight:** The "perfect storm" - fatigue + misalignment + trust deficit

2. **cognitive_energy + intent + intent_mismatch:** 1,458 occurrences (26.7% of all drops)
   - **Insight:** Intent confusion compounds cognitive fatigue

**Interpretation:** Forces compound. Intent mismatch rarely exists alone - it combines with trust issues and cognitive fatigue to cause drops.

---

## 5. Funnel Progression: The Force Evolution

### Early Funnel (Steps 0-3): Multi-Factor Decisions

**Step 0 (Landing Page):**
- Trust: 49.0% | Intent mismatch: 28.8% | Cognitive energy: 9.3%
- **Pattern:** Trust-dominated, multi-factor

**Step 1:**
- Intent mismatch: 25.5% | Trust: 17.9% | Cognitive energy: 15.8%
- **Pattern:** More balanced, cognitive fatigue emerging

**Step 2:**
- Intent mismatch: 42.8% | Trust: 20.8% | Cognitive energy: 10.0%
- **Pattern:** Intent mismatch increasing

**Step 3:**
- Intent mismatch: 84.5% | Trust: 7.6% | Cognitive energy: 2.3%
- **Pattern:** Intent mismatch becomes dominant

### Mid Funnel (Steps 4-7): Intent Mismatch Dominates

**Steps 4-7:** Intent mismatch 91-100%
- **Pattern:** Pure intent filtering
- **Interpretation:** Users are committed. Only intent misalignment causes drops.

### Late Funnel (Steps 8-10): Pure Intent Filtering

**Steps 8-10:** Intent mismatch 100%
- **Pattern:** Single-factor decisions
- **Interpretation:** Users are highly committed. Drops are rare and purely intent-driven.

---

## 6. Actionable Product Insights

### Insight 1: The Trust Barrier

**Finding:** Trust drives 49% of landing page drops.

**Implication:** The landing page is a trust gate, not an intent gate.

**Actions:**
- Strengthen trust signals: security badges, testimonials, brand credibility
- Reduce trust friction: clarify data usage, show privacy policy
- Trust-building copy: "Trusted by X users", "Secure & Private"

### Insight 2: The Intent Transition

**Finding:** Intent mismatch becomes dominant after Step 3 (84.5%+).

**Implication:** Steps 0-3 are about trust and exploration. Steps 4+ are about intent alignment.

**Actions:**
- **Before Step 3:** Show value preview, reduce friction, build trust
- **After Step 3:** Ensure every step clearly serves the user's goal ("get a recommendation")
- **Critical:** Step 3 is the transition - ensure value is delivered by this point

### Insight 3: The Compound Effect

**Finding:** 60.9% of drops involve intent_mismatch + trust together.

**Implication:** Forces compound. Intent misalignment is worse when trust is low.

**Actions:**
- Build trust early (Steps 0-2) to reduce compound drops
- When intent alignment is unclear, strengthen trust signals
- Avoid trust-damaging steps (e.g., "share personal info") before value is clear

### Insight 4: The Fatigue Factor

**Finding:** Cognitive energy + intent_mismatch co-occurs in 37.6% of drops.

**Implication:** Fatigue makes intent misalignment more salient.

**Actions:**
- Reduce cognitive load in Steps 1-3 (before intent mismatch dominates)
- Show progress indicators to reduce perceived effort
- Break complex steps into smaller chunks

### Insight 5: The Commitment Effect

**Finding:** Drop rates decline from 20.6% (Step 0) to 9.0% (Step 10).

**Implication:** Users who pass the trust barrier are committed.

**Actions:**
- Focus optimization efforts on Steps 0-3 (highest impact)
- After Step 3, focus on intent alignment, not trust/friction
- Recognize that late-funnel drops are rare and intent-driven

---

## 7. Strategic Recommendations

### Priority 1: Fix the Trust Barrier (Step 0)

**Impact:** 20.6% drop rate, 1,445 drops

**Actions:**
1. Strengthen trust signals (security, testimonials, credibility)
2. Clarify value proposition upfront
3. Reduce trust friction (privacy, data usage)

**Expected Impact:** 10-15% reduction in Step 0 drops = 144-217 additional users continue

### Priority 2: Optimize Intent Alignment (Steps 1-3)

**Impact:** 53.2% combined drop rate (Steps 1-3)

**Actions:**
1. Show value preview before asking questions
2. Frame questions as part of recommendation process
3. Ensure Step 3 delivers clear value

**Expected Impact:** 20-30% reduction in Steps 1-3 drops = 440-660 additional users continue

### Priority 3: Maintain Intent Alignment (Steps 4+)

**Impact:** 9-15% drop rate (Steps 4-10)

**Actions:**
1. Ensure every step clearly serves user goal
2. Avoid steps that don't contribute to recommendation
3. Reduce intent confusion (clear explanations)

**Expected Impact:** 5-10% reduction in late-funnel drops = 90-180 additional users continue

---

## 8. The Decision Mechanics Equation

### For CONTINUE Decisions:
```
P(CONTINUE) ≈ Trust (51%) + Value (2.5%) - Intent Mismatch (1.6%)
```

**Interpretation:** Trust enables continuation. Value helps. Intent alignment is present but not dominant.

### For DROP Decisions:
```
P(DROP) ≈ Intent Mismatch (55.6%) + Trust Deficit (20.7%) + Cognitive Fatigue (7.4%)
```

**Interpretation:** Intent misalignment is the primary driver. Trust deficits compound. Fatigue amplifies.

### The Compound Effect:
```
P(DROP) ≈ Intent Mismatch × (1 + Trust Deficit Factor) × (1 + Fatigue Factor)
```

**Interpretation:** Forces multiply. Intent mismatch is worse when trust is low and fatigue is high.

---

## 9. Limitations & Caveats

1. **Simulated Data:** These insights are from simulated decisions, not real user behavior
2. **Attribution Normalization:** SHAP values are normalized to percentages for readability
3. **Force Aggregation:** Some forces are aggregated (e.g., step_effort + effort_tolerance → effort)
4. **Step Context:** Step-level analysis doesn't account for user journey context

---

## 10. Next Steps

1. **Validate with Real Data:** Compare simulated insights with actual user drop data
2. **A/B Test Recommendations:** Test trust signals, intent alignment improvements
3. **Refine Attribution:** Optimize Shapley computation for production use
4. **Expand Analysis:** Persona-level attribution, cross-product comparisons

---

**This analysis transforms "what happened" into "why it happened" with mathematical rigor.**
The Decision Attribution Layer enables evidence-based product decisions.

