#!/usr/bin/env python3
"""
Main runner for decision SHAP explainability analysis.

Loads decision traces, computes SHAP values, aggregates results,
and generates reports.
"""

import json
import sys
import os
from typing import Dict, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision_explainability.shap_model import (
    DecisionSurrogateModel,
    prepare_decision_features,
    compute_shap_values_for_decision
)

from decision_explainability.shap_aggregator import (
    aggregate_step_importance,
    aggregate_drop_trigger_analysis,
    aggregate_persona_sensitivity
)

from decision_explainability.shap_report_generator import (
    generate_feature_importance_report,
    generate_step_fragility_report,
    generate_persona_sensitivity_report
)


def load_traces_from_ledger(ledger_file: str) -> List[Dict]:
    """
    Load decision traces from benchmark ledger.
    
    Args:
        ledger_file: Path to ledger JSON file
    
    Returns:
        List of trace dictionaries
    """
    with open(ledger_file, 'r') as f:
        data = json.load(f)
    
    # Extract target traces (Credigo)
    traces = data.get('target_traces', [])
    
    return traces


def compute_shap_for_all_traces(
    traces: List[Dict],
    use_tree: bool = False
) -> List[Dict]:
    """
    Compute SHAP values for all traces.
    
    Args:
        traces: List of trace dictionaries
        use_tree: Whether to use tree model (else logistic regression)
    
    Returns:
        List of traces with 'shap_values' key added
    """
    print(f"Preparing features from {len(traces)} traces...")
    X, y, feature_names = prepare_decision_features(traces)
    
    print(f"Fitting surrogate model ({'tree' if use_tree else 'logistic regression'})...")
    model = DecisionSurrogateModel(use_tree=use_tree)
    model.fit(X, y, feature_names)
    
    print("Computing SHAP values for each decision...")
    traces_with_shap = []
    
    for i, trace in enumerate(traces):
        shap_values = compute_shap_values_for_decision(trace, model, feature_names)
        trace_with_shap = trace.copy()
        trace_with_shap['shap_values'] = shap_values.to_dict()
        traces_with_shap.append(trace_with_shap)
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} / {len(traces)} traces...")
    
    print(f"✓ Computed SHAP values for {len(traces_with_shap)} decisions")
    
    return traces_with_shap


def aggregate_all_analyses(traces_with_shap: List[Dict]) -> Dict:
    """
    Run all aggregation analyses.
    
    Returns:
        Dictionary with all aggregation results
    """
    print("\nAggregating analyses...")
    
    # Group by step
    by_step = defaultdict(list)
    for trace in traces_with_shap:
        step_id = trace.get('step_id', 'unknown')
        by_step[step_id].append(trace)
    
    # Per-step importance
    print("  Computing per-step importance...")
    step_importance = {}
    for step_id, step_traces in by_step.items():
        importance = aggregate_step_importance(step_traces, step_id=step_id)
        step_importance[step_id] = importance
    
    # Drop trigger analysis (overall)
    print("  Analyzing drop triggers...")
    drop_analysis = aggregate_drop_trigger_analysis(traces_with_shap)
    
    # Persona sensitivity
    print("  Analyzing persona sensitivity...")
    persona_analysis = aggregate_persona_sensitivity(traces_with_shap)
    
    print("✓ Aggregation complete")
    
    return {
        'step_importance': step_importance,
        'drop_trigger_analysis': drop_analysis,
        'persona_sensitivity': persona_analysis
    }


def generate_all_reports(
    aggregation_results: Dict,
    output_dir: str = "."
) -> Dict[str, str]:
    """
    Generate all markdown reports.
    
    Returns:
        Dictionary mapping report name to file path
    """
    print("\nGenerating reports...")
    
    step_importance = aggregation_results['step_importance']
    drop_analysis = aggregation_results['drop_trigger_analysis']
    persona_analysis = aggregation_results['persona_sensitivity']
    
    reports = {}
    
    # Feature importance report
    print("  Generating feature importance report...")
    importance_file = os.path.join(output_dir, "decision_feature_importance.md")
    generate_feature_importance_report(step_importance, importance_file)
    reports['feature_importance'] = importance_file
    
    # Step fragility report
    print("  Generating step fragility report...")
    fragility_file = os.path.join(output_dir, "step_fragility_shap.md")
    generate_step_fragility_report(step_importance, drop_analysis, fragility_file)
    reports['step_fragility'] = fragility_file
    
    # Persona sensitivity report
    print("  Generating persona sensitivity report...")
    sensitivity_file = os.path.join(output_dir, "persona_sensitivity_shap.md")
    generate_persona_sensitivity_report(persona_analysis, sensitivity_file)
    reports['persona_sensitivity'] = sensitivity_file
    
    print("✓ Reports generated")
    
    return reports


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute SHAP explainability for decision traces")
    parser.add_argument('ledger_file', type=str, help='Path to decision ledger JSON file')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for reports')
    parser.add_argument('--use-tree', action='store_true', help='Use decision tree instead of logistic regression')
    parser.add_argument('--save-traces', type=str, help='Save traces with SHAP values to JSON file')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DECISION SHAP EXPLAINABILITY ANALYSIS")
    print("=" * 80)
    print()
    
    # Load traces
    print(f"Loading traces from {args.ledger_file}...")
    traces = load_traces_from_ledger(args.ledger_file)
    print(f"✓ Loaded {len(traces)} traces")
    print()
    
    # Compute SHAP values
    traces_with_shap = compute_shap_for_all_traces(traces, use_tree=args.use_tree)
    print()
    
    # Save traces with SHAP if requested
    if args.save_traces:
        print(f"Saving traces with SHAP values to {args.save_traces}...")
        with open(args.save_traces, 'w') as f:
            json.dump(traces_with_shap, f, indent=2)
        print("✓ Saved")
        print()
    
    # Aggregate analyses
    aggregation_results = aggregate_all_analyses(traces_with_shap)
    print()
    
    # Generate reports
    reports = generate_all_reports(aggregation_results, output_dir=args.output_dir)
    print()
    
    # Print summary
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Generated reports:")
    for report_name, report_path in reports.items():
        print(f"  - {report_name}: {report_path}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

