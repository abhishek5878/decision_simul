"""
Comparative Sensitivity Analyzer

Compares target product against benchmarks to identify differences.
"""

from typing import Dict, List
from collections import defaultdict
import numpy as np

from sensitivity_engine.decision_trace_extended import SensitivityDecisionTrace, DecisionOutcome
from sensitivity_engine.decision_trace_extended import compute_force_contributions


class ComparativeAnalyzer:
    """
    Analyzes differences between target product and benchmarks.
    """
    
    def analyze_benchmarks(
        self,
        unified_ledger: Dict
    ) -> Dict:
        """
        Compare target product against all benchmarks.
        
        Returns:
            Dictionary with comparative analysis results
        """
        target_product = unified_ledger['target_product']
        target_traces = [
            SensitivityDecisionTrace.from_dict(t)
            for t in unified_ledger['target_traces']
        ]
        
        benchmark_results = {}
        
        for benchmark_product, benchmark_data in unified_ledger['benchmark_traces'].items():
            benchmark_traces = [
                SensitivityDecisionTrace.from_dict(t)
                for t in benchmark_data['traces']
            ]
            
            comparison = self._compare_products(
                target_product, target_traces,
                benchmark_product, benchmark_traces
            )
            
            benchmark_results[benchmark_product] = comparison
        
        return {
            'target_product': target_product,
            'comparisons': benchmark_results
        }
    
    def _compare_products(
        self,
        target_name: str,
        target_traces: List[SensitivityDecisionTrace],
        benchmark_name: str,
        benchmark_traces: List[SensitivityDecisionTrace]
    ) -> Dict:
        """Compare two products."""
        # Index traces by step_id and persona_id
        target_index = self._index_traces(target_traces)
        benchmark_index = self._index_traces(benchmark_traces)
        
        # Find common steps
        target_steps = set(target_index.keys())
        benchmark_steps = set(benchmark_index.keys())
        common_steps = target_steps & benchmark_steps
        
        # Step-by-step comparisons
        step_comparisons = {}
        
        for step_id in common_steps:
            target_at_step = target_index[step_id]
            benchmark_at_step = benchmark_index[step_id]
            
            # Find common personas
            common_personas = set(target_at_step.keys()) & set(benchmark_at_step.keys())
            
            if not common_personas:
                continue
            
            # Compute metrics
            comparison = self._compare_step(
                step_id,
                [target_at_step[p] for p in common_personas],
                [benchmark_at_step[p] for p in common_personas]
            )
            
            step_comparisons[step_id] = comparison
        
        # Overall comparisons
        overall = self._compare_overall(target_traces, benchmark_traces)
        
        # Force dominance analysis
        force_dominance = self._compare_force_dominance(target_traces, benchmark_traces)
        
        # Persona survival analysis
        persona_survival = self._compare_persona_survival(target_traces, benchmark_traces)
        
        return {
            'step_comparisons': step_comparisons,
            'overall': overall,
            'force_dominance': force_dominance,
            'persona_survival': persona_survival
        }
    
    def _index_traces(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, Dict[str, SensitivityDecisionTrace]]:
        """Index traces by step_id -> persona_id."""
        index = defaultdict(dict)
        for trace in traces:
            index[trace.step_id][trace.persona_id] = trace
        return dict(index)
    
    def _compare_step(
        self,
        step_id: str,
        target_traces: List[SensitivityDecisionTrace],
        benchmark_traces: List[SensitivityDecisionTrace]
    ) -> Dict:
        """Compare a single step between two products."""
        # Drop rates
        target_drops = sum(1 for t in target_traces if t.decision == DecisionOutcome.DROP)
        benchmark_drops = sum(1 for t in benchmark_traces if t.decision == DecisionOutcome.DROP)
        
        target_drop_rate = target_drops / len(target_traces) if target_traces else 0.0
        benchmark_drop_rate = benchmark_drops / len(benchmark_traces) if benchmark_traces else 0.0
        
        # Force sensitivity (avg force values)
        target_avg_forces = self._compute_avg_forces(target_traces)
        benchmark_avg_forces = self._compute_avg_forces(benchmark_traces)
        
        # Force ratio (target / benchmark)
        force_ratios = {}
        for force_name in target_avg_forces.keys():
            if benchmark_avg_forces.get(force_name, 0) > 0:
                force_ratios[force_name] = target_avg_forces[force_name] / benchmark_avg_forces[force_name]
            else:
                force_ratios[force_name] = float('inf') if target_avg_forces[force_name] > 0 else 1.0
        
        # Fragility (drop rate sensitivity)
        fragility_ratio = target_drop_rate / benchmark_drop_rate if benchmark_drop_rate > 0 else float('inf')
        
        return {
            'step_id': step_id,
            'target_drop_rate': float(target_drop_rate),
            'benchmark_drop_rate': float(benchmark_drop_rate),
            'drop_rate_ratio': float(fragility_ratio),
            'target_avg_forces': {k: float(v) for k, v in target_avg_forces.items()},
            'benchmark_avg_forces': {k: float(v) for k, v in benchmark_avg_forces.items()},
            'force_ratios': {k: float(v) if v != float('inf') else None for k, v in force_ratios.items()}
        }
    
    def _compute_avg_forces(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, float]:
        """Compute average force values across traces."""
        forces_sum = defaultdict(float)
        count = len(traces)
        
        for trace in traces:
            forces = trace.forces_applied
            forces_sum['effort'] += forces.effort
            forces_sum['risk'] += forces.risk
            forces_sum['value'] += forces.value
            forces_sum['trust'] += forces.trust
            forces_sum['intent_mismatch'] += forces.intent_mismatch
        
        return {
            force_name: forces_sum[force_name] / count if count > 0 else 0.0
            for force_name in ['effort', 'risk', 'value', 'trust', 'intent_mismatch']
        }
    
    def _compare_overall(
        self,
        target_traces: List[SensitivityDecisionTrace],
        benchmark_traces: List[SensitivityDecisionTrace]
    ) -> Dict:
        """Compare overall metrics."""
        # Completion rates
        target_completions = sum(1 for t in target_traces if t.decision == DecisionOutcome.CONTINUE)
        benchmark_completions = sum(1 for t in benchmark_traces if t.decision == DecisionOutcome.CONTINUE)
        
        target_completion_rate = target_completions / len(target_traces) if target_traces else 0.0
        benchmark_completion_rate = benchmark_completions / len(benchmark_traces) if benchmark_traces else 0.0
        
        # Average steps completed
        target_avg_steps = self._compute_avg_steps_completed(target_traces)
        benchmark_avg_steps = self._compute_avg_steps_completed(benchmark_traces)
        
        return {
            'target_completion_rate': float(target_completion_rate),
            'benchmark_completion_rate': float(benchmark_completion_rate),
            'completion_rate_diff': float(target_completion_rate - benchmark_completion_rate),
            'target_avg_steps': float(target_avg_steps),
            'benchmark_avg_steps': float(benchmark_avg_steps),
            'avg_steps_diff': float(target_avg_steps - benchmark_avg_steps)
        }
    
    def _compute_avg_steps_completed(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> float:
        """Compute average steps completed per persona."""
        # Group by persona_id
        persona_steps = defaultdict(int)
        
        for trace in traces:
            if trace.decision == DecisionOutcome.CONTINUE:
                persona_steps[trace.persona_id] = max(
                    persona_steps[trace.persona_id],
                    trace.step_index + 1
                )
        
        if not persona_steps:
            return 0.0
        
        return np.mean(list(persona_steps.values()))
    
    def _compare_force_dominance(
        self,
        target_traces: List[SensitivityDecisionTrace],
        benchmark_traces: List[SensitivityDecisionTrace]
    ) -> Dict:
        """Compare which forces dominate decisions."""
        target_dominance = self._compute_force_dominance(target_traces)
        benchmark_dominance = self._compute_force_dominance(benchmark_traces)
        
        return {
            'target': target_dominance,
            'benchmark': benchmark_dominance,
            'difference': {
                force: target_dominance.get(force, 0.0) - benchmark_dominance.get(force, 0.0)
                for force in set(target_dominance.keys()) | set(benchmark_dominance.keys())
            }
        }
    
    def _compute_force_dominance(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, float]:
        """Compute average force contribution (dominance)."""
        all_contributions = defaultdict(list)
        
        for trace in traces:
            contributions = compute_force_contributions(
                trace.state_before,
                trace.forces_applied,
                trace.decision
            )
            
            for fc in contributions:
                all_contributions[fc.force_name].append(fc.contribution)
        
        return {
            force_name: np.mean(contributions) if contributions else 0.0
            for force_name, contributions in all_contributions.items()
        }
    
    def _compare_persona_survival(
        self,
        target_traces: List[SensitivityDecisionTrace],
        benchmark_traces: List[SensitivityDecisionTrace]
    ) -> Dict:
        """Compare which persona classes survive in each product."""
        target_survival = self._compute_persona_survival(target_traces)
        benchmark_survival = self._compute_persona_survival(benchmark_traces)
        
        # Compare survival rates by persona class
        all_classes = set(target_survival.keys()) | set(benchmark_survival.keys())
        comparison = {}
        
        for persona_class in all_classes:
            target_rate = target_survival.get(persona_class, 0.0)
            benchmark_rate = benchmark_survival.get(persona_class, 0.0)
            
            comparison[persona_class] = {
                'target_survival_rate': float(target_rate),
                'benchmark_survival_rate': float(benchmark_rate),
                'difference': float(target_rate - benchmark_rate)
            }
        
        return comparison
    
    def _compute_persona_survival(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, float]:
        """Compute survival rate by persona class (simplified: by cognitive_energy)."""
        # Group by persona and determine if they completed
        persona_completed = {}
        
        for trace in traces:
            persona_id = trace.persona_id
            if persona_id not in persona_completed:
                persona_completed[persona_id] = False
            
            # If they continued, they're still in
            if trace.decision == DecisionOutcome.CONTINUE:
                persona_completed[persona_id] = True
        
        # Classify personas by cognitive_energy (from first trace)
        persona_classes = {}
        for trace in traces:
            if trace.persona_id not in persona_classes:
                energy = trace.state_before.cognitive_energy
                if energy < 0.33:
                    persona_classes[trace.persona_id] = 'low_energy'
                elif energy < 0.67:
                    persona_classes[trace.persona_id] = 'medium_energy'
                else:
                    persona_classes[trace.persona_id] = 'high_energy'
        
        # Compute survival rates per class
        class_counts = defaultdict(lambda: {'total': 0, 'survived': 0})
        
        for persona_id, completed in persona_completed.items():
            persona_class = persona_classes.get(persona_id, 'unknown')
            class_counts[persona_class]['total'] += 1
            if completed:
                class_counts[persona_class]['survived'] += 1
        
        return {
            class_name: counts['survived'] / counts['total'] if counts['total'] > 0 else 0.0
            for class_name, counts in class_counts.items()
        }

