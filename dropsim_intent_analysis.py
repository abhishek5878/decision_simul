"""
dropsim_intent_analysis.py - Intent-Aware Analysis and Reporting

Generates intent-level insights and explanations from simulation results.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from datetime import datetime

from dropsim_intent_model import (
    CANONICAL_INTENTS,
    detect_intent_conflicts,
    generate_intent_aware_explanation
)


# ============================================================================
# INTENT PROFILE GENERATION
# ============================================================================

def generate_intent_profile(result_df: pd.DataFrame, product_steps: Dict) -> Dict:
    """
    Generate intent profile from simulation results.
    
    Returns:
    {
        "overall_intent_distribution": {...},
        "intent_by_persona_segment": {...},
        "intent_stability": 0.85
    }
    """
    # Aggregate intent distributions across all personas
    all_intent_dists = []
    for _, row in result_df.iterrows():
        intent_dist = row.get('intent_distribution', {})
        if intent_dist:
            all_intent_dists.append(intent_dist)
    
    if not all_intent_dists:
        return {"error": "No intent distributions found in results"}
    
    # Compute overall distribution (average)
    overall_dist = {}
    for intent_id in CANONICAL_INTENTS.keys():
        overall_dist[intent_id] = np.mean([dist.get(intent_id, 0) for dist in all_intent_dists])
    
    # Compute intent stability (how consistent distributions are)
    intent_stability = 1.0 - np.mean([
        np.std([dist.get(intent_id, 0) for dist in all_intent_dists])
        for intent_id in CANONICAL_INTENTS.keys()
    ])
    
    return {
        "overall_intent_distribution": overall_dist,
        "intent_stability": float(intent_stability),
        "total_personas": len(all_intent_dists)
    }


# ============================================================================
# INTENT-WEIGHTED FUNNEL ANALYSIS
# ============================================================================

def generate_intent_weighted_funnel(
    result_df: pd.DataFrame,
    product_steps: Dict
) -> Dict:
    """
    Generate funnel analysis weighted by intent.
    
    Shows how different intents perform at each step.
    """
    step_intent_performance = defaultdict(lambda: defaultdict(lambda: {'entered': 0, 'exited': 0}))
    
    for _, row in result_df.iterrows():
        intent_dist = row.get('intent_distribution', {})
        if not intent_dist:
            continue
        
        for traj in row.get('trajectories', []):
            journey = traj.get('journey', [])
            
            for step_data in journey:
                step_name = step_data.get('step', 'Unknown')
                continued = step_data.get('continue', 'True') == 'True'
                
                # Weight by intent distribution
                for intent_id, intent_weight in intent_dist.items():
                    step_intent_performance[step_name][intent_id]['entered'] += intent_weight
                    if not continued:
                        step_intent_performance[step_name][intent_id]['exited'] += intent_weight
    
    # Convert to structured format
    funnel_data = {}
    for step_name in product_steps.keys():
        step_data = {}
        for intent_id in CANONICAL_INTENTS.keys():
            perf = step_intent_performance[step_name][intent_id]
            entered = perf['entered']
            exited = perf['exited']
            drop_rate = (exited / entered * 100) if entered > 0 else 0
            
            step_data[intent_id] = {
                'entered': entered,
                'exited': exited,
                'drop_rate': drop_rate
            }
        
        funnel_data[step_name] = step_data
    
    return funnel_data


# ============================================================================
# INTENT CONFLICT MATRIX
# ============================================================================

def generate_intent_conflict_matrix(
    result_df: pd.DataFrame,
    product_steps: Dict
) -> Dict:
    """
    Generate intent conflict matrix showing which steps conflict with which intents.
    """
    # Aggregate intent distributions
    all_intent_dists = []
    for _, row in result_df.iterrows():
        intent_dist = row.get('intent_distribution', {})
        if intent_dist:
            all_intent_dists.append(intent_dist)
    
    if not all_intent_dists:
        return {"error": "No intent distributions found"}
    
    # Compute average intent distribution
    avg_intent_dist = {}
    for intent_id in CANONICAL_INTENTS.keys():
        avg_intent_dist[intent_id] = np.mean([dist.get(intent_id, 0) for dist in all_intent_dists])
    
    # Detect conflicts
    conflicts = detect_intent_conflicts(product_steps, avg_intent_dist)
    
    # Build conflict matrix
    conflict_matrix = {}
    for step_name in product_steps.keys():
        step_conflicts = [c for c in conflicts if c['step_name'] == step_name]
        
        if step_conflicts:
            primary_conflict = step_conflicts[0]
            conflict_matrix[step_name] = {
                'has_conflict': True,
                'severity': primary_conflict['severity'],
                'conflict_type': primary_conflict['conflict_type'],
                'conflicting_intents': primary_conflict['conflicting_intents'],
                'affected_intent_pct': primary_conflict['affected_intent_pct']
            }
        else:
            conflict_matrix[step_name] = {
                'has_conflict': False,
                'severity': 0.0,
                'conflict_type': None,
                'conflicting_intents': [],
                'affected_intent_pct': 0.0
            }
    
    return {
        'conflict_matrix': conflict_matrix,
        'overall_conflicts': conflicts,
        'avg_intent_distribution': avg_intent_dist
    }


# ============================================================================
# INTENT-AWARE EXPLANATION GENERATION
# ============================================================================

def generate_intent_explanation_report(
    result_df: pd.DataFrame,
    product_steps: Dict
) -> str:
    """
    Generate human-readable intent-aware explanation report.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("INTENT-AWARE ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # 1. Overall Intent Distribution
    intent_profile = generate_intent_profile(result_df, product_steps)
    if 'error' not in intent_profile:
        lines.append("## Overall Intent Distribution")
        lines.append("-" * 80)
        for intent_id, weight in sorted(intent_profile['overall_intent_distribution'].items(), 
                                        key=lambda x: x[1], reverse=True):
            intent = CANONICAL_INTENTS[intent_id]
            lines.append(f"{intent.description}: {weight:.1%}")
        lines.append("")
    
    # 2. Intent Conflicts
    conflict_matrix = generate_intent_conflict_matrix(result_df, product_steps)
    if 'error' not in conflict_matrix:
        lines.append("## Intent Conflicts by Step")
        lines.append("-" * 80)
        
        for step_name, conflict_data in conflict_matrix['conflict_matrix'].items():
            if conflict_data['has_conflict']:
                lines.append(f"\n{step_name}:")
                lines.append(f"  Conflict Type: {conflict_data['conflict_type']}")
                lines.append(f"  Severity: {conflict_data['severity']:.2f}")
                lines.append(f"  Affected Intents: {', '.join(conflict_data['conflicting_intents'])}")
                lines.append(f"  Affected User %: {conflict_data['affected_intent_pct']:.1%}")
        lines.append("")
    
    # 3. Step-by-Step Intent-Aware Explanations
    lines.append("## Step-by-Step Intent-Aware Explanations")
    lines.append("-" * 80)
    
    # Compute funnel
    step_entries = Counter()
    step_exits = Counter()
    
    for _, row in result_df.iterrows():
        for traj in row.get('trajectories', []):
            journey = traj.get('journey', [])
            for step_data in journey:
                step_name = step_data.get('step', 'Unknown')
                step_entries[step_name] += 1
                if step_data.get('continue', 'True') == 'False':
                    step_exits[step_name] += 1
    
    # Get average intent distribution
    all_intent_dists = [row.get('intent_distribution', {}) for _, row in result_df.iterrows() 
                       if row.get('intent_distribution')]
    if all_intent_dists:
        avg_intent_dist = {}
        for intent_id in CANONICAL_INTENTS.keys():
            avg_intent_dist[intent_id] = np.mean([dist.get(intent_id, 0) for dist in all_intent_dists])
        
        conflicts = detect_intent_conflicts(product_steps, avg_intent_dist)
        
        for step_name in product_steps.keys():
            entered = step_entries.get(step_name, 0)
            exited = step_exits.get(step_name, 0)
            drop_rate = (exited / entered * 100) if entered > 0 else 0
            
            if drop_rate > 10:  # Only explain significant drop-offs
                explanation = generate_intent_aware_explanation(
                    step_name, drop_rate, avg_intent_dist, conflicts
                )
                
                lines.append(f"\n### {step_name}")
                lines.append(f"Drop Rate: {drop_rate:.1f}%")
                lines.append(f"Primary Reason: {explanation['primary_reason']}")
                
                if explanation['primary_reason'] == 'intent_misalignment':
                    lines.append(f"Intent Mismatch Score: {explanation['intent_mismatch_score']:.2f}")
                    lines.append(f"Primary Violated Intent: {explanation['primary_violated_intent']}")
                    lines.append(f"Explanation: {explanation['explanation']}")
                    if explanation['alternative_path_suggestion']:
                        lines.append(f"Suggestion: {explanation['alternative_path_suggestion']}")
                else:
                    lines.append(f"Explanation: {explanation['explanation']}")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


# ============================================================================
# EXPORT INTENT ARTIFACTS
# ============================================================================

def export_intent_artifacts(
    result_df: pd.DataFrame,
    product_steps: Dict,
    output_dir: str = "."
) -> Dict[str, str]:
    """
    Export all intent-aware artifacts.
    
    Returns dict of file paths:
    {
        "intent_profile": "intent_profile.json",
        "intent_weighted_funnel": "intent_weighted_funnel.json",
        "intent_conflict_matrix": "intent_conflict_matrix.json",
        "intent_explanation": "intent_explanation.md"
    }
    """
    artifacts = {}
    
    # 1. Intent Profile
    intent_profile = generate_intent_profile(result_df, product_steps)
    profile_path = f"{output_dir}/intent_profile.json"
    with open(profile_path, 'w') as f:
        json.dump(intent_profile, f, indent=2)
    artifacts['intent_profile'] = profile_path
    
    # 2. Intent-Weighted Funnel
    intent_funnel = generate_intent_weighted_funnel(result_df, product_steps)
    funnel_path = f"{output_dir}/intent_weighted_funnel.json"
    with open(funnel_path, 'w') as f:
        json.dump(intent_funnel, f, indent=2)
    artifacts['intent_weighted_funnel'] = funnel_path
    
    # 3. Intent Conflict Matrix
    conflict_matrix = generate_intent_conflict_matrix(result_df, product_steps)
    conflict_path = f"{output_dir}/intent_conflict_matrix.json"
    with open(conflict_path, 'w') as f:
        json.dump(conflict_matrix, f, indent=2)
    artifacts['intent_conflict_matrix'] = conflict_path
    
    # 4. Intent Explanation (Markdown)
    explanation_text = generate_intent_explanation_report(result_df, product_steps)
    explanation_path = f"{output_dir}/intent_explanation.md"
    with open(explanation_path, 'w') as f:
        f.write(explanation_text)
    artifacts['intent_explanation'] = explanation_path
    
    return artifacts

