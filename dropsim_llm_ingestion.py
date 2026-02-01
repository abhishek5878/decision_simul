#!/usr/bin/env python3
"""
dropsim_llm_ingestion.py - LLM-Augmented Ingestion Layer

Extracts structured LiteScenario + TargetGroup from product descriptions
using LLM, then runs DropSim simulation.
"""

from typing import Dict, List, Optional, Tuple
import json
import re
from dropsim_lite_input import LiteScenario, LitePersona, LiteStep
from dropsim_target_filter import TargetGroup


# ============================================================================
# LLM Client Interface (Abstract)
# ============================================================================

class LLMClient:
    """
    Abstract LLM client interface.
    
    Implementations should provide a `.complete(prompt: str) -> str` method.
    """
    
    def complete(self, prompt: str) -> str:
        """
        Complete a prompt and return the response text.
        
        Args:
            prompt: The prompt string
        
        Returns:
            Response text from the LLM
        """
        raise NotImplementedError("Subclasses must implement complete()")


# ============================================================================
# Prompt Engineering
# ============================================================================

# ============================================================================
# Fintech Archetypes
# ============================================================================

FINTECH_ARCHETYPES = [
    "payments_wallet",      # UPI, wallets, P2P
    "neo_bank",             # Accounts, cards, deposits
    "lending_bnpl",         # Credit, BNPL, loans
    "trading_investing",    # Stock trading, mutual funds, crypto
    "insurance",            # Health, life, motor insurance
    "personal_finance_manager"  # PFM, spend analytics, goal-based savings
]


