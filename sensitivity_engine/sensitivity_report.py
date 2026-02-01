"""
Sensitivity Report Generator

Generates human-readable reports from sensitivity analysis.
"""

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from sensitivity_engine.sensitivity_analyzer import PerturbationSensitivity, StepSensitivity


@dataclass
class DecisionSensitivityReport:
    """
    Final sensitivity report containing:
    - Top leverage steps
    - Forces that actually move decisions
    - Persona segments most responsive to change
    """
    product_name: str
    baseline_experiment_id: str
    
    # Top leverage steps (by fragility score)
    top_leverage_steps: List[Dict]
    
    # Forces that move decisions (ranked by impact)
    force_impact_rankings: List[Dict]
    
    # Persona segments most responsive
    responsive_persona_segments: Dict[str, float]
    
    # Perturbation results
    perturbation_results: List[PerturbationSensitivity]
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'product_name': self.product_name,
            'baseline_experiment_id': self.baseline_experiment_id,
            'top_leverage_steps': self.top_leverage_steps,
            'force_impact_rankings': self.force_impact_rankings,
            'responsive_persona_segments': self.responsive_persona_segments,
            'perturbation_results': [p.to_dict() for p in self.perturbation_results],
            'generated_at': self.generated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionSensitivityReport':
        from sensitivity_engine.sensitivity_analyzer import PerturbationSensitivity
        return cls(
            product_name=data['product_name'],
            baseline_experiment_id=data['baseline_experiment_id'],
            top_leverage_steps=data['top_leverage_steps'],
            force_impact_rankings=data['force_impact_rankings'],
            responsive_persona_segments=data['responsive_persona_segments'],
            perturbation_results=data['perturbation_results'],  # Keep as dict for now
            generated_at=data.get('generated_at', '')
        )


