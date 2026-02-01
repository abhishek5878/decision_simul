"""
journey_simulator.py - Step-by-Step Journey Simulation for Credigo.club

This module simulates each persona's journey through the Credigo.club funnel:

JOURNEY STEPS:
1. Landing Page - "Your Credit Card Story Starts Here", privacy claims
2. Quiz Start - First spending/lifestyle questions appear
3. Quiz Progression - Mid-quiz (questions continue)
4. Quiz Completion - User finishes all questions
5. Results Page - Personalized card recommendations shown
6. Post-Results - No direct apply; manual bank redirect

For each step, we track:
- intent_score (0-100, starts high, drops based on friction/refusals)
- emotional_reaction (Excited, Skeptical, Frustrated, Hopeful, Bored, etc.)
- rational_reaction (logical thought tied to features)
- next_action (Continue, Bounce, Complete, Pursue, Apply Intent)
- dominant_refusal (one of 7 primitives or None)

REFUSAL PRIMITIVES:
1. Status Quo Sufficiency - "My current solution works fine"
2. Habit Entrenchment - "I'm used to my existing patterns"
3. Switching Cost Asymmetry - "Too much effort to try something new"
4. Maintenance Fatigue - "Another app/card to manage"
5. Trust Threshold Not Met - "Don't trust new fintech apps"
6. Delayed Value Realization - "Benefits not immediate/clear"
7. Responsibility Avoidance - "Don't want credit/debt responsibility"

Rules calibrated for 2025 India FinTech context.
"""

import pandas as pd
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


# ============================================================================
# JOURNEY CONFIGURATION
# ============================================================================

JOURNEY_STEPS = [
    "Landing Page",
    "Quiz Start",
    "Quiz Progression",
    "Quiz Completion",
    "Results Page",
    "Post-Results"
]

STEP_INDICES = {step: i for i, step in enumerate(JOURNEY_STEPS)}


# ============================================================================
# REFUSAL PRIMITIVES
# ============================================================================

@dataclass
class RefusalPrimitive:
    id: int
    name: str
    code: str
    description: str
    
REFUSALS = {
    1: RefusalPrimitive(1, "Status Quo Sufficiency", "STATUS_QUO", 
                        "My current solution works fine, why change?"),
    2: RefusalPrimitive(2, "Habit Entrenchment", "HABIT",
                        "I'm used to my existing patterns"),
    3: RefusalPrimitive(3, "Switching Cost Asymmetry", "SWITCH_COST",
                        "Too much effort to try something new"),
    4: RefusalPrimitive(4, "Maintenance Fatigue", "MAINTENANCE",
                        "Another app/card to manage"),
    5: RefusalPrimitive(5, "Trust Threshold Not Met", "TRUST",
                        "Don't trust new fintech apps with money"),
    6: RefusalPrimitive(6, "Delayed Value Realization", "DELAYED_VALUE",
                        "Benefits not immediate or clearly valuable"),
    7: RefusalPrimitive(7, "Responsibility Avoidance", "RESPONSIBILITY",
                        "Don't want credit card/debt burden")
}


# ============================================================================
# EMOTIONAL REACTIONS BY PERSONA TYPE
# ============================================================================

EMOTIONAL_REACTIONS = {
    "positive": ["Excited", "Curious", "Hopeful", "Intrigued", "Optimistic", "Eager"],
    "neutral": ["Interested", "Cautious", "Analytical", "Observing", "Calculating"],
    "negative": ["Skeptical", "Anxious", "Frustrated", "Bored", "Suspicious", "Overwhelmed", "Hesitant"]
}

# Rational thoughts by step and persona type
RATIONAL_THOUGHTS = {
    "Landing Page": {
        "positive": [
            "60 seconds is nothing, and no data sharing sounds safe",
            "Privacy-first approach is rare, worth exploring",
            "Could help optimize my spending rewards",
            "Professional design, seems legitimate"
        ],
        "neutral": [
            "Need to understand what exactly they're offering",
            "Let me see what this quiz is about",
            "Interesting concept but what's the catch?",
            "Will check but won't share anything sensitive"
        ],
        "negative": [
            "Another fintech trying to sell credit cards",
            "Free quiz means they're collecting data somehow",
            "Don't need recommendations, my bank is fine",
            "Looks like a marketing gimmick"
        ]
    },
    "Quiz Start": {
        "positive": [
            "Questions seem relevant to my spending patterns",
            "Quick and easy so far",
            "This feels personalized already",
            "Good that they're asking about lifestyle not income"
        ],
        "neutral": [
            "Standard questionnaire, let's see where this goes",
            "Taking mental notes of what they're asking",
            "Hope this doesn't take too long"
        ],
        "negative": [
            "Why do they need to know this?",
            "Feels like I'm being profiled",
            "Questions are too personal",
            "This is taking longer than 60 seconds"
        ]
    },
    "Quiz Progression": {
        "positive": [
            "Almost done, questions are smart",
            "Can see how this will help match cards",
            "Glad they're thorough"
        ],
        "neutral": [
            "Halfway through, committed now",
            "Hope the recommendations are actually useful",
            "Let's finish this and see"
        ],
        "negative": [
            "This is dragging on",
            "Do I really need a credit card?",
            "Thinking of abandoning this"
        ]
    },
    "Quiz Completion": {
        "positive": [
            "Done! Excited to see recommendations",
            "That was quick and painless",
            "Eager to see what cards fit my profile"
        ],
        "neutral": [
            "Finished, let's see what they suggest",
            "Curious about the results",
            "Hope this was worth my time"
        ],
        "negative": [
            "Finally done, this better be good",
            "Skeptical about what they'll recommend",
            "Already regretting this"
        ]
    },
    "Results Page": {
        "positive": [
            "These recommendations actually match my lifestyle!",
            "The rewards on these cards are impressive",
            "Clear comparison, very helpful",
            "Lounge access and travel rewards - perfect for me"
        ],
        "neutral": [
            "Some interesting options here",
            "Need to research these cards more",
            "Will compare with what I already have",
            "Decent suggestions but need to verify"
        ],
        "negative": [
            "Nothing I couldn't have found myself",
            "These are just popular cards, not personalized",
            "Still don't see why I need a credit card",
            "Annual fees are too high for my spending"
        ]
    },
    "Post-Results": {
        "positive": [
            "Will definitely apply for the top recommendation",
            "Good to have options, will apply this week",
            "Bookmarking to apply through bank site",
            "This saved me hours of research"
        ],
        "neutral": [
            "Might consider applying later",
            "Will discuss with family first",
            "Need to check my eligibility separately",
            "Useful info but no rush to apply"
        ],
        "negative": [
            "No direct apply button? More effort required",
            "Lost interest, too many steps to actually apply",
            "UPI works fine, don't need credit card hassle",
            "Will probably forget about this tomorrow"
        ]
    }
}