def build_llm_prompt_for_fintech_ingestion(
    product_text: str,
    persona_notes: Optional[str] = None,
    target_group_notes: Optional[str] = None,
) -> str:
    """
    Build a deterministic, instruction-heavy prompt for LLM to extract
    LiteScenario + TargetGroup from product description.
    
    Args:
        product_text: Product description, website copy, or OCR text
        persona_notes: Optional plain-language notes about target personas
        target_group_notes: Optional notes about target group filters
    
    Returns:
        Complete prompt string
    """
    prompt_parts = []
    
    prompt_parts.append("""You are a product analyst helping to extract structured information about a fintech product for behavioral simulation.

Your task is to analyze the product description and extract:
1. Key user personas (2-5 personas)
2. Product funnel steps (4-8 steps, in order from first touch to first value)
3. Primary target group filters (optional)

**IMPORTANT**: If the input contains a "PRODUCT_WEBSITE_ANALYSIS" section, prioritize that analysis as it contains pre-processed insights from the actual website. Use it as the primary source for step extraction and archetype classification.

CRITICAL: You must output ONLY valid JSON matching the exact schema below. Use only the allowed categorical values specified.
""")
    
    prompt_parts.append("""
## OUTPUT SCHEMA

```json
{
  "lite_scenario": {
    "product_type": "fintech",
    "fintech_archetype": "payments_wallet" | "neo_bank" | "lending_bnpl" | "trading_investing" | "insurance" | "personal_finance_manager",
    "personas": [
      {
        "name": "Persona Name",
        "sec": "low" | "mid" | "high",
        "urban_rural": "rural" | "tier2" | "metro",
        "digital_skill": "low" | "medium" | "high",
        "family_influence": "low" | "medium" | "high",
        "aspiration": "low" | "medium" | "high",
        "price_sensitivity": "low" | "medium" | "high",
        "risk_attitude": "risk_averse" | "balanced" | "risk_tolerant" (optional),
        "age_bucket": "senior" | "middle" | "young",
        "intent": "low" | "medium" | "high"
      }
    ],
    "steps": [
      {
        "name": "Step Name (use EXACT question or heading from screenshot)",
        "type": "landing" | "signup" | "kyc" | "payment" | "consent" | "other",
        "mental_complexity": "low" | "medium" | "high",
        "effort": "low" | "medium" | "high",
        "risk": "low" | "medium" | "high",
        "irreversible": true | false,
        "value_visibility": "low" | "medium" | "high",
        "delay_to_value": "instant" | "soon" | "later",
        "reassurance": "low" | "medium" | "high",
        "authority": "low" | "medium" | "high"
      }
    ]
  },
  "target_group": {
    "sec": ["low", "mid", "high"] (optional),
    "urban_rural": ["rural", "tier2", "metro"] (optional),
    "age_bucket": ["young", "middle", "senior"] (optional),
    "digital_skill": ["low", "medium", "high"] (optional),
    "risk_attitude": ["risk_averse", "balanced", "risk_tolerant"] (optional),
    "intent": ["low", "medium", "high"] (optional)
  }
}
```
""")
    
    prompt_parts.append("""
## FINTECH ARCHETYPE CLASSIFICATION

**CRITICAL: Carefully analyze the product to determine the correct archetype. Look for:**
- Primary value proposition (what problem does it solve?)
- Core transaction type (payments, lending, investing, insurance, savings)
- User journey focus (onboarding for what purpose?)

Classify the product into ONE of these archetypes:

- **payments_wallet**: UPI, digital wallets, P2P transfers, payment apps
  - Key indicators: "send money", "UPI", "wallet", "pay bills", "recharge"
  - Examples: PhonePe, Paytm, Google Pay, Razorpay
  
- **neo_bank**: Digital banking accounts, cards, deposits, banking services
  - Key indicators: "bank account", "savings account", "current account", "debit card", "banking"
  - Examples: RazorpayX, Jupiter, Fi, Niyo
  
- **lending_bnpl**: Credit cards, BNPL, personal loans, credit lines, borrowing money
  - Key indicators: "loan", "credit", "borrow", "EMI", "BNPL", "credit card", "repay", "interest rate"
  - Examples: Slice, ZestMoney, KreditBee, MoneyTap, EarlySalary
  
- **trading_investing**: Stock trading, mutual funds, crypto, SIPs, investment platforms
  - Key indicators: "invest", "stocks", "mutual funds", "SIP", "trading", "portfolio", "returns"
  - Examples: Zerodha, Groww, CoinSwitch, Upstox, Paytm Money
  
- **insurance**: Health, life, motor insurance, insurance policies
  - Key indicators: "insurance", "premium", "coverage", "policy", "claim", "health insurance", "life insurance"
  - Examples: PolicyBazaar, Digit, Acko, Care Health
  
- **personal_finance_manager**: PFM, spend analytics, goal-based savings, expense tracking, credit card recommendations
  - Key indicators: "expense tracking", "spend analytics", "savings goals", "budget", "PFM", "money management", "credit card recommendation", "card comparison", "card finder"
  - Examples: ET Money, Walnut, CRED, MoneyView, Credigo.club

**Classification Rules:**
1. If the product mentions loans, credit, borrowing, or repayment → **lending_bnpl**
2. If the product mentions investing, trading, stocks, or mutual funds → **trading_investing**
3. If the product mentions insurance, premium, or coverage → **insurance**
4. If the product is primarily about payments, UPI, or money transfers → **payments_wallet**
5. If the product offers banking accounts or banking services → **neo_bank**
6. If the product focuses on tracking expenses, savings goals, money management, OR credit card recommendations/comparisons → **personal_finance_manager**

**Be precise**: 
- A credit card recommendation/comparison tool (like Credigo.club) is **personal_finance_manager**, NOT lending_bnpl.
- A savings app that helps users save money for goals is **personal_finance_manager**, NOT lending_bnpl.
- A payment app that processes transactions is **payments_wallet**, NOT lending_bnpl.

Set `fintech_archetype` in the output JSON.

## PERSONA EXTRACTION GUIDELINES

Extract **2-4 distinct personas** that represent different user segments. Each persona must be meaningfully different (e.g., "New-to-credit Tier-2 salaried", "Metro trader Gen Z", "Middle-aged homemaker saver").

For each persona, infer attributes from the product description:

- **sec**: Income/SEC hints (low = lower income, mid = middle class, high = affluent)
- **urban_rural**: City/tier hints (rural = rural areas, tier2 = smaller cities, metro = Tier-1 metros)
- **digital_skill**: Comfort with apps/UPI/netbanking (low = basic, medium = moderate, high = power user)
- **family_influence**: Family decision dynamics (low = individualistic, high = family-led decisions)
- **aspiration**: Growth orientation (low = stability-focused, high = upwardly mobile)
- **price_sensitivity**: Deal-seeking behavior (low = price insensitive, high = deal-only)
- **risk_attitude**: Risk preferences (risk_averse = conservative, risk_tolerant = trading/credit/BNPL comfortable)
- **age_bucket**: Age cues (senior = 50+, middle = 30-50, young = <30)
- **intent**: Motivation level (low = casual browser, high = urgent need)

If uncertain, choose the most conservative option (lower risk, lower effort) consistent with the description.
""")
    
    prompt_parts.append("""
## STEP EXTRACTION GUIDELINES

**CRITICAL: If screenshots are provided, extract EXACTLY as many steps as there are screenshots.**

**DYNAMIC STEP EXTRACTION**: Extract steps based on the actual product flow described, not generic templates.

**If PRODUCT_SCREENSHOT_ANALYSIS is provided:**
- Count the number of screenshots mentioned (e.g., "Screenshot ss1", "Screenshot ss2", etc.)
- Extract EXACTLY that many steps - ONE step per screenshot
- DO NOT consolidate similar steps
- DO NOT skip any screenshots
- Each screenshot = one step in the flow

**If no screenshots:**
- Identify funnel steps in order from first touch to first value
- Extract **4-8 steps** that represent the complete onboarding flow

**If PRODUCT_WEBSITE_ANALYSIS is provided:**
- Use the USER FLOW ANALYSIS section as the primary source
- Extract steps exactly as identified in that analysis
- Map each step to appropriate attributes based on the analysis notes

**If only product description is provided:**
- Infer steps from the product description
- Look for explicit mentions of onboarding flows, signup processes, verification steps
- Identify the actual user journey, not generic fintech steps

Common fintech steps by archetype:

**payments_wallet / neo_bank:**
- **Landing / education**: Product explanation, value proposition (low risk, low effort, low mental complexity)
- **Phone + OTP**: Phone verification (low risk, medium effort, low mental complexity)
- **KYC**: PAN, Aadhaar, selfie upload (medium risk, high effort, high mental complexity, high authority)
- **Bank-linking / UPI / card linking**: Financial data linking (high risk, medium effort, irreversible)
- **Consent / terms**: Legal consent (medium risk, low effort, medium mental complexity)
- **First transaction / value event**: First payment, investment, savings goal (low risk, low effort, instant value)

**lending_bnpl:**
- **Landing / education**: Product explanation, credit limit preview (low risk, low effort)
- **Phone + OTP**: Verification (low risk, medium effort)
- **KYC**: PAN, Aadhaar, selfie (medium risk, high effort, high mental complexity)
- **Credit check / approval**: Credit score check, limit assignment (high risk, low effort, irreversible)
- **Mandate / repayment setup**: Auto-debit setup, repayment terms (high risk, medium effort, irreversible)
- **First purchase / disbursement**: First BNPL purchase or loan disbursement (medium risk, low effort, instant value)

**trading_investing:**
- **Landing / education**: Product explanation, investment options (low risk, low effort)
- **Phone + OTP**: Verification (low risk, medium effort)
- **KYC**: PAN, Aadhaar, bank details (medium risk, high effort, high mental complexity)
- **Instrument selection**: Choose stocks/MFs/crypto (high mental complexity, medium effort)
- **Funding / bank linking**: Add money, link bank (high risk, medium effort, irreversible)
- **First trade / investment**: Place first order or start SIP (medium risk, low effort, instant value)

**insurance:**
- **Landing / quote**: Get quote, compare plans (low risk, low effort)
- **Phone + OTP**: Verification (low risk, medium effort)
- **KYC**: PAN, Aadhaar, nominee details (medium risk, high effort, high mental complexity)
- **Health check / underwriting**: Medical tests, risk assessment (high risk, high effort, high mental complexity)
- **Payment / premium**: Pay first premium (high risk, medium effort, irreversible)
- **Policy activation**: Policy document, coverage start (low risk, low effort, instant value)

**personal_finance_manager:**

**For credit card recommendation tools (quiz-based, like Credigo.club):**
- **Landing / education**: Product explanation, "60-second quiz" hook, privacy claims ("no PAN, no sensitive data") (low risk, low effort, low mental complexity, high reassurance)
- **Quiz start**: First spending/lifestyle questions appear (low risk, low effort, low mental complexity)
- **Quiz progression**: Mid-quiz, questions continue (low risk, low effort, medium mental complexity)
- **Quiz completion**: User finishes all questions (low risk, low effort, medium mental complexity)
- **Results page**: Personalized card recommendations shown (rewards, low fees, lounge) (low risk, low effort, instant value, high value visibility)
- **Post-results**: No direct apply button, manual redirect to bank sites (medium risk, high effort, irreversible, delayed value)

**For PFM apps with bank linking:**
- **Landing / education**: Product explanation, value proposition (low risk, low effort)
- **Phone + OTP**: Verification (low risk, medium effort)
- **Bank linking / account aggregation**: Connect bank accounts, credit cards (high risk, medium effort, irreversible)
- **Goal setup**: Create savings goals, budgets (medium mental complexity, medium effort)
- **First sync / insights**: First data sync, spending insights (low risk, low effort, instant value)

For each step, map attributes:
- **mental_complexity**: How much thinking/decision-making required (low = simple, high = complex forms/choices)
- **effort**: Physical/time effort (low = click, high = find documents, upload, retry)
- **risk**: Data/financial risk perception (low = browsing, high = sharing financial data)
- **irreversible**: Can user undo this? (true = bank linking, payment; false = browsing, signup)
- **value_visibility**: How clear is the benefit? (low = vague promise, high = immediate benefit shown)
- **delay_to_value**: Steps until payoff (instant = immediate value, soon = 1-2 steps, later = 3+ steps)
- **reassurance**: Trust signals (low = none, high = security badges, testimonials)
- **authority**: Official backing (low = none, high = bank/govt partnership)

If uncertain, choose conservative (lower risk, lower effort) consistent with the description.
""")
    
    prompt_parts.append("""
## TARGET GROUP EXTRACTION

If the product description mentions a specific target audience, extract filters:
- Focus on the primary target (e.g., "young professionals" → age_bucket: ["young"], urban_rural: ["metro"])
- If no clear target mentioned, omit target_group or leave it empty

## ARCHETYPE-SPECIFIC BIASES

When mapping steps to attributes, apply these archetype-specific biases:

**lending_bnpl:**
- Credit approval/mandate steps: higher `risk` (0.7-0.9), higher `delay_to_value` ("later")
- Repayment setup: `irreversible: true`, higher `risk`

**payments_wallet:**
- Bank-linking/UPI mandate: higher `effort` (0.6-0.8), higher `risk` (0.7-0.9), `irreversible: true`
- First transaction: lower `delay_to_value` ("instant"), higher `value_visibility` ("high")

**trading_investing:**
- Instrument selection/onboarding: higher `mental_complexity` (0.7-0.9)
- Funding/buy steps: higher `risk` (0.6-0.8), `irreversible: true`

**insurance:**
- Health check/underwriting: higher `mental_complexity` (0.7-0.9), higher `effort` (0.7-0.9)
- Premium payment: higher `risk` (0.7-0.9), `irreversible: true`

**personal_finance_manager:**
- Bank linking: higher `risk` (0.6-0.8), `irreversible: true`
- First sync/insights: lower `delay_to_value` ("instant"), higher `value_visibility` ("high")

## CONSTRAINTS

- Output ONLY valid JSON, no markdown, no explanations
- Use only the exact categorical values specified (case-sensitive)
- Keep personas to 2-4
- Steps: Extract ALL steps from screenshots (if 10 screenshots, extract 10 steps). DO NOT consolidate steps.
- Ensure steps are in chronological order
- If a field is truly unknown, use the most conservative option
- Each persona must be meaningfully distinct (different SEC, age, digital skill, or risk attitude)

## FALLBACK BEHAVIOR

If the product flow is ambiguous or inputs are sparse:
- Infer a reasonable generic fintech onboarding for the identified archetype (payments, lending, trading, etc.)
- Use common step patterns for that archetype (see archetype-specific step templates above)
- Keep personas and steps interpretable and realistic
- It's better to infer a complete, usable scenario than to return incomplete data
""")
    
    # The product_text may already contain structured sections from consolidate_product_context
    # Check if it has section headers
    if "## PRODUCT_URL" in product_text or "## SCREENSHOT_" in product_text or "## PRODUCT_WEBSITE_ANALYSIS" in product_text or "## PRODUCT_SCREENSHOT_ANALYSIS" in product_text:
        # Already structured by wizard, use as-is
        prompt_parts.append("\n## PRODUCT CONTEXT\n")
        prompt_parts.append(product_text)
        
        # Add special instructions if screenshot analysis is present (HIGHEST PRIORITY)
        if "## PRODUCT_SCREENSHOT_ANALYSIS" in product_text:
            prompt_parts.append("""
## PRIORITY INSTRUCTIONS FOR SCREENSHOT-ANALYZED CONTENT

The PRODUCT_SCREENSHOT_ANALYSIS section above contains pre-analyzed insights from actual product screenshots. 
**THIS IS THE HIGHEST PRIORITY SOURCE** - Screenshots show the exact user flow.

**PRIORITIZE THIS SECTION** for:
- Product archetype classification (use the archetype identified in the analysis)
- Step extraction (use the EXACT USER FLOW FROM SCREENSHOTS section as the primary source)
- Step ordering (use the exact order and step numbers from screenshots)
- Step names (use the exact names from screenshots, e.g., "Step 1 of 7: Landing", "Step 2 of 7: Quiz start")

The SCREENSHOT_X_RAW sections are provided for additional context if needed.

When extracting steps:
1. Use the EXACT steps identified in the EXACT USER FLOW FROM SCREENSHOTS section
2. Preserve the exact step names and order from screenshots
3. Map each step to the LiteStep schema with appropriate attributes
4. Use the step numbers if visible (Step X of Y) to ensure correct ordering
5. Use the key attributes (risk, effort, complexity) mentioned in the analysis as guidance
""")
        elif "## PRODUCT_WEBSITE_ANALYSIS" in product_text:
            prompt_parts.append("""
## PRIORITY INSTRUCTIONS FOR LLM-ANALYZED CONTENT

The PRODUCT_WEBSITE_ANALYSIS section above contains pre-analyzed insights from the actual website. 
**PRIORITIZE THIS SECTION** for:
- Product archetype classification (use the archetype identified in the analysis)
- Step extraction (use the USER FLOW ANALYSIS section as the primary source)
- Persona hints (use the PERSONA HINTS section if available)

The PRODUCT_WEBSITE_RAW_CONTENT section is provided for additional context if needed.

When extracting steps:
1. Use the steps identified in the USER FLOW ANALYSIS section
2. Map each step to the LiteStep schema with appropriate attributes
3. Ensure steps are in the exact chronological order from the analysis
4. Use the key attributes (risk, effort, complexity) mentioned in the analysis as guidance
""")
        
        # Extract persona and target notes if they're in the structured format
        if "## PERSONA_NOTES" in product_text:
            persona_section = product_text.split("## PERSONA_NOTES")[1].split("##")[0].strip()
            if persona_section:
                persona_notes = persona_section
        if "## TARGET_GROUP_NOTES" in product_text:
            target_section = product_text.split("## TARGET_GROUP_NOTES")[1].split("##")[0].strip()
            if target_section:
                target_group_notes = target_section
    else:
        # Plain text, add as product description
        prompt_parts.append("\n## PRODUCT DESCRIPTION\n")
        prompt_parts.append(product_text)
    
    # Add explicit instructions for screenshot-aware extraction
    if "## SCREENSHOT_" in product_text:
        prompt_parts.append("""
## SCREENSHOT-AWARE EXTRACTION INSTRUCTIONS

When extracting steps:
- **PRIORITIZE SCREENSHOT sections** - Screenshots show the actual user flow and step order
- **Use PRODUCT_TEXT** for product description and value proposition
- **Infer step order** from screenshot sequence:
  - First screens typically show: welcome/landing, signup/phone/OTP
  - Middle screens: KYC, bank-linking, mandates, consent
  - Final screens: first value event (transaction, investment, loan disbursement, etc.)
- **Map screenshot labels/buttons** to step names (e.g., "Verify Phone" → Phone verification step)
- If screenshots are sparse, use PRODUCT_TEXT to fill gaps, but prioritize screenshot order

When extracting personas:
- **Use PERSONA_NOTES** to bias persona attributes, but map to standardized enum bands
- **Use TARGET_GROUP_NOTES** to infer target group filters
- If notes are vague, infer reasonable personas based on product archetype and typical users
""")
    
    if persona_notes and "## PERSONA_NOTES" not in product_text:
        prompt_parts.append("\n## PERSONA NOTES\n")
        prompt_parts.append(persona_notes)
    
    if target_group_notes and "## TARGET_GROUP_NOTES" not in product_text:
        prompt_parts.append("\n## TARGET GROUP NOTES\n")
        prompt_parts.append(target_group_notes)
    
    prompt_parts.append("\n\n## OUTPUT (JSON ONLY)\n")
    
    return "\n".join(prompt_parts)


