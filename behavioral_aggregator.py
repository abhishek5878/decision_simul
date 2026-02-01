"""
behavioral_aggregator.py - Aggregation and Output Formatting for Behavioral Engine

Implements the spec's output format:
- "Step t fails for X of Y state-variants"
- Primary/Secondary cost labels
- Drill-down to persona × state traces
- JSON export for data science teams
"""

import json
import pandas as pd
from typing import Dict, List, Optional
from collections import Counter
from behavioral_engine import PRODUCT_STEPS, FailureReason
from typing import Optional


def format_failure_mode_report(df: pd.DataFrame, product_steps: Optional[Dict] = None) -> str:
    """
    Format the primary output: failure rates and costs per step.
    
    This is the FIRST UI surface - "WHY before WHO"
    """
    total_personas = len(df)
    total_variants = total_personas * 7  # 7 variants per persona
    
    # Use custom product steps if provided
    steps_to_use = product_steps if product_steps else PRODUCT_STEPS
    
    # Collect all failures
    step_failures = {step: {'count': 0, 'reasons': Counter()} for step in steps_to_use.keys()}
    
    for _, row in df.iterrows():
        trajectories = row.get('trajectories', [])
        for traj in trajectories:
            exit_step = traj.get('exit_step', 'Unknown')
            if exit_step != 'Completed' and exit_step in step_failures:
                step_failures[exit_step]['count'] += 1
                if traj.get('failure_reason'):
                    step_failures[exit_step]['reasons'][traj['failure_reason']] += 1
    
    # Build report
    lines = []
    lines.append("=" * 80)
    lines.append("📊 FAILURE MODE ANALYSIS")
    lines.append("   (WHY they dropped at step t - before WHO)")
    lines.append("=" * 80)
    lines.append("")
    
    for step_name in steps_to_use.keys():
        failures = step_failures[step_name]
        failure_count = failures['count']
        failure_rate = (failure_count / total_variants * 100) if total_variants > 0 else 0
        
        # Primary and secondary costs
        reasons = failures['reasons']
        if reasons:
            primary = reasons.most_common(1)[0]
            secondary = reasons.most_common(2)[1] if len(reasons) > 1 else None
            
            primary_pct = (primary[1] / failure_count * 100) if failure_count > 0 else 0
            secondary_pct = (secondary[1] / failure_count * 100) if secondary and failure_count > 0 else 0
        else:
            primary = (None, 0)
            secondary = None
            primary_pct = 0
            secondary_pct = 0
        
        # Format: "Step t fails for X of Y state-variants"
        lines.append(f"Step: {step_name}")
        lines.append(f"  Fails for: {failure_count} of {total_variants} state-variants ({failure_rate:.1f}%)")
        lines.append(f"  Primary cost: {primary[0] if primary[0] else 'None'} ({primary_pct:.1f}% of failures)")
        if secondary and secondary_pct > 0:
            lines.append(f"  Secondary cost: {secondary[0]} ({secondary_pct:.1f}% of failures)")
        else:
            lines.append(f"  Secondary cost: Multi-factor or None")
        lines.append("")
    
    return "\n".join(lines)


