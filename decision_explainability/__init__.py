"""
Decision Explainability Module

SHAP-style explainability for behavioral simulation decisions.
"""

from decision_explainability.shap_model import (
    DecisionSurrogateModel,
    compute_shap_values_for_decision,
    prepare_decision_features
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

__all__ = [
    'DecisionSurrogateModel',
    'compute_shap_values_for_decision',
    'prepare_decision_features',
    'aggregate_step_importance',
    'aggregate_drop_trigger_analysis',
    'aggregate_persona_sensitivity',
    'generate_feature_importance_report',
    'generate_step_fragility_report',
    'generate_persona_sensitivity_report'
]

