#!/usr/bin/env python3
"""
dropsim_narrative.py - Narrative Summary Generator

Generates plain-language narrative summaries from DropSim results.
For founders/PMs to quote directly in decks and strategy docs.
"""

from typing import Dict, List, Optional
from collections import Counter


def generate_narrative_summary(
    scenario_result: Dict,
    product_steps: Dict,
    calibration_report: Optional[Dict] = None,
    result_df: Optional = None
) -> str:
    """
    Generate 5-10 sentences of plain-language narrative.
    
    Args:
        scenario_result: Dict from generate_full_report
        product_steps: Dict of product step definitions
        calibration_report: Optional CalibrationReport dict
        result_df: Optional DataFrame with persona results
    
    Returns:
        Plain-language narrative string
    """
    sentences = []
    
    failure_modes = scenario_result.get('failure_modes', {})
    total_variants = scenario_result.get('total_variants', 1)
    
    # Find step with maximum failure rate
    max_failure_step = None
    max_failure_rate = 0.0
    max_primary_cost = None
    
    for step_name, step_data in failure_modes.items():
        if 'failure_rate' in step_data:
            failure_rate = step_data['failure_rate'] / 100.0
        elif 'failure_count' in step_data:
            failure_rate = step_data['failure_count'] / total_variants if total_variants > 0 else 0.0
        else:
            continue
        
        if failure_rate > max_failure_rate:
            max_failure_rate = failure_rate
            max_failure_step = step_name
            max_primary_cost = step_data.get('primary_cost', 'Unknown')
    
    # Opening sentence: Most failures happen at X step
    if max_failure_step:
        sentences.append(
            f"Most failures occur at the '{max_failure_step}' step, "
            f"with {max_failure_rate*100:.1f}% of state-variants dropping off."
        )
        
        if max_primary_cost and max_primary_cost != 'None' and max_primary_cost != 'Multi-factor':
            cost_label = max_primary_cost
            # Capitalize cost labels properly
            cost_label_formatted = cost_label
            if cost_label == "System 2 fatigue":
                cost_label_formatted = "System 2 fatigue"
            elif cost_label == "Loss aversion":
                cost_label_formatted = "Loss aversion"
            elif cost_label == "Temporal discounting":
                cost_label_formatted = "Temporal discounting"
            elif cost_label == "Low ability":
                cost_label_formatted = "Low ability"
            
            sentences.append(
                f"This step is primarily driven by {cost_label_formatted}, "
                f"indicating that users are dropping due to this behavioral factor."
            )
    
    # Analyze persona patterns if result_df available
    if result_df is not None:
        # Check for consistency patterns
        high_consistency = []
        low_consistency = []
        
        for _, row in result_df.iterrows():
            consistency = row.get('consistency_score', 0)
            persona_name = str(row['persona_name']).split('\n')[0]
            exit_step = row.get('dominant_exit_step', 'Unknown')
            
            if consistency >= 0.7:
                high_consistency.append((persona_name, exit_step))
            elif consistency < 0.4:
                low_consistency.append((persona_name, exit_step))
        
        if high_consistency:
            sentences.append(
                f"Several personas show high consistency (≥70%) in their exit points, "
                f"suggesting structural product flaws rather than intent-sensitive behavior."
            )
        
        if low_consistency:
            sentences.append(
                f"Some personas show low consistency (<40%), indicating that drop-off is "
                f"highly dependent on arrival state (energy, motivation, trust) rather than persona traits alone."
            )
        
        # Check for energy/fatigue patterns
        if result_df is not None:
            fatigue_exits = []
            for _, row in result_df.iterrows():
                exit_step = row.get('dominant_exit_step', '')
                failure_reason = row.get('dominant_failure_reason', '')
                if 'System 2 fatigue' in str(failure_reason):
                    fatigue_exits.append(exit_step)
            
            if fatigue_exits:
                unique_fatigue_steps = list(set(fatigue_exits))
                if len(unique_fatigue_steps) >= 2:
                    sentences.append(
                        f"Multiple personas drop at different steps due to System 2 fatigue, "
                        f"suggesting that cognitive demand accumulates across the funnel and "
                        f"low-energy variants are particularly vulnerable."
                    )
    
    # Calibration insights
    if calibration_report:
        underestimates = calibration_report.get('underestimates', [])
        overestimates = calibration_report.get('overestimates', [])
        mae = calibration_report.get('overall_mae', 0.0)
        
        if underestimates:
            largest_underestimate = max(underestimates, key=lambda x: abs(x.get('delta', 0)))
            step_name = largest_underestimate.get('step_name', 'Unknown')
            delta = abs(largest_underestimate.get('delta', 0))
            
            sentences.append(
                f"Observed funnel data shows that DropSim underestimates drop-off at '{step_name}' "
                f"by {delta*100:.1f} percentage points, suggesting that the model may be "
                f"under-weighting certain behavioral costs (risk, effort, or cognitive demand) for this step."
            )
        
        if overestimates:
            largest_overestimate = max(overestimates, key=lambda x: abs(x.get('delta', 0)))
            step_name = largest_overestimate.get('step_name', 'Unknown')
            delta = largest_overestimate.get('delta', 0)
            
            sentences.append(
                f"DropSim overestimates drop-off at '{step_name}' by {delta*100:.1f} percentage points, "
                f"indicating that users may be more motivated or the step may be easier than modeled."
            )
        
        if mae < 0.10:
            sentences.append(
                f"Overall, DropSim predictions are within {mae*100:.1f} percentage points of observed data on average, "
                f"demonstrating strong alignment between the behavioral model and real user behavior."
            )
    
    # Closing sentence: Overall assessment
    if not sentences:
        sentences.append(
            "DropSim simulation reveals step-level failure patterns with behavioral attribution."
        )
    else:
        # Add a closing insight
        total_steps = len(product_steps)
        steps_with_failures = len([s for s in failure_modes.values() if s.get('failure_count', 0) > 0])
        
        if steps_with_failures < total_steps * 0.5:
            sentences.append(
                f"Only {steps_with_failures} of {total_steps} steps show significant drop-off, "
                f"suggesting that the funnel has a few critical failure points rather than uniform leakage."
            )
    
    return " ".join(sentences)

