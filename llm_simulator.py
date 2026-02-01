"""
llm_simulator.py - LLM-Powered Journey Simulation for Credigo.club

Uses OpenAI GPT-4o-mini to generate intelligent, contextual predictions for each persona.

Instead of rule-based logic, the LLM:
1. Understands the persona's background, goals, and psychology
2. Simulates realistic reactions at each funnel step
3. Generates vivid, culturally-authentic Indian quotes
4. Identifies refusal primitives based on context

This creates much richer, more realistic simulation outputs.
"""

import os
import json
import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from openai import OpenAI

# ============================================================================
# CONFIGURATION
# ============================================================================

# Journey steps
JOURNEY_STEPS = [
    "Landing Page",
    "Quiz Start", 
    "Quiz Progression",
    "Quiz Completion",
    "Results Page",
    "Post-Results"
]

# Product context for LLM
PRODUCT_CONTEXT = """
PRODUCT: Credigo.club (December 2025)
- AI credit card recommender: "Your Credit Card Story Starts Here"
- 60-second quiz on spending habits/lifestyle
- STRONG PRIVACY: No PAN required, no sensitive data, no credit check
- Output: Instant personalized card recommendations (rewards, low fees, lounge access)
- No direct apply button – just recommendations (user must go to bank site)
- Target: Young professionals in India

JOURNEY STEPS:
1. Landing Page - User sees "60-sec private quiz" promise, no-data claims
2. Quiz Start - First questions appear (spending patterns, lifestyle)
3. Quiz Progression - More questions (travel, dining, shopping habits)
4. Quiz Completion - User finishes quiz, anticipates results
5. Results Page - Personalized card recommendations shown
6. Post-Results - No apply button, must manually visit bank sites

KEY FRICTION: No direct apply = extra effort to actually get the card
"""

# Refusal primitives
REFUSAL_PRIMITIVES = """
REFUSAL PRIMITIVES (choose exactly ONE that dominates, or "None" if engaged):
1. Status Quo Sufficiency - "UPI/current solution works fine, why change?"
2. Habit Entrenchment - "I'm used to my existing patterns"
3. Switching Cost Asymmetry - "Too much effort to try something new"
4. Maintenance Fatigue - "Another app/card to manage"
5. Trust Threshold Not Met - "Don't trust new fintech apps"
6. Delayed Value Realization - "Benefits not immediate/clear"
7. Responsibility Avoidance - "Don't want credit/debt burden"
"""


# ============================================================================
# LLM CLIENT
# ============================================================================

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


# ============================================================================
# PERSONA FORMATTING
# ============================================================================

def format_persona_context(row: pd.Series, derived: Dict) -> str:
    """Format persona data into a readable context for the LLM."""
    
    # Basic demographics
    context = f"""
PERSONA PROFILE:
- Age: {row.get('age', 'Unknown')} years old
- Sex: {row.get('sex', 'Unknown')}
- Location: {row.get('district', 'Unknown')}, {row.get('state', 'Unknown')}
- Zone: {derived.get('urban_rural', 'Unknown')} ({derived.get('regional_cluster', 'Unknown')} India)

BACKGROUND:
- Education: {row.get('education_level', 'Unknown')}
- Occupation: {row.get('occupation', 'Unknown')[:100]}
- Languages: {row.get('first_language', 'Unknown')} (primary), {row.get('second_language', 'Unknown')} (secondary)
- English Proficiency: {derived.get('english_proficiency', 'Unknown')}

PSYCHOGRAPHICS (0-10 scale):
- Digital Literacy: {derived.get('digital_literacy', 'Unknown')} ({derived.get('digital_literacy_score', 'N/A')}/10)
- Aspirational Intensity: {derived.get('aspirational_intensity', 'Unknown')} ({derived.get('aspirational_score', 'N/A')}/10)
- Trust/Risk Orientation: {derived.get('trust_orientation', 'Unknown')} ({derived.get('trust_score', 'N/A')}/10 conservatism)
- Status Quo Satisfaction: {derived.get('status_quo_sufficiency', 'Unknown')} ({derived.get('status_quo_score', 'N/A')}/10)
- Debt Aversion: {derived.get('debt_aversion', 'Unknown')} ({derived.get('debt_aversion_score', 'N/A')}/10)
- Credit Card Relevance: {derived.get('cc_relevance', 'Unknown')} ({derived.get('cc_relevance_score', 'N/A')}/10)

GENERATION: {derived.get('generation_bucket', 'Unknown')}

CAREER GOALS & AMBITIONS:
{row.get('career_goals_and_ambitions', 'Not specified')[:300]}

CULTURAL BACKGROUND:
{row.get('cultural_background', 'Not specified')[:200]}

HOBBIES & INTERESTS:
{row.get('hobbies_and_interests', 'Not specified')[:200]}
"""
    return context.strip()