# ============================================================================
# Persona Deduplication
# ============================================================================

def deduplicate_and_limit_personas(
    personas: List[LitePersona],
    max_personas: int = 4,
    target_group: Optional[TargetGroup] = None
) -> List[LitePersona]:
    """
    Merge obviously redundant personas and cap the total.
    Prefer keeping personas that best match the inferred target group (if any).
    
    Args:
        personas: List of LitePersona objects
        max_personas: Maximum number of personas to keep
        target_group: Optional target group to prioritize matching personas
    
    Returns:
        Deduplicated and limited list of personas
    """
    if len(personas) <= max_personas:
        return personas
    
    # Group personas by key attributes (SEC + age + urban_rural + digital_skill + intent)
    seen = {}
    unique_personas = []
    
    for persona in personas:
        # Create a key for deduplication
        key = (
            persona.sec,
            persona.age_bucket,
            persona.urban_rural,
            persona.digital_skill,
            persona.intent
        )
        
        if key not in seen:
            seen[key] = persona
            unique_personas.append(persona)
        else:
            # If duplicate, prefer the one with more specific attributes or better name
            existing = seen[key]
            # Keep the one with risk_attitude if the other doesn't have it
            if persona.risk_attitude and not existing.risk_attitude:
                seen[key] = persona
                unique_personas[unique_personas.index(existing)] = persona
    
    # If still too many, prioritize by target group match
    if len(unique_personas) > max_personas and target_group:
        # Score each persona by how well it matches target group
        def score_persona(p: LitePersona) -> int:
            score = 0
            tg_dict = target_group.to_dict()
            
            if tg_dict.get('sec') and p.sec in tg_dict['sec']:
                score += 3
            if tg_dict.get('age_bucket') and p.age_bucket in tg_dict['age_bucket']:
                score += 3
            if tg_dict.get('urban_rural') and p.urban_rural in tg_dict['urban_rural']:
                score += 2
            if tg_dict.get('digital_skill') and p.digital_skill in tg_dict['digital_skill']:
                score += 2
            if tg_dict.get('risk_attitude') and p.risk_attitude and p.risk_attitude in tg_dict['risk_attitude']:
                score += 2
            if tg_dict.get('intent') and p.intent in tg_dict['intent']:
                score += 1
            
            return score
        
        # Sort by score (descending) and take top max_personas
        unique_personas.sort(key=score_persona, reverse=True)
        unique_personas = unique_personas[:max_personas]
    elif len(unique_personas) > max_personas:
        # No target group, just take first max_personas
        unique_personas = unique_personas[:max_personas]
    
    return unique_personas


