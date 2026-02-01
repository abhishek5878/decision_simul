#!/usr/bin/env python3
"""
dropsim_cli.py - DropSim CLI for PMs

Single entrypoint for running behavioral simulations.
Mixpanel-ish but behavioral: step-level failure rates with labeled reasons.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

from fintech_presets import get_default_fintech_scenario
from fintech_demo import (
    run_fintech_demo_simulation,
    print_fintech_trace,
    export_fintech_json
)
from behavioral_aggregator import generate_full_report
from dropsim_calibration import (
    ObservedFunnel,
    compare_scenario_to_observed,
    suggest_coefficient_adjustments,
    format_calibration_report,
    format_tuning_suggestions
)
from dropsim_visualization_data import (
    build_step_level_series,
    export_step_level_csv,
    export_step_level_json,
    build_trajectory_series,
    export_trajectory_csv,
    export_trajectory_json
)
from dropsim_narrative import generate_narrative_summary
from dropsim_lite_input import load_lite_scenario, lite_to_scenario
from dropsim_target_filter import load_target_group, TargetGroup
from dropsim_llm_ingestion import (
    infer_lite_scenario_and_target_from_llm,
    OpenAILLMClient,
    LLMClient
)
from dropsim_wizard import (
    WizardInput,
    run_fintech_wizard
)


def load_scenario_from_json(filepath: str) -> Dict:
    """Load scenario from JSON file matching ScenarioConfig schema."""
    with open(filepath, 'r') as f:
        return json.load(f)


def run_scenario_simulation(scenario: Dict, verbose: bool = True, target_group: Optional[TargetGroup] = None) -> Dict:
    """
    Run simulation for a generic scenario (not just fintech).
    
    Args:
        scenario: ScenarioConfig dict with personas, steps, optional state_variants
        verbose: Print progress
        target_group: Optional TargetGroup filter
    
    Returns:
        Dict with results_df and summary
    """
    from fintech_demo import run_fintech_demo_simulation
    from behavioral_engine import STATE_VARIANTS
    
    # Extract components
    personas = scenario.get('personas', [])
    product_steps = {step['name']: step for step in scenario.get('steps', [])}
    state_variants = scenario.get('state_variants', STATE_VARIANTS)
    
    # Compile personas (if not already compiled) and ensure meta tags exist
    compiled_personas = []
    for persona in personas:
        if 'compiled_priors' not in persona:
            from fintech_presets import compile_persona_from_raw
            priors = compile_persona_from_raw(persona.get('raw_fields', {}))
            persona['priors'] = priors
        else:
            persona['priors'] = persona['compiled_priors']
        
        # Ensure meta tags exist
        if 'meta' not in persona:
            from fintech_presets import extract_persona_meta_from_raw
            raw_fields = persona.get('raw_fields', {})
            persona['meta'] = extract_persona_meta_from_raw(raw_fields, persona)
        
        compiled_personas.append(persona)
    
    # Run simulation (reuse fintech demo logic)
    target_group_dict = target_group.to_dict() if target_group else None
    result_df = run_fintech_demo_simulation(
        compiled_personas,
        state_variants,
        product_steps,
        verbose=verbose,
        target_group=target_group_dict
    )
    
    return {
        'result_df': result_df,
        'personas': compiled_personas,
        'state_variants': state_variants,
        'product_steps': product_steps
    }


def format_step_summary(step_name: str, failure_rate: float, primary_cost: Optional[str], 
                       secondary_cost: Optional[str], total_trajectories: int) -> str:
    """Format step summary in design doc language."""
    failures = int(failure_rate * total_trajectories)
    primary_pct = "100.0%" if primary_cost else "0.0%"
    
    lines = [
        f"Step: {step_name}",
        f"  Fails for: {failures} of {total_trajectories} state-variants ({failure_rate*100:.1f}%)",
        f"  Primary cost: {primary_cost if primary_cost else 'None'} ({primary_pct} of failures)"
    ]
    
    if secondary_cost:
        lines.append(f"  Secondary cost: {secondary_cost}")
    else:
        lines.append(f"  Secondary cost: Multi-factor or None")
    
    return "\n".join(lines)


def export_plot_data(results: Dict, product_steps: Dict, output_path: str, calibration_report_dict: Optional[Dict] = None):
    """Export step-level plot data to CSV/JSON."""
    result_df = results['result_df']
    report = generate_full_report(result_df, product_steps=product_steps)
    
    # Build step-level series
    series = build_step_level_series(report, product_steps, calibration_report_dict)
    
    # Determine format from extension
    output_path_obj = Path(output_path)
    if output_path_obj.suffix.lower() == '.csv':
        export_step_level_csv(series, output_path)
        print(f"\n✅ Exported step-level plot data to {output_path} (CSV)")
    else:
        export_step_level_json(series, output_path)
        print(f"\n✅ Exported step-level plot data to {output_path} (JSON)")
    
    print(f"   Contains {len(series)} steps with predicted failure rates")
    if calibration_report_dict:
        print(f"   Includes observed failure rates and deltas")
    print(f"   Import into Sheets, Tableau, or your notebook for visualization")


def export_trajectory_plot_data(result_df, persona_name: str, variant: str, product_steps: Dict, output_path: str):
    """Export trajectory plot data for a specific persona × variant."""
    # Find persona and variant
    persona_row = None
    for idx, row in result_df.iterrows():
        pname = str(row['persona_name']).split('\n')[0] if '\n' in str(row['persona_name']) else str(row['persona_name'])
        if persona_name in pname:
            persona_row = row
            break
    
    if persona_row is None:
        print(f"❌ Persona '{persona_name}' not found")
        return
    
    trajectories = persona_row.get('trajectories', [])
    traj = next((t for t in trajectories if t.get('variant') == variant), None)
    
    if not traj:
        print(f"❌ Variant '{variant}' not found for persona '{persona_name}'")
        return
    
    # Build trajectory series
    series = build_trajectory_series(traj, product_steps)
    
    # Determine format from extension
    output_path_obj = Path(output_path)
    if output_path_obj.suffix.lower() == '.csv':
        export_trajectory_csv(series, output_path)
        print(f"\n✅ Exported trajectory plot data to {output_path} (CSV)")
    else:
        export_trajectory_json(series, output_path)
        print(f"\n✅ Exported trajectory plot data to {output_path} (JSON)")
    
    print(f"   Contains {len(series)} steps for {persona_name} × {variant}")
    print(f"   Includes state variables (energy, value, risk, effort, control) and costs")
    print(f"   Import into Sheets, Tableau, or your notebook for visualization")


def print_narrative_summary(results: Dict, product_steps: Dict, calibration_report_dict: Optional[Dict] = None):
    """Print narrative summary for founders/PMs."""
    result_df = results['result_df']
    report = generate_full_report(result_df, product_steps=product_steps)
    
    narrative = generate_narrative_summary(
        report,
        product_steps,
        calibration_report_dict,
        result_df
    )
    
    print("\n" + "=" * 80)
    print("📝 NARRATIVE SUMMARY")
    print("=" * 80)
    print()
    print(narrative)
    print()


def print_simulation_summary(results: Dict, product_steps: Dict):
    """Print PM-friendly summary matching design doc format."""
    result_df = results['result_df']
    total_trajectories = len(result_df) * 7  # 7 variants per persona
    
    print("\n" + "=" * 80)
    print("📊 FAILURE MODE ANALYSIS")
    print("   (WHY they dropped at step t - before WHO)")
    print("=" * 80)
    print()
    
    # Generate report
    report = generate_full_report(result_df, product_steps=product_steps)
    
    # Parse and reformat to match design doc language
    report_text = report['report_text']
    
    # Replace cost labels to match design doc
    report_text = report_text.replace("System 2 fatigue", "System 2 fatigue")
    report_text = report_text.replace("Low ability", "Low ability")
    report_text = report_text.replace("Loss aversion", "Loss aversion")
    report_text = report_text.replace("Temporal discounting", "Temporal discounting")
    
    print(report_text)
    
    # Persona summary
    print("\n" + "=" * 80)
    print("👥 PERSONA SUMMARY")
    print("=" * 80)
    
    for _, row in result_df.iterrows():
        persona_name = str(row['persona_name']).split('\n')[0] if '\n' in str(row['persona_name']) else str(row['persona_name'])
        persona_desc = str(row['persona_description']).split('\n')[0] if '\n' in str(row['persona_description']) else str(row['persona_description'])
        print(f"\n{persona_name}: {persona_desc}")
        print(f"   Exit: {row['dominant_exit_step']} | Reason: {row['dominant_failure_reason']}")
        print(f"   Completed: {row['variants_completed']}/{row['variants_total']} variants")
        print(f"   Consistency: {row['consistency_score']:.2f}")


def print_calibration_report(results: Dict, product_steps: Dict, observed_funnel_path: str) -> Optional[Dict]:
    """Load observed funnel and print calibration report. Returns calibration_report dict if available."""
    # Load observed funnel
    with open(observed_funnel_path, 'r') as f:
        observed_data = json.load(f)
    
    observed_funnel = ObservedFunnel.from_dict(observed_data)
    
    # Get scenario result (from generate_full_report)
    result_df = results['result_df']
    report = generate_full_report(result_df, product_steps=product_steps)
    
    # Add result_df to report for fallback computation
    report['result_df'] = result_df
    
    # Compare
    calibration_report = compare_scenario_to_observed(
        report,
        observed_funnel,
        product_steps
    )
    
    # Print calibration report
    print(format_calibration_report(calibration_report))
    
    # Get tuning suggestions
    suggestions = suggest_coefficient_adjustments(
        report,
        observed_funnel,
        product_steps
    )
    
    # Print tuning suggestions
    if suggestions:
        print(format_tuning_suggestions(suggestions))
    
    # Return calibration_report as dict for visualization
    return calibration_report.to_dict()


def main():
    parser = argparse.ArgumentParser(
        description="DropSim: Behavioral Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run fintech preset
  python dropsim_cli.py simulate --preset fintech
  
  # Run custom scenario
  python dropsim_cli.py simulate --scenario-file examples/fintech_onboarding.json
  
  # View specific persona × variant trace
  python dropsim_cli.py simulate --preset fintech \\
    --persona-name "Salaried_Tier2_Cautious" \\
    --variant tired_commuter
  
  # Export to JSON
  python dropsim_cli.py simulate --preset fintech --export fintech_traces.json
  
  # Calibration with observed funnel
  python dropsim_cli.py simulate --preset fintech \
    --observed-funnel examples/fintech_observed_funnel.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # simulate command
    sim_parser = subparsers.add_parser('simulate', help='Run behavioral simulation')
    
    # simulate-lite command
    lite_parser = subparsers.add_parser('simulate-lite', help='Run simulation with lite input (human-friendly labels)')
    
    # ingest-fintech command
    ingest_parser = subparsers.add_parser('ingest-fintech', help='Extract scenario from product text using LLM and run simulation')
    
    # wizard-fintech command
    wizard_parser = subparsers.add_parser('wizard-fintech', help='Wizard mode: provide URL, screenshots, notes and get simulation automatically')
    sim_parser.add_argument('--preset', type=str, choices=['fintech'], help='Use preset scenario')
    sim_parser.add_argument('--scenario-file', type=str, help='Path to scenario JSON file')
    sim_parser.add_argument('--persona-name', type=str, help='View trace for specific persona')
    sim_parser.add_argument('--variant', type=str, help='State variant name for trace')
    sim_parser.add_argument('--observed-funnel', type=str, help='Path to observed funnel JSON file for calibration')
    sim_parser.add_argument('--target-group', type=str, help='Path to target group filter JSON file')
    sim_parser.add_argument('--export', type=str, help='Export traces to JSON file')
    sim_parser.add_argument('--export-plot-data', type=str, help='Export step-level plot data to CSV/JSON')
    sim_parser.add_argument('--trace-plot-data', type=str, help='Export trajectory plot data to CSV/JSON (requires --persona-name and --variant)')
    
    # simulate-lite arguments
    lite_parser.add_argument('--lite-scenario-file', type=str, required=True, help='Path to lite scenario JSON file')
    lite_parser.add_argument('--persona-name', type=str, help='View trace for specific persona')
    lite_parser.add_argument('--variant', type=str, help='State variant name for trace')
    lite_parser.add_argument('--observed-funnel', type=str, help='Path to observed funnel JSON file for calibration')
    lite_parser.add_argument('--target-group', type=str, help='Path to target group filter JSON file')
    lite_parser.add_argument('--export', type=str, help='Export traces to JSON file')
    lite_parser.add_argument('--export-plot-data', type=str, help='Export step-level plot data to CSV/JSON')
    lite_parser.add_argument('--trace-plot-data', type=str, help='Export trajectory plot data to CSV/JSON (requires --persona-name and --variant)')
    
    # ingest-fintech arguments
    ingest_parser.add_argument('--product-text-file', type=str, required=True, help='Path to product description text file')
    ingest_parser.add_argument('--persona-notes-file', type=str, help='Path to optional persona notes file')
    ingest_parser.add_argument('--target-notes-file', type=str, help='Path to optional target group notes file')
    ingest_parser.add_argument('--openai-api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    ingest_parser.add_argument('--llm-model', type=str, default='gpt-4o-mini', help='LLM model name (default: gpt-4o-mini)')
    ingest_parser.add_argument('--export-lite-scenario', type=str, help='Export inferred lite scenario to JSON')
    ingest_parser.add_argument('--export-scenario', type=str, help='Export full scenario to JSON')
    ingest_parser.add_argument('--observed-funnel', type=str, help='Path to observed funnel JSON file for calibration')
    ingest_parser.add_argument('--export-plot-data', type=str, help='Export step-level plot data to CSV/JSON')
    ingest_parser.add_argument('--export', type=str, help='Export traces to JSON file')
    ingest_parser.add_argument('--verbose', action='store_true', help='Print debug information')
    ingest_parser.add_argument('--dry-run', action='store_true', help='Only extract scenario, do not run simulation')
    
    # wizard-fintech arguments
    wizard_parser.add_argument('--product-url', type=str, help='Product URL (for reference, not crawled)')
    wizard_parser.add_argument('--product-text-file', type=str, help='Path to product description text file')
    wizard_parser.add_argument('--screenshot-text-file', type=str, help='Path to screenshot text file (OCR output, separated by --- or blank lines)')
    wizard_parser.add_argument('--persona-notes-file', type=str, help='Path to persona notes file')
    wizard_parser.add_argument('--target-notes-file', type=str, help='Path to target group notes file')
    wizard_parser.add_argument('--openai-api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    wizard_parser.add_argument('--llm-model', type=str, default='gpt-4o-mini', help='LLM model name (default: gpt-4o-mini)')
    wizard_parser.add_argument('--firecrawl-api-key', type=str, help='Firecrawl API key for URL fetching (or set FIRECRAWL_API_KEY env var)')
    wizard_parser.add_argument('--observed-funnel', type=str, help='Path to observed funnel JSON file for calibration')
    wizard_parser.add_argument('--export-lite-scenario', type=str, help='Export inferred lite scenario to JSON')
    wizard_parser.add_argument('--export', type=str, help='Export traces to JSON file')
    wizard_parser.add_argument('--export-plot-data', type=str, help='Export step-level plot data to CSV/JSON')
    wizard_parser.add_argument('--n-personas', type=int, default=1000, help='Number of personas to load from database (default: 1000)')
    wizard_parser.add_argument('--use-database-personas', action='store_true', default=True, help='Use personas from database (default: True)')
    wizard_parser.add_argument('--use-preset-personas', action='store_true', help='Use preset personas instead of database')
    wizard_parser.add_argument('--verbose', action='store_true', help='Print debug information')
    
    args = parser.parse_args()
    
    if args.command not in ['simulate', 'simulate-lite', 'ingest-fintech', 'wizard-fintech']:
        parser.print_help()
        sys.exit(1)
    
    # Handle wizard-fintech command first (before simulate checks)
    if args.command == 'wizard-fintech':
        print("\n" + "=" * 80)
        print("🧙 DropSim Fintech Wizard")
        print("=" * 80)
        
        # Collect inputs
        product_url = args.product_url
        product_text = None
        if args.product_text_file:
            with open(args.product_text_file, 'r') as f:
                product_text = f.read()
        
        screenshot_texts = None
        if args.screenshot_text_file:
            with open(args.screenshot_text_file, 'r') as f:
                screenshot_content = f.read()
                # Split by --- or double newlines
                if '---' in screenshot_content:
                    screenshot_texts = [s.strip() for s in screenshot_content.split('---') if s.strip()]
                else:
                    screenshot_texts = [s.strip() for s in screenshot_content.split('\n\n') if s.strip()]
        
        persona_notes = None
        if args.persona_notes_file:
            with open(args.persona_notes_file, 'r') as f:
                persona_notes = f.read()
        
        target_group_notes = None
        if args.target_notes_file:
            with open(args.target_notes_file, 'r') as f:
                target_group_notes = f.read()
        
        # Validate at least one input
        if not product_url and not product_text and not screenshot_texts:
            print("❌ Error: At least one of --product-url, --product-text-file, or --screenshot-text-file must be provided")
            sys.exit(1)
        
        # Initialize LLM client
        api_key = args.openai_api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ Error: OpenAI API key required")
            print("   Set --openai-api-key or OPENAI_API_KEY environment variable")
            sys.exit(1)
        
        llm_client = OpenAILLMClient(api_key=api_key, model=args.llm_model)
        
        # Get Firecrawl API key if provided
        firecrawl_key = args.firecrawl_api_key or os.environ.get('FIRECRAWL_API_KEY')
        if product_url and firecrawl_key:
            print(f"\n🌐 Fetching content from {product_url} using Firecrawl...")
        
        # Build wizard input
        wizard_input = WizardInput(
            product_url=product_url,
            product_text=product_text,
            screenshot_texts=screenshot_texts,
            persona_notes=persona_notes,
            target_group_notes=target_group_notes
        )
        
        # Load observed funnel if provided
        observed_funnel = None
        if args.observed_funnel:
            with open(args.observed_funnel, 'r') as f:
                funnel_data = json.load(f)
                observed_funnel = ObservedFunnel.from_dict(funnel_data)
        
        # Determine persona source
        use_database = args.use_database_personas and not args.use_preset_personas
        
        # Run wizard
        print("\n🧙 Running wizard...")
        try:
            wizard_result = run_fintech_wizard(
                wizard_input,
                llm_client,
                simulate=True,
                observed_funnel=observed_funnel,
                verbose=args.verbose,
                firecrawl_api_key=firecrawl_key,
                n_personas=args.n_personas,
                use_database_personas=use_database
            )
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            print("\n💡 Suggestions:")
            print("   - Ensure at least one input is provided (product text, screenshots, or URL)")
            print("   - Check that input files are readable")
            print("   - Verify OpenAI API key is valid")
            sys.exit(1)
        
        # Print wizard summary
        print("\n" + "=" * 80)
        print("📋 WIZARD SUMMARY")
        print("=" * 80)
        
        product_label = product_url if product_url else ("Custom text only" if product_text else "Screenshots only")
        print(f"Product: {product_label}")
        
        if wizard_result.get('fintech_archetype'):
            print(f"Fintech archetype: {wizard_result['fintech_archetype']}")
        
        lite_scenario = wizard_result['lite_scenario']
        print(f"Personas inferred: {len(lite_scenario.personas)}")
        for p in lite_scenario.personas:
            print(f"  - {p.name}: {p.sec} SEC, {p.urban_rural}, {p.digital_skill} digital skill, {p.intent} intent")
        
        print(f"\nSteps inferred: {len(lite_scenario.steps)}")
        for s in lite_scenario.steps:
            print(f"  - {s.name} ({s.type})")
        
        target_group = wizard_result.get('target_group')
        if target_group:
            tg_dict = target_group.to_dict()
            print(f"\nTarget group: {tg_dict if tg_dict else 'none'}")
        else:
            print("\nTarget group: none")
        
        print(f"\nLLM confidence: {wizard_result.get('confidence', 'unknown')}")
        
        # Export lite scenario if requested
        if args.export_lite_scenario:
            lite_dict = {
                'product_type': lite_scenario.product_type,
                'personas': [p.__dict__ for p in lite_scenario.personas],
                'steps': [s.__dict__ for s in lite_scenario.steps]
            }
            if wizard_result.get('fintech_archetype'):
                lite_dict['fintech_archetype'] = wizard_result['fintech_archetype']
            with open(args.export_lite_scenario, 'w') as f:
                json.dump(lite_dict, f, indent=2)
            print(f"\n✅ Exported lite scenario to {args.export_lite_scenario}")
        
        # Print simulation results
        if 'scenario_result' in wizard_result:
            scenario_result = wizard_result['scenario_result']
            product_steps = scenario_result['product_steps']
            
            print("\n" + "=" * 80)
            print("🚀 SIMULATION RESULTS")
            print("=" * 80)
            
            # Print step-level summary
            print_simulation_summary({
                'result_df': scenario_result['result_df'],
                'full_report': scenario_result['full_report'],
                'personas': scenario_result['personas'],
                'product_steps': product_steps
            }, product_steps)
            
            # Calibration if provided
            calibration_report_dict = None
            if 'calibration_report' in wizard_result:
                calibration_report_dict = wizard_result['calibration_report']
                print_calibration_report(
                    {
                        'result_df': scenario_result['result_df'],
                        'full_report': scenario_result['full_report'],
                        'product_steps': product_steps
                    },
                    product_steps,
                    args.observed_funnel
                )
            
            # Export plot data
            if args.export_plot_data:
                export_plot_data(
                    {
                        'result_df': scenario_result['result_df'],
                        'full_report': scenario_result['full_report'],
                        'product_steps': product_steps
                    },
                    product_steps,
                    args.export_plot_data,
                    calibration_report_dict
                )
            
            # Export traces
            if args.export:
                export_fintech_json(
                    scenario_result['personas'],
                    scenario_result['result_df'],
                    scenario_result['state_variants'],
                    product_steps,
                    args.export
                )
            
            # Print narrative summary
            if 'narrative_summary' in wizard_result:
                print("\n" + "=" * 80)
                print("📝 NARRATIVE SUMMARY")
                print("=" * 80)
                print(wizard_result['narrative_summary'])
            
            # Next step suggestion
            if args.export_lite_scenario:
                print("\n" + "=" * 80)
                print("💡 NEXT STEP")
                print("=" * 80)
                print(f"Review and optionally edit the generated LiteScenario JSON at {args.export_lite_scenario}")
                print("before sharing with your team or re-running with simulate-lite.")
        
        print("\n" + "=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)
        return
    
    # Handle ingest-fintech command
    if args.command == 'ingest-fintech':
        print("\n" + "=" * 80)
        print("🤖 DropSim LLM Ingest: Fintech Product")
        print("=" * 80)
        
        # Load product text
        with open(args.product_text_file, 'r') as f:
            product_text = f.read()
        
        # Load optional notes
        persona_notes = None
        if args.persona_notes_file:
            with open(args.persona_notes_file, 'r') as f:
                persona_notes = f.read()
        
        target_group_notes = None
        if args.target_notes_file:
            with open(args.target_notes_file, 'r') as f:
                target_group_notes = f.read()
        
        # Initialize LLM client
        api_key = args.openai_api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ Error: OpenAI API key required")
            print("   Set --openai-api-key or OPENAI_API_KEY environment variable")
            sys.exit(1)
        
        llm_client = OpenAILLMClient(api_key=api_key, model=args.llm_model)
        
        # Extract scenario from LLM
        print("\n🤖 Extracting scenario from product description using LLM...")
        try:
            lite_scenario, target_group, fintech_archetype = infer_lite_scenario_and_target_from_llm(
                product_text,
                persona_notes,
                target_group_notes,
                llm_client,
                verbose=args.verbose,
                dry_run=args.dry_run
            )
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            print("\n💡 Suggestions:")
            print("   - Check that product text is clear and detailed")
            print("   - Try adding --persona-notes-file with explicit persona descriptions")
            print("   - Verify OpenAI API key is valid")
            print("   - Ensure product description includes onboarding flow steps and user types")
            sys.exit(1)
        
        # Print inferred scenario summary
        print("\n" + "=" * 80)
        print("📋 INFERRED SCENARIO")
        print("=" * 80)
        if fintech_archetype:
            print(f"Fintech archetype: {fintech_archetype}")
        print(f"\nInferred personas: {len(lite_scenario.personas)}")
        for p in lite_scenario.personas:
            print(f"  - {p.name}: {p.sec} SEC, {p.urban_rural}, {p.digital_skill} digital skill, {p.intent} intent")
        print(f"\nInferred steps: {len(lite_scenario.steps)}")
        for s in lite_scenario.steps:
            print(f"  - {s.name} ({s.type})")
        
        if target_group:
            tg_dict = target_group.to_dict()
            print(f"\nTarget group filters: {tg_dict if tg_dict else 'none'}")
        else:
            print("\nTarget group filters: none")
        
        # Dry run mode - exit early
        if args.dry_run:
            print("\n" + "=" * 80)
            print("✅ DRY RUN COMPLETE (No simulation run)")
            print("=" * 80)
            if args.export_lite_scenario:
                print(f"✅ Exported lite scenario to {args.export_lite_scenario}")
            return
        
        # Export lite scenario if requested
        if args.export_lite_scenario:
            lite_dict = {
                'product_type': lite_scenario.product_type,
                'personas': [p.__dict__ for p in lite_scenario.personas],
                'steps': [s.__dict__ for s in lite_scenario.steps]
            }
            if fintech_archetype:
                lite_dict['fintech_archetype'] = fintech_archetype
            with open(args.export_lite_scenario, 'w') as f:
                json.dump(lite_dict, f, indent=2)
            print(f"\n✅ Exported lite scenario to {args.export_lite_scenario}")
        
        # Convert to full scenario
        scenario = lite_to_scenario(lite_scenario)
        
        # Export full scenario if requested
        if args.export_scenario:
            with open(args.export_scenario, 'w') as f:
                json.dump(scenario, f, indent=2)
            print(f"✅ Exported full scenario to {args.export_scenario}")
        
        # Run simulation
        print("\n" + "=" * 80)
        print("🚀 Running Simulation on Inferred Scenario")
        print("=" * 80)
        
        results = run_scenario_simulation(scenario, verbose=True, target_group=target_group)
        
        # Print summary
        print_simulation_summary(results, results['product_steps'])
        
        # Calibration if observed funnel provided
        calibration_report_dict = None
        if args.observed_funnel:
            calibration_report_dict = print_calibration_report(results, results['product_steps'], args.observed_funnel)
        
        # Export plot data
        if args.export_plot_data:
            export_plot_data(results, results['product_steps'], args.export_plot_data, calibration_report_dict)
        
        # Export
        if args.export:
            export_fintech_json(
                results['personas'],
                results['result_df'],
                results['state_variants'],
                results['product_steps'],
                args.export
            )
        
        # Print narrative summary
        print_narrative_summary(results, results['product_steps'], calibration_report_dict)
        
        print("\n" + "=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)
        return
    
    # Handle simulate-lite command
    if args.command == 'simulate-lite':
        print("\n" + "=" * 80)
        print("🚀 DropSim: Lite Input Mode (Human-Friendly Labels)")
        print("=" * 80)
        print(f"   Lite scenario: {args.lite_scenario_file}")
        print("=" * 80)
        
        # Load lite scenario
        lite_scenario = load_lite_scenario(args.lite_scenario_file)
        print(f"\n📋 Loaded lite scenario:")
        print(f"   Product type: {lite_scenario.product_type}")
        print(f"   Personas: {len(lite_scenario.personas)}")
        print(f"   Steps: {len(lite_scenario.steps)}")
        
        # Convert to full scenario
        scenario = lite_to_scenario(lite_scenario)
        print(f"\n🔄 Converted to full scenario configuration")
        
        # Load target group if provided
        target_group = None
        if args.target_group:
            target_group = load_target_group(args.target_group)
            print(f"\n🎯 Target group filter: {args.target_group}")
            print(f"   Filters: {target_group.to_dict()}")
            # Filter personas in scenario
            from dropsim_target_filter import filter_personas_by_target
            original_count = len(scenario.get('personas', []))
            scenario['personas'] = filter_personas_by_target(
                scenario.get('personas', []),
                target_group
            )
            filtered_count = len(scenario['personas'])
            print(f"   Matched: {filtered_count} of {original_count} personas")
            
            if filtered_count == 0:
                print("⚠️  WARNING: No personas matched the target group filters.")
                print("   Returning empty results.")
                # Return empty results structure
                return
        
        # Run simulation
        results = run_scenario_simulation(scenario, verbose=True, target_group=target_group)
        
        # Print summary
        print_simulation_summary(results, results['product_steps'])
        
        # Calibration if observed funnel provided
        calibration_report_dict = None
        if args.observed_funnel:
            calibration_report_dict = print_calibration_report(results, results['product_steps'], args.observed_funnel)
        
        # Drill-down trace
        if args.persona_name:
            variant = args.variant if args.variant else 'fresh_motivated'
            print_fintech_trace(
                results['result_df'],
                args.persona_name,
                variant,
                results['product_steps']
            )
        
        # Export plot data
        if args.export_plot_data:
            export_plot_data(results, results['product_steps'], args.export_plot_data, calibration_report_dict)
        
        # Export trajectory plot data
        if args.trace_plot_data:
            if not args.persona_name:
                print("⚠️  Warning: --trace-plot-data requires --persona-name and --variant")
            else:
                variant = args.variant if args.variant else 'fresh_motivated'
                export_trajectory_plot_data(
                    results['result_df'],
                    args.persona_name,
                    variant,
                    results['product_steps'],
                    args.trace_plot_data
                )
        
        # Export
        if args.export:
            export_fintech_json(
                results['personas'],
                results['result_df'],
                results['state_variants'],
                results['product_steps'],
                args.export
            )
        
        # Print narrative summary
        print_narrative_summary(results, results['product_steps'], calibration_report_dict)
        
        print("\n" + "=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)
        return
    
    # Handle regular simulate command
    # Validate arguments
    if not args.preset and not args.scenario_file:
        print("❌ Error: Must specify either --preset or --scenario-file")
        sys.exit(1)
    
    if args.preset and args.scenario_file:
        print("❌ Error: Cannot specify both --preset and --scenario-file")
        sys.exit(1)
    
    # Run simulation
    if args.preset == 'fintech':
        print("\n" + "=" * 80)
        print("🏦 DropSim: Fintech Onboarding Simulation")
        print("=" * 80)
        
        # Load fintech preset
        personas, state_variants, product_steps = get_default_fintech_scenario()
        
        # Load target group if provided
        target_group = None
        if args.target_group:
            target_group = load_target_group(args.target_group)
            print(f"\n🎯 Target group filter: {args.target_group}")
            print(f"   Filters: {target_group.to_dict()}")
        
        # Run simulation
        result_df = run_fintech_demo_simulation(
            personas, state_variants, product_steps, verbose=True,
            target_group=target_group.to_dict() if target_group else None
        )
        
        results = {
            'result_df': result_df,
            'personas': personas,
            'state_variants': state_variants,
            'product_steps': product_steps
        }
        
        # Print summary
        print_simulation_summary(results, product_steps)
        
        # Calibration if observed funnel provided
        calibration_report_dict = None
        if args.observed_funnel:
            calibration_report_dict = print_calibration_report(results, product_steps, args.observed_funnel)
        
        # Drill-down trace
        if args.persona_name:
            variant = args.variant if args.variant else 'fresh_motivated'
            print_fintech_trace(result_df, args.persona_name, variant, product_steps)
        
        # Export plot data
        if args.export_plot_data:
            export_plot_data(results, product_steps, args.export_plot_data, calibration_report_dict)
        
        # Export trajectory plot data
        if args.trace_plot_data:
            if not args.persona_name:
                print("⚠️  Warning: --trace-plot-data requires --persona-name and --variant")
            else:
                variant = args.variant if args.variant else 'fresh_motivated'
                export_trajectory_plot_data(result_df, args.persona_name, variant, product_steps, args.trace_plot_data)
        
        # Export
        if args.export:
            export_fintech_json(personas, result_df, state_variants, product_steps, args.export)
        
        # Print narrative summary
        print_narrative_summary(results, product_steps, calibration_report_dict)
    
    elif args.scenario_file:
        print("\n" + "=" * 80)
        print(f"📊 DropSim: Custom Scenario Simulation")
        print(f"   Scenario: {args.scenario_file}")
        print("=" * 80)
        
        # Load scenario
        scenario = load_scenario_from_json(args.scenario_file)
        
        # Load target group if provided
        target_group = None
        if args.target_group:
            target_group = load_target_group(args.target_group)
            print(f"\n🎯 Target group filter: {args.target_group}")
            print(f"   Filters: {target_group.to_dict()}")
            # Filter personas in scenario
            from dropsim_target_filter import filter_personas_by_target
            scenario['personas'] = filter_personas_by_target(
                scenario.get('personas', []),
                target_group
            )
            if len(scenario['personas']) == 0:
                print("⚠️  WARNING: No personas matched the target group filters.")
                print("   Returning empty results.")
                # Return empty results structure
                return
        
        # Run simulation
        results = run_scenario_simulation(scenario, verbose=True)
        
        # Print summary
        print_simulation_summary(results, results['product_steps'])
        
        # Calibration if observed funnel provided
        calibration_report_dict = None
        if args.observed_funnel:
            calibration_report_dict = print_calibration_report(results, results['product_steps'], args.observed_funnel)
        
        # Drill-down trace
        if args.persona_name:
            variant = args.variant if args.variant else 'fresh_motivated'
            print_fintech_trace(
                results['result_df'],
                args.persona_name,
                variant,
                results['product_steps']
            )
        
        # Export plot data
        if args.export_plot_data:
            export_plot_data(results, results['product_steps'], args.export_plot_data, calibration_report_dict)
        
        # Export trajectory plot data
        if args.trace_plot_data:
            if not args.persona_name:
                print("⚠️  Warning: --trace-plot-data requires --persona-name and --variant")
            else:
                variant = args.variant if args.variant else 'fresh_motivated'
                export_trajectory_plot_data(
                    results['result_df'],
                    args.persona_name,
                    variant,
                    results['product_steps'],
                    args.trace_plot_data
                )
        
        # Export
        if args.export:
            export_fintech_json(
                results['personas'],
                results['result_df'],
                results['state_variants'],
                results['product_steps'],
                args.export
            )
        
        # Print narrative summary
        print_narrative_summary(results, results['product_steps'], calibration_report_dict)
    
    print("\n" + "=" * 80)
    print("✅ SIMULATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

