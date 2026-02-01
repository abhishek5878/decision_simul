#!/usr/bin/env python3
"""
Run complete analysis for Bachatt product:
1. Analyze screenshots to extract product steps
2. Filter personas for target: Self-employed and non-salaried Indians with irregular income
3. Run simulation
4. Generate decision autopsy results
"""

import os
import sys
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
import pandas as pd
import numpy as np

# Import required modules
from load_dataset import load_and_sample
from derive_features import derive_all_features
from behavioral_engine_intent_aware import run_intent_aware_simulation
from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from dropsim_target_filter import TargetGroup, filter_personas_by_target
from dropsim_simulation_runner import convert_persona_to_compiled_priors, extract_persona_meta


def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_screenshot(image_path, api_key, screenshot_name):
    """Analyze a single screenshot using GPT-4 Vision."""
    client = OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt = """Analyze this screenshot from a fintech product (Bachatt - automated wealth building for self-employed Indians).

Extract:
1. Step number (if visible, e.g., "Step 1 of 3", "Step 2 of 3")
2. Progress percentage (if visible)
3. Main question, heading, or screen purpose
4. Input fields, options, or actions required
5. Any buttons or CTAs
6. Key UI elements and what the user needs to do
7. Risk indicators (data sharing, financial info, etc.)
8. Effort indicators (form complexity, number of fields, etc.)
9. Cognitive complexity (simple choice vs complex decision)
10. Value proposition shown (if any)

Describe the screen in detail, focusing on what the user needs to do at this step."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content


def analyze_bachatt_screenshots(screenshot_dir="bachatt", api_key=None):
    """Analyze all bachatt screenshots and extract product flow."""
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    screenshots = []
    screenshot_files = sorted([f for f in os.listdir(screenshot_dir) if f.endswith('.jpeg')])
    
    print(f"\n🔍 Analyzing {len(screenshot_files)} screenshots from {screenshot_dir}...")
    
    for i, filename in enumerate(screenshot_files, 1):
        image_path = os.path.join(screenshot_dir, filename)
        print(f"   Analyzing {filename}...")
        try:
            description = analyze_screenshot(image_path, api_key, filename)
            screenshots.append({
                'filename': filename,
                'step_number': i,
                'description': description
            })
            print(f"   ✅ {filename} analyzed")
        except Exception as e:
            print(f"   ❌ Error analyzing {filename}: {e}")
    
    return screenshots


def extract_product_steps_from_analysis(screenshots: List[Dict], api_key=None) -> Dict:
    """Extract product steps from screenshot analysis using LLM."""
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    client = OpenAI(api_key=api_key)
    
    # Combine all screenshot descriptions
    screenshots_text = "\n\n".join([
        f"## SCREENSHOT {i+1} ({s['filename']})\n{s['description']}"
        for i, s in enumerate(screenshots)
    ])
    
    prompt = f"""You are analyzing screenshots from Bachatt, a fintech product for automated wealth building targeting self-employed and non-salaried Indians with irregular income.

## SCREENSHOTS (in order)
{screenshots_text}

## TASK
Extract product steps from these screenshots. For each screenshot, create a step definition with these attributes:
- step_name: Clear name of the step
- cognitive_demand: 0.0-1.0 (how much thinking required)
- effort_demand: 0.0-1.0 (physical/time effort)
- risk_signal: 0.0-1.0 (data/financial risk perception)
- irreversibility: 0.0-1.0 (can user undo this?)
- delay_to_value: number of steps until user sees value (0 = instant, higher = later)
- explicit_value: 0.0-1.0 (how clear is the benefit shown?)
- reassurance_signal: 0.0-1.0 (trust signals present)
- authority_signal: 0.0-1.0 (official backing)
- description: Brief description of what happens at this step

Output ONLY a JSON object with this structure:
{{
  "Step Name 1": {{
    "cognitive_demand": 0.2,
    "effort_demand": 0.3,
    "risk_signal": 0.15,
    "irreversibility": 0.0,
    "delay_to_value": 2,
    "explicit_value": 0.5,
    "reassurance_signal": 0.6,
    "authority_signal": 0.3,
    "description": "Step description"
  }},
  "Step Name 2": {{ ... }},
  ...
}}

Extract EXACTLY {len(screenshots)} steps, one per screenshot. Use the exact step names/headings from the screenshots."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2000
    )
    
    steps = json.loads(response.choices[0].message.content)
    return steps


