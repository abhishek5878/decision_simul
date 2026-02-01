"""
dropsim_confidence_calibrator.py - Confidence Calibration Logic

Adjusts confidence scores based on:
- Contradictions detected
- Severity of contradictions
- Diversity of conflicting evidence
- Stability of results

Transforms the system from "I detected contradictions but still believe my answer"
to "Given conflicting evidence, my confidence is reduced."
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceBand(Enum):
    """Confidence level bands."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


@dataclass
class ContradictionInfo:
    """Information about detected contradictions."""
    count: int
    severity: float  # 0-1, higher = more severe
    types: List[str]  # Types of contradictions
    sources: List[str]  # Where contradictions were detected
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'count': self.count,
            'severity': self.severity,
            'types': self.types,
            'sources': self.sources
        }


@dataclass
class ConfidenceAssessment:
    """Complete confidence assessment."""
    raw_confidence: float
    adjusted_confidence: float
    confidence_band: str  # "HIGH", "MODERATE", "LOW"
    contradiction_count: int
    primary_uncertainty_sources: List[str]
    adjustment_rationale: str
    stability_factor: float
    evidence_diversity: float
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'raw_confidence': self.raw_confidence,
            'adjusted_confidence': self.adjusted_confidence,
            'confidence_band': self.confidence_band,
            'contradiction_count': self.contradiction_count,
            'primary_uncertainty_sources': self.primary_uncertainty_sources,
            'adjustment_rationale': self.adjustment_rationale,
            'stability_factor': self.stability_factor,
            'evidence_diversity': self.evidence_diversity
        }


# ============================================================================
# Contradiction Detection and Analysis
# ============================================================================

def detect_contradictions(result: Dict) -> ContradictionInfo:
    """
    Detect contradictions in the result.
    
    Returns:
        ContradictionInfo with count, severity, types, and sources
    """
    contradictions = []
    types = []
    sources = []
    total_severity = 0.0
    
    # Source 1: Signal quality risk flags
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            risk_flags = sq.get('risk_flags', [])
            if risk_flags:
                contradictions.extend(risk_flags)
                types.append('risk_flags')
                sources.append('signal_quality_evaluation')
                # Each risk flag adds to severity
                total_severity += min(0.3, len(risk_flags) * 0.1)
    
    # Source 2: False certainty warnings
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            # Check for false certainty indicators
            false_certainty = sq.get('false_certainty_warnings', [])
            if false_certainty:
                contradictions.extend(false_certainty)
                if 'false_certainty' not in types:
                    types.append('false_certainty')
                if 'false_certainty_detection' not in sources:
                    sources.append('false_certainty_detection')
                total_severity += min(0.2, len(false_certainty) * 0.05)
    
    # Source 3: Impossible patterns in context graph
    if 'context_graph' in result:
        cg = result['context_graph']
        if cg and 'nodes' in cg:
            nodes = cg['nodes']
            impossible_patterns = []
            
            # Check for impossible completion patterns
            for i in range(len(nodes) - 1):
                if isinstance(nodes[i], dict) and isinstance(nodes[i+1], dict):
                    current_drop = nodes[i].get('drop_rate', 0.5)
                    next_drop = nodes[i+1].get('drop_rate', 0.5)
                    # If later step has lower drop (higher completion), it's impossible
                    if current_drop > next_drop + 0.15:  # Significant difference
                        impossible_patterns.append(f"Step {i+1} has higher completion than step {i}")
            
            if impossible_patterns:
                contradictions.extend(impossible_patterns)
                if 'impossible_patterns' not in types:
                    types.append('impossible_patterns')
                if 'context_graph_analysis' not in sources:
                    sources.append('context_graph_analysis')
                total_severity += min(0.25, len(impossible_patterns) * 0.1)
    
    # Source 4: Conflicting behavioral signals
    if 'context_graph' in result:
        cg = result['context_graph']
        if cg and 'nodes' in cg:
            nodes = cg['nodes']
            conflicting_signals = []
            
            for node in nodes:
                if isinstance(node, dict):
                    effort = node.get('avg_perceived_effort', 0.5)
                    drop_rate = node.get('drop_rate', 0.5)
                    # High effort but low drop (high completion) is contradictory
                    if effort > 0.8 and drop_rate < 0.2:
                        conflicting_signals.append(f"High effort ({effort:.1%}) but high completion ({1-drop_rate:.1%})")
            
            if conflicting_signals:
                contradictions.extend(conflicting_signals)
                if 'conflicting_signals' not in types:
                    types.append('conflicting_signals')
                if 'behavioral_analysis' not in sources:
                    sources.append('behavioral_analysis')
                total_severity += min(0.2, len(conflicting_signals) * 0.08)
    
    # Source 5: Overconfidence detection
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            confidence_calibration = sq.get('confidence_calibration', {})
            if isinstance(confidence_calibration, dict):
                if confidence_calibration.get('overconfidence_detected', False):
                    contradictions.append("Overconfidence detected in confidence calibration")
                    if 'overconfidence' not in types:
                        types.append('overconfidence')
                    if 'confidence_calibration' not in sources:
                        sources.append('confidence_calibration')
                    total_severity += 0.15
    
    # Calculate average severity
    severity = min(1.0, total_severity) if contradictions else 0.0
    
    return ContradictionInfo(
        count=len(contradictions),
        severity=severity,
        types=types,
        sources=sources
    )