# ============================================================================
# LLM SIMULATION PROMPT
# ============================================================================

def create_simulation_prompt(persona_context: str) -> str:
    """Create the simulation prompt for a single persona."""
    
    prompt = f"""You are simulating how a real Indian person would react to the Credigo.club product.

{PRODUCT_CONTEXT}

{persona_context}

{REFUSAL_PRIMITIVES}

TASK: Simulate this persona's journey through all 6 steps. For each step, predict:
1. Intent Score (0-100): How likely they are to continue/convert
   - 0-20: Will bounce/abandon
   - 21-40: Very hesitant, likely to leave
   - 41-60: On the fence
   - 61-80: Engaged, will continue
   - 81-100: Very engaged, high conversion potential

2. Emotional Reaction: One word (Excited, Curious, Skeptical, Anxious, Bored, Frustrated, Hopeful, Confused, etc.)

3. Rational Thought: What they're thinking (1 sentence, in their voice)

4. Next Action: What they'll do (Continue, Hesitate, Consider Leaving, Bounce, Complete, etc.)

IMPORTANT RULES:
- Be realistic for 2025 India. UPI is ubiquitous, credit cards are seen as "for rich people" by many.
- Intent CAN INCREASE at some steps (e.g., quiz completion gives accomplishment feeling, good recommendations excite aspirational users)
- The "no direct apply button" at Post-Results is a MAJOR friction point
- Rural/older/conservative personas will struggle early
- Young urban digital natives are the sweet spot
- Generate authentic Indian reactions (references to UPI, Sharma ji, EMI traps, etc.)

Respond in this exact JSON format:
{{
    "journey": [
        {{
            "step": "Landing Page",
            "intent": <0-100>,
            "emotion": "<one word>",
            "thought": "<their internal thought>",
            "action": "<what they do>"
        }},
        // ... all 6 steps
    ],
    "final_intent": <0-100>,
    "completed_funnel": <true/false>,
    "exit_step": "<step name where they exit, or 'Completed'>",
    "dominant_refusal": "<one of the 7 primitives, or 'None'>",
    "vivid_quote": {{
        "think": "<internal thought in their voice, 1-2 sentences>",
        "say": "<what they'd say out loud, 1 sentence, authentic Indian English/Hinglish>"
    }},
    "conversion_probability": <0.0-1.0>,
    "segment_suggestion": "<brief label like 'Young Urban Aspirational' or 'Rural UPI Loyalist'>"
}}
"""
    return prompt


# ============================================================================
# SINGLE PERSONA SIMULATION
# ============================================================================

def simulate_persona_llm(
    client: OpenAI,
    row: pd.Series,
    derived: Dict,
    model: str = "gpt-4o-mini",
    max_retries: int = 3
) -> Dict:
    """
    Simulate a single persona's journey using LLM.
    
    Returns:
        Dictionary with simulation results
    """
    persona_context = format_persona_context(row, derived)
    prompt = create_simulation_prompt(persona_context)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in Indian consumer behavior and fintech adoption. Generate realistic, culturally-authentic simulations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return {"error": f"JSON parse error: {e}"}
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                time.sleep(5)
                continue
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"error": str(e)}
    
    return {"error": "Max retries exceeded"}


# ============================================================================
# BATCH SIMULATION
# ============================================================================

