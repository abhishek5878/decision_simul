# DIS Consistency Invariants

This document explains the consistency invariants enforced by the DIS generator to ensure the summary is internally consistent, reconcilable, and defensible.

---

## Overview

The Decision Intelligence Summary (DIS) enforces strict consistency invariants that guarantee:

1. **Step-Level Reconciliation** - All counts reconcile at the step level
2. **Persona Trace Consistency** - Persona counts are identical across sections
3. **Factor Presence Semantics** - Clear, consistent definition of factor presence
4. **Step Coverage Completeness** - All steps appear consistently
5. **Cross-Section Audit** - All numbers are derivable and consistent

If any invariant is violated, generation fails with a clear error message.

---

## Invariant 1: Step-Level Reconciliation

**Rule:** For every step, the sum of acceptance occurrences plus the sum of rejection occurrences must equal the total traces reaching that step.

**Mathematical Expression:**
```
For step S:
  Sum(acceptance_counts) + Sum(rejection_counts) = Total_traces(S)
```

**Validation:**
- Groups decision boundaries by step_id
- Sums acceptance and rejection counts for each step
- Compares sum to total supporting trace count
- Fails if mismatch detected

**Example Violation:**
```
Step 'Landing Page': Acceptance (2800) + Rejection (750) = 3550, 
but total traces = 3600
```

**Why This Matters:**
Ensures that every trace is accounted for at each step. Prevents scenarios where acceptance and rejection counts don't add up to the total, which would indicate data inconsistency.

---

## Invariant 2: Persona Trace Consistency

**Rule:** Persona trace counts must be identical wherever referenced across sections (step boundaries, acceptance patterns, rejection patterns).

**Validation:**
- Builds persona class trace counts from decision boundaries (source of truth)
- Verifies consistency within boundaries section
- Checks that patterns reference persona classes that exist in boundaries
- Fails if inconsistencies detected

**Example Violation:**
```
Persona 'low_energy_medium_risk' at step 'Step 2': 
Inconsistent trace counts in boundaries
```

**Why This Matters:**
Prevents different sections from reporting different counts for the same persona class, which would create confusion and undermine trust in the document.

---

## Invariant 3: Factor Presence Semantics

**Rule:** The term "factor present" has one explicit definition:
> "Factor present" means a factor appeared in at least one DecisionTrace at that step for that persona class.

**Definition Location:**
- Explicitly stated in Methodology Notes section
- All factor presence counts use this definition consistently

**Validation:**
- Definition must appear in Methodology Notes
- All factor counts must be computed using the same rule
- No alternative definitions allowed

**Why This Matters:**
Provides clarity on what "factor present" means, preventing misinterpretation. Ensures all factor counts are comparable and consistent.

---

## Invariant 4: Step Coverage Completeness

**Rule:** If a step appears anywhere in the document (acceptance patterns, rejection patterns, termination points), it MUST appear in "Decision Boundaries by Step" with at least a minimal entry.

**Validation:**
- Collects all step IDs from all sections
- Verifies all steps appear in Decision Boundaries section
- Fails if any step is missing from boundaries

**Example Violation:**
```
Steps appearing in patterns/termination but missing from boundaries: 
['Step 5', 'Step 7']
```

**Why This Matters:**
Ensures complete step coverage. Prevents scenarios where patterns reference steps that don't appear in the main boundaries section, which would create confusion about which steps are being analyzed.

---

## Invariant 5: Cross-Section Audit

**Rule:** All counts must reconcile across sections. No section may introduce numbers not derivable from the Decision Ledger.

**Validation:**
- Verifies pattern occurrence counts don't exceed boundary counts
- Checks that all numbers can be traced back to ledger assertions
- Fails if unreconcilable counts detected

**Example Violation:**
```
Acceptance pattern at 'Step 2' for 'low_energy_medium_risk': 
Occurrence count (5000) exceeds boundary total (3500)
```

**Why This Matters:**
Ensures the DIS is fully derivable from the ledger. Prevents scenarios where different sections report incompatible numbers, which would indicate computation errors or data manipulation.

---

## Error Handling

When a consistency invariant is violated:

1. **Generation Fails Immediately**
   - No partial DIS is generated
   - Clear error message explains which invariant failed

2. **Error Message Format:**
   ```
   Consistency Invariant Error: 
     - Step 'X': [specific violation]
     - [Additional violations]
   
   This indicates the ledger data has internal inconsistencies.
   The DIS cannot be generated until these are resolved.
   ```

3. **Required Actions:**
   - Review the Decision Ledger for data quality issues
   - Fix ledger generation if needed
   - Regenerate DIS after fixes

---

## Reconciliation Standards

The DIS generator provides the following guarantees:

1. **Step-Level Reconciliation**
   - Every count at the step level can be verified
   - Acceptance + Rejection = Total traces (for each step)

2. **Cross-Section Consistency**
   - Numbers in different sections don't contradict
   - All counts trace back to the same source (Decision Ledger)

3. **Complete Coverage**
   - All steps referenced anywhere appear in boundaries
   - No silent omissions

4. **Semantic Clarity**
   - All terms have explicit definitions
   - Definitions are consistent throughout

---

## Verification

To verify consistency invariants are working:

1. Run the DIS generator on a ledger
2. If generation succeeds, all invariants passed
3. If generation fails, review the error message for specific violations
4. Fix ledger data and regenerate

**Test Command:**
```bash
python decision_intelligence/generate_dis.py \
  <ledger_file> \
  <product_name> \
  <output_file>
```

---

## Example: Valid Ledger

A valid ledger that passes all consistency checks:

```json
{
  "decision_boundaries": [
    {
      "step_id": "Step 1",
      "persona_class": "persona_a",
      "accepted_count": 100,
      "rejected_count": 50,
      "supporting_trace_count": 150
    }
  ],
  "precedents_acceptance": [
    {
      "step_id": "Step 1",
      "persona_class": "persona_a",
      "occurrence_count": 100
    }
  ]
}
```

This passes because:
- Step-level: 100 + 50 = 150 ✓
- Persona consistency: All reference "persona_a" consistently ✓
- Step coverage: "Step 1" appears in boundaries ✓
- Cross-section: Pattern count (100) ≤ boundary count (150) ✓

---

## Example: Invalid Ledger (Would Fail)

An invalid ledger that would fail consistency checks:

```json
{
  "decision_boundaries": [
    {
      "step_id": "Step 1",
      "persona_class": "persona_a",
      "accepted_count": 100,
      "rejected_count": 50,
      "supporting_trace_count": 200  // Mismatch: 100 + 50 ≠ 200
    }
  ],
  "precedents_acceptance": [
    {
      "step_id": "Step 2",  // Missing from boundaries
      "persona_class": "persona_a",
      "occurrence_count": 100
    }
  ]
}
```

This fails because:
- Step-level: 100 + 50 ≠ 200 ✗
- Step coverage: "Step 2" not in boundaries ✗

---

## Summary

The consistency invariants ensure that:

✅ Every number in the DIS can be reconciled end-to-end  
✅ Different sections don't tell different stories  
✅ The DIS cannot drift from the ledger silently  
✅ Founders can trust the numerical consistency  
✅ Auditors can verify all claims  

If a founder asks: "Can every number here be reconciled end-to-end?"

**The answer is unambiguously yes.**