# ============================================================================
# VIVID QUOTE TEMPLATES (Indian flavor)
# ============================================================================

VIVID_QUOTES = {
    "young_urban_aspirational": {
        "think": [
            "Finally, something that respects my data while helping me optimize rewards!",
            "My friends will be jealous when I get lounge access",
            "₹30k monthly spends deserve better rewards than my basic card",
            "This could help me flex on LinkedIn about my travel perks"
        ],
        "say": [
            "Interesting! Let me check what rewards I've been missing",
            "60 seconds for better rewards? I'm in",
            "Show me what I'm missing out on"
        ]
    },
    "tier2_aspirational": {
        "think": [
            "Finally something for people like me, not just metro folks",
            "Credit card used to feel like a big city thing",
            "Maybe I can also get those airport lounge benefits",
            "This could help me upgrade my lifestyle"
        ],
        "say": [
            "Let me see if there's something for ₹40k salary",
            "Interesting, but is it for people outside metros too?",
            "Will try if it's really private"
        ]
    },
    "conservative_family": {
        "think": [
            "Credit card means EMI trap, I've seen what happened to Sharma ji's son",
            "My father managed without credit cards, so can I",
            "UPI gives me enough control over spending",
            "What if they call me for sales later?"
        ],
        "say": [
            "UPI is enough for us",
            "Will show my spouse and decide later",
            "Not interested in credit, we manage fine"
        ]
    },
    "rural_traditional": {
        "think": [
            "Credit card? That's for IT people in Bangalore",
            "My local dukan gives me udhar when needed",
            "These apps always have hidden charges",
            "What will I even use a credit card for in village?"
        ],
        "say": [
            "Don't need card, UPI works everywhere now",
            "This is not for people like us",
            "Sharma ji got trapped in credit card debt"
        ]
    },
    "gen_z_cautious": {
        "think": [
            "Saw too many reels about credit card debt spirals",
            "Debit card gives me control, credit is risky",
            "No PAN sounds good but what's the catch?",
            "My income is not stable enough for credit commitments"
        ],
        "say": [
            "Credit scares me ngl, sticking to debit",
            "Privacy sounds good but idk about credit cards",
            "Maybe when I have stable income"
        ]
    },
    "boomer_skeptic": {
        "think": [
            "At my age, why complicate finances with new cards?",
            "My children can look into these things",
            "Fixed deposits are safer than any card rewards",
            "These online quizzes always lead to spam calls"
        ],
        "say": [
            "I've managed fine without credit cards all these years",
            "Not interested, thank you",
            "My son handles all this tech stuff"
        ]
    },
    "tech_professional": {
        "think": [
            "Data-driven recommendations beat random research",
            "The privacy claims check out, no PAN required",
            "Could optimize my ₹50k monthly spend better",
            "Professional product, worth the 60 seconds"
        ],
        "say": [
            "Clean UX, let me see the recommendations",
            "Good that it's not asking for sensitive data",
            "Will compare with my current card's rewards"
        ]
    }
}


# ============================================================================
# STEP-BY-STEP INTENT CALCULATION
# ============================================================================

