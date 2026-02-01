"""
Credigo Report Generator

Generates founder-ready markdown report comparing Credigo against benchmarks.
"""

from typing import Dict, List
from collections import defaultdict
import json


def generate_credigo_report(
    unified_ledger: Dict,
    comparative_results: Dict,
    sensitivity_results: List[Dict],
    output_dir: str = "."
) -> str:
    """
    Generate founder-ready markdown report.
    """
    lines = []
    
    # Header
    lines.append("# Credigo vs India's Best Onboarding Flows — Decision Analysis")
    lines.append("")
    lines.append("**Analysis Date:** Generated from decision trace comparison")
    lines.append("**Methodology:** Fixed personas (100) through identical simulation pipeline")
    lines.append("**Benchmarks:** Zerodha, Groww, CRED")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Load trace data for detailed analysis
    from sensitivity_engine.decision_trace_extended import SensitivityDecisionTrace
    
    credigo_traces = [
        SensitivityDecisionTrace.from_dict(t)
        for t in unified_ledger['target_traces']
    ]
    
    benchmark_traces = {}
    for product, data in unified_ledger['benchmark_traces'].items():
        benchmark_traces[product] = [
            SensitivityDecisionTrace.from_dict(t)
            for t in data['traces']
        ]
    
    # Section 1: What Credigo Filters Earlier Than Benchmarks
    lines.append("## 1. What Credigo Filters Earlier Than Benchmarks")
    lines.append("")
    
    comparisons = comparative_results.get('comparisons', {})
    
    # Find steps where Credigo has higher drop rates
    early_filtering = []
    
    for benchmark_name, comp_data in comparisons.items():
        step_comps = comp_data.get('step_comparisons', {})
        
        for step_id, step_comp in step_comps.items():
            drop_rate_ratio = step_comp.get('drop_rate_ratio', 1.0)
            if drop_rate_ratio and drop_rate_ratio > 1.2:  # 20% higher
                target_drop = step_comp.get('target_drop_rate', 0.0)
                benchmark_drop = step_comp.get('benchmark_drop_rate', 0.0)
                
                early_filtering.append({
                    'step_id': step_id,
                    'benchmark': benchmark_name,
                    'credigo_drop_rate': target_drop,
                    'benchmark_drop_rate': benchmark_drop,
                    'ratio': drop_rate_ratio
                })
    
    if early_filtering:
        lines.append("Credigo shows higher drop rates at these steps compared to benchmarks:")
        lines.append("")
        for item in early_filtering[:5]:  # Top 5
            lines.append(f"- **{item['step_id']}**: Credigo {item['credigo_drop_rate']:.1%} vs {item['benchmark'].capitalize()} {item['benchmark_drop_rate']:.1%} ({item['ratio']:.1f}× higher)")
    else:
        lines.append("No steps identified where Credigo filters significantly earlier than benchmarks.")
    
    lines.append("")
    
    # Section 2: Where Credigo Asks for Commitment Sooner
    lines.append("## 2. Where Credigo Asks for Commitment Sooner")
    lines.append("")
    
    # Compare first value step
    lines.append("### Value Delivery Timing")
    lines.append("")
    lines.append("Credigo delivers first value at step 5 (personalized recommendation).")
    lines.append("")
    lines.append("Benchmark comparison:")
    lines.append("- **Groww**: First value at step 2 (browse mode, no signup)")
    lines.append("- **CRED**: First value at step 4 (rewards view)")
    lines.append("- **Zerodha**: First value at step 5 (account activated)")
    lines.append("")
    lines.append("Credigo asks for 4 preference/data steps before showing value, similar to Zerodha but later than Groww and CRED.")
    lines.append("")
    
    # Section 3: Where Credigo is Structurally Strong
    lines.append("## 3. Where Credigo is Structurally Strong")
    lines.append("")
    
    # Find steps where Credigo has lower drop rates
    strong_steps = []
    
    for benchmark_name, comp_data in comparisons.items():
        step_comps = comp_data.get('step_comparisons', {})
        
        for step_id, step_comp in step_comps.items():
            drop_rate_ratio = step_comp.get('drop_rate_ratio', 1.0)
            if drop_rate_ratio and drop_rate_ratio < 0.8:  # 20% lower
                target_drop = step_comp.get('target_drop_rate', 0.0)
                benchmark_drop = step_comp.get('benchmark_drop_rate', 0.0)
                
                strong_steps.append({
                    'step_id': step_id,
                    'benchmark': benchmark_name,
                    'credigo_drop_rate': target_drop,
                    'benchmark_drop_rate': benchmark_drop,
                    'ratio': drop_rate_ratio
                })
    
    if strong_steps:
        lines.append("Steps where Credigo shows lower drop rates than benchmarks:")
        lines.append("")
        for item in strong_steps[:5]:
            lines.append(f"- **{item['step_id']}**: Credigo {item['credigo_drop_rate']:.1%} vs {item['benchmark'].capitalize()} {item['benchmark_drop_rate']:.1%} ({1/item['ratio']:.1f}× lower)")
    else:
        lines.append("No steps identified where Credigo is significantly stronger than benchmarks.")
    
    lines.append("")
    
    # Section 4: Force Dominance Analysis
    lines.append("## 4. Force Dominance Comparison")
    lines.append("")
    
    lines.append("Which forces dominate decisions in Credigo vs benchmarks:")
    lines.append("")
    
    for benchmark_name, comp_data in comparisons.items():
        force_dom = comp_data.get('force_dominance', {})
        target_dom = force_dom.get('target', {})
        benchmark_dom = force_dom.get('benchmark', {})
        differences = force_dom.get('difference', {})
        
        lines.append(f"### Credigo vs {benchmark_name.capitalize()}")
        lines.append("")
        
        if differences:
            # Sort by absolute difference
            sorted_diffs = sorted(
                differences.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            for force_name, diff in sorted_diffs[:3]:
                if abs(diff) > 0.05:  # 5% difference
                    target_val = target_dom.get(force_name, 0.0)
                    bench_val = benchmark_dom.get(force_name, 0.0)
                    
                    if diff > 0:
                        lines.append(f"- **{force_name}**: Credigo relies more ({target_val:.1%} vs {bench_val:.1%}, +{diff:.1%})")
                    else:
                        lines.append(f"- **{force_name}**: {benchmark_name.capitalize()} relies more ({bench_val:.1%} vs {target_val:.1%}, {diff:.1%})")
        else:
            lines.append("No significant force dominance differences identified.")
        
        lines.append("")
    
    # Section 5: Persona Survival Analysis
    lines.append("## 5. Persona Survival Analysis")
    lines.append("")
    
    lines.append("Which persona classes survive in benchmarks but drop in Credigo (and vice versa):")
    lines.append("")
    
    for benchmark_name, comp_data in comparisons.items():
        persona_survival = comp_data.get('persona_survival', {})
        
        lines.append(f"### Credigo vs {benchmark_name.capitalize()}")
        lines.append("")
        
        if persona_survival:
            for persona_class, survival_data in persona_survival.items():
                if isinstance(survival_data, dict):
                    credigo_rate = survival_data.get('target_survival_rate', 0.0)
                    benchmark_rate = survival_data.get('benchmark_survival_rate', 0.0)
                    diff = survival_data.get('difference', 0.0)
                    
                    if abs(diff) > 0.1:  # 10% difference
                        if diff < 0:
                            lines.append(f"- **{persona_class}**: More survive in {benchmark_name.capitalize()} ({benchmark_rate:.1%} vs {credigo_rate:.1%})")
                        else:
                            lines.append(f"- **{persona_class}**: More survive in Credigo ({credigo_rate:.1%} vs {benchmark_rate:.1%})")
        else:
            lines.append("No significant persona survival differences identified.")
        
        lines.append("")
    
    # Section 6: Sensitivity Analysis (Which Changes Would Matter)
    lines.append("## 6. Which Changes Would Matter vs Which Wouldn't")
    lines.append("")
    
    lines.append("Sensitivity simulation results (Credigo-only perturbations):")
    lines.append("")
    
    # Group by perturbation type
    by_type = defaultdict(list)
    for result in sensitivity_results:
        pert_type = result['perturbation']['perturbation_type']
        by_type[pert_type].append(result)
    
    for pert_type, results in by_type.items():
        lines.append(f"### {pert_type.replace('_', ' ').title()}")
        lines.append("")
        
        for result in results:
            pert = result['perturbation']
            sens = result['sensitivity']
            change_rate = sens.get('overall_decision_change_rate', 0.0)
            magnitude = pert.get('magnitude', 0.0)
            step_idx = pert.get('step_index', 0)
            
            lines.append(f"- **Step {step_idx}, {magnitude:.0%} change**: {change_rate:.1%} decision change rate")
            
            if change_rate > 0.15:  # 15% change
                lines.append(f"  → **High impact**: This change would meaningfully affect outcomes")
            elif change_rate > 0.05:  # 5% change
                lines.append(f"  → **Moderate impact**: This change would have some effect")
            else:
                lines.append(f"  → **Low impact**: This change would have minimal effect")
        
        lines.append("")
    
    # Section 7: Summary Tables
    lines.append("## 7. Summary Tables")
    lines.append("")
    
    # Step fragility comparison
    lines.append("### Step Fragility Comparison")
    lines.append("")
    lines.append("| Step | Credigo Drop Rate | vs Zerodha | vs Groww | vs CRED |")
    lines.append("|------|-------------------|------------|----------|---------|")
    
    # Aggregate step data
    step_data = defaultdict(lambda: {'credigo': 0.0, 'zerodha': 0.0, 'groww': 0.0, 'cred': 0.0})
    
    for benchmark_name, comp_data in comparisons.items():
        step_comps = comp_data.get('step_comparisons', {})
        for step_id, step_comp in step_comps.items():
            step_data[step_id]['credigo'] = step_comp.get('target_drop_rate', 0.0)
            step_data[step_id][benchmark_name] = step_comp.get('benchmark_drop_rate', 0.0)
    
    for step_id, data in sorted(step_data.items(), key=lambda x: x[1]['credigo'], reverse=True)[:10]:
        lines.append(f"| {step_id} | {data['credigo']:.1%} | {data['zerodha']:.1%} | {data['groww']:.1%} | {data['cred']:.1%} |")
    
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("**Note:** All comparisons are based on decision traces from identical fixed personas. ")
    lines.append("Relative differences are more meaningful than absolute metrics. ")
    lines.append("This analysis identifies structural differences, not optimization prescriptions.")
    lines.append("")
    
    return "\n".join(lines)

