# Decision Intelligence Summary

## Overview

The **Decision Intelligence Summary (DIS)** is a human-readable interpretation layer derived from the Decision Ledger. It provides decision patterns and hypotheses for product strategy.

This is **not** the Decision Ledger itself. The Decision Ledger is the authoritative, immutable record.

The DIS is generated deterministically from the ledger using the `generate_dis.py` script. It is a product artifact, not a consulting document.

---

## When to Use Decision Intelligence Summary vs Decision Ledger

### Use Decision Intelligence Summary When:

✅ Presenting findings to founders, product teams, or stakeholders  
✅ Generating product strategy hypotheses  
✅ Communicating decision patterns in business language  
✅ Creating actionable recommendations (framed as testable hypotheses)  
✅ Reviewing product flow optimization opportunities  

### Use Decision Ledger When:

✅ Auditing decision records  
✅ Verifying specific decision assertions  
✅ Replaying historical decisions  
✅ Comparing decisions across policy versions  
✅ Building systems that require immutable decision records  
✅ Legal or compliance review requiring audit-grade data  

---

## Document Contract

### Required Sections

Every Decision Intelligence Summary **must** include:

1. **Document Type Declaration** — Explicit statement that this is a summary, not the ledger
2. **Executive Summary** — High-level decision patterns
3. **Decision Boundaries by Step** — Step-by-step observations
4. **Acceptance Patterns** — Patterns leading to continuation
5. **Rejection Patterns** — Patterns leading to drops
6. **Decision Termination Points** — Where users exit the flow
7. **Decision Pattern Hypotheses** — Testable hypotheses with disclaimer
8. **Methodology Notes** — Data source and generation details
9. **Ledger Traceability** — Reference to source ledger file

### Optional Sections

- Persona Class Distribution (if relevant)
- Additional pattern analysis (if supported by ledger data)

### Forbidden Sections

❌ Model internals (parameters, weights, algorithms)  
❌ Probabilities as predictions about future outcomes  
❌ Optimization guarantees or performance promises  
❌ Language implying ground truth beyond recorded decisions  
❌ Claims that cannot be traced to the Decision Ledger  

---

## Language Safety Rules

### Allowed Verbs

- observed
- recorded
- derived
- grouped
- documented
- mapped

### Forbidden Verbs

- predicts
- optimizes
- guarantees
- proves
- ensures
- calculates (when implying prediction)

### Terminology Replacements

- ❌ "insight" → ✅ "decision pattern"
- ❌ "analysis" → ✅ "summary" or "patterns"
- ❌ "recommendation" → ✅ "hypothesis" (with disclaimer)
- ❌ "prediction" → ✅ "observed pattern"
- ❌ "optimization" → ✅ "hypothesis for testing"

---

## Recommendation Boundaries

All recommendations must:

1. Be explicitly framed as **hypotheses**
2. Be tied to **specific decision boundaries** from the ledger
3. Include a **testable action list**
4. Be preceded by the **recommendation disclaimer**
5. Never claim guaranteed improvements or optimization

### Standard Disclaimer

Include this disclaimer before all hypotheses:

> **⚠️ RECOMMENDATION DISCLAIMER**
>
> The hypotheses below are derived from observed decision patterns in the Decision Ledger. They are not guaranteed improvements, optimization recommendations, or predictions. They represent testable hypotheses based on recorded decision boundaries.

---

## Ledger Traceability Requirements

Every Decision Intelligence Summary must include:

1. **Source Ledger Filename** — Exact name of the ledger file
2. **Ledger Generation Timestamp** — When the ledger was generated
3. **Summary Generation Timestamp** — When this summary was generated
4. **Total Sequences Count** — Number of sequences in the ledger
5. **Total Steps Count** — Number of steps analyzed

### Regeneration Statement

Include this statement in the Ledger Traceability section:

> This document can be regenerated from the Decision Ledger at any time. Manual edits to this summary are not recommended, as regeneration will overwrite changes.

---

## Template Usage

1. Copy `DECISION_INTELLIGENCE_SUMMARY_TEMPLATE.md`
2. Replace all `[PLACEHOLDER]` values with actual data
3. Follow language safety rules strictly
4. Ensure all hypotheses include the disclaimer
5. Verify ledger traceability information is complete

---

## Quality Checklist

Before delivering a Decision Intelligence Summary:

- [ ] Document Type Declaration is present and clear
- [ ] All required sections are included
- [ ] No forbidden sections or language
- [ ] All verbs follow language safety rules
- [ ] All recommendations are framed as hypotheses
- [ ] Recommendation disclaimer is included
- [ ] Ledger traceability is complete
- [ ] Regeneration statement is included
- [ ] No claims beyond what the ledger contains

---

## Examples

- `CREDIGO_DECISION_INTELLIGENCE_SUMMARY.md` — Credigo product example
- `DECISION_INTELLIGENCE_SUMMARY_TEMPLATE.md` — Standard template

