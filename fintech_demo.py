"""
fintech_demo.py - Fintech Demo Simulation Runner

Runs the behavioral engine with fintech onboarding presets.
Provides PM-friendly output and drill-down capabilities.
"""

import json
from typing import Dict, List, Optional
from fintech_presets import (
    get_default_fintech_scenario,
    get_persona_by_name,
    FINTECH_ONBOARDING_STEPS
)
from behavioral_engine import (
    simulate_persona_trajectories,
    initialize_state,
    update_state,
    should_continue,
    identify_failure_reason,
    STATE_VARIANTS
)
from behavioral_aggregator import (
    format_failure_mode_report,
    generate_full_report,
    get_persona_state_trace,
    export_persona_traces_json
)
import pandas as pd


def create_persona_dataframe(personas: List[Dict]) -> pd.DataFrame:
    """
    Convert persona list to DataFrame format compatible with behavioral engine.
    
    Creates a minimal DataFrame with required fields.
    """
    rows = []
    for persona in personas:
        # Create a minimal row with required fields
        row = {
            'age': 30,  # Placeholder
            'sex': 'Unknown',
            'state': 'Unknown',
            'district': 'Unknown',
            'occupation': persona['description'],
            'education_level': 'Unknown',
            'first_language': 'Unknown',
            'second_language': 'Unknown',
            'third_language': 'Unknown',
            'marital_status': 'Unknown',
            'persona_name': persona['name'],
            'persona_description': persona['description']
        }
        rows.append(row)
    
    return pd.DataFrame(rows)