# ============================================================================
# Step Normalization
# ============================================================================

def normalize_fintech_steps(steps: List[LiteStep], fintech_archetype: Optional[str] = None) -> List[LiteStep]:
    """
    Ensures:
      - Steps are ordered from first touch to first value
      - There is at most one of each heavy step type (kyc, payment, consent) unless clearly justified
      - Names are cleaned (consistent formatting)
      - Steps are between 3-10 in count
    
    Args:
        steps: List of LiteStep objects
        fintech_archetype: Optional archetype for archetype-specific normalization
    
    Returns:
        Normalized list of steps
    """
    if len(steps) == 0:
        return steps
    
    # Clean step names (consistent formatting)
    for step in steps:
        step.name = step.name.strip()
        # Normalize separators
        step.name = step.name.replace(' & ', ' + ')
        step.name = step.name.replace(' and ', ' + ')
    
    # Remove extremely low-value "noise" steps
    noise_keywords = ['scrolling', 'browsing', 'viewing', 'reading', 'clicking']
    filtered_steps = [
        s for s in steps
        if not any(keyword in s.name.lower() for keyword in noise_keywords)
    ]
    
    if len(filtered_steps) < len(steps):
        # Some steps were filtered
        steps = filtered_steps
    
    # Ensure steps are in reasonable order (landing first, value steps later)
    # For credit card recommendation tools, use semantic ordering
    if fintech_archetype == 'personal_finance_manager':
        # Check if this is a quiz-based flow (credit card recommendation)
        quiz_keywords = ['quiz', 'question', 'recommendation', 'result']
        has_quiz = any(kw in s.name.lower() for s in steps for kw in quiz_keywords)
        
        if has_quiz:
            # Semantic ordering for quiz-based credit card recommendation
            def quiz_step_order(s: LiteStep) -> int:
                name_lower = s.name.lower()
                if 'landing' in name_lower or 'education' in name_lower:
                    return 1
                elif 'quiz start' in name_lower or ('quiz' in name_lower and 'start' in name_lower):
                    return 2
                elif 'quiz progression' in name_lower or ('quiz' in name_lower and 'progress' in name_lower):
                    return 3
                elif 'quiz completion' in name_lower or ('quiz' in name_lower and 'complet' in name_lower):
                    return 4
                elif 'result' in name_lower and 'post' not in name_lower:
                    return 5
                elif 'post' in name_lower or 'apply' in name_lower:
                    return 6
                else:
                    return 99
            
            steps = sorted(steps, key=quiz_step_order)
        else:
            # Regular PFM flow ordering
            type_order = {
                'landing': 1,
                'signup': 2,
                'kyc': 3,
                'consent': 4,
                'payment': 5,
                'other': 6
            }
            
            def step_sort_key(s: LiteStep) -> tuple:
                type_priority = type_order.get(s.type, 99)
                delay_priority = {'instant': 3, 'soon': 2, 'later': 1}.get(s.delay_to_value, 2)
                return (type_priority, delay_priority)
            
            steps = sorted(steps, key=step_sort_key)
    else:
        # Simple heuristic: landing/signup early, kyc/payment middle, value events late
        type_order = {
            'landing': 1,
            'signup': 2,
            'kyc': 3,
            'consent': 4,
            'payment': 5,
            'other': 6
        }
        
        def step_sort_key(s: LiteStep) -> tuple:
            type_priority = type_order.get(s.type, 99)
            delay_priority = {'instant': 3, 'soon': 2, 'later': 1}.get(s.delay_to_value, 2)
            return (type_priority, delay_priority)
        
        steps = sorted(steps, key=step_sort_key)
    
    # Clamp step count to 3-10
    if len(steps) < 3:
        # If too few, synthesize a missing core step if archetype demands it
        if fintech_archetype == 'lending_bnpl' and not any(s.type == 'kyc' for s in steps):
            # Add a KYC step
            steps.insert(-1, LiteStep(
                name="KYC Verification",
                type="kyc",
                mental_complexity="high",
                effort="high",
                risk="medium",
                irreversible=False,
                value_visibility="low",
                delay_to_value="later",
                reassurance="high",
                authority="high"
            ))
        elif fintech_archetype in ['trading_investing', 'neo_bank'] and not any(s.type == 'kyc' for s in steps):
            steps.insert(-1, LiteStep(
                name="KYC Verification",
                type="kyc",
                mental_complexity="high",
                effort="high",
                risk="medium",
                irreversible=False,
                value_visibility="low",
                delay_to_value="later",
                reassurance="high",
                authority="high"
            ))
    
    if len(steps) > 10:
        # Keep first (landing), last (value), and middle steps
        keep_indices = {0, len(steps) - 1}
        # Also keep all kyc, payment, consent steps
        for i, step in enumerate(steps):
            if step.type in ['kyc', 'payment', 'consent']:
                keep_indices.add(i)
        
        # Fill gaps to get ~10 steps
        if len(keep_indices) < 10:
            step = 1
            while len(keep_indices) < 10 and step < len(steps):
                keep_indices.add(step)
                step += 2
        
        steps = [steps[i] for i in sorted(keep_indices) if i < len(steps)]
    
    return steps