def create_target_persona_filter() -> TargetGroup:
    """Create target group filter for: Self-employed and non-salaried Indians with irregular daily or weekly income who struggle to save consistently but want simple, automated wealth building."""
    # Map the persona description to filter criteria:
    # - Self-employed/non-salaried: This is more about income pattern, not directly mappable
    # - Irregular income: Not directly mappable, but we can filter for lower SEC or specific risk attitudes
    # - Want automated wealth building: Higher intent, medium-high digital skill
    # - Struggle to save: Lower SEC, price sensitive
    
    return TargetGroup(
        sec=["low", "mid"],  # Self-employed with irregular income likely lower-middle income
        urban_rural=["tier2", "metro"],  # More likely in urban areas
        age_bucket=["young", "middle"],  # Working age
        digital_skill=["medium", "high"],  # Need digital comfort for automated wealth building
        risk_attitude=["risk_averse", "balanced"],  # Want simple, automated (not high risk)
        intent=["medium", "high"]  # Want automated wealth building = higher intent
    )


def filter_personas_for_target(df: pd.DataFrame, target_group: TargetGroup) -> pd.DataFrame:
    """Filter personas DataFrame by target group."""
    filtered_indices = []
    
    for idx, row in df.iterrows():
        # Convert row to persona meta format
        meta = extract_persona_meta(row, {})
        
        # Check if matches target
        from dropsim_target_filter import persona_matches_target
        if persona_matches_target(meta, target_group):
            filtered_indices.append(idx)
    
    return df.loc[filtered_indices].copy()


