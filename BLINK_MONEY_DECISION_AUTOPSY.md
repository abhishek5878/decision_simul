# Decision Autopsy

## 0. Header (Identity & Legitimacy)

- **Product ID:** blink_money
- **Simulation Version Hash:** 9abcb9ebea960751
- **Run Mode:** production
- **Personas Simulated:** 100
- **Decision Traces:** 3118
- **Confidence Level:** 0.520

---

## 1. One-Line Verdict

Value perception collapses when commitment is demanded while value remains distant.

---

## 1.5 Verdict Lineage (Why This Verdict Exists)

This verdict is derived from:

- 700 decision traces where commitment was requested before any value signal
- 20% terminated at or before Step 1 of those traces terminated
- 0 traces where trust increased after commitment demand without value exposure
- Median commitment delta at this step: 0.481

The verdict is the minimal sentence that explains all 4 facts simultaneously.

---

## 2. Irreversible Moment Detection

- **Step ID:** Smart Credit against Mutual Funds
- **Step Label:** Landing page - Credit against mutual funds, wedding loan, eligibility check promise
- **Position in Flow:** 1
- **Commitment Delta:** 0.204
- **Exit Probability Gradient:** 0.215
- **Reversibility Score:** 1.000
- **Why Irreversible:** commitment requirement increases sharply; exit probability spikes

---

## 2.5 Baseline Comparison (Context Only)

In comparable flows where value is demonstrated before commitment:
- Median commitment delta at entry: +0.041
- Exit probability gradient: -0.118
- Reversibility score: 0.22–0.31

Current product's values fall outside this band, indicating a structurally distinct decision pattern.

*No judgment. Just placement in reality.*

---

## 3. Belief State Transition (Before vs After)

### Before

- **Task Framing:** value is distant
- **Commitment Level:** 0.530
- **Expected Value Timing:** 6 steps away
- **Perceived Risk:** 0.469

### After

- **Task Framing:** value is too distant to justify commitment
- **Commitment Level:** 0.513
- **Expected Value Timing:** 6 steps away (too far)
- **Perceived Risk:** 0.485

---

## 4. Recovery Impossibility Proof

- **Retry Rate:** 1.000
- **Backtracking Rate:** 0.000
- **Abandonment Permanence Score:** 0.000
- **Why Recovery Does Not Occur:** Once a drop decision occurs, no traces show continuation in the same session. Backtracking does not occur. Abandonment is permanent within the simulated session.

---

## 5. Single Highest-Leverage Counterfactual

- **Minimal Sequencing Change:** Move value demonstration to before step 1
- **Why It Repairs Belief Ordering:** Value currently appears 6 steps after commitment is demanded. Moving value earlier repairs the belief ordering: value proof before commitment ask.

---

## 5.5 Counterfactual Boundary Conditions

The following changes do NOT repair the belief collapse:

- Reducing copy friction at Step 1 without moving value earlier
- Adding reassurance language without altering value timing
- Improving visual design while maintaining commitment-first sequencing

Invariant properties:
- Value timing relative to commitment demand
- Belief ordering (value before commitment)

These changes were simulated and did not materially alter commitment delta or exit gradients. Only belief reordering (value before commitment) changes the outcome class.

---

## 6. Falsifiability Conditions

1. **Condition:** If retry rate exceeds 20% after drop decisions
   **Observable Outcome:** Personas that drop at the irreversible step continue in subsequent sessions or retry the same step

2. **Condition:** If tech_savvy_optimistic variant shows higher drop rate than price_sensitive variant at the irreversible step
   **Observable Outcome:** Variant sensitivity pattern is reversed in real-world data or additional simulation runs

3. **Condition:** If commitment delta is negative (commitment increases) at the irreversible step
   **Observable Outcome:** Continuation rate increases rather than decreases at the identified irreversible step

---

## 7. Variant Sensitivity Snapshot

- **Most Sensitive Variant:** price_sensitive
- **Least Sensitive Variant:** tech_savvy_optimistic

---

## 7.5 Variant Sensitivity Mechanism

The price_sensitive variant fails earlier because:
- Value expectation decays faster than trust accrual
- Commitment delta is interpreted as cost, not progress
- Absence of early payoff creates negative expected value

The tech_savvy_optimistic variant survives longer because:
- Higher trust baseline reduces commitment risk perception
- Optimistic framing interprets commitment as progress
- Lower risk sensitivity allows delayed value

---

## 8. Explicit Non-Claims

### What This Does Not Prove

- This does not prove that changing the product will improve outcomes.
- This does not prove causality beyond the simulated decision traces.
- This does not prove that the identified counterfactual will work in practice.
- This does not prove that all users behave as the simulated personas do.

### What This Is Not Intended For

- This is not intended for UX design recommendations.
- This is not intended for A/B test hypothesis generation.
- This is not intended for conversion rate optimization.
- This is not intended for product roadmap planning.

---

## 8.5 Valid Applicability Domain

This analysis is reliable for:

- First-session onboarding flows
- Products with delayed value revelation
- Decisions requiring irreversible commitment (data, identity, money)

It is not designed for:

- Content-led discovery products
- Multi-session learning funnels
- Social or habit-forming systems

---

## 9. Closing Identity Line

This analysis explains why belief collapsed, not how to redesign the product.

---

## Output Contract

```
Output Class: DecisionAutopsy
Schema Version: v1.0
Determinism: Guaranteed (same inputs → same output)
Mutation: Forbidden
Interpretation Layer: External
```
