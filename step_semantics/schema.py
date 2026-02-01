"""
step_semantics/schema.py - Core Schema for Step Semantic Profiles

Defines the structure for semantic information extracted from product steps.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum


class KnowledgeLevel(str, Enum):
    """Implied user knowledge level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IntentShift(BaseModel):
    """How a step shifts user intent."""
    intent_type: str  # e.g., "explore", "commit", "compare", "validate"
    delta: float = Field(..., ge=-1.0, le=1.0)  # -1 to +1 shift magnitude
    direction: str = Field(..., pattern="^(increase|decrease)$")


class EmotionalDelta(BaseModel):
    """Emotional state changes induced by step."""
    emotion: str  # e.g., "confidence", "anxiety", "fatigue", "excitement"
    delta: float = Field(..., ge=-1.0, le=1.0)  # -1 to +1 change
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)  # How confident we are in this inference


class StepSemanticProfile(BaseModel):
    """
    Rich semantic profile of a product step.
    
    Captures psychological, visual, and cognitive signals that affect
    user behavior beyond simple numeric attributes.
    """
    
    # Cognitive Load & Effort
    visual_load: float = Field(..., ge=0.0, le=1.0, description="Visual/cognitive load (0=low, 1=high)")
    perceived_effort: float = Field(..., ge=0.0, le=1.0, description="How hard this step feels")
    choice_overload: float = Field(..., ge=0.0, le=1.0, description="Number & complexity of options")
    
    # Trust & Credibility
    trust_signal: float = Field(..., ge=0.0, le=1.0, description="Perceived credibility/trust")
    
    # Temporal & Control
    urgency: float = Field(..., ge=0.0, le=1.0, description="Time pressure perceived")
    reversibility: float = Field(..., ge=0.0, le=1.0, description="Perceived ability to undo (1=fully reversible)")
    
    # Knowledge Assumptions
    implied_user_knowledge: KnowledgeLevel = Field(..., description="What knowledge level does step assume?")
    
    # Intent Dynamics
    intent_shift: Dict[str, float] = Field(
        default_factory=dict,
        description="How step shifts user intent (e.g., {'explore': +0.2, 'commit': -0.1})"
    )
    
    # Emotional Impact
    emotional_deltas: Dict[str, float] = Field(
        default_factory=dict,
        description="Emotional state changes (e.g., {'confidence': +0.3, 'anxiety': -0.2})"
    )
    
    # Psychological Promises & Risks
    inferred_psychological_promises: List[str] = Field(
        default_factory=list,
        description="What psychological promises does step make? (e.g., 'fast', 'safe', 'no commitment')"
    )
    inferred_risks: List[str] = Field(
        default_factory=list,
        description="What risks does step imply? (e.g., 'data sharing', 'irreversible action')"
    )
    
    # Metadata
    extraction_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence in extraction")
    extraction_method: str = Field(default="rule_based", description="How was this extracted? (rule_based, llm, vision)")
    
    class Config:
        use_enum_values = True


class IntentAlignmentResult(BaseModel):
    """Result of intent alignment analysis."""
    intent_alignment_score: float = Field(..., ge=0.0, le=1.0, description="How well step aligns with user intent")
    conflict_axes: List[str] = Field(default_factory=list, description="Axes of conflict (e.g., 'commitment', 'knowledge_gap')")
    predicted_effect: str = Field(..., description="Predicted effect: 'increase_drop_probability', 'decrease_drop_probability', 'neutral'")
    semantic_reason: str = Field(..., description="Human-readable reason for alignment/mismatch")
    friction_delta: float = Field(default=0.0, description="Expected change in friction (positive = more friction)")

