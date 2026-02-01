"""
simulation_engine.py - Per-Persona Prediction Engine for Credigo.club

This module simulates each persona's reaction to the Credigo.club product:
- 60-second credit card recommender quiz
- Privacy-first (no PAN, no sensitive data, no credit check)
- Instant personalized card recommendations
- Targets young professionals, free/private/fast

Predictions per persona:
1. Quiz Start Likelihood (0-100%)
2. Completion Rate (0-100%)
3. Apply/Pursue Intent (0-100%)
4. Dominant Refusal Primitive (1 of 7)
5. Vivid Reaction Quote (Think + Say)

Refusal Primitives:
1. Status Quo Sufficiency - "My current solution works fine"
2. Habit Entrenchment - "I'm used to my existing patterns"
3. Switching Cost Asymmetry - "Too much effort to change"
4. Maintenance Fatigue - "Another app/card to manage"
5. Trust Threshold Not Met - "Don't trust new fintech apps"
6. Delayed Value Realization - "Benefits not immediate/clear"
7. Responsibility Avoidance - "Don't want credit/debt burden"

All rules calibrated for 2025 India FinTech context.
"""

import pandas as pd
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass


# ============================================================================
# PRODUCT CONTEXT: CREDIGO.CLUB (December 2025)
# ============================================================================

PRODUCT_INFO = {
    "name": "Credigo.club",
    "tagline": "Your Credit Card Story Starts Here",
    "pitch": "Discover Credigo.club – free 60-sec private quiz for perfect credit card rewards, no PAN/data/check.",
    "features": [
        "60-second quiz on spending habits/lifestyle",
        "No PAN, no sensitive data, no credit check",
        "Instant personalized card recommendations",
        "Focus on rewards, low fees, lounge access",
        "No direct apply button – just recommendations"
    ],
    "target_spending": "₹25k/month+ spends",
    "target_audience": "Young professionals, digitally savvy"
}


# ============================================================================
# REFUSAL PRIMITIVES
# ============================================================================

@dataclass
class RefusalPrimitive:
    """Represents one of the 7 refusal primitives."""
    id: int
    name: str
    short_code: str
    description: str


REFUSAL_PRIMITIVES = {
    1: RefusalPrimitive(1, "Status Quo Sufficiency", "STATUS_QUO",
                        "My current solution works fine, why change?"),
    2: RefusalPrimitive(2, "Habit Entrenchment", "HABIT",
                        "I'm used to my existing patterns and tools"),
    3: RefusalPrimitive(3, "Switching Cost Asymmetry", "SWITCH_COST",
                        "Too much effort/friction to try something new"),
    4: RefusalPrimitive(4, "Maintenance Fatigue", "MAINTENANCE",
                        "Another app/card to manage, track, maintain"),
    5: RefusalPrimitive(5, "Trust Threshold Not Met", "TRUST",
                        "Don't trust new/unknown fintech apps with money"),
    6: RefusalPrimitive(6, "Delayed Value Realization", "DELAYED_VALUE",
                        "Benefits are not immediate or clearly valuable"),
    7: RefusalPrimitive(7, "Responsibility Avoidance", "RESPONSIBILITY",
                        "Don't want credit card/debt responsibility")
}


# ============================================================================
# REACTION QUOTE TEMPLATES
# ============================================================================

