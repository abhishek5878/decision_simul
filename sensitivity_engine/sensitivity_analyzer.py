"""
Sensitivity Analyzer

Compares baseline vs perturbed decision traces to compute sensitivity metrics.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from sensitivity_engine.decision_trace_extended import SensitivityDecisionTrace, DecisionOutcome


@dataclass
class StepSensitivity:
    """
    Sensitivity metrics for a single step.
    """
    step_id: str
    step_index: int
    
    # Decision change rate
    decision_change_rate: float  # 0-1, % of personas that changed decision
    
    # Persona-class elasticity (which personas are most affected)
    high_sensitivity_personas: List[str]  # Personas that changed decision
    low_sensitivity_personas: List[str]   # Personas that didn't change
    
    # Force contributions (from baseline)
    force_contributions: Dict[str, float]  # force_name -> avg contribution
    
    # Fragility score (0-1, higher = more fragile)
    fragility_score: float
    
    def to_dict(self) -> Dict:
        return {
            'step_id': self.step_id,
            'step_index': self.step_index,
            'decision_change_rate': float(self.decision_change_rate),
            'high_sensitivity_personas': self.high_sensitivity_personas,
            'low_sensitivity_personas': self.low_sensitivity_personas,
            'force_contributions': {k: float(v) for k, v in self.force_contributions.items()},
            'fragility_score': float(self.fragility_score)
        }


@dataclass
class PerturbationSensitivity:
    """
    Sensitivity analysis for a single perturbation.
    """
    perturbation_id: str
    perturbation_type: str
    step_id: str
    
    # Overall metrics
    overall_decision_change_rate: float
    steps_affected: List[str]
    
    # Per-step sensitivity
    step_sensitivities: List[StepSensitivity]
    
    # Persona segments most responsive
    responsive_persona_classes: Dict[str, float]  # persona_class -> change_rate
    
    def to_dict(self) -> Dict:
        return {
            'perturbation_id': self.perturbation_id,
            'perturbation_type': self.perturbation_type,
            'step_id': self.step_id,
            'overall_decision_change_rate': float(self.overall_decision_change_rate),
            'steps_affected': self.steps_affected,
            'step_sensitivities': [s.to_dict() for s in self.step_sensitivities],
            'responsive_persona_classes': {k: float(v) for k, v in self.responsive_persona_classes.items()}
        }


class SensitivityAnalyzer:
    """
    Analyzes sensitivity by comparing baseline vs perturbed traces.
    """
    
    def compare_traces(
        self,
        baseline_traces: List[SensitivityDecisionTrace],
        perturbed_traces: List[SensitivityDecisionTrace],
        perturbation_id: str,
        perturbation_type: str
    ) -> PerturbationSensitivity:
        """
        Compare baseline and perturbed traces to compute sensitivity.
        """
        # Index traces by (persona_id, step_id)
        baseline_index = self._index_traces(baseline_traces)
        perturbed_index = self._index_traces(perturbed_traces)
        
        # Find all step_ids
        all_step_ids = set(baseline_index.keys()) | set(perturbed_index.keys())
        
        # Compute per-step sensitivity
        step_sensitivities = []
        total_changes = 0
        total_comparisons = 0
        
        for step_id in sorted(all_step_ids):
            baseline_at_step = baseline_index.get(step_id, {})
            perturbed_at_step = perturbed_index.get(step_id, {})
            
            # Find personas present in both
            common_personas = set(baseline_at_step.keys()) & set(perturbed_at_step.keys())
            
            if not common_personas:
                continue
            
            # Count decision changes
            changes = 0
            high_sensitivity = []
            low_sensitivity = []
            
            for persona_id in common_personas:
                baseline_decision = baseline_at_step[persona_id].decision
                perturbed_decision = perturbed_at_step[persona_id].decision
                
                if baseline_decision != perturbed_decision:
                    changes += 1
                    high_sensitivity.append(persona_id)
                else:
                    low_sensitivity.append(persona_id)
            
            change_rate = changes / len(common_personas) if common_personas else 0.0
            total_changes += changes
            total_comparisons += len(common_personas)
            
            # Get step_index from first trace
            step_index = baseline_at_step[list(common_personas)[0]].step_index if common_personas else 0
            
            # Compute force contributions (from baseline)
            force_contributions = self._compute_avg_force_contributions(
                [baseline_at_step[p] for p in common_personas]
            )
            
            # Fragility score (change rate weighted by step importance)
            # Steps earlier in flow are more fragile
            fragility_score = change_rate * (1.0 / (step_index + 1))
            
            step_sens = StepSensitivity(
                step_id=step_id,
                step_index=step_index,
                decision_change_rate=change_rate,
                high_sensitivity_personas=high_sensitivity,
                low_sensitivity_personas=low_sensitivity,
                force_contributions=force_contributions,
                fragility_score=fragility_score
            )
            
            step_sensitivities.append(step_sens)
        
        # Overall change rate
        overall_change_rate = total_changes / total_comparisons if total_comparisons > 0 else 0.0
        
        # Find step_id that was perturbed (first step with high change rate)
        perturbed_step_id = step_sensitivities[0].step_id if step_sensitivities else ""
        
        # Persona class responsiveness (simplified - group by state ranges)
        responsive_classes = self._compute_persona_class_responsiveness(
            baseline_traces, perturbed_traces
        )
        
        return PerturbationSensitivity(
            perturbation_id=perturbation_id,
            perturbation_type=perturbation_type,
            step_id=perturbed_step_id,
            overall_decision_change_rate=overall_change_rate,
            steps_affected=[s.step_id for s in step_sensitivities if s.decision_change_rate > 0.05],
            step_sensitivities=step_sensitivities,
            responsive_persona_classes=responsive_classes
        )
    
    def _index_traces(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, Dict[str, SensitivityDecisionTrace]]:
        """Index traces by step_id -> persona_id."""
        index = defaultdict(dict)
        for trace in traces:
            index[trace.step_id][trace.persona_id] = trace
        return dict(index)
    
    def _compute_avg_force_contributions(
        self,
        traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, float]:
        """Compute average force contributions across traces."""
        from sensitivity_engine.decision_trace_extended import compute_force_contributions
        
        all_contributions = defaultdict(list)
        
        for trace in traces:
            contributions = compute_force_contributions(
                trace.state_before,
                trace.forces_applied,
                trace.decision
            )
            
            for fc in contributions:
                all_contributions[fc.force_name].append(fc.contribution)
        
        # Average contributions
        avg_contributions = {
            force_name: np.mean(contributions)
            for force_name, contributions in all_contributions.items()
        }
        
        # Normalize to sum to 1.0
        total = sum(avg_contributions.values())
        if total > 0:
            avg_contributions = {k: v / total for k, v in avg_contributions.items()}
        
        return avg_contributions
    
    def _compute_persona_class_responsiveness(
        self,
        baseline_traces: List[SensitivityDecisionTrace],
        perturbed_traces: List[SensitivityDecisionTrace]
    ) -> Dict[str, float]:
        """
        Compute which persona classes (by state ranges) are most responsive.
        
        Groups personas by cognitive_energy ranges for simplicity.
        """
        # Index by persona_id
        baseline_by_persona = {t.persona_id: t for t in baseline_traces}
        perturbed_by_persona = {t.persona_id: t for t in perturbed_traces}
        
        # Group by cognitive_energy ranges
        classes = {
            'low_energy': [],  # < 0.33
            'medium_energy': [],  # 0.33 - 0.67
            'high_energy': []  # > 0.67
        }
        
        common_personas = set(baseline_by_persona.keys()) & set(perturbed_by_persona.keys())
        
        for persona_id in common_personas:
            baseline = baseline_by_persona[persona_id]
            perturbed = perturbed_by_persona[persona_id]
            
            energy = baseline.state_before.cognitive_energy
            
            if energy < 0.33:
                classes['low_energy'].append((baseline, perturbed))
            elif energy < 0.67:
                classes['medium_energy'].append((baseline, perturbed))
            else:
                classes['high_energy'].append((baseline, perturbed))
        
        # Compute change rates per class
        responsive_classes = {}
        for class_name, pairs in classes.items():
            if not pairs:
                continue
            
            changes = sum(1 for b, p in pairs if b.decision != p.decision)
            change_rate = changes / len(pairs) if pairs else 0.0
            responsive_classes[class_name] = change_rate
        
        return responsive_classes

