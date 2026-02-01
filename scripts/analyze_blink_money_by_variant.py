#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Analyze Blink Money results by state variant.
Generate separate results for each of the 7 state variants.
"""

import json
from collections import defaultdict

STATE_VARIANTS = [
    "fresh_motivated",
    "tired_commuter",
    "distrustful_arrival",
    "browsing_casually",
    "urgent_need",
    "price_sensitive",
    "tech_savvy_optimistic"
]

def extract_variant_from_persona_id(persona_id: str) -> str:
    """Extract variant name from persona_id (format: index_variant_name)."""
    # Try each variant name - check if it appears in persona_id
    for variant in STATE_VARIANTS:
        # Check if variant name is at the end of persona_id
        if persona_id.endswith(variant):
            return variant
        # Also check if it's after an underscore (format: index_variant_name)
        if f'_{variant}' in persona_id:
            return variant
    return None

def analyze_by_variant(data_file: str):
    """Analyze results by state variant."""
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    traces = data.get('decision_traces', [])
    print(f"Total traces: {len(traces):,}")
    
    # Group traces by variant
    traces_by_variant = defaultdict(list)
    unknown_variants = []
    
    for trace in traces:
        persona_id = trace.get('persona_id', '')
        variant = extract_variant_from_persona_id(persona_id)
        if variant:
            traces_by_variant[variant].append(trace)
        else:
            unknown_variants.append(trace)
    
    print(f"\nTraces by variant:")
    for variant in STATE_VARIANTS:
        count = len(traces_by_variant[variant])
        print(f"  {variant}: {count:,} traces")
    if unknown_variants:
        print(f"  Unknown: {len(unknown_variants)} traces")
    
    # Analyze each variant
    results_by_variant = {}
    
    for variant in STATE_VARIANTS:
        variant_traces = traces_by_variant[variant]
        if not variant_traces:
            continue
        
        # Group by persona (each persona appears once per variant)
        personas = set()
        for trace in variant_traces:
            # Extract base persona_id (remove variant suffix)
            persona_id = trace.get('persona_id', '')
            base_id = persona_id.rsplit('_', 1)[0] if '_' in persona_id else persona_id
            personas.add(base_id)
        
        # Calculate metrics
        total_personas = len(personas)
        
        # Step progression
        step_stats = defaultdict(lambda: {'total': 0, 'continue': 0, 'drop': 0})
        for trace in variant_traces:
            step_id = trace.get('step_id', 'unknown')
            decision = trace.get('decision')
            step_stats[step_id]['total'] += 1
            if decision == 'CONTINUE':
                step_stats[step_id]['continue'] += 1
            elif decision == 'DROP':
                step_stats[step_id]['drop'] += 1
        
        # Calculate completion rate (personas that reach final step with CONTINUE)
        # Find personas that completed
        personas_completed = set()
        personas_reached_step = defaultdict(set)
        
        for trace in variant_traces:
            persona_id = trace.get('persona_id', '')
            base_id = persona_id.rsplit('_', 1)[0] if '_' in persona_id else persona_id
            step_id = trace.get('step_id', 'unknown')
            decision = trace.get('decision')
            
            personas_reached_step[step_id].add(base_id)
            
            # Check if this is the last step for this persona
            # (We'll determine completion by checking if they reached step 6 and continued)
            if step_id == 'Final Confirmation' and decision == 'CONTINUE':
                personas_completed.add(base_id)
        
        # Alternatively, count unique personas reaching each step
        steps_list = sorted(step_stats.keys(), key=lambda x: list(step_stats.keys()).index(x) if x in step_stats else 999)
        
        # Completion: personas that reached final step and continued
        completion_count = len(personas_completed)
        completion_rate = completion_count / total_personas if total_personas > 0 else 0
        
        # Step-by-step drop rates
        step_drop_rates = {}
        step_progression = {}
        for step_id, stats in step_stats.items():
            drop_rate = stats['drop'] / stats['total'] if stats['total'] > 0 else 0
            step_drop_rates[step_id] = drop_rate
            step_progression[step_id] = {
                'reached': stats['total'],
                'continued': stats['continue'],
                'dropped': stats['drop'],
                'drop_rate': drop_rate
            }
        
        # Force attribution for drops
        drop_forces = defaultdict(list)
        for trace in variant_traces:
            if trace.get('decision') == 'DROP' and trace.get('attribution'):
                attr = trace['attribution']
                shap = attr.get('shap_values', {})
                for force, value in shap.items():
                    drop_forces[force].append(abs(value))
        
        drop_stats = {}
        for force, values in drop_forces.items():
            drop_stats[force] = {
                'mean': sum(values) / len(values) if values else 0,
                'total': sum(values),
                'count': len(values)
            }
        
        drop_total = sum(stats['total'] for stats in drop_stats.values())
        drop_percentages = {}
        if drop_total > 0:
            drop_percentages = {
                force: (stats['total']/drop_total)*100
                for force, stats in drop_stats.items()
            }
        
        results_by_variant[variant] = {
            'total_personas': total_personas,
            'completion_count': completion_count,
            'completion_rate': completion_rate,
            'step_progression': step_progression,
            'step_drop_rates': step_drop_rates,
            'drop_force_percentages': drop_percentages,
            'total_traces': len(variant_traces)
        }
    
    # Generate report
    report_lines = []
    report_lines.append("# Blink Money: Results by State Variant")
    report_lines.append("")
    report_lines.append("**Analysis Date:** January 2025")
    report_lines.append("**Sample Size:** 1,000 personas per variant")
    report_lines.append("**Product:** Blink Money (7-step onboarding)")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    for variant in STATE_VARIANTS:
        if variant not in results_by_variant:
            continue
        
        results = results_by_variant[variant]
        report_lines.append(f"## Variant: {variant.replace('_', ' ').title()}")
        report_lines.append("")
        report_lines.append(f"**Total Personas:** {results['total_personas']:,}")
        report_lines.append(f"**Completion Rate:** {results['completion_rate']:.2%} ({results['completion_count']} completed)")
        report_lines.append(f"**Total Traces:** {results['total_traces']:,}")
        report_lines.append("")
        
        # Step progression
        report_lines.append("### Step Progression")
        report_lines.append("")
        report_lines.append("| Step | Reached | Continued | Dropped | Drop Rate |")
        report_lines.append("|------|---------|-----------|---------|-----------|")
        
        step_order = ['Smart Credit against Mutual Funds', 'Check Your Eligibility - Mobile Number', 
                     'Check Limit - PAN and DOB', 'OTP Verification', 'Bank Account Linking',
                     'Eligibility Results', 'Final Confirmation']
        
        for step_id in step_order:
            if step_id in results['step_progression']:
                prog = results['step_progression'][step_id]
                report_lines.append(f"| {step_id} | {prog['reached']} | {prog['continued']} | {prog['dropped']} | {prog['drop_rate']:.1%} |")
        
        report_lines.append("")
        
        # Force attribution
        if results['drop_force_percentages']:
            report_lines.append("### Drop Force Attribution")
            report_lines.append("")
            sorted_forces = sorted(results['drop_force_percentages'].items(), key=lambda x: x[1], reverse=True)
            for force, pct in sorted_forces[:5]:
                report_lines.append(f"- **{force.capitalize()}:** {pct:.1f}%")
            report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
    
    # Comparison table
    report_lines.append("## Comparison Across Variants")
    report_lines.append("")
    report_lines.append("| Variant | Completion Rate | Total Personas | Top Drop Force |")
    report_lines.append("|---------|----------------|----------------|----------------|")
    
    for variant in STATE_VARIANTS:
        if variant not in results_by_variant:
            continue
        results = results_by_variant[variant]
        top_force = max(results['drop_force_percentages'].items(), key=lambda x: x[1])[0] if results['drop_force_percentages'] else 'N/A'
        report_lines.append(f"| {variant.replace('_', ' ').title()} | {results['completion_rate']:.2%} | {results['total_personas']:,} | {top_force.capitalize()} ({results['drop_force_percentages'].get(top_force, 0):.1f}%) |")
    
    report_lines.append("")
    report_lines.append("---")
    
    # Save report
    report_text = "\n".join(report_lines)
    output_file = 'BLINK_MONEY_RESULTS_BY_VARIANT.md'
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(f"\n✅ Report generated: {output_file}")
    
    # Also save JSON for programmatic access
    json_output = {
        variant: {
            'completion_rate': results['completion_rate'],
            'total_personas': results['total_personas'],
            'completion_count': results['completion_count'],
            'step_progression': results['step_progression'],
            'drop_force_percentages': results['drop_force_percentages']
        }
        for variant, results in results_by_variant.items()
    }
    
    json_file = 'blink_money_results_by_variant.json'
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2)
    
    print(f"✅ JSON data saved: {json_file}")
    
    return results_by_variant

if __name__ == "__main__":
    analyze_by_variant('blink_money_pipeline_result.json')
