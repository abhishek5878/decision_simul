# Decision Ledger Output Format

## Overview

The decision ledger is an audit-grade, interpretation-free record of decisions.

**This output is a decision ledger, not an analysis or recommendation.**

## Architectural Rule: Interpretation is Forbidden

This module generates ONLY:
1. **Assertion Layer**: Machine-verifiable facts
2. **Precedent Layer**: Historical grounding (timestamps, occurrence counts)

Interpretation, narrative, and explanatory text must be generated separately (if at all) and explicitly labeled as non-binding.

## Output Structure

### 1. Decision Boundary Assertions

Machine-verifiable facts about decision boundaries at each step.

Each assertion includes:
- Step identifier
- Persona class definition
- Persona class coherence metrics (stability proof)
- Accepted/rejected counts
- Observed cognitive thresholds
- Supporting trace count
- Explicit counterexamples (if any)
- Precedent layer (timestamps, occurrence counts)

**No interpretation. No narrative. Only facts.**

### 2. Precedent Assertions

Historical grounding for recurring decision patterns.

Each assertion includes:
- Step identifier
- Persona class
- Dominant factors
- Outcome (CONTINUE/DROP)
- Occurrence count
- First/last observed timestamps
- Time span
- Occurrence rate
- Stability flag

**No explanation. Only historical grounding.**

### 3. Decision Density Assertions

Decision boundaries and density (replaces "acceptance surface").

Each assertion includes:
- Step identifier
- Has observed rejections (boolean)
- Rejection decision count
- Decision density (rejections per reaching persona)
- Is last decision boundary (boolean)
- First/last rejection timestamps

**No completion rates. No funnel language. Only decision boundaries.**

## Persona Class Rules

- Persona classes are artifacts, not truth
- Coherence must be computed before using classes
- Only stable classes (coherence >= threshold) are included in assertions
- Coherence metrics include:
  - Internal variance (cognitive state dimensions)
  - Dominant factor variance
  - Counterexample rate
  - Coherence score (0-1)

## Language Constraints

- Neutral, ledger-style language
- Short lines, structured bullets
- No adjectives like "high", "low", "significant" unless numerically defined
- No narrative text
- No interpretation
- No funnel language (completion, conversion, drop rate)
- No claims of importance, primacy, or causality

## Usage

```python
from decision_graph.decision_ledger import generate_decision_ledger
from decision_graph.ledger_formatter import format_decision_ledger_as_text

# Generate ledger
ledger_data = generate_decision_ledger(sequences, product_steps)

# Export as JSON
import json
with open('ledger.json', 'w') as f:
    json.dump(ledger_data, f, indent=2)

# Export as text
ledger_text = format_decision_ledger_as_text(ledger_data)
with open('ledger.txt', 'w') as f:
    f.write(ledger_text)
```

## What is NOT Included

❌ Key Insights  
❌ Summary paragraphs  
❌ Interpretive language  
❌ Funnel metrics (completion rates, conversion)  
❌ Monocausal explanations  
❌ Claims of importance or primacy  
❌ Narrative text  

## What IS Included

✅ Machine-verifiable facts  
✅ Supporting trace counts  
✅ Counterexamples  
✅ Persona class coherence metrics  
✅ Historical grounding (timestamps)  
✅ Decision boundaries (not completion rates)  

Every assertion can be verified directly from DecisionTrace objects.