class SensitivityReportGenerator:
    """
    Generates sensitivity reports from analysis results.
    """
    
    def generate_report(
        self,
        product_name: str,
        baseline_experiment_id: str,
        perturbation_results: List[PerturbationSensitivity]
    ) -> DecisionSensitivityReport:
        """
        Generate comprehensive sensitivity report.
        """
        # Extract top leverage steps (by fragility score)
        top_leverage_steps = self._extract_top_leverage_steps(perturbation_results)
        
        # Rank forces by impact
        force_impact_rankings = self._rank_forces_by_impact(perturbation_results)
        
        # Identify responsive persona segments
        responsive_segments = self._identify_responsive_segments(perturbation_results)
        
        return DecisionSensitivityReport(
            product_name=product_name,
            baseline_experiment_id=baseline_experiment_id,
            top_leverage_steps=top_leverage_steps,
            force_impact_rankings=force_impact_rankings,
            responsive_persona_segments=responsive_segments,
            perturbation_results=perturbation_results
        )
    
    def _extract_top_leverage_steps(
        self,
        perturbation_results: List[PerturbationSensitivity]
    ) -> List[Dict]:
        """Extract top leverage steps (high fragility, high change rate)."""
        step_scores = {}
        
        for pert_result in perturbation_results:
            for step_sens in pert_result.step_sensitivities:
                step_id = step_sens.step_id
                
                if step_id not in step_scores:
                    step_scores[step_id] = {
                        'step_id': step_id,
                        'step_index': step_sens.step_index,
                        'max_change_rate': step_sens.decision_change_rate,
                        'max_fragility': step_sens.fragility_score,
                        'combined_score': step_sens.decision_change_rate * step_sens.fragility_score
                    }
                else:
                    # Update with max values
                    if step_sens.decision_change_rate > step_scores[step_id]['max_change_rate']:
                        step_scores[step_id]['max_change_rate'] = step_sens.decision_change_rate
                    if step_sens.fragility_score > step_scores[step_id]['max_fragility']:
                        step_scores[step_id]['max_fragility'] = step_sens.fragility_score
                    step_scores[step_id]['combined_score'] = (
                        step_scores[step_id]['max_change_rate'] * 
                        step_scores[step_id]['max_fragility']
                    )
        
        # Sort by combined score
        top_steps = sorted(
            step_scores.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return top_steps[:10]  # Top 10
    
    def _rank_forces_by_impact(
        self,
        perturbation_results: List[PerturbationSensitivity]
    ) -> List[Dict]:
        """Rank forces by their impact on decisions."""
        force_impacts = {}
        
        for pert_result in perturbation_results:
            for step_sens in pert_result.step_sensitivities:
                for force_name, contribution in step_sens.force_contributions.items():
                    if force_name not in force_impacts:
                        force_impacts[force_name] = {
                            'force_name': force_name,
                            'total_impact': 0.0,
                            'occurrence_count': 0,
                            'avg_contribution': 0.0
                        }
                    
                    # Impact = contribution * change_rate
                    impact = contribution * step_sens.decision_change_rate
                    force_impacts[force_name]['total_impact'] += impact
                    force_impacts[force_name]['occurrence_count'] += 1
        
        # Compute averages
        for force_data in force_impacts.values():
            if force_data['occurrence_count'] > 0:
                force_data['avg_contribution'] = (
                    force_data['total_impact'] / force_data['occurrence_count']
                )
        
        # Sort by total impact
        ranked = sorted(
            force_impacts.values(),
            key=lambda x: x['total_impact'],
            reverse=True
        )
        
        return ranked
    
    def _identify_responsive_segments(
        self,
        perturbation_results: List[PerturbationSensitivity]
    ) -> Dict[str, float]:
        """Identify persona segments most responsive to changes."""
        segment_responsiveness = {}
        
        for pert_result in perturbation_results:
            for segment, change_rate in pert_result.responsive_persona_classes.items():
                if segment not in segment_responsiveness:
                    segment_responsiveness[segment] = []
                segment_responsiveness[segment].append(change_rate)
        
        # Average change rates per segment
        avg_responsiveness = {
            segment: sum(rates) / len(rates) if rates else 0.0
            for segment, rates in segment_responsiveness.items()
        }
        
        return avg_responsiveness
    
    def generate_markdown_report(self, report: DecisionSensitivityReport) -> str:
        """Generate human-readable markdown report."""
        lines = []
        
        lines.append(f"# Decision Sensitivity Report: {report.product_name}")
        lines.append("")
        lines.append(f"**Generated:** {report.generated_at}")
        lines.append(f"**Baseline Experiment:** {report.baseline_experiment_id}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Top Leverage Steps
        lines.append("## Top Leverage Steps")
        lines.append("")
        lines.append("Steps with highest sensitivity (fragility × change rate):")
        lines.append("")
        for i, step in enumerate(report.top_leverage_steps[:5], 1):
            lines.append(f"{i}. **{step['step_id']}** (Step {step['step_index']})")
            lines.append(f"   - Change Rate: {step['max_change_rate']:.1%}")
            lines.append(f"   - Fragility Score: {step['max_fragility']:.3f}")
            lines.append(f"   - Combined Score: {step['combined_score']:.3f}")
            lines.append("")
        
        # Force Impact Rankings
        lines.append("## Forces That Move Decisions")
        lines.append("")
        lines.append("Forces ranked by impact on decisions:")
        lines.append("")
        for i, force in enumerate(report.force_impact_rankings[:5], 1):
            lines.append(f"{i}. **{force['force_name']}**")
            lines.append(f"   - Total Impact: {force['total_impact']:.3f}")
            lines.append(f"   - Avg Contribution: {force['avg_contribution']:.1%}")
            lines.append(f"   - Occurrences: {force['occurrence_count']}")
            lines.append("")
        
        # Responsive Persona Segments
        lines.append("## Responsive Persona Segments")
        lines.append("")
        lines.append("Persona segments most responsive to changes:")
        lines.append("")
        for segment, change_rate in sorted(
            report.responsive_persona_segments.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            lines.append(f"- **{segment}**: {change_rate:.1%} avg change rate")
        lines.append("")
        
        # Perturbation Results Summary
        lines.append("## Perturbation Results Summary")
        lines.append("")
        for pert_result in report.perturbation_results:
            lines.append(f"### {pert_result.perturbation_type} @ {pert_result.step_id}")
            lines.append(f"- Overall Change Rate: {pert_result.overall_decision_change_rate:.1%}")
            lines.append(f"- Steps Affected: {len(pert_result.steps_affected)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_report(self, report: DecisionSensitivityReport, filepath: str):
        """Save report to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def save_markdown_report(self, report: DecisionSensitivityReport, filepath: str):
        """Save markdown report."""
        markdown = self.generate_markdown_report(report)
        with open(filepath, 'w') as f:
            f.write(markdown)