# ============================================================================
# LLM Response Parsing & Validation
# ============================================================================

def parse_llm_json_response(response_text: str) -> Dict:
    """
    Parse JSON from LLM response, handling markdown code blocks if present.
    
    Args:
        response_text: Raw LLM response
    
    Returns:
        Parsed JSON dict
    """
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()
    
    # Parse JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}\n\nResponse text:\n{response_text[:500]}")


def validate_lite_persona(persona_dict: Dict) -> Optional[Dict]:
    """
    Validate and normalize a LitePersona dict.
    
    Returns normalized dict or None if invalid.
    """
    # Required fields
    required = ['name', 'sec', 'urban_rural', 'digital_skill', 'family_influence', 
                'aspiration', 'price_sensitivity', 'age_bucket', 'intent']
    
    for field in required:
        if field not in persona_dict:
            return None
    
    # Validate enum values
    valid_sec = ['low', 'mid', 'high']
    valid_urban_rural = ['rural', 'tier2', 'metro']
    valid_digital_skill = ['low', 'medium', 'high']
    valid_family_influence = ['low', 'medium', 'high']
    valid_aspiration = ['low', 'medium', 'high']
    valid_price_sensitivity = ['low', 'medium', 'high']
    valid_age_bucket = ['senior', 'middle', 'young']
    valid_intent = ['low', 'medium', 'high']
    valid_risk_attitude = ['risk_averse', 'balanced', 'risk_tolerant']
    
    # Normalize values (case-insensitive matching)
    normalized = {}
    normalized['name'] = str(persona_dict['name'])
    
    # Map to closest valid value
    def normalize_enum(value, valid_values):
        value_lower = str(value).lower()
        for v in valid_values:
            if v.lower() == value_lower:
                return v
        # Default to first valid value if no match
        return valid_values[0]
    
    normalized['sec'] = normalize_enum(persona_dict['sec'], valid_sec)
    normalized['urban_rural'] = normalize_enum(persona_dict['urban_rural'], valid_urban_rural)
    normalized['digital_skill'] = normalize_enum(persona_dict['digital_skill'], valid_digital_skill)
    normalized['family_influence'] = normalize_enum(persona_dict['family_influence'], valid_family_influence)
    normalized['aspiration'] = normalize_enum(persona_dict['aspiration'], valid_aspiration)
    normalized['price_sensitivity'] = normalize_enum(persona_dict['price_sensitivity'], valid_price_sensitivity)
    normalized['age_bucket'] = normalize_enum(persona_dict['age_bucket'], valid_age_bucket)
    normalized['intent'] = normalize_enum(persona_dict['intent'], valid_intent)
    
    # Optional risk_attitude
    if 'risk_attitude' in persona_dict and persona_dict['risk_attitude']:
        normalized['risk_attitude'] = normalize_enum(persona_dict['risk_attitude'], valid_risk_attitude)
    
    return normalized