# ============================================================================
# Confidence Adjustment Logic
# ============================================================================

def adjust_confidence(
    raw_confidence: float,
    contradiction_info: ContradictionInfo,
    stability_factor: float = 1.0,
    evidence_diversity: float = 1.0
) -> Tuple[float, str]:
    """
    Adjust confidence based on contradictions and other factors.
    
    Args:
        raw_confidence: Original confidence score (0-1)
        contradiction_info: Information about detected contradictions
        stability_factor: Stability of results across runs (0-1)
        evidence_diversity: Diversity of evidence sources (0-1)
    
    Returns:
        (adjusted_confidence, rationale)
    """
    adjusted = raw_confidence
    rationale_parts = []
    
    # Base adjustment: contradictions reduce confidence
    if contradiction_info.count > 0:
        # Each contradiction reduces confidence
        contradiction_penalty = min(0.4, contradiction_info.count * 0.1)
        # Severity also matters
        severity_penalty = contradiction_info.severity * 0.3
        
        # Combined penalty
        total_penalty = min(0.6, contradiction_penalty + severity_penalty)
        adjusted *= (1.0 - total_penalty)
        
        rationale_parts.append(
            f"{contradiction_info.count} contradiction(s) detected "
            f"(severity: {contradiction_info.severity:.1%}) → "
            f"reduced confidence by {total_penalty:.1%}"
        )
    
    # Stability adjustment
    if stability_factor < 1.0:
        stability_penalty = (1.0 - stability_factor) * 0.2
        adjusted *= (1.0 - stability_penalty)
        rationale_parts.append(
            f"Low stability ({stability_factor:.1%}) → "
            f"reduced confidence by {stability_penalty:.1%}"
        )
    
    # Evidence diversity adjustment
    if evidence_diversity < 0.6:
        diversity_penalty = (0.6 - evidence_diversity) * 0.15
        adjusted *= (1.0 - diversity_penalty)
        rationale_parts.append(
            f"Low evidence diversity ({evidence_diversity:.1%}) → "
            f"reduced confidence by {diversity_penalty:.1%}"
        )
    
    # Sanity check: if contradictions exist but confidence is still high
    if contradiction_info.count > 0 and adjusted > 0.8:
        # Force reduction
        adjusted = min(adjusted, 0.65)
        rationale_parts.append(
            "Sanity check: contradictions present but confidence high → "
            "forced reduction to 65%"
        )
    
    # Ensure bounds
    adjusted = max(0.0, min(1.0, adjusted))
    
    # Generate rationale
    if rationale_parts:
        rationale = "; ".join(rationale_parts)
    else:
        rationale = "No adjustments needed - high confidence supported by evidence"
    
    return adjusted, rationale