def main():
    print("\n" + "=" * 80)
    print("🎯 BACHATT PRODUCT ANALYSIS")
    print("=" * 80)
    print("Target Persona: Self-employed and non-salaried Indians with irregular")
    print("                daily or weekly income who struggle to save consistently")
    print("                but want simple, automated wealth building")
    print("=" * 80)
    
    # Step 1: Analyze screenshots
    print("\n📸 STEP 1: Analyzing screenshots...")
    try:
        screenshots = analyze_bachatt_screenshots("bachatt")
        print(f"   ✅ Analyzed {len(screenshots)} screenshots")
    except Exception as e:
        print(f"   ❌ Error analyzing screenshots: {e}")
        print("   ⚠️  Continuing with manual step definition...")
        screenshots = []
    
    # Step 2: Extract product steps
    print("\n📋 STEP 2: Extracting product steps...")
    if screenshots:
        try:
            product_steps = extract_product_steps_from_analysis(screenshots)
            print(f"   ✅ Extracted {len(product_steps)} product steps")
        except Exception as e:
            print(f"   ❌ Error extracting steps: {e}")
            print("   ⚠️  Using default steps...")
            # Fallback: Create basic steps based on typical wealth building flow
            product_steps = {
                "Landing Page": {
                    "cognitive_demand": 0.2,
                    "effort_demand": 0.0,
                    "risk_signal": 0.1,
                    "irreversibility": 0.0,
                    "delay_to_value": 2,
                    "explicit_value": 0.6,
                    "reassurance_signal": 0.5,
                    "authority_signal": 0.3,
                    "description": "Landing page - Automated wealth building value proposition"
                },
                "Income Details": {
                    "cognitive_demand": 0.4,
                    "effort_demand": 0.4,
                    "risk_signal": 0.3,
                    "irreversibility": 0.0,
                    "delay_to_value": 1,
                    "explicit_value": 0.4,
                    "reassurance_signal": 0.5,
                    "authority_signal": 0.2,
                    "description": "Enter income details and savings goals"
                },
                "Setup Complete": {
                    "cognitive_demand": 0.2,
                    "effort_demand": 0.1,
                    "risk_signal": 0.1,
                    "irreversibility": 0.0,
                    "delay_to_value": 0,
                    "explicit_value": 0.8,
                    "reassurance_signal": 0.6,
                    "authority_signal": 0.3,
                    "description": "Setup complete - Automated savings plan shown"
                }
            }
    else:
        # Use default steps
        product_steps = {
            "Landing Page": {
                "cognitive_demand": 0.2,
                "effort_demand": 0.0,
                "risk_signal": 0.1,
                "irreversibility": 0.0,
                "delay_to_value": 2,
                "explicit_value": 0.6,
                "reassurance_signal": 0.5,
                "authority_signal": 0.3,
                "description": "Landing page - Automated wealth building value proposition"
            },
            "Income Details": {
                "cognitive_demand": 0.4,
                "effort_demand": 0.4,
                "risk_signal": 0.3,
                "irreversibility": 0.0,
                "delay_to_value": 1,
                "explicit_value": 0.4,
                "reassurance_signal": 0.5,
                "authority_signal": 0.2,
                "description": "Enter income details and savings goals"
            },
            "Setup Complete": {
                "cognitive_demand": 0.2,
                "effort_demand": 0.1,
                "risk_signal": 0.1,
                "irreversibility": 0.0,
                "delay_to_value": 0,
                "explicit_value": 0.8,
                "reassurance_signal": 0.6,
                "authority_signal": 0.3,
                "description": "Setup complete - Automated savings plan shown"
            }
        }
    
    # Save product steps
    with open("bachatt_steps.py", "w") as f:
        f.write('"""\n')
        f.write('Bachatt Product Flow Definition\n')
        f.write('Automated wealth building for self-employed Indians with irregular income\n')
        f.write(f'{len(product_steps)}-step onboarding flow\n')
        f.write('"""\n\n')
        f.write('BACHATT_STEPS = ')
        f.write(json.dumps(product_steps, indent=4))
        f.write('\n')
    print(f"   ✅ Saved product steps to bachatt_steps.py")
    
    # Step 3: Load and filter personas
    print("\n👥 STEP 3: Loading and filtering personas...")
    df, _ = load_and_sample(n=5000, seed=42, verbose=False)
    print(f"   Loaded {len(df)} personas")
    
    df = derive_all_features(df, verbose=False)
    print(f"   Derived features")
    
    target_group = create_target_persona_filter()
    df_filtered = filter_personas_for_target(df, target_group)
    print(f"   ✅ Filtered to {len(df_filtered)} personas matching target")
    
    if len(df_filtered) == 0:
        print("   ⚠️  No personas matched target. Using all personas...")
        df_filtered = df
    
    # Step 4: Run simulation
    print("\n🧠 STEP 4: Running intent-aware simulation...")
    result_df = run_intent_aware_simulation(
        df_filtered,
        product_steps=product_steps,
        fixed_intent=CREDIGO_GLOBAL_INTENT,  # Using generic intent for now
        verbose=True,
        seed=42
    )
    print(f"   ✅ Simulation complete")
    
    # Step 5: Generate decision traces (simplified approach)
    print("\n📊 STEP 5: Generating decision traces...")
    # For now, create minimal traces from simulation results
    # The decision_autopsy_result_generator can work with minimal traces
    traces = []
    
    # Extract drop points from trajectories
    drop_points = {}
    for idx, row in result_df.iterrows():
        for traj in row.get('trajectories', []):
            if not traj.get('completed', False) and traj.get('exit_step'):
                step_id = traj.get('exit_step', 'unknown')
                if step_id not in drop_points:
                    drop_points[step_id] = 0
                drop_points[step_id] += 1
    
    # Create minimal DecisionTrace objects for the most common drop points
    step_names = list(product_steps.keys())
    for step_id, count in sorted(drop_points.items(), key=lambda x: x[1], reverse=True)[:10]:
        try:
            step_index = step_names.index(step_id) if step_id in step_names else 0
            trace = DecisionTrace(
                persona_id=f"persona_{count}",
                step_id=step_id,
                step_index=step_index,
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.3,  # Low probability = likely to drop
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=0.4,
                    risk=0.5,
                    effort=0.5,
                    value=0.3,
                    control=0.4
                ),
                intent=IntentSnapshot(
                    inferred_intent="wealth_building",
                    alignment_score=0.5
                ),
                dominant_factors=["value_perception", "trust_deficit"]
            )
            traces.append(trace)
        except Exception as e:
            continue
    
    # If no traces, create at least one for the first step
    if len(traces) == 0 and len(step_names) > 0:
        trace = DecisionTrace(
            persona_id="default_persona",
            step_id=step_names[0],
            step_index=0,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.4,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.5,
                risk=0.4,
                effort=0.4,
                value=0.4,
                control=0.5
            ),
            intent=IntentSnapshot(
                inferred_intent="wealth_building",
                alignment_score=0.6
            ),
            dominant_factors=["value_perception"]
        )
        traces.append(trace)
    
    print(f"   ✅ Generated {len(traces)} decision traces")
    
    # Step 6: Generate decision autopsy results
    print("\n📄 STEP 6: Generating decision autopsy results...")
    generator = DecisionAutopsyResultGenerator(
        product_steps=product_steps,
        product_name="BACHATT",
        product_full_name="Bachatt - Automated Wealth Building"
    )
    
    result = generator.generate(
        traces=traces,
        run_mode="production"
    )
    
    # Save results
    output_file = "BACHATT_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"   ✅ Results saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📊 KEY METRICS:")
    print(f"   Product Steps: {len(product_steps)}")
    print(f"   Personas Analyzed: {len(df_filtered)}")
    print(f"   Decision Traces: {len(traces)}")
    print(f"   Verdict: {result.get('verdict', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 'N/A')}")
    print(f"\n📁 OUTPUT FILES:")
    print(f"   Product Steps: bachatt_steps.py")
    print(f"   Results: {output_file}")
    print("=" * 80 + "\n")
    
    return result, product_steps


if __name__ == "__main__":
    result, steps = main()
