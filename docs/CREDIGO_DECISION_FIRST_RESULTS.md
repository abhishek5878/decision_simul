# Credigo: Decision-First Results

**Generated using decision-first queries (not analytics-style aggregations)**

## Overview

- **Decision Sequences**: 7,000
- **Product Steps**: 11 steps
- **Analysis Method**: Decision boundaries, stable precedents, competing explanations, acceptance surfaces

---

## 1. Decision Boundaries at Landing Page

**Step**: "Find the Best Credit Card In 60 seconds"

**6 Persona Classes at Decision Boundary:**

### Persona Class: `low_energy_medium_risk_low_effort`
- **Accepted**: 2,813
- **Rejected**: 755
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.05 - 0.30
  - Risk: 0.34 - 0.58

### Persona Class: `low_energy_low_risk_low_effort`
- **Accepted**: 1,619
- **Rejected**: 430
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.05 - 0.30
  - Risk: 0.20 - 0.28

### Persona Class: `medium_energy_low_risk_low_effort`
- **Accepted**: 740
- **Rejected**: 176
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.30 - 0.60
  - Risk: 0.20 - 0.28

### Persona Class: `medium_energy_medium_risk_low_effort`
- **Accepted**: 349
- **Rejected**: 81
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.30 - 0.59
  - Risk: 0.34 - 0.58

### Persona Class: `high_energy_low_risk_low_effort`
- **Accepted**: 32
- **Rejected**: 3
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.60 - 0.74
  - Risk: 0.20 - 0.27

### Persona Class: `high_energy_medium_risk_low_effort`
- **Accepted**: 2
- **Rejected**: 0
- **Cognitive Thresholds (accepted personas)**:
  - Energy: 0.60 - 0.62
  - Risk: 0.55 - 0.56

**Key Insight**: The landing page decision boundary separates personas primarily by energy and risk levels. Low-energy, medium-risk personas show the highest rejection rate (755 rejected vs 2,813 accepted).

---

## 2. Stable Precedents (Top 10 Recurring Patterns)

**25 stable precedents found (min 50 occurrences)**

### Pattern 1: Multi-Factor Continuation
- **Step**: "What kind of perks excite you the most?"
- **Persona Class**: `low_energy_high_risk_medium_effort`
- **Factors**: cognitive_fatigue, intent_mismatch, risk_spike
- **Outcome**: CONTINUE
- **Occurrences**: 4,403

### Pattern 2: Landing Page Continuation
- **Step**: "Find the Best Credit Card In 60 seconds"
- **Persona Class**: `low_energy_medium_risk_low_effort`
- **Factors**: cognitive_fatigue, intent_mismatch
- **Outcome**: CONTINUE
- **Occurrences**: 3,568

### Pattern 3: Multi-Factor Drop
- **Step**: "straightforward + options are clearly defined"
- **Persona Class**: `low_energy_high_risk_high_effort`
- **Factors**: cognitive_fatigue, effort_demand, intent_mismatch, risk_spike
- **Outcome**: DROP
- **Occurrences**: 3,038

### Pattern 4: Landing Page Drop
- **Step**: "Find the Best Credit Card In 60 seconds"
- **Persona Class**: `low_energy_low_risk_low_effort`
- **Factors**: cognitive_fatigue, intent_mismatch
- **Outcome**: DROP
- **Occurrences**: 2,049

**Key Insight**: The most stable precedent shows continuation at step 2 despite multiple negative factors (cognitive_fatigue, intent_mismatch, risk_spike). This pattern recurs 4,403 times, indicating that multi-factor reasoning is necessary to explain outcomes.

---

## 3. Competing Explanations (Multi-Factor Reasoning)

**6 competing explanations found**

### Continuations Despite LOW Intent Alignment

**Pattern**: Users continue through steps despite low intent alignment scores (0.30), explained by competing factors:

1. **Landing Page** (5,555 traces)
   - Intent Alignment: 0.30 (LOW)
   - Competing Factors: intent_mismatch, cognitive_fatigue
   - Outcome: CONTINUE

2. **Step 2: "What kind of perks excite you the most?"** (4,459 traces)
   - Intent Alignment: 0.30 (LOW)
   - Competing Factors: intent_mismatch, cognitive_fatigue, risk_spike
   - Outcome: CONTINUE

3. **Step 3: "Any preference on annual fee?"** (3,639 traces)
   - Intent Alignment: 0.30 (LOW)
   - Competing Factors: intent_mismatch, cognitive_fatigue, risk_spike
   - Outcome: CONTINUE

**Key Insight**: Intent alignment alone cannot explain continuation decisions. Users continue despite low alignment due to competing factors like cognitive fatigue and intent mismatch being insufficient to trigger drops.

---

## 4. Acceptance Surface (Deepest Step per Persona Class)

**6 persona class acceptance surfaces**

### `low_energy_medium_risk_low_effort`
- **Deepest Step Reached**: Step 10 (index 10)
- **Traces Reaching Step**: 804
- **Traces Completing Funnel**: 727

### `low_energy_low_risk_low_effort`
- **Deepest Step Reached**: Step 10 (index 10)
- **Traces Reaching Step**: 489
- **Traces Completing Funnel**: 438

### `medium_energy_low_risk_low_effort`
- **Deepest Step Reached**: Step 10 (index 10)
- **Traces Reaching Step**: 258
- **Traces Completing Funnel**: 249

### `medium_energy_medium_risk_low_effort`
- **Deepest Step Reached**: Step 10 (index 10)
- **Traces Reaching Step**: 121
- **Traces Completing Funnel**: 108

**Key Insight**: All persona classes that reach step 10 show high completion rates from that point (85-90% completion). The acceptance surface is relatively flat across persona classes at the deeper steps.

---

## Summary

All results are **decision-first** (not analytics-style):

✓ **Decision boundaries** per persona class with cognitive thresholds  
✓ **Stable precedents** showing recurring patterns (not global percentages)  
✓ **Competing explanations** forcing multi-factor reasoning  
✓ **Acceptance surfaces** per persona class (not aggregate funnel metrics)  

**No global drop rates, funnel percentages, or monocausal claims.**

All insights are precedent-based, conditioned on persona classes, and audit-safe (traceable to DecisionTrace objects).