def get_persona_state_trace(
    df: pd.DataFrame,
    persona_idx: int,
    variant_name: Optional[str] = None
) -> Dict:
    """
    Get full trace for a specific persona × state variant.
    
    Returns JSON-serializable trace with full journey.
    """
    row = df.iloc[persona_idx]
    trajectories = row.get('trajectories', [])
    
    if variant_name:
        # Get specific variant
        traj = next((t for t in trajectories if t['variant'] == variant_name), None)
        if not traj:
            return {"error": f"Variant '{variant_name}' not found"}
    else:
        # Get first variant as default
        traj = trajectories[0] if trajectories else None
        if not traj:
            return {"error": "No trajectories found"}
    
    # Build trace
    trace = {
        "persona_id": persona_idx,
        "persona_summary": {
            "age": int(row.get('age', 0)),
            "sex": str(row.get('sex', 'Unknown')),
            "state": str(row.get('state', 'Unknown')),
            "occupation": str(row.get('occupation', 'Unknown'))[:50],
            "urban_rural": str(row.get('urban_rural', 'Unknown')),
            "generation": str(row.get('generation_bucket', 'Unknown'))
        },
        "variant": {
            "name": traj['variant'],
            "description": traj['variant_desc']
        },
        "priors": {
            "CC": round(traj['priors']['CC'], 3),
            "FR": round(traj['priors']['FR'], 3),
            "RT": round(traj['priors']['RT'], 3),
            "LAM": round(traj['priors']['LAM'], 3),
            "ET": round(traj['priors']['ET'], 3),
            "TB": round(traj['priors']['TB'], 3),
            "DR": round(traj['priors']['DR'], 3),
            "CN": round(traj['priors']['CN'], 3),
            "MS": round(traj['priors']['MS'], 3)
        },
        "journey": []
    }
    
    # Add step-by-step journey
    for step_data in traj['journey']:
        step_trace = {
            "step": step_data['step'],
            "state": {
                "cognitive_energy": round(step_data['cognitive_energy'], 3),
                "perceived_risk": round(step_data['perceived_risk'], 3),
                "perceived_effort": round(step_data['perceived_effort'], 3),
                "perceived_value": round(step_data['perceived_value'], 3),
                "perceived_control": round(step_data['perceived_control'], 3)
            },
            "costs": {
                "cognitive_cost": round(step_data['costs']['cognitive_cost'], 3),
                "effort_cost": round(step_data['costs']['effort_cost'], 3),
                "risk_cost": round(step_data['costs']['risk_cost'], 3),
                "total_cost": round(step_data['costs']['total_cost'], 3)
            },
            "decision": "continue"  # Will be updated if this is exit step
        }
        
        # Check if this was the exit step
        if step_data['step'] == traj['exit_step']:
            step_trace['decision'] = "drop"
            step_trace['failure_reason'] = traj['failure_reason']
        
        trace['journey'].append(step_trace)
    
    trace['outcome'] = {
        "exit_step": traj['exit_step'],
        "failure_reason": traj['failure_reason'],
        "final_state": {
            "cognitive_energy": round(traj['final_state']['cognitive_energy'], 3),
            "perceived_risk": round(traj['final_state']['perceived_risk'], 3),
            "perceived_effort": round(traj['final_state']['perceived_effort'], 3),
            "perceived_value": round(traj['final_state']['perceived_value'], 3),
            "perceived_control": round(traj['final_state']['perceived_control'], 3)
        }
    }
    
    return trace


def export_persona_traces_json(
    df: pd.DataFrame,
    output_path: str,
    persona_indices: Optional[List[int]] = None,
    all_variants: bool = False
) -> None:
    """
    Export persona × state traces to JSON.
    
    Args:
        df: Results DataFrame
        output_path: Path to save JSON
        persona_indices: Which personas to export (None = all)
        all_variants: If True, export all variants per persona
    """
    if persona_indices is None:
        persona_indices = list(range(len(df)))
    
    traces = []
    
    for idx in persona_indices:
        if all_variants:
            # Export all variants for this persona
            row = df.iloc[idx]
            trajectories = row.get('trajectories', [])
            for traj in trajectories:
                trace = get_persona_state_trace(df, idx, traj['variant'])
                traces.append(trace)
        else:
            # Export first variant only
            trace = get_persona_state_trace(df, idx)
            traces.append(trace)
    
    with open(output_path, 'w') as f:
        json.dump({
            "metadata": {
                "total_traces": len(traces),
                "personas": len(persona_indices),
                "all_variants": all_variants
            },
            "traces": traces
        }, f, indent=2)
    
    print(f"✅ Exported {len(traces)} traces to {output_path}")


