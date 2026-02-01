"""
Aggregation layer for SHAP values.

Aggregates SHAP values across steps, drop decisions, and persona classes.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


def aggregate_step_importance(
    traces_with_shap: List[Dict],
    step_id: Optional[str] = None
) -> Dict:
    """
    Aggregate SHAP values by step.
    
    Computes mean absolute SHAP value per feature per step,
    and ranks features by decision influence.
    
    Args:
        traces_with_shap: List of traces with 'shap_values' key
        step_id: If provided, filter to this step only
    
    Returns:
        Dictionary with:
        - step_id
        - feature_importance: {feature_name: mean_abs_shap}
        - feature_rank: List of (feature, importance) sorted by importance
        - total_decisions: Count of decisions at this step
        - continue_count: Count of CONTINUE decisions
        - drop_count: Count of DROP decisions
    """
    # Filter by step if needed
    if step_id:
        traces = [t for t in traces_with_shap if t.get('step_id') == step_id]
    else:
        traces = traces_with_shap
    
    if not traces:
        return {}
    
    # Get step_id from first trace
    step_id_actual = traces[0].get('step_id', 'unknown')
    
    # Aggregate SHAP values
    feature_abs_shap = defaultdict(float)
    feature_counts = defaultdict(int)
    
    continue_count = 0
    drop_count = 0
    
    for trace in traces:
        shap_values = trace.get('shap_values', {})
        if not shap_values:
            continue
        
        decision = trace.get('decision', 'DROP')
        if decision == 'CONTINUE':
            continue_count += 1
        else:
            drop_count += 1
        
        feature_contributions = shap_values.get('feature_contributions', {})
        for feature, contribution in feature_contributions.items():
            feature_abs_shap[feature] += abs(contribution)
            feature_counts[feature] += 1
    
    # Compute mean absolute SHAP
    feature_importance = {
        feature: feature_abs_shap[feature] / feature_counts[feature]
        if feature_counts[feature] > 0 else 0.0
        for feature in feature_abs_shap.keys()
    }
    
    # Rank features
    feature_rank = sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        'step_id': step_id_actual,
        'feature_importance': feature_importance,
        'feature_rank': feature_rank,
        'total_decisions': len(traces),
        'continue_count': continue_count,
        'drop_count': drop_count
    }


def aggregate_drop_trigger_analysis(
    traces_with_shap: List[Dict]
) -> Dict:
    """
    Analyze which features most strongly cause DROP decisions.
    
    Args:
        traces_with_shap: List of traces with 'shap_values' key
    
    Returns:
        Dictionary with:
        - drop_triggers: {feature_name: mean_negative_shap} for DROP decisions
        - insufficient_features: {feature_name: mean_positive_shap} for DROP decisions
        - drop_count: Total DROP decisions analyzed
        - top_drop_triggers: Ranked list of features causing drops
    """
    drop_traces = [t for t in traces_with_shap if t.get('decision') == 'DROP']
    
    if not drop_traces:
        return {
            'drop_triggers': {},
            'insufficient_features': {},
            'drop_count': 0,
            'top_drop_triggers': []
        }
    
    # For DROP decisions, negative SHAP values indicate features pushing toward drop
    # Positive SHAP values indicate features that were insufficient (should have pushed continue)
    feature_negative_shap = defaultdict(list)
    feature_positive_shap = defaultdict(list)
    
    for trace in drop_traces:
        shap_values = trace.get('shap_values', {})
        if not shap_values:
            continue
        
        feature_contributions = shap_values.get('feature_contributions', {})
        for feature, contribution in feature_contributions.items():
            if contribution < 0:
                feature_negative_shap[feature].append(contribution)
            else:
                feature_positive_shap[feature].append(contribution)
    
    # Compute means
    drop_triggers = {
        feature: np.mean(values) if values else 0.0
        for feature, values in feature_negative_shap.items()
    }
    
    insufficient_features = {
        feature: np.mean(values) if values else 0.0
        for feature, values in feature_positive_shap.items()
    }
    
    # Rank drop triggers by magnitude
    top_drop_triggers = sorted(
        drop_triggers.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    return {
        'drop_triggers': drop_triggers,
        'insufficient_features': insufficient_features,
        'drop_count': len(drop_traces),
        'top_drop_triggers': top_drop_triggers
    }


def aggregate_persona_sensitivity(
    traces_with_shap: List[Dict],
    persona_classifier: callable = None
) -> Dict:
    """
    Compare SHAP distributions across persona clusters.
    
    Args:
        traces_with_shap: List of traces with 'shap_values' key
        persona_classifier: Function that takes a trace and returns persona class
    
    Returns:
        Dictionary with:
        - persona_classes: {class_name: {feature: mean_abs_shap}}
        - feature_sensitivity_by_class: {feature: {class: mean_abs_shap}}
    """
    if persona_classifier is None:
        # Default: classify by intent_strength quartiles
        def default_classifier(trace):
            intent = trace.get('state_before', {}).get('intent_strength', 0.5)
            if intent < 0.25:
                return 'low_intent'
            elif intent < 0.5:
                return 'medium_low_intent'
            elif intent < 0.75:
                return 'medium_high_intent'
            else:
                return 'high_intent'
        persona_classifier = default_classifier
    
    # Group by persona class
    by_class = defaultdict(list)
    for trace in traces_with_shap:
        persona_class = persona_classifier(trace)
        by_class[persona_class].append(trace)
    
    persona_classes = {}
    feature_sensitivity_by_class = defaultdict(lambda: defaultdict(float))
    
    for class_name, class_traces in by_class.items():
        # Aggregate SHAP for this class
        feature_abs_shap = defaultdict(float)
        feature_counts = defaultdict(int)
        
        for trace in class_traces:
            shap_values = trace.get('shap_values', {})
            if not shap_values:
                continue
            
            feature_contributions = shap_values.get('feature_contributions', {})
            for feature, contribution in feature_contributions.items():
                feature_abs_shap[feature] += abs(contribution)
                feature_counts[feature] += 1
        
        class_importance = {
            feature: feature_abs_shap[feature] / feature_counts[feature]
            if feature_counts[feature] > 0 else 0.0
            for feature in feature_abs_shap.keys()
        }
        
        persona_classes[class_name] = class_importance
        
        # Also build cross-class view
        for feature, importance in class_importance.items():
            feature_sensitivity_by_class[feature][class_name] = importance
    
    return {
        'persona_classes': persona_classes,
        'feature_sensitivity_by_class': dict(feature_sensitivity_by_class)
    }

