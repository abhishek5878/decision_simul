#!/usr/bin/env python3
"""
dropsim_visualization_data.py - Plot-Ready Data Exports

Transforms DropSim results into plot-friendly JSON/CSV formats.
No plotting code—just data shaping for external tools (Sheets, Tableau, notebooks).
"""

from typing import Dict, List, Optional
import json
import csv
from pathlib import Path


# ============================================================================
# Step-Level Data
# ============================================================================

def build_step_level_series(
    scenario_result: Dict,
    product_steps: Dict,
    calibration_report: Optional[Dict] = None
) -> List[Dict]:
    """
    Build step-level series for plotting.
    
    Args:
        scenario_result: Dict from generate_full_report
        product_steps: Dict of product step definitions
        calibration_report: Optional CalibrationReport dict
    
    Returns:
        List of dicts, one per step, with:
        - step_name
        - step_index
        - predicted_failure_rate
        - observed_failure_rate (if calibration_report provided)
        - delta (if calibration_report provided)
        - primary_cost
        - secondary_cost
        - total_trajectories
        - failures
    """
    failure_modes = scenario_result.get('failure_modes', {})
    total_variants = scenario_result.get('total_variants', 1)
    
    # Build step name -> observed data map if calibration provided
    observed_map = {}
    if calibration_report:
        for comp in calibration_report.get('step_comparisons', []):
            observed_map[comp['step_name']] = {
                'observed_failure_rate': comp['observed_failure_rate'],
                'delta': comp['delta']
            }
    
    series = []
    step_names = list(product_steps.keys())
    
    for idx, step_name in enumerate(step_names):
        step_data = failure_modes.get(step_name, {})
        
        # Get predicted failure rate
        if 'failure_rate' in step_data:
            predicted_failure_rate = step_data['failure_rate'] / 100.0  # Convert from percentage
        elif 'failure_count' in step_data:
            predicted_failure_rate = step_data['failure_count'] / total_variants if total_variants > 0 else 0.0
        else:
            predicted_failure_rate = 0.0
        
        # Get costs
        primary_cost = step_data.get('primary_cost', 'None')
        secondary_cost = step_data.get('secondary_cost', 'Multi-factor')
        
        # Get failure count
        failures = step_data.get('failure_count', 0)
        
        row = {
            'step_index': idx + 1,
            'step_name': step_name,
            'predicted_failure_rate': predicted_failure_rate,
            'primary_cost': primary_cost,
            'secondary_cost': secondary_cost,
            'total_trajectories': total_variants,
            'failures': failures
        }
        
        # Add observed data if available
        if step_name in observed_map:
            obs_data = observed_map[step_name]
            row['observed_failure_rate'] = obs_data['observed_failure_rate']
            row['delta'] = obs_data['delta']
            row['underestimate'] = obs_data['delta'] < -0.05
            row['overestimate'] = obs_data['delta'] > 0.05
        
        series.append(row)
    
    return series


def export_step_level_csv(series: List[Dict], output_path: str):
    """Export step-level series to CSV."""
    if not series:
        return
    
    fieldnames = [
        'step_index', 'step_name', 'predicted_failure_rate',
        'observed_failure_rate', 'delta', 'underestimate', 'overestimate',
        'primary_cost', 'secondary_cost', 'total_trajectories', 'failures'
    ]
    
    # Filter fieldnames to only include those present in data
    available_fields = [f for f in fieldnames if any(f in row for row in series)]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=available_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(series)


def export_step_level_json(series: List[Dict], output_path: str):
    """Export step-level series to JSON."""
    with open(output_path, 'w') as f:
        json.dump(series, f, indent=2)


# ============================================================================
# Trajectory Data
# ============================================================================

def build_trajectory_series(
    trace: Dict,
    product_steps: Dict
) -> List[Dict]:
    """
    Build trajectory series for a single persona × variant.
    
    Args:
        trace: Dict with 'journey' list from trajectory
        product_steps: Dict of product step definitions
    
    Returns:
        List of dicts, one per step in journey, with:
        - step_index
        - step_name
        - cognitive_energy
        - perceived_value
        - perceived_risk
        - perceived_effort
        - perceived_control
        - continue_or_drop
        - cognitive_cost
        - effort_cost
        - risk_cost
        - value_yield
    """
    journey = trace.get('journey', [])
    exit_step = trace.get('exit_step', 'Completed')
    
    series = []
    step_names = list(product_steps.keys())
    
    for idx, step_trace in enumerate(journey):
        step_name = step_trace.get('step', 'Unknown')
        step_index = step_names.index(step_name) + 1 if step_name in step_names else idx + 1
        
        # Get state values
        cognitive_energy = step_trace.get('cognitive_energy', 0)
        perceived_risk = step_trace.get('perceived_risk', 0)
        perceived_effort = step_trace.get('perceived_effort', 0)
        perceived_value = step_trace.get('perceived_value', 0)
        perceived_control = step_trace.get('perceived_control', 0)
        
        # Get costs
        costs = step_trace.get('costs', {})
        cognitive_cost = costs.get('cognitive_cost', 0)
        effort_cost = costs.get('effort_cost', 0)
        risk_cost = costs.get('risk_cost', 0)
        value_yield = costs.get('value_yield', 0)
        
        # Determine if this step was the drop point
        is_drop = step_name == exit_step
        
        row = {
            'step_index': step_index,
            'step_name': step_name,
            'cognitive_energy': round(cognitive_energy, 3),
            'perceived_value': round(perceived_value, 3),
            'perceived_risk': round(perceived_risk, 3),
            'perceived_effort': round(perceived_effort, 3),
            'perceived_control': round(perceived_control, 3),
            'continue_or_drop': 'drop' if is_drop else 'continue',
            'cognitive_cost': round(cognitive_cost, 3),
            'effort_cost': round(effort_cost, 3),
            'risk_cost': round(risk_cost, 3),
            'value_yield': round(value_yield, 3)
        }
        
        series.append(row)
    
    return series


def export_trajectory_csv(series: List[Dict], output_path: str):
    """Export trajectory series to CSV."""
    if not series:
        return
    
    fieldnames = [
        'step_index', 'step_name',
        'cognitive_energy', 'perceived_value', 'perceived_risk',
        'perceived_effort', 'perceived_control',
        'continue_or_drop',
        'cognitive_cost', 'effort_cost', 'risk_cost', 'value_yield'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(series)


def export_trajectory_json(series: List[Dict], output_path: str):
    """Export trajectory series to JSON."""
    with open(output_path, 'w') as f:
        json.dump(series, f, indent=2)