# Template: (Think, Say) tuples by persona archetype
REACTION_TEMPLATES = {
    # High Engagement (will likely convert)
    "young_urban_aspirational": [
        ("Rewards and cashback sound tempting, 60 sec is nothing",
         "This looks interesting, let me check what cards fit my travel lifestyle"),
        ("No PAN means no spam calls, finally someone gets it",
         "Free quiz? Sure, I'm always looking for better reward cards"),
        ("Could help me optimize my ₹30k monthly spends better",
         "Show me what I'm missing out on with my current card"),
    ],
    
    "tech_savvy_professional": [
        ("Data says personalized recommendations beat manual research",
         "60 seconds to potentially save thousands in fees? Efficient"),
        ("Privacy-first approach aligns with my values",
         "Let me see if there's a better card for my Amazon/Swiggy spends"),
        ("Quick ROI calculation - worth the time investment",
         "I'll try it, no harm if it's truly no-data"),
    ],
    
    # Medium Engagement (curious but hesitant)
    "tier2_aspirational": [
        ("Sounds useful but is it really free? What's the catch",
         "Maybe I'll check it out later when I have time"),
        ("Credit cards seem like a metro thing, is it for people like me",
         "Interesting, but I need to understand more first"),
        ("Could help me get lounge access like my colleagues have",
         "Let me see what options are there for someone earning ₹40k"),
    ],
    
    "family_oriented_salaried": [
        ("Another finance app, but no PAN is reassuring",
         "I'll show this to my spouse, we've been thinking about a card"),
        ("60 seconds is quick, won't hurt to try",
         "Let me see if there's a card with good grocery rewards"),
        ("Might help with managing household expenses better",
         "Will check later, but sounds simpler than going to the bank"),
    ],
    
    # Low Engagement (unlikely to convert)
    "conservative_traditional": [
        ("Credit cards are debt traps, my father warned me",
         "UPI is enough for me, don't need credit"),
        ("These new apps always have hidden agendas",
         "I'm happy with my bank, no need for outside recommendations"),
        ("Why would I tell a website about my spending",
         "Not interested, I manage my money the traditional way"),
    ],
    
    "rural_cash_preference": [
        ("Credit card? That's for city people with IT jobs",
         "I don't spend that much, UPI handles everything"),
        ("What if they sell my data to collection agents",
         "No thanks, I've heard too many credit card horror stories"),
        ("My shopkeeper gives me better udhar than any card",
         "Not for people like us"),
    ],
    
    "older_risk_averse": [
        ("At my age, why take on new financial complications",
         "I've managed fine without credit cards all these years"),
        ("These online quizzes always lead to spam",
         "My children can look into this, I don't trust apps"),
        ("Fixed deposit and savings are safer than credit",
         "Not interested in any card, thank you"),
    ],
    
    "debt_averse_youth": [
        ("Credit means debt, debt means stress, no thanks",
         "I prefer debit card, what I have is what I spend"),
        ("My friends are stuck in credit card EMI cycles",
         "UPI rewards are good enough, don't need another card"),
        ("60 seconds is quick but then the sales calls start",
         "I'll stick to my current setup"),
    ]
}


# ============================================================================
# PREDICTION FUNCTIONS
# ============================================================================

def predict_quiz_start_likelihood(derived: Dict) -> int:
    """
    Predict likelihood (0-100%) that persona will start the quiz.
    
    Boosters: Digital literacy, aspirational, young, urban, English proficiency
    Reducers: Trust issues, status quo satisfaction, rural, older
    """
    base = 30  # Base likelihood
    
    # Digital literacy is crucial for app engagement
    digital_score = derived.get('digital_literacy_score', 0.3)
    base += int(digital_score * 25)
    
    # Urban/Metro personas more likely to engage with fintech
    urban_rural = derived.get('urban_rural', 'Rural')
    if urban_rural == 'Metro':
        base += 15
    elif urban_rural == 'Urban':
        base += 10
    elif urban_rural == 'Semi-Urban':
        base += 3
    else:  # Rural
        base -= 5
    
    # Age factor (younger = more open to new apps)
    age_bucket = derived.get('age_bucket', 'Gen X')
    if age_bucket == 'Gen Z':
        base += 12
    elif age_bucket == 'Millennial':
        base += 15  # Sweet spot for CC adoption
    elif age_bucket == 'Gen X':
        base += 2
    else:  # Boomer
        base -= 10
    
    # Aspirational intensity
    aspiration_score = derived.get('aspirational_score', 0.3)
    base += int(aspiration_score * 15)
    
    # Trust threshold (lower = more willing to try)
    trust_threshold = derived.get('trust_threshold', 0.5)
    base -= int((trust_threshold - 0.4) * 20)
    
    # Status quo satisfaction (higher = less interested)
    status_quo = derived.get('status_quo_score', 0.5)
    base -= int((status_quo - 0.4) * 15)
    
    # Privacy hook boost (product emphasizes no PAN/data)
    # This specifically counters trust issues
    if trust_threshold < 0.5:  # Open/trusting personas
        base += 8
    
    # English proficiency (product is in English)
    english = derived.get('english_proficiency', 'None')
    if english == 'Native':
        base += 8
    elif english == 'Fluent':
        base += 5
    elif english == 'Basic':
        base += 2
    
    # Hobby breadth (more open = more curious)
    hobby = derived.get('hobby_breadth', 'Narrow')
    if hobby == 'Broad':
        base += 5
    
    return max(0, min(100, base))


