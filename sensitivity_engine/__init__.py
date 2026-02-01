"""
Decision Sensitivity Simulation Engine

Provides fixed personas, perturbation engine, and sensitivity analysis.
"""

from sensitivity_engine.fixed_personas import (
    FixedPersona,
    generate_fixed_personas,
    save_fixed_personas,
    load_fixed_personas
)

from sensitivity_engine.decision_trace_extended import (
    SensitivityDecisionTrace,
    ForcesApplied,
    PersonaState,
    ForceContribution,
    compute_force_contributions,
    DecisionOutcome
)

from sensitivity_engine.perturbation_engine import (
    Perturbation,
    PerturbationType,
    PerturbationEngine
)

from sensitivity_engine.sensitivity_analyzer import (
    StepSensitivity,
    PerturbationSensitivity,
    SensitivityAnalyzer
)

__all__ = [
    'FixedPersona',
    'generate_fixed_personas',
    'save_fixed_personas',
    'load_fixed_personas',
    'SensitivityDecisionTrace',
    'ForcesApplied',
    'PersonaState',
    'ForceContribution',
    'compute_force_contributions',
    'DecisionOutcome',
    'Perturbation',
    'PerturbationType',
    'PerturbationEngine',
    'StepSensitivity',
    'PerturbationSensitivity',
    'SensitivityAnalyzer'
]