def validate_lite_step(step_dict: Dict) -> Optional[Dict]:
    """
    Validate and normalize a LiteStep dict.
    
    Returns normalized dict or None if invalid.
    """
    # Required fields
    required = ['name', 'type', 'mental_complexity', 'effort', 'risk', 
                'irreversible', 'value_visibility', 'delay_to_value']
    
    for field in required:
        if field not in step_dict:
            return None
    
    # Validate enum values
    valid_type = ['landing', 'signup', 'kyc', 'payment', 'consent', 'other']
    valid_complexity = ['low', 'medium', 'high']
    valid_effort = ['low', 'medium', 'high']
    valid_risk = ['low', 'medium', 'high']
    valid_value_visibility = ['low', 'medium', 'high']
    valid_delay = ['instant', 'soon', 'later']
    valid_reassurance = ['low', 'medium', 'high']
    valid_authority = ['low', 'medium', 'high']
    
    normalized = {}
    normalized['name'] = str(step_dict['name'])
    # Helper function
    def normalize_enum(value, valid_values):
        value_lower = str(value).lower()
        for v in valid_values:
            if v.lower() == value_lower:
                return v
        return valid_values[0]
    
    normalized['type'] = normalize_enum(step_dict['type'], valid_type)
    normalized['mental_complexity'] = normalize_enum(step_dict['mental_complexity'], valid_complexity)
    normalized['effort'] = normalize_enum(step_dict['effort'], valid_effort)
    normalized['risk'] = normalize_enum(step_dict['risk'], valid_risk)
    normalized['irreversible'] = bool(step_dict['irreversible'])
    normalized['value_visibility'] = normalize_enum(step_dict['value_visibility'], valid_value_visibility)
    normalized['delay_to_value'] = normalize_enum(step_dict['delay_to_value'], valid_delay)
    
    # Optional fields with defaults
    normalized['reassurance'] = normalize_enum(step_dict.get('reassurance', 'medium'), valid_reassurance)
    normalized['authority'] = normalize_enum(step_dict.get('authority', 'medium'), valid_authority)
    
    return normalized


