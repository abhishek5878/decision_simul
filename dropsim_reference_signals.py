"""
dropsim_reference_signals.py - Reference Signal Layer

Simple interface to anchor system predictions to real-world signals.
Not more logic, not more models - just anchoring to reality.

Turns the system from "I think this is right"
into "I've been right before in similar cases."
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class ReferenceSignal:
    """A reference signal from external source."""
    source: str  # e.g. "A/B test", "user interview", "expert label"
    confidence: float  # trust in this reference (0-1)
    assertion: dict  # what it claims is true
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    signal_id: str = field(default_factory=lambda: f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'source': self.source,
            'confidence': self.confidence,
            'assertion': self.assertion,
            'timestamp': self.timestamp,
            'signal_id': self.signal_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReferenceSignal':
        """Create from dict."""
        return cls(
            source=data['source'],
            confidence=data['confidence'],
            assertion=data['assertion'],
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            signal_id=data.get('signal_id', f"ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        )


@dataclass
class CalibrationRecord:
    """Record of how well system matched a reference signal."""
    signal_id: str
    reference_signal: ReferenceSignal
    system_prediction: Dict
    match_score: float  # 0-1, how well they matched
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            'signal_id': self.signal_id,
            'reference_signal': self.reference_signal.to_dict(),
            'system_prediction': self.system_prediction,
            'match_score': self.match_score,
            'timestamp': self.timestamp
        }


class ReferenceSignalStore:
    """Simple store for reference signals and calibration history."""
    
    def __init__(self, store_path: str = "config/reference_signals.json"):
        self.store_path = store_path
        self.signals: List[ReferenceSignal] = []
        self.calibration_history: List[CalibrationRecord] = []
        self._load()
    
    def _load(self):
        """Load signals and history from disk."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r') as f:
                    data = json.load(f)
                    self.signals = [ReferenceSignal.from_dict(s) for s in data.get('signals', [])]
                    self.calibration_history = [
                        CalibrationRecord(
                            signal_id=r['signal_id'],
                            reference_signal=ReferenceSignal.from_dict(r['reference_signal']),
                            system_prediction=r['system_prediction'],
                            match_score=r['match_score'],
                            timestamp=r.get('timestamp', datetime.now().isoformat())
                        )
                        for r in data.get('calibration_history', [])
                    ]
            except Exception:
                # If load fails, start fresh
                self.signals = []
                self.calibration_history = []
    
    def _save(self):
        """Save signals and history to disk."""
        data = {
            'signals': [s.to_dict() for s in self.signals],
            'calibration_history': [r.to_dict() for r in self.calibration_history]
        }
        with open(self.store_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_reference_signal(self, signal: ReferenceSignal):
        """Add a reference signal."""
        self.signals.append(signal)
        self._save()
    
    def add_calibration_record(self, record: CalibrationRecord):
        """Add a calibration record."""
        self.calibration_history.append(record)
        self._save()
    
    def get_recent_calibration_score(self, n: int = 10) -> Optional[float]:
        """Get average match score from recent calibration records."""
        if not self.calibration_history:
            return None
        
        recent = self.calibration_history[-n:]
        if not recent:
            return None
        
        return sum(r.match_score for r in recent) / len(recent)
    
    def get_calibration_trend(self) -> Dict:
        """Get calibration trend over time."""
        if not self.calibration_history:
            return {
                'average_match': None,
                'recent_match': None,
                'trend': 'insufficient_data'
            }
        
        # Recent (last 10)
        recent_score = self.get_recent_calibration_score(10)
        
        # Older (previous 10, if available)
        if len(self.calibration_history) >= 20:
            older = self.calibration_history[-20:-10]
            older_score = sum(r.match_score for r in older) / len(older)
            
            if recent_score > older_score + 0.1:
                trend = 'improving'
            elif recent_score < older_score - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # Overall average
        overall_score = sum(r.match_score for r in self.calibration_history) / len(self.calibration_history)
        
        return {
            'average_match': overall_score,
            'recent_match': recent_score,
            'trend': trend
        }


# ============================================================================
# Comparison Logic
# ============================================================================

def compare_to_reference(
    system_result: Dict,
    reference_signal: ReferenceSignal
) -> float:
    """
    Compare system prediction to reference signal.
    
    Returns:
        Match score (0-1), where 1.0 = perfect match
    """
    assertion = reference_signal.assertion
    
    # Extract what reference claims
    # Common assertion types:
    # - "top_drop_step": step_id that has highest drop rate
    # - "drop_rate_at_step": {"step_id": "X", "drop_rate": 0.3}
    # - "completion_rate": 0.7
    # - "top_recommendation": step_id or action
    
    match_scores = []
    
    # Check top drop step
    if 'top_drop_step' in assertion:
        ref_top_step = assertion['top_drop_step']
        
        # Find system's top drop step
        system_top_step = None
        if 'context_graph' in system_result:
            cg = system_result['context_graph']
            if cg and 'nodes' in cg:
                nodes = cg['nodes']
                if nodes:
                    # Find node with highest drop rate
                    max_drop = 0.0
                    for node in nodes:
                        if isinstance(node, dict):
                            drop_rate = node.get('drop_rate', 0.0)
                            if drop_rate > max_drop:
                                max_drop = drop_rate
                                system_top_step = node.get('step_id', '')
                    
                    if system_top_step == ref_top_step:
                        match_scores.append(1.0)
                    else:
                        match_scores.append(0.0)
    
    # Check drop rate at specific step
    if 'drop_rate_at_step' in assertion:
        ref_data = assertion['drop_rate_at_step']
        ref_step = ref_data.get('step_id')
        ref_rate = ref_data.get('drop_rate', 0.5)
        
        # Find system's drop rate for this step
        system_rate = None
        if 'context_graph' in system_result:
            cg = system_result['context_graph']
            if cg and 'nodes' in cg:
                for node in cg['nodes']:
                    if isinstance(node, dict) and node.get('step_id') == ref_step:
                        system_rate = node.get('drop_rate', 0.5)
                        break
        
        if system_rate is not None:
            # Compare rates (within 10% = match)
            diff = abs(system_rate - ref_rate)
            if diff < 0.1:
                match_scores.append(1.0)
            elif diff < 0.2:
                match_scores.append(0.5)
            else:
                match_scores.append(0.0)
    
    # Check completion rate
    if 'completion_rate' in assertion:
        ref_completion = assertion['completion_rate']
        
        # Calculate system's completion rate
        system_completion = None
        if 'context_graph' in system_result:
            cg = system_result['context_graph']
            if cg and 'nodes' in cg:
                nodes = cg['nodes']
                if nodes:
                    # Completion = 1 - drop_rate at last step
                    last_node = nodes[-1]
                    if isinstance(last_node, dict):
                        last_drop = last_node.get('drop_rate', 0.5)
                        system_completion = 1.0 - last_drop
        
        if system_completion is not None:
            diff = abs(system_completion - ref_completion)
            if diff < 0.1:
                match_scores.append(1.0)
            elif diff < 0.2:
                match_scores.append(0.5)
            else:
                match_scores.append(0.0)
    
    # Check top recommendation
    if 'top_recommendation' in assertion:
        ref_recommendation = assertion['top_recommendation']
        
        # Find system's top recommendation
        system_top_rec = None
        if 'decision_report' in system_result:
            dr = system_result['decision_report']
            if dr and 'recommended_actions' in dr and dr['recommended_actions']:
                system_top_rec = dr['recommended_actions'][0].get('target_step')
        
        if system_top_rec:
            if system_top_rec == ref_recommendation:
                match_scores.append(1.0)
            else:
                match_scores.append(0.0)
    
    # Return average match score
    if match_scores:
        return sum(match_scores) / len(match_scores)
    else:
        # No assertions matched - return neutral
        return 0.5


def adjust_confidence_with_reference(
    system_result: Dict,
    reference_signal: ReferenceSignal,
    store: ReferenceSignalStore
) -> Dict:
    """
    Compare system result to reference and adjust confidence.
    
    If mismatch occurs, reduce confidence.
    If match occurs, maintain or slightly increase confidence.
    """
    # Compare
    match_score = compare_to_reference(system_result, reference_signal)
    
    # Record calibration
    record = CalibrationRecord(
        signal_id=reference_signal.signal_id,
        reference_signal=reference_signal,
        system_prediction=system_result,
        match_score=match_score
    )
    store.add_calibration_record(record)
    
    # Adjust confidence based on match
    confidence_assessment = system_result.get('confidence_assessment', {})
    if not confidence_assessment:
        # Create basic assessment if missing
        confidence_assessment = {
            'raw_confidence': 0.5,
            'adjusted_confidence': 0.5,
            'confidence_band': 'MODERATE'
        }
    
    current_confidence = confidence_assessment.get('adjusted_confidence', 0.5)
    
    # If mismatch (match_score < 0.5), reduce confidence
    if match_score < 0.5:
        # Mismatch penalty
        penalty = (0.5 - match_score) * 0.3  # Up to 15% reduction
        adjusted = max(0.0, current_confidence - penalty)
        
        confidence_assessment['adjusted_confidence'] = adjusted
        confidence_assessment['reference_mismatch'] = True
        confidence_assessment['reference_match_score'] = match_score
        
        # Update confidence band
        if adjusted >= 0.7:
            confidence_assessment['confidence_band'] = 'HIGH'
        elif adjusted >= 0.5:
            confidence_assessment['confidence_band'] = 'MODERATE'
        else:
            confidence_assessment['confidence_band'] = 'LOW'
    elif match_score > 0.7:
        # Good match - slight confidence boost (but cap at 0.9)
        boost = (match_score - 0.7) * 0.1  # Up to 2% increase
        adjusted = min(0.9, current_confidence + boost)
        
        confidence_assessment['adjusted_confidence'] = adjusted
        confidence_assessment['reference_match'] = True
        confidence_assessment['reference_match_score'] = match_score
    
    # Update result
    system_result['confidence_assessment'] = confidence_assessment
    
    # Add reference calibration info
    calibration_trend = store.get_calibration_trend()
    system_result['reference_calibration'] = {
        'match_score': match_score,
        'recent_calibration': calibration_trend.get('recent_match'),
        'calibration_trend': calibration_trend.get('trend')
    }
    
    return system_result


def check_reference_signals(
    system_result: Dict,
    store: ReferenceSignalStore
) -> Dict:
    """
    Check system result against all relevant reference signals.
    
    Returns:
        Updated system_result with confidence adjustments
    """
    if not store.signals:
        # No reference signals available
        return system_result
    
    # Find relevant reference signals (could filter by product, step, etc.)
    # For now, check all signals
    for signal in store.signals:
        system_result = adjust_confidence_with_reference(
            system_result,
            signal,
            store
        )
    
    return system_result