def determine_confidence_band(adjusted_confidence: float) -> str:
    """
    Determine confidence band based on adjusted confidence.
    
    Returns:
        "HIGH", "MODERATE", or "LOW"
    """
    if adjusted_confidence >= 0.7:
        return ConfidenceBand.HIGH.value
    elif adjusted_confidence >= 0.5:
        return ConfidenceBand.MODERATE.value
    else:
        return ConfidenceBand.LOW.value


# ============================================================================
# Main Calibration Function
# ============================================================================

def calibrate_confidence_with_contradictions(
    result: Dict,
    raw_confidence: Optional[float] = None
) -> ConfidenceAssessment:
    """
    Calibrate confidence based on contradictions and evidence quality.
    
    Args:
        result: Full result dictionary
        raw_confidence: Original confidence (if None, extracted from result)
    
    Returns:
        ConfidenceAssessment with adjusted confidence and rationale
    """
    # Extract raw confidence
    if raw_confidence is None:
        if 'decision_report' in result and result['decision_report']:
            raw_confidence = result['decision_report'].get('overall_confidence', 0.5)
        elif 'signal_quality' in result:
            sq = result['signal_quality']
            if isinstance(sq, dict):
                raw_confidence = sq.get('overall_trust_index', 0.5)
            else:
                raw_confidence = 0.5
        else:
            raw_confidence = 0.5
    
    # Detect contradictions
    contradiction_info = detect_contradictions(result)
    
    # Extract stability factor
    stability_factor = 1.0
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            stability = sq.get('stability', {})
            if isinstance(stability, dict):
                stability_factor = stability.get('consistency_score', 1.0)
    
    # Extract evidence diversity
    evidence_diversity = 1.0
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            signal_strength = sq.get('signal_strength', {})
            if isinstance(signal_strength, dict):
                evidence_diversity = signal_strength.get('evidence_diversity', 1.0)
    
    # Adjust confidence
    adjusted_confidence, rationale = adjust_confidence(
        raw_confidence,
        contradiction_info,
        stability_factor,
        evidence_diversity
    )
    
    # Determine confidence band
    confidence_band = determine_confidence_band(adjusted_confidence)
    
    # Identify primary uncertainty sources
    uncertainty_sources = []
    if contradiction_info.count > 0:
        uncertainty_sources.extend(contradiction_info.types)
    if stability_factor < 0.7:
        uncertainty_sources.append('low_stability')
    if evidence_diversity < 0.5:
        uncertainty_sources.append('low_evidence_diversity')
    
    if not uncertainty_sources:
        uncertainty_sources.append('none')
    
    return ConfidenceAssessment(
        raw_confidence=raw_confidence,
        adjusted_confidence=adjusted_confidence,
        confidence_band=confidence_band,
        contradiction_count=contradiction_info.count,
        primary_uncertainty_sources=uncertainty_sources,
        adjustment_rationale=rationale,
        stability_factor=stability_factor,
        evidence_diversity=evidence_diversity
    )


def apply_confidence_calibration(result: Dict) -> Dict:
    """
    Apply confidence calibration to a result and update it in-place.
    
    Args:
        result: Result dictionary to calibrate
    
    Returns:
        Updated result with confidence_assessment
    """
    # Run calibration
    assessment = calibrate_confidence_with_contradictions(result)
    
    # Add to result
    result['confidence_assessment'] = assessment.to_dict()
    
    # Update decision report confidence if it exists
    if 'decision_report' in result and result['decision_report']:
        result['decision_report']['overall_confidence'] = assessment.adjusted_confidence
    
    # Update signal quality trust index if it exists
    if 'signal_quality' in result:
        sq = result['signal_quality']
        if isinstance(sq, dict):
            # Update overall_trust_index to reflect adjusted confidence
            sq['overall_trust_index'] = assessment.adjusted_confidence
    
    return result