def infer_lite_scenario_and_target_from_llm(
    product_text: str,
    persona_notes: Optional[str] = None,
    target_group_notes: Optional[str] = None,
    llm_client: LLMClient = None,
    verbose: bool = False,
    dry_run: bool = False,
    force_steps: Optional[List] = None
) -> Tuple[LiteScenario, Optional[TargetGroup], Optional[str]]:
    """
    Use LLM to extract LiteScenario + TargetGroup from product description.
    
    Args:
        product_text: Product description text
        persona_notes: Optional persona notes
        target_group_notes: Optional target group notes
        llm_client: LLM client instance (must implement .complete())
        verbose: Print debug info
        dry_run: If True, return early after extraction (no validation)
    
    Returns:
        Tuple of (LiteScenario, Optional[TargetGroup], Optional[fintech_archetype])
    
    Raises:
        ValueError: If LLM response cannot be parsed or validated
    """
    if llm_client is None:
        raise ValueError("llm_client must be provided")
    
    # Build prompt
    prompt = build_llm_prompt_for_fintech_ingestion(
        product_text, persona_notes, target_group_notes
    )
    
    if verbose:
        print("📝 LLM Prompt (first 500 chars):")
        print(prompt[:500] + "...")
        print()
    
    # Call LLM
    try:
        response_text = llm_client.complete(prompt)
    except Exception as e:
        raise ValueError(f"LLM call failed: {e}")
    
    if verbose:
        print("🤖 LLM Response (first 500 chars):")
        print(response_text[:500] + "...")
        print()
    
    # Parse JSON
    try:
        parsed = parse_llm_json_response(response_text)
    except ValueError as e:
        raise ValueError(f"Failed to parse LLM response: {e}")
    
    if verbose:
        print("📋 Parsed JSON structure:")
        print(f"   Keys: {list(parsed.keys())}")
        print()
    
    # Extract lite_scenario
    if 'lite_scenario' not in parsed:
        raise ValueError("LLM response missing 'lite_scenario' field")
    
    lite_scenario_dict = parsed['lite_scenario']
    
    # Extract fintech_archetype
    fintech_archetype = lite_scenario_dict.get('fintech_archetype')
    if fintech_archetype and fintech_archetype not in FINTECH_ARCHETYPES:
        if verbose:
            print(f"⚠️  Warning: Invalid fintech_archetype '{fintech_archetype}', defaulting to 'personal_finance_manager'")
        fintech_archetype = "personal_finance_manager"
    
    # If no archetype provided, try to infer from product context
    if not fintech_archetype:
        # Try to infer from product_text keywords
        product_lower = product_text.lower() if product_text else ""
        archetype_keywords = {
            'lending_bnpl': ['loan', 'credit', 'borrow', 'emi', 'repay', 'interest rate', 'credit card', 'bnpl'],
            'payments_wallet': ['pay', 'upi', 'wallet', 'transfer', 'send money', 'payment app'],
            'trading_investing': ['invest', 'stock', 'mutual fund', 'sip', 'trading', 'portfolio', 'returns'],
            'insurance': ['insurance', 'premium', 'coverage', 'policy', 'claim', 'health insurance'],
            'neo_bank': ['bank account', 'savings account', 'current account', 'banking', 'digital bank'],
            'personal_finance_manager': ['expense', 'track', 'save', 'budget', 'goal', 'spend', 'pfm', 'money management']
        }
        
        # Count keyword matches
        matches = {arch: sum(1 for kw in keywords if kw in product_lower) 
                  for arch, keywords in archetype_keywords.items()}
        best_match = max(matches.items(), key=lambda x: x[1])
        
        if best_match[1] > 0:
            fintech_archetype = best_match[0]
            if verbose:
                print(f"ℹ️  Inferred archetype: {fintech_archetype} (from product context)")
        else:
            fintech_archetype = "personal_finance_manager"
            if verbose:
                print(f"⚠️  No archetype provided and couldn't infer from context, defaulting to 'personal_finance_manager'")
    
    # Extract target_group early (needed for persona deduplication)
    target_group = None
    if 'target_group' in parsed and parsed['target_group']:
        target_group_dict = parsed['target_group']
        try:
            target_group = TargetGroup.from_dict(target_group_dict)
        except Exception as e:
            if verbose:
                print(f"⚠️  Warning: Invalid target_group, ignoring: {e}")
            target_group = None
    
    # Validate and normalize personas
    validated_personas = []
    for persona_dict in lite_scenario_dict.get('personas', []):
        validated = validate_lite_persona(persona_dict)
        if validated:
            validated_personas.append(LitePersona.from_dict(validated))
        elif verbose:
            print(f"⚠️  Warning: Dropped invalid persona: {persona_dict.get('name', 'Unknown')}")
    
    if len(validated_personas) == 0:
        raise ValueError("No valid personas extracted from LLM response. Try adding more detail about your user types.")
    
    # Deduplicate and limit personas
    validated_personas = deduplicate_and_limit_personas(
        validated_personas,
        max_personas=4,
        target_group=target_group
    )
    
    if len(validated_personas) == 0:
        raise ValueError("No valid personas after deduplication. Try adding more detail about distinct user segments.")
    
    # If force_steps is provided (direct extraction), use those instead
    if force_steps is not None:
        if verbose:
            print(f"📸 Using directly extracted steps: {len(force_steps)} steps (bypassing LLM step extraction)")
        validated_steps = force_steps
        # Still normalize names/formatting but don't consolidate
        for step in validated_steps:
            step.name = step.name.strip()
            step.name = step.name.replace(' & ', ' + ')
            step.name = step.name.replace(' and ', ' + ')
    else:
        # Validate and normalize steps from LLM
        validated_steps = []
        for step_dict in lite_scenario_dict.get('steps', []):
            validated = validate_lite_step(step_dict)
            if validated:
                validated_steps.append(LiteStep.from_dict(validated))
            elif verbose:
                print(f"⚠️  Warning: Dropped invalid step: {step_dict.get('name', 'Unknown')}")
        
        if len(validated_steps) == 0:
            raise ValueError("No valid steps extracted from LLM response. Try adding more detail about your onboarding flow.")
        
        # Check if we have explicit screenshot count - if so, preserve ALL steps
        screenshot_count = None
        if "## PRODUCT_SCREENSHOT_ANALYSIS" in product_text or "## SCREENSHOT_" in product_text:
            import re
            screenshot_matches = re.findall(r'Screenshot (ss\d+|SCREENSHOT \d+)', product_text)
            if screenshot_matches:
                screenshot_count = len(set(screenshot_matches))
                if verbose:
                    print(f"📸 Detected {screenshot_count} screenshots - preserving all {screenshot_count} steps (no consolidation)")
        
        # Normalize steps - but skip consolidation if we have explicit screenshot count
        if screenshot_count and len(validated_steps) == screenshot_count:
            # Perfect match - just clean names, don't consolidate
            for step in validated_steps:
                step.name = step.name.strip()
                step.name = step.name.replace(' & ', ' + ')
                step.name = step.name.replace(' and ', ' + ')
            validated_steps = validated_steps  # Keep as-is
            if verbose:
                print(f"✅ Preserved all {screenshot_count} steps (one per screenshot)")
        elif screenshot_count and len(validated_steps) < screenshot_count:
            # LLM consolidated - warn but proceed
            if verbose:
                print(f"⚠️  WARNING: LLM extracted {len(validated_steps)} steps but {screenshot_count} screenshots provided")
                print(f"   The LLM consolidated steps. This defeats the purpose.")
                print(f"   Proceeding with {len(validated_steps)} steps, but ideally should be {screenshot_count}")
            validated_steps = normalize_fintech_steps(validated_steps, fintech_archetype)
        else:
            # Normal normalization
            validated_steps = normalize_fintech_steps(validated_steps, fintech_archetype)
    
    if len(validated_steps) < 3:
        raise ValueError(f"Too few steps after normalization ({len(validated_steps)}). DropSim needs at least 3 steps. Try adding more detail about your onboarding flow.")
    
    # Build LiteScenario
    lite_scenario = LiteScenario(
        product_type=lite_scenario_dict.get('product_type', 'fintech'),
        personas=validated_personas,
        steps=validated_steps,
        fintech_archetype=fintech_archetype
    )
    
    # Post-validation: Check archetype consistency with steps
    if verbose and fintech_archetype:
        step_keywords = ' '.join([step.name.lower() + ' ' + getattr(step, 'type', '').lower() 
                                 for step in validated_steps])
        archetype_keywords = {
            'lending_bnpl': ['loan', 'credit', 'borrow', 'emi', 'repay', 'interest', 'approval', 'mandate'],
            'payments_wallet': ['pay', 'upi', 'wallet', 'transfer', 'send', 'payment'],
            'trading_investing': ['invest', 'stock', 'mutual', 'sip', 'trading', 'fund'],
            'insurance': ['insurance', 'premium', 'coverage', 'policy', 'claim'],
            'neo_bank': ['bank', 'account', 'savings', 'current', 'banking'],
            'personal_finance_manager': ['expense', 'track', 'save', 'budget', 'goal', 'spend', 'insight']
        }
        
        expected_keywords = archetype_keywords.get(fintech_archetype, [])
        matches = sum(1 for kw in expected_keywords if kw in step_keywords)
        if matches == 0 and len(expected_keywords) > 0:
            print(f"⚠️  Warning: Archetype '{fintech_archetype}' may not match step content. Review manually.")
        elif matches > 0:
            print(f"✅ Archetype '{fintech_archetype}' validated against step content ({matches} keyword matches)")
    
    if dry_run:
        return lite_scenario, target_group, fintech_archetype
    
    return lite_scenario, target_group, fintech_archetype


# ============================================================================
# Helper: Simple OpenAI Client (Example Implementation)
# ============================================================================

class OpenAILLMClient(LLMClient):
    """Simple OpenAI client implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini)
        """
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt: str) -> str:
        """Complete prompt using OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from product descriptions. Always output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for deterministic extraction
                max_tokens=2000
            )
            return response.choices[0].message.content
        except ImportError:
            raise ValueError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {e}")