def print_persona_state_trace(df: pd.DataFrame, persona_idx: int, variant_name: Optional[str] = None):
    """Print a readable trace for a persona × state variant."""
    trace = get_persona_state_trace(df, persona_idx, variant_name)
    
    if "error" in trace:
        print(f"❌ {trace['error']}")
        return
    
    print("\n" + "=" * 80)
    print(f"📋 PERSONA × STATE TRACE")
    print("=" * 80)
    
    print(f"\n👤 PERSONA:")
    p = trace['persona_summary']
    print(f"   {p['age']}yo {p['sex']} from {p['state']}")
    print(f"   {p['occupation']}...")
    print(f"   {p['urban_rural']} | {p['generation']}")
    
    print(f"\n🎭 STATE VARIANT:")
    v = trace['variant']
    print(f"   {v['name']}: {v['description']}")
    
    print(f"\n🧠 BEHAVIORAL PRIORS:")
    priors = trace['priors']
    print(f"   CC (Cognitive Capacity): {priors['CC']}")
    print(f"   FR (Fatigue Rate): {priors['FR']}")
    print(f"   RT (Risk Tolerance): {priors['RT']}")
    print(f"   LAM (Loss Aversion): {priors['LAM']}")
    print(f"   ET (Effort Tolerance): {priors['ET']}")
    print(f"   TB (Trust Baseline): {priors['TB']}")
    print(f"   DR (Discount Rate): {priors['DR']}")
    print(f"   CN (Control Need): {priors['CN']}")
    print(f"   MS (Motivation Strength): {priors['MS']}")
    
    print(f"\n📊 JOURNEY:")
    print("-" * 80)
    
    for step_trace in trace['journey']:
        step = step_trace['step']
        state = step_trace['state']
        costs = step_trace['costs']
        decision = step_trace['decision']
        
        print(f"\n  {step}:")
        print(f"    State: energy={state['cognitive_energy']:.2f}, "
              f"risk={state['perceived_risk']:.2f}, "
              f"effort={state['perceived_effort']:.2f}, "
              f"value={state['perceived_value']:.2f}, "
              f"control={state['perceived_control']:.2f}")
        print(f"    Costs: cognitive={costs['cognitive_cost']:.3f}, "
              f"effort={costs['effort_cost']:.3f}, "
              f"risk={costs['risk_cost']:.3f}")
        print(f"    Decision: {decision.upper()}")
        
        if decision == "drop":
            print(f"    ❌ FAILURE REASON: {step_trace.get('failure_reason', 'Unknown')}")
    
    print("-" * 80)
    
    outcome = trace['outcome']
    print(f"\n🎯 OUTCOME:")
    print(f"   Exit Step: {outcome['exit_step']}")
    if outcome['failure_reason']:
        print(f"   Failure Reason: {outcome['failure_reason']}")
    else:
        print(f"   ✅ Completed all steps")
    
    final = outcome['final_state']
    print(f"\n   Final State:")
    print(f"     Cognitive Energy: {final['cognitive_energy']:.2f}")
    print(f"     Perceived Risk: {final['perceived_risk']:.2f}")
    print(f"     Perceived Effort: {final['perceived_effort']:.2f}")
    print(f"     Perceived Value: {final['perceived_value']:.2f}")
    print(f"     Perceived Control: {final['perceived_control']:.2f}")
    
    print("=" * 80)


# ============================================================================
# MAIN AGGREGATION FUNCTION
# ============================================================================

def generate_full_report(df: pd.DataFrame, output_dir: Optional[str] = None, product_steps: Optional[Dict] = None) -> Dict:
    """
    Generate complete report matching spec requirements.
    
    Returns dict with all aggregated data.
    """
    total_personas = len(df)
    total_variants = total_personas * 7
    
    # Use custom product steps if provided
    steps_to_use = product_steps if product_steps else PRODUCT_STEPS
    
    # Failure mode analysis
    failure_modes = {}
    for step_name in steps_to_use.keys():
        step_failures = {'count': 0, 'reasons': Counter(), 'personas': set()}
        
        for idx, row in df.iterrows():
            trajectories = row.get('trajectories', [])
            for traj in trajectories:
                if traj['exit_step'] == step_name:
                    step_failures['count'] += 1
                    if traj['failure_reason']:
                        step_failures['reasons'][traj['failure_reason']] += 1
                    step_failures['personas'].add(idx)
        
        reasons = step_failures['reasons']
        primary = reasons.most_common(1)[0] if reasons else (None, 0)
        secondary = reasons.most_common(2)[1] if len(reasons) > 1 else None
        
        failure_modes[step_name] = {
            'failure_count': step_failures['count'],
            'failure_rate': step_failures['count'] / total_variants * 100,
            'persona_count': len(step_failures['personas']),
            'primary_cost': primary[0] if primary[0] else 'None',
            'primary_count': primary[1],
            'secondary_cost': secondary[0] if secondary else 'Multi-factor',
            'secondary_count': secondary[1] if secondary else 0
        }
    
    # Format report text
    report_text = format_failure_mode_report(df, product_steps)
    
    return {
        'failure_modes': failure_modes,
        'report_text': report_text,
        'total_personas': total_personas,
        'total_variants': total_variants
    }