def calculate_landing_intent(derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate intent after seeing Landing Page.
    
    This is the FIRST IMPRESSION - can go very high or very low!
    
    INTENT CAN GO ABOVE 100 (capped) if:
    - Privacy messaging resonates strongly
    - "60 seconds" feels quick and easy
    - Persona is perfect fit (young urban professional)
    
    INTENT DROPS if:
    - Trust issues (skeptical of fintech)
    - Debt fear (credit = danger)
    - Status quo satisfaction (UPI is enough)
    """
    # Base intent starts at 70 (neutral landing)
    intent = 70
    details = {}
    
    # === STRONG BOOSTERS (can push above base!) ===
    
    # Privacy hook is THE differentiator - huge boost for aware personas
    privacy_score = derived.get('privacy_score', 5)
    digital_score = derived.get('digital_literacy_score', 5)
    if privacy_score >= 7 and digital_score >= 7:
        intent += 25  # "Finally, someone who gets it! No PAN needed!"
        details['privacy_resonance'] = +25
    elif privacy_score >= 6 and digital_score >= 5:
        intent += 15
        details['privacy_boost'] = +15
    elif digital_score >= 6:
        intent += 8
        details['digital_comfort'] = +8
    
    # Aspirational personas LOVE optimization messaging
    aspiration_score = derived.get('aspirational_score', 5)
    if aspiration_score >= 8:
        intent += 15  # "Optimize my rewards? Yes please!"
        details['aspiration_excitement'] = +15
    elif aspiration_score >= 6:
        intent += 10
        details['aspiration_interest'] = +10
    elif aspiration_score >= 4:
        intent += 3
        details['mild_interest'] = +3
    
    # Young urban = perfect target audience
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    urban = derived.get('urban_rural', 'Rural')
    if gen_bucket in ['Gen Z', 'Young Millennial'] and urban == 'Metro':
        intent += 15  # "This is made for people like me"
        details['perfect_fit_boost'] = +15
    elif gen_bucket in ['Gen Z', 'Young Millennial'] and urban == 'Urban':
        intent += 10
        details['good_fit_boost'] = +10
    elif gen_bucket in ['Core Millennial'] and urban in ['Metro', 'Urban']:
        intent += 8
        details['decent_fit_boost'] = +8
    
    # "60 seconds" messaging - quick = attractive
    if digital_score >= 5:
        intent += 5  # "60 seconds? That's nothing!"
        details['quick_quiz_appeal'] = +5
    
    # CC relevance - if they were already looking for cards
    cc_score = derived.get('cc_relevance_score', 5)
    if cc_score >= 7:
        intent += 10  # "This is exactly what I was looking for!"
        details['active_seeker_boost'] = +10
    elif cc_score >= 5:
        intent += 5
        details['passive_interest'] = +5
    
    # === REDUCERS ===
    
    # Trust issues (conservative personas skeptical of new apps)
    trust_score = derived.get('trust_score', 5)
    if trust_score >= 9:
        intent -= 35  # "Another fintech scam"
        details['severe_distrust'] = -35
    elif trust_score >= 7:
        intent -= 20
        details['trust_barrier'] = -20
    elif trust_score >= 5:
        intent -= 8
        details['mild_skepticism'] = -8
    
    # Debt aversion (credit = debt mindset)
    debt_score = derived.get('debt_aversion_score', 5)
    if debt_score >= 9:
        intent -= 25  # "Credit cards are debt traps!"
        details['strong_debt_fear'] = -25
    elif debt_score >= 7:
        intent -= 15
        details['debt_aversion'] = -15
    elif debt_score >= 5:
        intent -= 5
        details['credit_hesitation'] = -5
    
    # Status quo satisfaction
    sq_score = derived.get('status_quo_score', 5)
    if sq_score >= 8:
        intent -= 18  # "UPI works perfectly, why bother?"
        details['strong_status_quo'] = -18
    elif sq_score >= 6:
        intent -= 10
        details['status_quo_inertia'] = -10
    
    # Low English proficiency (product is in English)
    english_score = derived.get('english_score', 5)
    if english_score <= 1:
        intent -= 25  # Can't understand the product
        details['language_barrier'] = -25
    elif english_score <= 3:
        intent -= 10
        details['language_difficulty'] = -10
    
    # Age friction for older users
    if gen_bucket == 'Boomer':
        intent -= 15  # "This app stuff isn't for me"
        details['age_disconnect'] = -15
    elif gen_bucket == 'Gen X' and digital_score <= 4:
        intent -= 8
        details['tech_hesitation'] = -8
    
    intent = max(0, min(100, intent))
    return (intent, details)


def calculate_quiz_start_intent(prev_intent: int, derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate intent at Quiz Start.
    
    Friction: Need to answer questions
    But: Quick/easy questions can INCREASE intent for engaged users!
    
    INTENT CAN INCREASE if:
    - Digital natives find the UX smooth
    - Privacy-conscious see no invasive questions
    - Aspirational get excited about optimization
    """
    intent = prev_intent
    details = {}
    
    # Base quiz friction (small)
    intent -= 3
    details['quiz_friction'] = -3
    
    # === INTENT BOOSTERS (increases!) ===
    
    # Digital natives ENJOY quick quizzes - intent INCREASES
    digital_score = derived.get('digital_literacy_score', 5)
    if digital_score >= 8:
        intent += 8  # Actually excited!
        details['digital_delight'] = +8
    elif digital_score >= 6:
        intent += 4
        details['digital_comfort'] = +4
    
    # Privacy-conscious see questions are non-invasive → trust builds
    privacy_score = derived.get('privacy_score', 5)
    if privacy_score >= 7 and prev_intent >= 60:
        intent += 5  # "Oh, they're not asking for PAN/Aadhaar!"
        details['privacy_relief'] = +5
    
    # Aspirational get excited about personalization
    aspiration_score = derived.get('aspirational_score', 5)
    if aspiration_score >= 6:
        intent += 3  # "I want to see what cards I qualify for!"
        details['aspiration_curiosity'] = +3
    
    # === INTENT REDUCERS ===
    
    # Older users more friction with quizzes
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    if gen_bucket == 'Boomer':
        intent -= 12
        details['age_friction'] = -12
    elif gen_bucket == 'Gen X':
        intent -= 5
        details['age_friction'] = -5
    
    # Low attention span
    openness_score = derived.get('openness_score', 5)
    if openness_score <= 3:
        intent -= 5
        details['patience_penalty'] = -5
    
    intent = max(0, min(100, intent))
    return (intent, details)


def calculate_quiz_progress_intent(prev_intent: int, derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate intent mid-quiz.
    
    KEY INSIGHT: Those who made it this far are COMMITTED.
    Sunk cost psychology kicks in - many will see intent INCREASE.
    
    INTENT INCREASES if:
    - Engaged users feel momentum ("almost done!")
    - Questions feel relevant to their lifestyle
    - No scary asks (no PAN, no income proof)
    """
    intent = prev_intent
    details = {}
    
    # === MOMENTUM BOOST (key insight!) ===
    # Users who made it here are committed - sunk cost kicks in
    if prev_intent >= 50:
        intent += 5  # "I'm already halfway, might as well finish"
        details['sunk_cost_commitment'] = +5
    
    # === INTENT BOOSTERS ===
    
    # Aspirational personas get MORE excited mid-quiz
    aspiration_score = derived.get('aspirational_score', 5)
    if aspiration_score >= 7:
        intent += 8  # "Can't wait to see my personalized cards!"
        details['aspiration_momentum'] = +8
    elif aspiration_score >= 5:
        intent += 4
        details['curiosity_boost'] = +4
    
    # High CC relevance = questions feel personally relevant
    cc_score = derived.get('cc_relevance_score', 5)
    if cc_score >= 6:
        intent += 5  # "These questions are exactly about my spending!"
        details['relevance_resonance'] = +5
    
    # Digital natives enjoy the smooth UX
    digital_score = derived.get('digital_literacy_score', 5)
    if digital_score >= 7:
        intent += 3
        details['ux_appreciation'] = +3
    
    # === INTENT REDUCERS ===
    
    # Slight natural friction
    intent -= 2
    details['progression_friction'] = -2
    
    # High privacy + high trust concern = mid-quiz doubt
    privacy_score = derived.get('privacy_score', 5)
    trust_score = derived.get('trust_score', 5)
    if trust_score >= 8:  # Very conservative
        intent -= 8
        details['mid_quiz_doubt'] = -8
    elif trust_score >= 6 and privacy_score >= 6:
        intent -= 3
        details['mild_concern'] = -3
    
    # Low openness = getting bored
    openness_score = derived.get('openness_score', 5)
    if openness_score <= 3:
        intent -= 4
        details['boredom_drop'] = -4
    
    intent = max(0, min(100, intent))
    return (intent, details)


def calculate_quiz_complete_intent(prev_intent: int, derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate intent at Quiz Completion.
    
    THIS IS A HIGH POINT - INTENT USUALLY INCREASES!
    
    Psychology:
    - "I did it!" accomplishment feeling
    - Anticipation of personalized results
    - Sunk cost + curiosity peak
    - "Show me what I qualify for!"
    """
    intent = prev_intent
    details = {}
    
    # === BIG COMPLETION BOOST (everyone feels good finishing!) ===
    base_completion_boost = 12
    intent += base_completion_boost
    details['completion_high'] = +base_completion_boost
    
    # === ANTICIPATION BOOSTERS ===
    
    # High aspirational = VERY excited about results
    aspiration_score = derived.get('aspirational_score', 5)
    if aspiration_score >= 7:
        intent += 10  # "Finally! Show me the premium cards!"
        details['aspiration_peak'] = +10
    elif aspiration_score >= 5:
        intent += 5
        details['result_curiosity'] = +5
    
    # Digital savvy expect great personalization
    digital_score = derived.get('digital_literacy_score', 5)
    if digital_score >= 7:
        intent += 5  # "This better be worth my time"
        details['personalization_expectation'] = +5
    elif digital_score >= 5:
        intent += 2
        details['mild_anticipation'] = +2
    
    # High CC relevance = "This is exactly what I need!"
    cc_score = derived.get('cc_relevance_score', 5)
    if cc_score >= 7:
        intent += 8
        details['high_relevance_excitement'] = +8
    elif cc_score >= 5:
        intent += 3
        details['moderate_interest'] = +3
    
    # Urban users more optimistic about personalization
    urban = derived.get('urban_rural', 'Rural')
    if urban in ['Metro', 'Urban']:
        intent += 3
        details['urban_optimism'] = +3
    
    # === SLIGHT REDUCER for skeptics ===
    trust_score = derived.get('trust_score', 5)
    if trust_score >= 8:
        intent -= 5  # Still skeptical even after completing
        details['persistent_skepticism'] = -5
    
    intent = max(0, min(100, intent))
    return (intent, details)


def calculate_results_intent(prev_intent: int, derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate intent at Results Page.
    
    THIS IS THE "AHA MOMENT" - MAKE OR BREAK!
    
    INTENT CAN SPIKE if:
    - Recommendations match lifestyle perfectly
    - Rewards are tangibly exciting (lounge, cashback)
    - Person sees cards they didn't know existed
    
    INTENT DROPS if:
    - Recommendations feel generic
    - Cards seem out of reach
    - Debt fear kicks in seeing credit limits
    """
    intent = prev_intent
    details = {}
    
    # === THE "AHA MOMENT" - Value Realization ===
    cc_relevance = derived.get('cc_relevance_score', 5)
    aspiration_score = derived.get('aspirational_score', 5)
    
    if cc_relevance >= 8:
        # Perfect match! "These cards are EXACTLY for me!"
        intent += 15
        details['perfect_match_aha'] = +15
    elif cc_relevance >= 6:
        # Good match - valuable recommendations
        intent += 8
        details['good_value_realized'] = +8
    elif cc_relevance >= 4:
        # Decent - some useful info
        intent += 2
        details['moderate_value'] = +2
    else:
        # Poor match - "these aren't for people like me"
        intent -= 12
        details['value_disappointment'] = -12
    
    # === EXCITEMENT BOOSTERS ===
    
    # Aspirational personas LOVE seeing premium options
    if aspiration_score >= 7:
        intent += 8  # "Lounge access! Travel rewards! Yes!"
        details['premium_excitement'] = +8
    elif aspiration_score >= 5:
        intent += 3
        details['reward_interest'] = +3
    
    # Travel/culinary personas see relevant rewards
    openness_score = derived.get('openness_score', 5)
    if openness_score >= 7:
        intent += 5  # Diverse lifestyle = many reward categories apply
        details['lifestyle_match'] = +5
    
    # Urban users see more applicable cards
    urban = derived.get('urban_rural', 'Rural')
    if urban == 'Metro':
        intent += 5  # More merchants, more reward opportunities
        details['metro_relevance'] = +5
    elif urban == 'Urban':
        intent += 2
        details['urban_relevance'] = +2
    
    # === INTENT REDUCERS ===
    
    # Debt aversion kicks in seeing credit limits
    debt_score = derived.get('debt_aversion_score', 5)
    if debt_score >= 8:
        intent -= 12  # "₹2L credit limit? That's scary debt potential"
        details['credit_fear_spike'] = -12
    elif debt_score >= 6:
        intent -= 5
        details['mild_credit_concern'] = -5
    
    # Rural users see rewards they can't use
    if urban == 'Rural':
        intent -= 8  # "Lounge access? Nearest airport is 200km away"
        details['reward_irrelevance'] = -8
    
    # Narrow lifestyle = many rewards feel useless
    if openness_score <= 3:
        intent -= 6
        details['limited_lifestyle_fit'] = -6
    
    intent = max(0, min(100, intent))
    return (intent, details)


def calculate_post_results_intent(prev_intent: int, derived: Dict) -> Tuple[int, Dict]:
    """
    Calculate final intent at Post-Results.
    
    CRITICAL FRICTION: No direct apply button!
    BUT: Highly motivated personas will push through!
    
    INTENT CAN STAY HIGH if:
    - Person is very motivated (saw great recommendations)
    - Digital native (doesn't mind going to bank site)
    - High aspiration (really wants those rewards)
    - Strong entry intent carried through
    """
    intent = prev_intent
    details = {}
    
    # === THE FRICTION: NO DIRECT APPLY ===
    # This hurts everyone, but hurts some more than others
    
    # Base drop scaled by digital comfort
    digital_score = derived.get('digital_literacy_score', 5)
    if digital_score >= 8:
        base_drop = -5  # Digital natives: "I'll just open bank site, NBD"
        details['minimal_friction'] = base_drop
    elif digital_score >= 6:
        base_drop = -12
        details['moderate_friction'] = base_drop
    else:
        base_drop = -25  # "Wait, I have to go somewhere else? Forget it"
        details['high_friction'] = base_drop
    intent += base_drop
    
    # === INTENT BOOSTERS (motivated personas push through!) ===
    
    # Very high CC relevance = "I NEED this card"
    cc_relevance = derived.get('cc_relevance_score', 5)
    if cc_relevance >= 8:
        intent += 15  # Will definitely follow through
        details['high_motivation_push'] = +15
    elif cc_relevance >= 6:
        intent += 8
        details['motivated_follow_through'] = +8
    
    # High aspiration = rewards too good to pass up
    aspiration_score = derived.get('aspirational_score', 5)
    if aspiration_score >= 7:
        intent += 10  # "Those lounge benefits are worth the extra click"
        details['aspiration_drive'] = +10
    elif aspiration_score >= 5:
        intent += 4
        details['reward_motivation'] = +4
    
    # If entry intent was very high and maintained, momentum carries
    if prev_intent >= 80:
        intent += 8  # Strong momentum = follows through
        details['momentum_carry'] = +8
    elif prev_intent >= 60:
        intent += 3
        details['moderate_momentum'] = +3
    
    # Young + digital = "I'll just apply on my phone later"
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    if gen_bucket in ['Gen Z', 'Young Millennial'] and digital_score >= 6:
        intent += 5
        details['young_digital_ease'] = +5
    
    # === INTENT REDUCERS ===
    
    # Switching cost asymmetry
    sq_score = derived.get('status_quo_score', 5)
    if sq_score >= 7:
        intent -= 15  # "Too much effort, my current card is fine"
        details['switching_cost_hit'] = -15
    elif sq_score >= 5:
        intent -= 5
        details['mild_inertia'] = -5
    
    # Maintenance fatigue for busy professionals
    if gen_bucket in ['Core Millennial', 'Gen X'] and aspiration_score >= 5:
        if sq_score >= 5:  # Busy AND somewhat satisfied
            intent -= 8
            details['busy_professional_fatigue'] = -8
    
    # Older users really struggle with extra steps
    if gen_bucket == 'Boomer':
        intent -= 15
        details['age_barrier'] = -15
    elif gen_bucket == 'Gen X':
        intent -= 5
        details['mild_age_friction'] = -5
    
    # Debt fear final resistance
    debt_score = derived.get('debt_aversion_score', 5)
    if debt_score >= 8:
        intent -= 10  # Last-minute cold feet
        details['debt_fear_resistance'] = -10
    
    intent = max(0, min(100, intent))
    return (intent, details)


# ============================================================================
# REFUSAL DETERMINATION
# ============================================================================

def determine_refusal(step: str, intent: int, derived: Dict) -> Tuple[Optional[int], str]:
    """
    Determine the dominant refusal primitive for a step.
    
    Returns: (refusal_id or None, refusal_reason)
    """
    # High intent = no refusal
    if intent >= 70:
        return (None, "Engaged, no major refusals")
    
    # Calculate refusal scores
    scores = {i: 0.0 for i in range(1, 8)}
    
    # Extract derived features
    sq_score = derived.get('status_quo_score', 5)
    trust_score = derived.get('trust_score', 5)
    debt_score = derived.get('debt_aversion_score', 5)
    digital_score = derived.get('digital_literacy_score', 5)
    aspiration_score = derived.get('aspirational_score', 5)
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    openness_score = derived.get('openness_score', 5)
    
    # 1. Status Quo Sufficiency
    scores[1] = sq_score * 2
    if derived.get('urban_rural') == 'Rural':
        scores[1] += 5  # UPI satisfaction
    
    # 2. Habit Entrenchment
    if gen_bucket in ['Gen X', 'Boomer']:
        scores[2] += 10
    scores[2] += (10 - digital_score)
    
    # 3. Switching Cost Asymmetry (spikes at Post-Results)
    if step == 'Post-Results':
        scores[3] += 15
    scores[3] += sq_score
    
    # 4. Maintenance Fatigue
    if aspiration_score >= 6:  # Busy high achievers
        scores[4] += 8
    if step in ['Quiz Progression', 'Post-Results']:
        scores[4] += 5
    
    # 5. Trust Threshold Not Met
    scores[5] = trust_score * 1.5
    if step == 'Landing Page':
        scores[5] += 5  # First impression skepticism
    
    # 6. Delayed Value Realization
    if openness_score <= 4:
        scores[6] += 10
    if step == 'Results Page':
        scores[6] += 5
    
    # 7. Responsibility Avoidance
    scores[7] = debt_score * 1.5
    if gen_bucket == 'Gen Z':
        scores[7] += 5  # Debt-conscious generation
    
    # Find dominant refusal
    if max(scores.values()) > 10:
        dominant_id = max(scores, key=scores.get)
        return (dominant_id, REFUSALS[dominant_id].description)
    
    return (None, "Minor hesitations, no dominant refusal")


# ============================================================================
# EMOTIONAL/RATIONAL REACTION GENERATION
# ============================================================================

def get_emotional_reaction(intent: int, intent_change: int, derived: Dict) -> str:
    """Generate emotional reaction based on intent level and change."""
    if intent >= 80:
        return random.choice(EMOTIONAL_REACTIONS["positive"])
    elif intent >= 50:
        if intent_change >= 0:
            return random.choice(EMOTIONAL_REACTIONS["positive"][:3] + EMOTIONAL_REACTIONS["neutral"])
        else:
            return random.choice(EMOTIONAL_REACTIONS["neutral"])
    elif intent >= 30:
        return random.choice(EMOTIONAL_REACTIONS["neutral"] + EMOTIONAL_REACTIONS["negative"][:3])
    else:
        return random.choice(EMOTIONAL_REACTIONS["negative"])


def get_rational_reaction(step: str, intent: int, derived: Dict) -> str:
    """Generate rational thought for the step."""
    if intent >= 70:
        thoughts = RATIONAL_THOUGHTS.get(step, {}).get("positive", ["Proceeding..."])
    elif intent >= 40:
        thoughts = RATIONAL_THOUGHTS.get(step, {}).get("neutral", ["Considering..."])
    else:
        thoughts = RATIONAL_THOUGHTS.get(step, {}).get("negative", ["Hesitating..."])
    
    return random.choice(thoughts)


def get_next_action(step: str, intent: int) -> str:
    """Determine next action based on step and intent."""
    step_idx = STEP_INDICES.get(step, 0)
    
    if intent < 20:
        return "Bounce"
    elif intent < 40:
        if step_idx < 3:
            return "Abandon"
        else:
            return "Unlikely to Act"
    elif intent < 60:
        if step == "Post-Results":
            return "Maybe Later"
        else:
            return "Continue (Hesitant)"
    elif intent < 80:
        if step == "Post-Results":
            return "Will Consider Applying"
        else:
            return "Continue"
    else:
        if step == "Post-Results":
            return "High Apply Intent"
        elif step == "Quiz Completion":
            return "Complete Quiz"
        else:
            return "Continue (Engaged)"


def get_vivid_quote(derived: Dict, final_intent: int) -> Tuple[str, str]:
    """Generate vivid Think + Say quote based on persona archetype."""
    # Determine archetype
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    urban = derived.get('urban_rural', 'Rural')
    aspiration = derived.get('aspirational_intensity', 'Medium')
    digital = derived.get('digital_literacy', 'Medium')
    cc_relevance = derived.get('cc_relevance', 'Medium')
    trust = derived.get('trust_orientation', 'Moderate')
    
    # Map to archetype
    if cc_relevance == 'High' and urban in ['Metro', 'Urban']:
        if digital == 'High':
            archetype = 'tech_professional'
        else:
            archetype = 'young_urban_aspirational'
    elif urban in ['Urban', 'Semi-Urban'] and aspiration in ['High', 'Medium']:
        archetype = 'tier2_aspirational'
    elif gen_bucket == 'Boomer' or (gen_bucket == 'Gen X' and trust == 'Conservative'):
        archetype = 'boomer_skeptic'
    elif gen_bucket == 'Gen Z' and trust == 'Conservative':
        archetype = 'gen_z_cautious'
    elif urban == 'Rural':
        archetype = 'rural_traditional'
    else:
        archetype = 'conservative_family'
    
    quotes = VIVID_QUOTES.get(archetype, VIVID_QUOTES['conservative_family'])
    think = random.choice(quotes['think'])
    say = random.choice(quotes['say'])
    
    return (think, say)


# ============================================================================
# MAIN JOURNEY SIMULATION
# ============================================================================

@dataclass
class StepResult:
    """Result for a single journey step."""
    step_name: str
    intent_score: int
    intent_change: int
    emotional_reaction: str
    rational_reaction: str
    next_action: str
    refusal_id: Optional[int]
    refusal_name: str
    bounced: bool = False


@dataclass
class JourneyResult:
    """Complete journey result for a persona."""
    steps: List[StepResult]
    final_intent: int
    funnel_exit_step: str
    completed_funnel: bool
    dominant_refusal_id: Optional[int]
    dominant_refusal_name: str
    vivid_think: str
    vivid_say: str


def simulate_journey(row: pd.Series, derived: Dict, seed: int = None) -> JourneyResult:
    """
    Simulate complete journey for a single persona.
    
    Args:
        row: Raw persona data
        derived: Derived features dictionary
        seed: Random seed for reproducibility
    
    Returns:
        JourneyResult with all step details
    """
    if seed is not None:
        random.seed(seed)
    
    steps = []
    prev_intent = 100  # Start at full intent
    bounced = False
    exit_step = "Post-Results"  # Default: completed funnel
    
    # Step 1: Landing Page
    intent, details = calculate_landing_intent(derived)
    change = intent - 100
    refusal_id, refusal_reason = determine_refusal("Landing Page", intent, derived)
    
    step1 = StepResult(
        step_name="Landing Page",
        intent_score=intent,
        intent_change=change,
        emotional_reaction=get_emotional_reaction(intent, change, derived),
        rational_reaction=get_rational_reaction("Landing Page", intent, derived),
        next_action=get_next_action("Landing Page", intent),
        refusal_id=refusal_id,
        refusal_name=REFUSALS[refusal_id].name if refusal_id else "None",
        bounced=intent < 20
    )
    steps.append(step1)
    
    if intent < 20:
        bounced = True
        exit_step = "Landing Page"
    prev_intent = intent
    
    # Continue through remaining steps if not bounced
    step_calculators = [
        ("Quiz Start", calculate_quiz_start_intent),
        ("Quiz Progression", calculate_quiz_progress_intent),
        ("Quiz Completion", calculate_quiz_complete_intent),
        ("Results Page", calculate_results_intent),
        ("Post-Results", calculate_post_results_intent)
    ]
    
    for step_name, calculator in step_calculators:
        if bounced:
            # Create empty step for bounced users
            step = StepResult(
                step_name=step_name,
                intent_score=0,
                intent_change=0,
                emotional_reaction="N/A",
                rational_reaction="N/A",
                next_action="Already Bounced",
                refusal_id=None,
                refusal_name="N/A",
                bounced=True
            )
        else:
            intent, details = calculator(prev_intent, derived)
            change = intent - prev_intent
            refusal_id, refusal_reason = determine_refusal(step_name, intent, derived)
            
            step = StepResult(
                step_name=step_name,
                intent_score=intent,
                intent_change=change,
                emotional_reaction=get_emotional_reaction(intent, change, derived),
                rational_reaction=get_rational_reaction(step_name, intent, derived),
                next_action=get_next_action(step_name, intent),
                refusal_id=refusal_id,
                refusal_name=REFUSALS[refusal_id].name if refusal_id else "None",
                bounced=intent < 20
            )
            
            if intent < 20:
                bounced = True
                exit_step = step_name
            
            prev_intent = intent
        
        steps.append(step)
    
    # Determine overall dominant refusal
    refusal_counts = {}
    for s in steps:
        if s.refusal_id:
            refusal_counts[s.refusal_id] = refusal_counts.get(s.refusal_id, 0) + 1
    
    if refusal_counts:
        dominant_id = max(refusal_counts, key=refusal_counts.get)
        dominant_name = REFUSALS[dominant_id].name
    else:
        dominant_id = None
        dominant_name = "None"
    
    # Get vivid quotes
    final_intent = steps[-1].intent_score if not bounced else 0
    vivid_think, vivid_say = get_vivid_quote(derived, final_intent)
    
    return JourneyResult(
        steps=steps,
        final_intent=final_intent,
        funnel_exit_step=exit_step,
        completed_funnel=not bounced,
        dominant_refusal_id=dominant_id,
        dominant_refusal_name=dominant_name,
        vivid_think=vivid_think,
        vivid_say=vivid_say
    )


# ============================================================================
# BATCH SIMULATION
# ============================================================================

def run_journey_simulation(df: pd.DataFrame, seed: int = 42, verbose: bool = True) -> pd.DataFrame:
    """
    Run journey simulation for all personas in DataFrame.
    
    Args:
        df: DataFrame with raw + derived features
        seed: Random seed
        verbose: Print progress
    
    Returns:
        DataFrame with journey results appended
    """
    if verbose:
        print("🎬 Running Step-by-Step Journey Simulation")
        print(f"   Simulating {len(df):,} personas through Credigo.club funnel")
        print(f"   Steps: {' → '.join(JOURNEY_STEPS)}")
    
    random.seed(seed)
    
    # Derived feature column names
    derived_cols = [
        'urban_rural', 'urban_score', 'regional_cluster',
        'primary_language', 'english_proficiency', 'english_score',
        'aspirational_intensity', 'aspirational_score',
        'digital_literacy', 'digital_literacy_score',
        'trust_orientation', 'trust_score',
        'status_quo_sufficiency', 'status_quo_score',
        'openness_hobby_breadth', 'openness_score',
        'debt_aversion', 'debt_aversion_score',
        'privacy_sensitivity', 'privacy_score',
        'generation_bucket', 'generation_code',
        'cc_relevance', 'cc_relevance_score'
    ]
    
    # Result columns for each step
    result_data = []
    
    for idx, row in df.iterrows():
        # Extract derived features
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        # Run journey simulation
        journey = simulate_journey(row, derived, seed=seed + idx)
        
        # Flatten results
        result = {
            'final_intent': journey.final_intent,
            'funnel_exit_step': journey.funnel_exit_step,
            'completed_funnel': journey.completed_funnel,
            'dominant_refusal_id': journey.dominant_refusal_id,
            'dominant_refusal': journey.dominant_refusal_name,
            'vivid_think': journey.vivid_think,
            'vivid_say': journey.vivid_say,
            'vivid_quote': f"Think: {journey.vivid_think}. Say: \"{journey.vivid_say}\""
        }
        
        # Add per-step details
        for step in journey.steps:
            step_key = step.step_name.replace(" ", "_").lower()
            result[f'{step_key}_intent'] = step.intent_score
            result[f'{step_key}_emotion'] = step.emotional_reaction
            result[f'{step_key}_action'] = step.next_action
            result[f'{step_key}_refusal'] = step.refusal_name
        
        result_data.append(result)
        
        if verbose and (idx + 1) % 200 == 0:
            print(f"   Simulated {idx + 1:,}/{len(df):,} journeys")
    
    # Convert to DataFrame and merge
    results_df = pd.DataFrame(result_data)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"✅ Journey simulation complete!")
        
        # Quick funnel summary
        print(f"\n📊 Funnel Summary:")
        exit_counts = results_df['funnel_exit_step'].value_counts()
        for step in JOURNEY_STEPS:
            count = exit_counts.get(step, 0)
            pct = count / len(results_df) * 100
            print(f"   Exit at {step}: {count} ({pct:.1f}%)")
        
        completed = results_df['completed_funnel'].sum()
        print(f"\n   Completed Full Funnel: {completed} ({completed/len(results_df)*100:.1f}%)")
        print(f"   Average Final Intent: {results_df['final_intent'].mean():.1f}")
    
    return final_df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🧪 Running journey_simulator.py test...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load small sample
        sample_df, meta = load_and_sample(n=50, seed=42, verbose=True)
        
        # Derive features
        print("\n" + "=" * 60)
        enriched_df = derive_all_features(sample_df, verbose=True)
        
        # Run journey simulation
        print("\n" + "=" * 60)
        results_df = run_journey_simulation(enriched_df, seed=42, verbose=True)
        
        # Show sample journeys
        print("\n📋 Sample Journey Details:")
        print("-" * 80)
        
        for i in range(min(3, len(results_df))):
            row = results_df.iloc[i]
            print(f"\n[{i+1}] {row['age']}yo {row['sex']} | {row['state']} | {row.get('generation_bucket', 'N/A')}")
            print(f"    Profile: {row['urban_rural']} | {row['digital_literacy']} digital | {row['cc_relevance']} CC relevance")
            print(f"\n    Journey:")
            for step in JOURNEY_STEPS:
                step_key = step.replace(" ", "_").lower()
                intent = row.get(f'{step_key}_intent', 'N/A')
                emotion = row.get(f'{step_key}_emotion', 'N/A')
                action = row.get(f'{step_key}_action', 'N/A')
                print(f"      {step}: Intent={intent} | {emotion} | {action}")
            
            print(f"\n    Final: {row['final_intent']} intent | Exit: {row['funnel_exit_step']}")
            print(f"    Dominant Refusal: {row['dominant_refusal']}")
            print(f"    💭 Think: {row['vivid_think'][:60]}...")
            print(f"    💬 Say: \"{row['vivid_say']}\"")
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