def predict_completion_rate(start_likelihood: int, derived: Dict) -> int:
    """
    Predict completion rate (0-100%) given they started the quiz.
    
    60-second quiz is designed to be quick, so completion is generally high
    if they start. Drop-off mainly from attention span or complexity fear.
    """
    # If unlikely to start, also unlikely to complete
    if start_likelihood < 20:
        return max(0, start_likelihood - 10)
    
    # Base completion is high due to short quiz (60 sec)
    base = 75
    
    # Digital literacy helps complete faster
    digital_score = derived.get('digital_literacy_score', 0.3)
    base += int(digital_score * 10)
    
    # Younger complete quizzes better
    age_bucket = derived.get('age_bucket', 'Gen X')
    if age_bucket == 'Gen Z':
        base += 8
    elif age_bucket == 'Millennial':
        base += 5
    elif age_bucket == 'Boomer':
        base -= 10
    
    # Trust issues may cause mid-quiz abandonment
    trust_threshold = derived.get('trust_threshold', 0.5)
    if trust_threshold > 0.6:
        base -= 15
    
    # English proficiency affects comprehension
    english = derived.get('english_proficiency', 'None')
    if english == 'None':
        base -= 20
    elif english == 'Basic':
        base -= 8
    
    return max(0, min(100, base))


