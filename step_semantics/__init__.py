"""
step_semantics - Step Semantic Inference Layer

Extracts rich latent signals from product steps (copy, UI, visuals) and feeds
them into the existing intent + energy simulation engine.

Philosophy: We are not predicting clicks — we are modeling cognition.
"""

from .schema import StepSemanticProfile, IntentShift, EmotionalDelta
from .semantic_extractor import StepSemanticExtractor
from .copy_inference import CopyInferenceEngine
from .visual_inference import VisualInferenceEngine
from .intent_alignment import IntentAlignmentAnalyzer

__all__ = [
    'StepSemanticProfile',
    'IntentShift',
    'EmotionalDelta',
    'StepSemanticExtractor',
    'CopyInferenceEngine',
    'VisualInferenceEngine',
    'IntentAlignmentAnalyzer',
]

