# Decision Intelligence Summary Schema

Strict schema definition for Decision Intelligence Summary (DIS) documents.

---

## Schema Contract

### Single Source of Truth

- DIS must be generated **ONLY** from a Decision Ledger file
- No manual overrides or additional data inputs
- Regeneration must produce identical output given the same ledger
- Generator is deterministic and versioned

### Required Sections

Every DIS **must** include these sections in order:

1. **Header** (not counted as section)
   - Product name
   - Generation timestamp
   - Source ledger filename
   - Ledger timestamp
   - "Regenerable from ledger. Non-authoritative." footer

2. **Document Type Declaration**
   - Explicit statement that this is a summary, not the ledger
   - Non-authoritative declaration
   - Regeneration statement

3. **Executive Summary**
   - High-level decision patterns (counts only)
   - Total boundaries, patterns, steps
   - Excluded patterns count

4. **Decision Boundaries by Step**
   - Step-by-step observations
   - Persona classes per step
   - Factor presence per step
   - Rejection/acceptance counts

5. **Acceptance Patterns**
   - Top acceptance patterns (by occurrence count)
   - Limited to 10 patterns for readability
   - Each pattern includes: step, persona, factors, outcome, count

6. **Rejection Patterns**
   - Top rejection patterns (by occurrence count)
   - Limited to 10 patterns for readability
   - Each pattern includes: step, persona, factors, outcome, count

7. **Decision Termination Points**
   - Rejection distribution across steps
   - Funnel stage breakdown (if applicable)
   - Total rejection counts

8. **Decision Pattern Hypotheses**
   - Must include disclaimer block (mandatory)
   - Each hypothesis must have:
     - Observed Pattern
     - Hypothesis statement
     - Testable Actions
   - Hypotheses are generated from observed patterns only

9. **Methodology Notes**
   - Counts of assertions in ledger
   - Data source reference
   - Timestamps (generation and ledger)
   - Format declaration

10. **Ledger Traceability**
    - Source ledger filename
    - Ledger timestamp
    - Total sequences and steps
    - Regeneration instructions

### Optional Sections

- **Persona Class Distribution** (appears only if relevant data exists)

### Forbidden Sections

❌ Model internals (parameters, weights, algorithms)  
❌ Probabilities as predictions  
❌ Optimization guarantees  
❌ Performance promises  
❌ Language implying ground truth beyond recorded decisions  

---

## Language Safety Rules

### Allowed Verbs

- observed
- recorded
- derived
- grouped
- mapped
- documented
- shows
- indicates
- contains
- includes
- represents

### Forbidden Verbs

- predicts
- optimizes
- guarantees
- proves
- causes
- ensures
- calculates (when implying prediction)
- forecasts
- determines
- decides

### Forbidden Terms

- "insight" → Use "decision pattern"
- "recommendation" → Use "hypothesis" (with disclaimer)
- "analysis" → Use "summary"

### Validation

Language safety is enforced at generation time. Generation fails if forbidden language is detected.

---

## Hypothesis Guardrails

Every hypothesis section must:

1. **Include Disclaimer Block** (mandatory, cannot be omitted)
   ```
   ⚠️ RECOMMENDATION DISCLAIMER
   
   The hypotheses below are derived from observed decision patterns...
   ```

2. **Reference Observed Patterns**
   - Each hypothesis must cite specific ledger assertions
   - Must reference step IDs, counts, or patterns

3. **Frame as Testable**
   - Use "may improve" not "will improve"
   - Use "hypothesis" not "recommendation"
   - Include "Testable Actions" list

4. **Never Prescriptive**
   - No guarantees
   - No optimization promises
   - No predictions

---

## Traceability Metadata

Every DIS must include:

- **Ledger Filename** (exact filename)
- **Ledger Timestamp** (from ledger metadata)
- **Generator Version** (generator version string)
- **Generation Timestamp** (when DIS was generated)

Header must include:
```
Regenerable from ledger. Non-authoritative.
```

---

## Output Format

### Primary Output: Markdown (.md)

- Standard Markdown format
- UTF-8 encoding
- Line breaks: LF (Unix-style)
- No manual formatting (all generated)

### Optional Output: JSON Sidecar

JSON sidecar contains:

```json
{
  "metadata": {
    "product_name": "...",
    "ledger_filename": "...",
    "ledger_timestamp": "...",
    "generator_version": "1.0.0",
    "generation_timestamp": "..."
  },
  "sections": [
    {
      "section_id": "...",
      "title": "...",
      "section_type": "required",
      "content_length": 1234
    }
  ],
  "validation": {
    "schema_valid": true,
    "language_safe": true
  }
}
```

---

## Validation Rules

Generation fails if:

1. **Schema Violation**
   - Missing required section
   - Section out of order
   - Forbidden section present

2. **Language Safety Violation**
   - Forbidden verb detected
   - Forbidden term detected

3. **Hypothesis Violation**
   - Missing disclaimer block
   - Hypothesis without observed pattern reference
   - Prescriptive language in hypotheses

---

## Generator Requirements

The DIS generator must:

1. **Be Deterministic**
   - Same ledger → Same output (given same version)
   - No randomness
   - No manual inputs

2. **Validate Strictly**
   - Fail on schema violations
   - Fail on language violations
   - Fail on hypothesis violations

3. **Be Versioned**
   - Generator version included in metadata
   - Version changes indicate behavior changes

4. **Be Traceable**
   - Include all required metadata
   - Reference source ledger explicitly
   - Enable regeneration

---

## Example Usage

```bash
python generate_dis.py \
  credigo_ss_decision_ledger.json \
  "Credigo Credit Card Recommendation Flow" \
  credigo_dis.md \
  --json-sidecar
```

This generates:
- `credigo_dis.md` - Markdown DIS
- `credigo_dis_metadata.json` - JSON sidecar (if flag set)

---

## Version History

- **1.0.0** - Initial schema definition
  - Required sections defined
  - Language safety rules established
  - Hypothesis guardrails defined
  - Traceability requirements specified

