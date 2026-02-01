# How the Model Works - Blink Money Example

## 🎯 Overview

The Decision Simulation Engine models how users make decisions at each step of your product onboarding flow. It predicts where and why users drop off using behavioral science principles.

---

## 📥 What Client Provides (Input)

### For Blink Money:

1. **Product Steps** (5 steps defined):
   - Step 0: Smart Credit Exploration
   - Step 1: Eligibility Check (Phone Number)
   - Step 2: PAN & DOB Input
   - Step 3: OTP Verification
   - Step 4: Eligibility Confirmation

2. **Step Attributes** (per step):
   - Risk level, effort required, value shown, delay to value
   - Example: Step 2 has `risk_signal: 0.7` (high risk - PAN is sensitive)

3. **Target Persona**:
   - "30+ Urban salaried/self-employed professionals with mutual fund holdings who need short-term liquidity"

4. **Screenshots** (optional but recommended):
   - One screenshot per step for richer analysis

**That's it.** No user data, no analytics, no historical conversion rates needed.

---

## ⚙️ How the Model Works

### Step 1: Load Personas
- Loads 1000 realistic Indian personas from NVIDIA database
- Filters to match target: 30+, salaried, Tier-1 cities, MF holders
- Result: ~684 matching personas

### Step 2: Simulate Each Persona
For each persona, the model:
1. **Tracks cognitive state** (energy, risk, effort, value, control)
2. **Infers user intent** (e.g., "short-term liquidity without selling investments")
3. **Evaluates each step**:
   - Computes perceived risk (PAN input = high risk)
   - Computes perceived value (no value shown until Step 4)
   - Computes intent alignment (does step match user's goal?)
4. **Makes decision**: Continue or Drop based on state

### Step 3: Identify Patterns
- Analyzes 1000 decision traces
- Finds where most users drop (Step 2: PAN & DOB Input)
- Identifies why (belief breaks when asked for sensitive data before value)

### Step 4: Generate Insights
- Creates step-specific recommendations
- Explains psychology behind abandonment
- Provides actionable "one bet" with execution details

---

## 📤 What Client Receives (Output)

### 1. Core Verdict (One Sentence)
**Blink Money Example:**
> "Trust collapses when personal information requests (PAN, DOB, OTP verification) appear before users see their credit limit estimate."

### 2. Belief Break Analysis
**Where:** Step 2 (PAN & DOB Input)  
**Why:** Users asked for sensitive data (PAN) before seeing value (credit limit)  
**Psychology:** "Users expect to see eligibility before committing sensitive information. When asked for PAN without seeing limit, belief collapses."

### 3. The One Bet (Actionable Recommendation)
**Headline:** "Show personalized credit limit estimate AFTER phone + PAN (Step 2-3), BEFORE OTP verification (Step 4)"

**Execution Specificity:**
- Step 1: Phone number
- Step 2: PAN + DOB
- **NEW:** Show "Estimated Credit Limit: ₹X - ₹Y" immediately
- Step 3: OTP verification (now with value already shown)
- Step 4: Final confirmation

**Why This Works:**
- Establishes value before asking for more trust (OTP)
- Reduces abandonment at Step 2-3
- Minimal change (just reordering flow)

### 4. Decision Simulation (Step-by-Step)
For each step, shows:
- **What user sees** (UI elements, text, buttons)
- **What user thinks** (mental model)
- **What user understands** (deeper comprehension)
- **Emotional state** (anxiety, confidence, etc.)

**Example (Step 2 - PAN Input):**
- Sees: "Enter PAN" field, "Verify" button, "No credit score impact" text
- Thinks: "They want my PAN but I haven't seen my limit yet"
- Understands: "Sensitive data requested before value shown - risky"
- Feels: "Anxious about sharing without seeing benefit"

### 5. Context Graph Visualization
- Visual diagram showing all 5 steps
- Color-coded: Red = belief breaks, Green = value shown
- Shows risk/value/delay metrics per step
- Reveals structural misalignment

### 6. Falsifiable Conditions
Testable conditions to validate recommendations:
- "If showing estimate early doesn't improve conversion, timing isn't the blocker"
- "If users don't engage with early estimate, they don't value seeing limit"

---

## 📊 Blink Money Results Summary

**Input:**
- 5 product steps
- Target persona: 30+ salaried professionals with MF holdings
- 1000 personas from database

**Output:**
- **Belief Break:** Step 2 (PAN & DOB Input) - 38% drop rate
- **Root Cause:** Value delayed until Step 4, but trust demanded at Steps 1-3
- **Recommendation:** Show credit limit estimate at Step 2-3, before OTP
- **Expected Impact:** 35-40% conversion improvement

**Deliverables:**
1. `BLINK_MONEY_DECISION_AUTOPSY_RESULT.json` (complete analysis)
2. `blink_money_3page_brief.pdf` (founder-facing summary)
3. Context graph visualization

---

## 🔄 Process Timeline

1. **Day 1:** Client provides product steps + target persona
2. **Day 1-2:** Model runs simulation (1000 personas × 5 steps)
3. **Day 2:** Analysis generated (belief breaks, recommendations)
4. **Day 2:** Results delivered (JSON + PDF)

**Total Time:** 1-2 days from input to output

---

## 💡 Key Differentiators

**What Makes This Different:**
- **No historical data needed** - works for new products
- **Explains WHY** - not just where users drop
- **Step-specific** - exact recommendations (not generic)
- **Testable** - includes falsifiable conditions
- **Actionable** - "one bet" with execution details

**Traditional Analytics:**
- "38% drop at Step 2" ❌ (doesn't explain why)

**This Model:**
- "38% drop at Step 2 because value delayed until Step 4, but trust demanded at Step 2. Solution: Show value at Step 2-3" ✅

---

**Example:** Blink Money  
**Input:** 5 steps, target persona  
**Output:** "Show credit limit at Step 2-3, not Step 4"  
**Result:** Actionable, testable recommendation with expected impact
