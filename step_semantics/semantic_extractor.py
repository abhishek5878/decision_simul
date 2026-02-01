"""
step_semantics/semantic_extractor.py - Main Semantic Extraction Orchestrator

Orchestrates extraction of semantic profiles from product steps.
"""

from typing import Dict, Optional
from .schema import StepSemanticProfile, KnowledgeLevel
from .copy_inference import CopyInferenceEngine, CopyInferenceResult
from .visual_inference import VisualInferenceEngine
from .intent_alignment import IntentAlignmentAnalyzer, IntentAlignmentResult


class StepSemanticExtractor:
    """
    Main orchestrator for extracting semantic profiles from product steps.
    
    Philosophy: We are not predicting clicks — we are modeling cognition.
    """
    
    def __init__(self, use_llm: bool = False, llm_client=None):
        """
        Initialize semantic extractor.
        
        Args:
            use_llm: Whether to use LLM for copy inference
            llm_client: LLM client (if use_llm=True)
        """
        self.copy_engine = CopyInferenceEngine(use_llm=use_llm, llm_client=llm_client)
        self.visual_engine = VisualInferenceEngine()
        self.alignment_analyzer = IntentAlignmentAnalyzer()
    
    def extract(self,
                step_def: Dict,
                ui_metadata: Optional[Dict] = None,
                screenshot_path: Optional[str] = None) -> StepSemanticProfile:
        """
        Extract complete semantic profile from a product step.
        
        Args:
            step_def: Step definition dict (from product_steps):
                {
                    "cognitive_demand": 0.3,
                    "effort_demand": 0.2,
                    "cta_phrasing": "Continue",
                    "description": "Step description",
                    ...
                }
            ui_metadata: Optional structured UI metadata
            screenshot_path: Optional path to screenshot
        
        Returns:
            StepSemanticProfile with all semantic information
        """
        # 1. Extract copy semantics
        copy_result = self.copy_engine.infer(
            cta_text=step_def.get('cta_phrasing'),
            helper_text=step_def.get('helper_text'),
            step_description=step_def.get('description'),
            step_name=list(step_def.keys())[0] if isinstance(step_def, dict) and 'name' not in step_def else step_def.get('name')
        )
        
        # 2. Extract visual semantics
        visual_result = self.visual_engine.infer(
            ui_metadata=ui_metadata,
            screenshot_path=screenshot_path
        )
        
        # 3. Combine into semantic profile
        # Map copy promises to psychological promises
        psychological_promises = copy_result.promises.copy()
        if copy_result.micro_intents.get('speed', 0) > 0.5:
            psychological_promises.append('fast')
        
        # Map risk signals to inferred risks
        inferred_risks = copy_result.risk_signals.copy()
        if visual_result.get('reversibility', 0.7) < 0.5:
            inferred_risks.append('irreversible_action')
        
        # Compute intent shift from micro-intents
        intent_shift = {}
        for intent, score in copy_result.micro_intents.items():
            if score > 0.3:
                intent_shift[intent] = score - 0.3  # Normalize
        
        # Compute emotional deltas
        emotional_deltas = {}
        if copy_result.urgency_signals:
            emotional_deltas['anxiety'] = 0.2  # Urgency can increase anxiety
        if 'safe' in copy_result.promises:
            emotional_deltas['confidence'] = 0.2  # Safety increases confidence
        if copy_result.implied_effort > 0.6:
            emotional_deltas['fatigue'] = 0.2  # High effort increases fatigue
        
        # Map implied knowledge
        knowledge_map = {
            'low': KnowledgeLevel.LOW,
            'medium': KnowledgeLevel.MEDIUM,
            'high': KnowledgeLevel.HIGH
        }
        implied_knowledge = knowledge_map.get(copy_result.implied_knowledge, KnowledgeLevel.MEDIUM)
        
        # Combine visual and copy into perceived effort
        perceived_effort = max(
            copy_result.implied_effort,
            visual_result.get('visual_load', 0.5) * 0.7
        )
        
        return StepSemanticProfile(
            visual_load=visual_result.get('visual_load', 0.5),
            perceived_effort=perceived_effort,
            trust_signal=visual_result.get('trust_signal', 0.5),
            urgency=visual_result.get('urgency', 0.3),
            reversibility=visual_result.get('reversibility', 0.7),
            choice_overload=visual_result.get('choice_overload', 0.2),
            implied_user_knowledge=implied_knowledge,
            intent_shift=intent_shift,
            emotional_deltas=emotional_deltas,
            inferred_psychological_promises=psychological_promises,
            inferred_risks=inferred_risks,
            extraction_confidence=0.8 if not self.copy_engine.use_llm else 0.9,
            extraction_method="llm" if self.copy_engine.use_llm else "rule_based"
        )
    
    def analyze_intent_alignment(self,
                                 semantic_profile: StepSemanticProfile,
                                 user_intent: Dict[str, float],
                                 persona_knowledge: str = "medium") -> IntentAlignmentResult:
        """
        Analyze how well step aligns with user intent.
        
        Args:
            semantic_profile: Step's semantic profile
            user_intent: User's intent distribution
            persona_knowledge: Persona's knowledge level
        
        Returns:
            IntentAlignmentResult
        """
        return self.alignment_analyzer.analyze(
            semantic_profile,
            user_intent,
            persona_knowledge
        )