def predict_apply_intent(completion_rate: int, derived: Dict) -> int:
    """
    Predict intent to pursue/apply (0-100%) based on recommendations.
    
    This is the key conversion metric - will they act on the recommendations?
    """
    # Must complete to have intent
    if completion_rate < 30:
        return max(0, completion_rate // 3)
    
    # Base intent is moderate
    base = 35
    
    # CC relevance is the strongest predictor
    cc_score = derived.get('cc_relevance_score', 0.3)
    base += int(cc_score * 30)
    
    # Aspirational want the rewards/status
    aspiration_score = derived.get('aspirational_score', 0.3)
    base += int(aspiration_score * 15)
    
    # Responsibility avoidance reduces intent
    trust_threshold = derived.get('trust_threshold', 0.5)
    if trust_threshold > 0.6:
        base -= 12
    
    # Status quo satisfaction kills conversion
    status_quo = derived.get('status_quo_score', 0.5)
    if status_quo > 0.6:
        base -= 18
    
    # Urban more likely to actually apply
    urban_rural = derived.get('urban_rural', 'Rural')
    if urban_rural == 'Metro':
        base += 10
    elif urban_rural == 'Urban':
        base += 5
    elif urban_rural == 'Rural':
        base -= 8
    
    # Age affects intent
    age_bucket = derived.get('age_bucket', 'Gen X')
    if age_bucket == 'Millennial':
        base += 8
    elif age_bucket == 'Gen Z':
        base += 5
    elif age_bucket == 'Boomer':
        base -= 12
    
    return max(0, min(100, base))


def predict_dominant_refusal(derived: Dict, start_pct: int, intent_pct: int) -> int:
    """
    Predict the dominant refusal primitive (1-7).
    
    Maps persona characteristics to the most likely refusal reason.
    """
    # Calculate refusal scores for each primitive
    scores = {i: 0 for i in range(1, 8)}
    
    age_bucket = derived.get('age_bucket', 'Gen X')
    urban_rural = derived.get('urban_rural', 'Rural')
    status_quo = derived.get('status_quo_score', 0.5)
    trust_threshold = derived.get('trust_threshold', 0.5)
    digital_score = derived.get('digital_literacy_score', 0.3)
    aspiration_score = derived.get('aspirational_score', 0.3)
    
    # 1. Status Quo Sufficiency
    scores[1] = status_quo * 40
    if urban_rural == 'Rural':
        scores[1] += 15  # UPI satisfaction in rural
    if age_bucket in ['Gen X', 'Boomer']:
        scores[1] += 10
    
    # 2. Habit Entrenchment
    if age_bucket in ['Gen X', 'Boomer']:
        scores[2] += 25
    if status_quo > 0.5:
        scores[2] += 15
    if digital_score < 0.4:
        scores[2] += 10
    
    # 3. Switching Cost Asymmetry
    if digital_score < 0.4:
        scores[3] += 20
    if age_bucket == 'Boomer':
        scores[3] += 15
    
    # 4. Maintenance Fatigue
    if age_bucket in ['Millennial', 'Gen X']:
        scores[4] += 15  # Busy professionals
    if aspiration_score > 0.5:
        scores[4] += 10  # Already juggling many things
    
    # 5. Trust Threshold Not Met
    scores[5] = trust_threshold * 35
    if urban_rural == 'Rural':
        scores[5] += 10
    if age_bucket in ['Gen X', 'Boomer']:
        scores[5] += 15
    
    # 6. Delayed Value Realization
    if aspiration_score < 0.4:
        scores[6] += 20
    if urban_rural in ['Rural', 'Semi-Urban']:
        scores[6] += 10
    
    # 7. Responsibility Avoidance (debt fear)
    if age_bucket == 'Gen Z':
        scores[7] += 15  # Debt-averse youth
    if trust_threshold > 0.5:
        scores[7] += 10
    if aspiration_score < 0.3:
        scores[7] += 15
    if urban_rural == 'Rural':
        scores[7] += 12  # Credit card horror stories
    
    # Find dominant refusal
    dominant = max(scores, key=scores.get)
    return dominant


def generate_reaction_quote(derived: Dict, start_pct: int, intent_pct: int) -> Tuple[str, str]:
    """
    Generate vivid reaction quote (Think, Say) based on persona profile.
    
    Returns: (think_text, say_text)
    """
    # Determine persona archetype
    age_bucket = derived.get('age_bucket', 'Gen X')
    urban_rural = derived.get('urban_rural', 'Rural')
    aspiration = derived.get('aspirational_intensity', 'Medium')
    digital = derived.get('digital_literacy', 'Low')
    trust = derived.get('trust_orientation', 'Moderate')
    cc_relevance = derived.get('cc_relevance', 'Low')
    
    # Map to archetype
    if cc_relevance == 'High':
        if urban_rural == 'Metro' and aspiration == 'High':
            archetype = 'young_urban_aspirational'
        elif digital == 'High':
            archetype = 'tech_savvy_professional'
        else:
            archetype = 'tier2_aspirational'
    elif cc_relevance == 'Medium':
        if urban_rural in ['Metro', 'Urban']:
            archetype = 'tier2_aspirational'
        else:
            archetype = 'family_oriented_salaried'
    else:  # Low relevance
        if age_bucket == 'Boomer' or (age_bucket == 'Gen X' and trust == 'Conservative'):
            archetype = 'older_risk_averse'
        elif urban_rural == 'Rural':
            archetype = 'rural_cash_preference'
        elif age_bucket == 'Gen Z' and trust == 'Conservative':
            archetype = 'debt_averse_youth'
        else:
            archetype = 'conservative_traditional'
    
    # Select random quote from archetype templates
    templates = REACTION_TEMPLATES.get(archetype, REACTION_TEMPLATES['conservative_traditional'])
    think, say = random.choice(templates)
    
    return (think, say)


# ============================================================================
# MAIN SIMULATION FUNCTION
# ============================================================================

def simulate_persona_reaction(row: pd.Series, derived: Dict, seed: int = None) -> Dict:
    """
    Run full simulation for a single persona.
    
    Args:
        row: Raw persona data from dataset
        derived: Derived feature dictionary for this persona
        seed: Optional random seed for reproducibility
    
    Returns:
        Dictionary with all prediction results
    """
    if seed is not None:
        random.seed(seed)
    
    # Core predictions
    start_pct = predict_quiz_start_likelihood(derived)
    completion_pct = predict_completion_rate(start_pct, derived)
    intent_pct = predict_apply_intent(completion_pct, derived)
    
    # Refusal primitive
    refusal_id = predict_dominant_refusal(derived, start_pct, intent_pct)
    refusal = REFUSAL_PRIMITIVES[refusal_id]
    
    # Reaction quote
    think, say = generate_reaction_quote(derived, start_pct, intent_pct)
    
    # Build result
    result = {
        # Predictions
        'quiz_start_pct': start_pct,
        'completion_pct': completion_pct,
        'apply_intent_pct': intent_pct,
        
        # Refusal analysis
        'refusal_id': refusal_id,
        'refusal_name': refusal.name,
        'refusal_code': refusal.short_code,
        
        # Reaction quote
        'reaction_think': think,
        'reaction_say': say,
        'reaction_quote': f"Think: {think}. Say: \"{say}\"",
        
        # Funnel stage
        'funnel_stage': categorize_funnel_stage(start_pct, completion_pct, intent_pct),
        
        # Conversion probability (simplified)
        'conversion_score': (start_pct * 0.3 + completion_pct * 0.3 + intent_pct * 0.4) / 100
    }
    
    return result


def categorize_funnel_stage(start: int, complete: int, intent: int) -> str:
    """Categorize persona into funnel stage."""
    if intent >= 60:
        return 'Hot Lead'
    elif intent >= 40:
        return 'Warm Lead'
    elif complete >= 60:
        return 'Engaged'
    elif start >= 50:
        return 'Curious'
    elif start >= 25:
        return 'Aware'
    else:
        return 'Cold'


# ============================================================================
# BATCH SIMULATION
# ============================================================================

def run_simulation(df: pd.DataFrame, seed: int = 42, verbose: bool = True) -> pd.DataFrame:
    """
    Run simulation on entire DataFrame of personas with derived features.
    
    Args:
        df: DataFrame with raw + derived features
        seed: Random seed for reproducibility
        verbose: Print progress
    
    Returns:
        DataFrame with simulation results appended
    """
    if verbose:
        print("🎬 Running Credigo.club Audience Simulation")
        print(f"   Product: {PRODUCT_INFO['name']} - {PRODUCT_INFO['tagline']}")
        print(f"   Personas: {len(df):,}")
        print(f"   Seed: {seed}")
    
    random.seed(seed)
    
    # Derived feature column names
    derived_cols = [
        'urban_rural', 'regional_cluster', 'primary_language', 'english_proficiency',
        'aspirational_intensity', 'aspirational_score', 'digital_literacy', 
        'digital_literacy_score', 'trust_orientation', 'trust_threshold',
        'status_quo_sufficiency', 'status_quo_score', 'hobby_breadth', 'hobby_count',
        'age_bucket', 'cc_relevance', 'cc_relevance_score'
    ]
    
    simulation_results = []
    
    for idx, row in df.iterrows():
        # Extract derived features
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        # Run simulation
        result = simulate_persona_reaction(row, derived, seed=seed + idx)
        simulation_results.append(result)
        
        if verbose and (idx + 1) % 200 == 0:
            print(f"   Simulated {idx + 1:,}/{len(df):,} personas")
    
    # Convert to DataFrame
    results_df = pd.DataFrame(simulation_results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"✅ Simulation complete!")
        
        # Quick summary
        print(f"\n📊 Quick Metrics:")
        print(f"   Avg Quiz Start: {results_df['quiz_start_pct'].mean():.1f}%")
        print(f"   Avg Completion: {results_df['completion_pct'].mean():.1f}%")
        print(f"   Avg Intent: {results_df['apply_intent_pct'].mean():.1f}%")
        print(f"\n   Funnel Distribution:")
        funnel = results_df['funnel_stage'].value_counts()
        for stage, count in funnel.items():
            print(f"     {stage}: {count} ({count/len(results_df)*100:.1f}%)")
    
    return final_df


# ============================================================================
# MAIN EXECUTION (for standalone testing)
# ============================================================================

if __name__ == "__main__":
    """Test simulation engine."""
    print("\n🧪 Running simulation_engine.py test...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load small sample
        sample_df, meta = load_and_sample(n=50, seed=42, verbose=True)
        
        # Derive features
        print("\n" + "=" * 60)
        enriched_df = derive_all_features(sample_df, verbose=True)
        
        # Run simulation
        print("\n" + "=" * 60)
        results_df = run_simulation(enriched_df, seed=42, verbose=True)
        
        # Show sample results
        print("\n📋 Sample Persona Reactions:")
        print("-" * 80)
        
        for i in range(min(5, len(results_df))):
            row = results_df.iloc[i]
            print(f"\n[{i+1}] {row['age']}yo {row['sex']} | {row['state']} | {row['occupation'][:40]}...")
            print(f"    📍 {row['urban_rural']} | {row['regional_cluster']} | {row['age_bucket']}")
            print(f"    📊 Start: {row['quiz_start_pct']}% | Complete: {row['completion_pct']}% | Intent: {row['apply_intent_pct']}%")
            print(f"    🚫 Refusal: {row['refusal_name']}")
            print(f"    💭 {row['reaction_quote'][:100]}...")
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