def run_llm_simulation(
    df: pd.DataFrame,
    batch_size: int = 5,
    model: str = "gpt-4o-mini",
    verbose: bool = True,
    sample_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Run LLM simulation on DataFrame.
    
    Args:
        df: DataFrame with raw + derived features
        batch_size: Process this many before sleeping (rate limit)
        model: OpenAI model to use
        verbose: Print progress
        sample_n: If set, only simulate this many personas (for testing)
    
    Returns:
        DataFrame with LLM simulation results appended
    """
    client = get_openai_client()
    
    # Optionally sample
    if sample_n and sample_n < len(df):
        df = df.sample(n=sample_n, random_state=42).reset_index(drop=True)
    
    if verbose:
        print("🤖 Running LLM-Powered Journey Simulation")
        print(f"   Model: {model}")
        print(f"   Personas: {len(df)}")
        print(f"   Batch size: {batch_size}")
    
    # Derived feature columns
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
    
    results = []
    errors = 0
    
    for idx, row in df.iterrows():
        # Extract derived features
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        # Run LLM simulation
        result = simulate_persona_llm(client, row, derived, model)
        
        if "error" in result:
            errors += 1
            if verbose:
                print(f"   ⚠️ Error at {idx}: {result['error'][:50]}")
            # Fallback to basic result
            result = {
                "final_intent": 30,
                "completed_funnel": False,
                "exit_step": "Landing Page",
                "dominant_refusal": "Status Quo Sufficiency",
                "vivid_quote": {"think": "Not sure about this", "say": "Maybe later"},
                "conversion_probability": 0.1,
                "segment_suggestion": "Unknown",
                "journey": []
            }
        
        # Flatten journey results
        flat_result = {
            'llm_final_intent': result.get('final_intent', 0),
            'llm_completed_funnel': result.get('completed_funnel', False),
            'llm_exit_step': result.get('exit_step', 'Unknown'),
            'llm_dominant_refusal': result.get('dominant_refusal', 'Unknown'),
            'llm_think': result.get('vivid_quote', {}).get('think', ''),
            'llm_say': result.get('vivid_quote', {}).get('say', ''),
            'llm_conversion_prob': result.get('conversion_probability', 0),
            'llm_segment': result.get('segment_suggestion', 'Unknown')
        }
        
        # Add per-step intents
        journey = result.get('journey', [])
        for step_data in journey:
            step_key = step_data.get('step', '').replace(' ', '_').lower()
            flat_result[f'llm_{step_key}_intent'] = step_data.get('intent', 0)
            flat_result[f'llm_{step_key}_emotion'] = step_data.get('emotion', '')
        
        results.append(flat_result)
        
        if verbose and (idx + 1) % 10 == 0:
            print(f"   Simulated {idx + 1}/{len(df)} personas")
        
        # Rate limiting
        if (idx + 1) % batch_size == 0:
            time.sleep(1)  # Pause between batches
    
    # Merge results
    results_df = pd.DataFrame(results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"\n✅ LLM Simulation complete!")
        print(f"   Successful: {len(df) - errors}")
        print(f"   Errors: {errors}")
        print(f"   Avg Final Intent: {results_df['llm_final_intent'].mean():.1f}")
        print(f"   Funnel Completion: {results_df['llm_completed_funnel'].sum()} ({results_df['llm_completed_funnel'].sum()/len(results_df)*100:.1f}%)")
    
    return final_df


# ============================================================================
# QUICK TEST
# ============================================================================

def test_single_persona():
    """Test LLM simulation on a single persona."""
    print("\n🧪 Testing LLM Simulation on 1 persona...\n")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load 1 persona
        df, _ = load_and_sample(n=1, seed=42, verbose=False)
        df = derive_all_features(df, verbose=False)
        
        row = df.iloc[0]
        derived_cols = [
            'urban_rural', 'regional_cluster', 'english_proficiency',
            'aspirational_intensity', 'aspirational_score',
            'digital_literacy', 'digital_literacy_score',
            'trust_orientation', 'trust_score',
            'status_quo_sufficiency', 'status_quo_score',
            'debt_aversion', 'debt_aversion_score',
            'generation_bucket', 'cc_relevance', 'cc_relevance_score'
        ]
        derived = {col: row[col] for col in derived_cols if col in row.index}
        
        print("📋 PERSONA:")
        print(f"   {row['age']}yo {row['sex']} from {row['state']}")
        print(f"   Occupation: {row['occupation'][:50]}...")
        print(f"   Digital: {derived.get('digital_literacy')} | CC Relevance: {derived.get('cc_relevance')}")
        
        print("\n🤖 Calling GPT-4o-mini...")
        client = get_openai_client()
        result = simulate_persona_llm(client, row, derived)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print("\n📊 LLM SIMULATION RESULT:")
        print("-" * 60)
        
        print("\nJourney:")
        for step in result.get('journey', []):
            print(f"   {step['step']}: Intent={step['intent']} | {step['emotion']}")
            print(f"      Thought: \"{step['thought'][:60]}...\"")
        
        print(f"\n🎯 Final Intent: {result.get('final_intent')}")
        print(f"   Completed: {result.get('completed_funnel')}")
        print(f"   Exit Step: {result.get('exit_step')}")
        print(f"   Dominant Refusal: {result.get('dominant_refusal')}")
        print(f"   Segment: {result.get('segment_suggestion')}")
        
        quote = result.get('vivid_quote', {})
        print(f"\n💭 Think: \"{quote.get('think', '')}\"")
        print(f"💬 Say: \"{quote.get('say', '')}\"")
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    test_single_persona()

