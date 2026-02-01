# Founder Read Guide: Decision Intelligence Summary

A quick guide to reading and using Decision Intelligence Summaries correctly.

---

## What This Document Is

✅ **A human-readable summary** of decision patterns from your product flow  
✅ **Hypotheses for testing** — ideas about what might improve your product  
✅ **Derived from immutable records** — the Decision Ledger  

## What This Document Is NOT

❌ **The Decision Ledger itself** — that's the authoritative, audit-grade record  
❌ **Predictions** — it describes what happened, not what will happen  
❌ **Optimization guarantees** — hypotheses need testing  
❌ **Analytics dashboard** — it's a decision pattern summary, not metrics  

---

## How to Read It (5 Steps)

### 1. Start with the Executive Summary

This gives you the high-level decision patterns:
- How many decision boundaries were observed
- Which steps show the most rejection patterns
- Key persona classes present in your flow

**Takeaway:** Understand the scale and scope of observed patterns.

---

### 2. Review Decision Boundaries by Step

Each step shows:
- How many rejections were recorded
- Which persona classes are present
- What factors are associated with decisions

**Takeaway:** Identify which steps are filtering users most aggressively.

---

### 3. Examine Acceptance and Rejection Patterns

These sections show:
- Which patterns lead to continuation (acceptance)
- Which patterns lead to drops (rejection)
- How frequently each pattern was observed

**Takeaway:** Understand which user types and conditions lead to different outcomes.

---

### 4. Read Decision Pattern Hypotheses Carefully

⚠️ **Important:** These are **hypotheses**, not guarantees.

Each hypothesis:
- Is tied to specific observed patterns
- Includes testable actions
- Represents a testable idea, not a promise

**Takeaway:** Use these as starting points for A/B tests or optimization experiments.

---

### 5. Check Ledger Traceability

At the bottom, you'll see:
- Source ledger file name
- When the ledger was generated
- When this summary was generated

**Takeaway:** This document can be regenerated from the ledger. It's a snapshot, not a manual report.

---

## Common Misunderstandings to Avoid

### ❌ "This predicts our conversion rate will improve by X%"

✅ **Correct:** "This observes that X% of users in this pattern continued. Testing this hypothesis may improve conversion."

### ❌ "This guarantees optimizing Step 1 will help"

✅ **Correct:** "This observes Step 1 has the most rejections. The hypothesis is that optimizing it may help. Test it."

### ❌ "These insights are the truth about our users"

✅ **Correct:** "These patterns were observed in the recorded decisions. They represent what happened, not universal truths."

### ❌ "I should edit this document to add my thoughts"

✅ **Correct:** "This document is auto-generated. If you have questions, reference the Decision Ledger or regenerate the summary."

---

## How to Use This Document

### ✅ Good Uses

1. **Product Strategy** — Use patterns to identify optimization opportunities
2. **A/B Test Planning** — Use hypotheses as test ideas
3. **Stakeholder Communication** — Share decision patterns with your team
4. **Product Roadmap** — Prioritize steps that show most rejection patterns

### ❌ Bad Uses

1. **Legal/Compliance Review** — Use the Decision Ledger instead
2. **Performance Guarantees** — This doesn't predict future performance
3. **Manual Editing** — Document will be regenerated, edits will be lost
4. **Model Validation** — Use the Decision Ledger for technical validation

---

## Questions to Ask

When reading a Decision Intelligence Summary, ask:

1. **"Which steps show the most rejection patterns?"**
   - These are priority candidates for optimization

2. **"Which persona classes are most affected?"**
   - These user segments may need targeted messaging

3. **"What hypotheses can I test?"**
   - Each hypothesis section provides testable actions

4. **"What does the ledger say?"**
   - If you need raw data, reference the Decision Ledger

5. **"Can I regenerate this?"**
   - Yes, this summary is generated from the ledger

---

## Key Takeaways

1. **This is a summary, not the source** — The Decision Ledger is authoritative
2. **Patterns, not predictions** — It describes what happened, not what will happen
3. **Hypotheses, not guarantees** — All recommendations are testable ideas
4. **Regeneratable** — This document can be recreated from the ledger
5. **Business-focused** — Designed for product strategy, not technical auditing

---

## Next Steps

After reading a Decision Intelligence Summary:

1. **Identify priority steps** — Which steps have the most rejection patterns?
2. **Formulate tests** — Convert hypotheses into A/B tests or experiments
3. **Reference the ledger** — If you need audit-grade data, use the Decision Ledger
4. **Plan optimization** — Use pattern observations to guide product improvements
5. **Track results** — After testing hypotheses, compare results to patterns

---

## Support

For questions about:
- **Decision Intelligence Summary** — Refer to `README.md` in this directory
- **Decision Ledger** — Refer to `decision_graph/DECISION_LEDGER_README.md`
- **Technical details** — Reference the Decision Ledger for audit-grade data