def run_fintech_demo_simulation(
    personas: List[Dict],
    state_variants: Dict,
    product_steps: Dict,
    verbose: bool = True,
    target_group: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Run behavioral simulation on fintech demo personas.
    
    Args:
        personas: List of persona dicts
        state_variants: Dict of state variants
        product_steps: Dict of product steps
        verbose: Print progress
        target_group: Optional TargetGroup filter
    
    Returns DataFrame with trajectories.
    """
    # Filter personas by target group if provided
    from dropsim_target_filter import TargetGroup, filter_personas_by_target
    
    if target_group is not None:
        if isinstance(target_group, dict):
            target_group = TargetGroup.from_dict(target_group)
        filtered_personas = filter_personas_by_target(personas, target_group)
        
        if len(filtered_personas) == 0:
            if verbose:
                print("⚠️  WARNING: No personas matched the target group filters.")
                print("   Returning empty results.")
            # Return empty DataFrame with correct structure
            return pd.DataFrame({
                'persona_name': [],
                'persona_description': [],
                'dominant_exit_step': [],
                'dominant_failure_reason': [],
                'consistency_score': [],
                'variants_completed': [],
                'variants_total': [],
                'trajectories': []
            })
        
        if verbose:
            print(f"🎯 Filtering personas by target group")
            print(f"   Matched: {len(filtered_personas)} of {len(personas)} personas")
        
        personas = filtered_personas
    
    if verbose:
        print("🏦 Running Fintech Onboarding Demo Simulation")
        print(f"   Personas: {len(personas)}")
        print(f"   State variants per persona: {len(state_variants)}")
        print(f"   Product steps: {len(product_steps)}")
        print(f"   Total trajectories: {len(personas) * len(state_variants)}")
    
    # Create DataFrame
    df = create_persona_dataframe(personas)
    
    # Simulate each persona
    all_results = []
    
    for idx, persona in enumerate(personas):
        # Create a row-like object
        row = df.iloc[idx]
        
        # Use persona's compiled priors directly
        priors = persona['priors']
        
        # Simulate all variants
        trajectories = []
        for variant_name in state_variants.keys():
            # Initialize state
            state = initialize_state(variant_name, priors)
            
            # Track journey
            journey = []
            exit_step = None
            failure_reason = None
            
            # Step through product flow
            for step_name, step_def in product_steps.items():
                # Update state
                state, costs = update_state(state, step_def, priors)
                
                # Record step
                journey.append({
                    'step': step_name,
                    'cognitive_energy': state.cognitive_energy,
                    'perceived_risk': state.perceived_risk,
                    'perceived_effort': state.perceived_effort,
                    'perceived_value': state.perceived_value,
                    'perceived_control': state.perceived_control,
                    'costs': costs
                })
                
                # Check continuation
                if not should_continue(state, priors):
                    exit_step = step_name
                    failure_reason = identify_failure_reason(costs)
                    break
            
            # If completed all steps
            if exit_step is None:
                exit_step = "Completed"
                failure_reason = None
            
            trajectories.append({
                'variant': variant_name,
                'variant_desc': state_variants[variant_name]['description'],
                'priors': priors,
                'journey': journey,
                'exit_step': exit_step,
                'failure_reason': failure_reason.value if failure_reason else None,
                'final_state': {
                    'cognitive_energy': state.cognitive_energy,
                    'perceived_risk': state.perceived_risk,
                    'perceived_effort': state.perceived_effort,
                    'perceived_value': state.perceived_value,
                    'perceived_control': state.perceived_control
                }
            })
        
        # Aggregate for this persona
        from collections import Counter
        exit_steps = [t['exit_step'] for t in trajectories]
        failure_reasons = [t['failure_reason'] for t in trajectories if t['failure_reason']]
        
        exit_counter = Counter(exit_steps)
        if exit_counter:
            dominant_exit = exit_counter.most_common(1)[0][0]
            consistency = exit_counter.most_common(1)[0][1] / len(trajectories) if trajectories else 0.0
        else:
            # All variants completed
            dominant_exit = "Completed"
            consistency = 1.0
        
        if failure_reasons:
            reason_counter = Counter(failure_reasons)
            dominant_reason = reason_counter.most_common(1)[0][0] if reason_counter else None
        else:
            dominant_reason = None
        
        all_results.append({
            'persona_name': persona['name'],
            'persona_description': persona['description'],
            'dominant_exit_step': dominant_exit,
            'dominant_failure_reason': dominant_reason,
            'consistency_score': consistency,
            'variants_completed': sum(1 for t in trajectories if t['exit_step'] == 'Completed'),
            'variants_total': len(trajectories),
            'trajectories': trajectories
        })
        
        if verbose and (idx + 1) % 2 == 0:
            print(f"   Simulated {idx + 1}/{len(personas)} personas")
    
    # Merge results
    results_df = pd.DataFrame(all_results)
    final_df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    if verbose:
        print(f"\n✅ Fintech demo simulation complete!")
        total_trajectories = len(personas) * len(state_variants)
        completed = sum(results_df['variants_completed'])
        print(f"   Completed: {completed}/{total_trajectories} ({completed/total_trajectories*100:.1f}%)")
    
    return final_df


def print_fintech_trace(
    df: pd.DataFrame,
    persona_name: str,
    variant_name: str,
    product_steps: Dict
):
    """Print compact trace for fintech demo."""
    # Find persona - iterate through rows to find match
    persona_row = None
    for idx, row in df.iterrows():
        # Get persona_name value (handle duplicate columns)
        pname = None
        if 'persona_name' in df.columns:
            pname = str(row['persona_name'])
        else:
            # Try to find it in any column
            for col in df.columns:
                if 'persona_name' in str(col).lower():
                    pname = str(row[col])
                    break
        
        if pname and persona_name in pname:
            persona_row = row
            break
    
    if persona_row is None:
        print(f"❌ Persona '{persona_name}' not found")
        # Get available personas
        if 'persona_name' in df.columns:
            available = df['persona_name'].unique()
            print(f"   Available: {', '.join([str(a) for a in available])}")
        return
    
    # Get trajectories
    if 'trajectories' in persona_row:
        trajectories = persona_row['trajectories']
    else:
        print("❌ Could not find trajectories for this persona")
        return
    
    # Find variant
    traj = next((t for t in trajectories if t['variant'] == variant_name), None)
    if not traj:
        print(f"❌ Variant '{variant_name}' not found")
        print(f"   Available: {', '.join([t['variant'] for t in trajectories])}")
        return
    
    # Print compact trace
    print("\n" + "=" * 80)
    print(f"📋 FINTECH DEMO: {persona_name} × {variant_name}")
    print("=" * 80)
    
    # Get persona description
    desc = None
    if 'persona_description' in persona_row:
        desc = str(persona_row['persona_description'])
        if '\n' in desc or 'Name:' in desc:
            desc = desc.split('\n')[0].split('Name:')[0].strip()
    else:
        desc = "Unknown"
    
    print(f"\n👤 {desc}")
    print(f"🎭 {traj.get('variant_desc', 'Unknown variant')}")
    
    print(f"\n📊 JOURNEY:")
    print("-" * 80)
    
    for i, step_trace in enumerate(traj['journey']):
        step_name = step_trace.get('step', 'Unknown')
        
        # Extract state values
        cognitive_energy = step_trace.get('cognitive_energy', 0)
        perceived_risk = step_trace.get('perceived_risk', 0)
        perceived_effort = step_trace.get('perceived_effort', 0)
        perceived_value = step_trace.get('perceived_value', 0)
        perceived_control = step_trace.get('perceived_control', 0)
        
        # Extract costs
        costs = step_trace.get('costs', {})
        cognitive_cost = costs.get('cognitive_cost', 0)
        effort_cost = costs.get('effort_cost', 0)
        risk_cost = costs.get('risk_cost', 0)
        
        # Check if this was exit step
        is_exit = step_name == traj['exit_step']
        
        # Decision
        decision = "❌ DROP" if is_exit else "✅ CONTINUE"
        
        print(f"\n  Step {i+1}: {step_name} {decision}")
        print(f"    State: value={perceived_value:.2f}, "
              f"risk={perceived_risk:.2f}, "
              f"effort={perceived_effort:.2f}, "
              f"control={perceived_control:.2f}, "
              f"energy={cognitive_energy:.2f}")
        
        if is_exit:
            print(f"    ❌ FAILURE: {traj.get('failure_reason', 'Unknown')}")
            print(f"    Costs: cognitive={cognitive_cost:.3f}, "
                  f"effort={effort_cost:.3f}, "
                  f"risk={risk_cost:.3f}")
    
    if traj['exit_step'] == 'Completed':
        print(f"\n  ✅ Completed all {len(traj['journey'])} steps")
    
    print("=" * 80)


def export_fintech_json(
    personas: List[Dict],
    df: pd.DataFrame,
    state_variants: Dict,
    product_steps: Dict,
    output_path: str
):
    """Export fintech demo to structured JSON."""
    export_data = {
        "metadata": {
            "scenario": "fintech_onboarding_demo",
            "personas": len(personas),
            "state_variants": len(state_variants),
            "product_steps": len(product_steps),
            "total_trajectories": len(personas) * len(state_variants)
        },
        "personas": [
            {
                "name": p['name'],
                "description": p['description'],
                "raw_fields": p['raw_fields'],
                "compiled_priors": p['priors']
            }
            for p in personas
        ],
        "state_variants": state_variants,
        "product_steps": product_steps,
        "trajectories": []
    }
    
    # Add all trajectories
    for idx in range(len(df)):
        row = df.iloc[idx]
        trajectories = row.get('trajectories', [])
        for traj in trajectories:
            # Get persona name (handle Series)
            pname = row.get('persona_name', 'Unknown')
            if hasattr(pname, 'iloc'):
                pname = pname.iloc[0] if len(pname) > 0 else 'Unknown'
            pname = str(pname).split('\n')[0].split('Name:')[0].strip()
            
            trajectory_data = {
                "persona_name": pname,
                "variant": traj.get('variant', 'Unknown'),
                "exit_step": traj.get('exit_step', 'Unknown'),
                "failure_reason": traj.get('failure_reason'),
                "journey": []
            }
            
            for step_trace in traj.get('journey', []):
                costs = step_trace.get('costs', {})
                trajectory_data['journey'].append({
                    "step": step_trace.get('step', 'Unknown'),
                    "state": {
                        "cognitive_energy": round(step_trace.get('cognitive_energy', 0), 3),
                        "perceived_risk": round(step_trace.get('perceived_risk', 0), 3),
                        "perceived_effort": round(step_trace.get('perceived_effort', 0), 3),
                        "perceived_value": round(step_trace.get('perceived_value', 0), 3),
                        "perceived_control": round(step_trace.get('perceived_control', 0), 3)
                    },
                    "costs": {
                        "cognitive_cost": round(costs.get('cognitive_cost', 0), 3),
                        "effort_cost": round(costs.get('effort_cost', 0), 3),
                        "risk_cost": round(costs.get('risk_cost', 0), 3),
                        "total_cost": round(costs.get('total_cost', 0), 3)
                    },
                    "dropped": step_trace.get('step') == traj.get('exit_step')
                })
            
            export_data['trajectories'].append(trajectory_data)
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported fintech demo to {output_path}")
    print(f"   {len(export_data['trajectories'])} trajectories")

