"""
step_semantics/copy_inference.py - Copy & CTA Semantic Inference

Uses LLM to infer semantic meaning from step copy, CTAs, and helper text.
"""

from typing import Dict, List, Optional
import json
from pydantic import BaseModel

from .schema import StepSemanticProfile, KnowledgeLevel


class CopyInferenceResult(BaseModel):
    """Structured result from copy inference."""
    micro_intents: Dict[str, float]  # e.g., {"explore": 0.3, "commit": 0.1}
    promises: List[str]  # e.g., ["fast", "safe", "no commitment"]
    hidden_assumptions: List[str]  # e.g., ["user understands credit score"]
    implied_effort: float  # 0-1
    implied_knowledge: str  # "low", "medium", "high"
    urgency_signals: List[str]  # e.g., ["limited time", "act now"]
    risk_signals: List[str]  # e.g., ["data sharing", "irreversible"]


class CopyInferenceEngine:
    """
    Infers semantic meaning from copy using LLM or rule-based heuristics.
    
    Philosophy: We are not predicting clicks — we are modeling cognition.
    """
    
    def __init__(self, use_llm: bool = False, llm_client=None):
        """
        Initialize copy inference engine.
        
        Args:
            use_llm: Whether to use LLM (requires llm_client) or rule-based
            llm_client: LLM client (if use_llm=True)
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
    
    def infer(self, 
              cta_text: Optional[str] = None,
              helper_text: Optional[str] = None,
              step_description: Optional[str] = None,
              step_name: Optional[str] = None) -> CopyInferenceResult:
        """
        Infer semantic meaning from copy.
        
        Args:
            cta_text: CTA button text
            helper_text: Helper/instructional text
            step_description: Step description
            step_name: Step name/title
        
        Returns:
            CopyInferenceResult with inferred semantics
        """
        if self.use_llm and self.llm_client:
            return self._infer_with_llm(cta_text, helper_text, step_description, step_name)
        else:
            return self._infer_rule_based(cta_text, helper_text, step_description, step_name)
    
    def _infer_rule_based(self,
                          cta_text: Optional[str],
                          helper_text: Optional[str],
                          step_description: Optional[str],
                          step_name: Optional[str]) -> CopyInferenceResult:
        """
        Rule-based inference (deterministic, fast, no API calls).
        """
        # Combine all text
        all_text = " ".join(filter(None, [step_name, cta_text, helper_text, step_description]))
        text_lower = all_text.lower() if all_text else ""
        
        # Infer micro-intents
        micro_intents = {}
        if any(word in text_lower for word in ['compare', 'find best', 'find the best', 'options', 'alternatives', 'best']):
            micro_intents['compare'] = 0.6
        if any(word in text_lower for word in ['explore', 'learn', 'discover', 'understand']):
            micro_intents['explore'] = 0.5
        if any(word in text_lower for word in ['apply', 'sign up', 'commit', 'proceed']):
            micro_intents['commit'] = 0.4
        if any(word in text_lower for word in ['verify', 'validate', 'check', 'confirm', 'eligibility']):
            micro_intents['validate'] = 0.5
        if any(word in text_lower for word in ['quick', 'fast', 'instant', '60s', '60 seconds', '10s', '10 seconds']):
            micro_intents['speed'] = 0.7
        
        # Infer promises
        promises = []
        if any(word in text_lower for word in ['fast', 'quick', 'instant', '60 seconds', '10 seconds']):
            promises.append('fast')
        if any(word in text_lower for word in ['safe', 'secure', 'private', 'no pan', 'no data']):
            promises.append('safe')
        if any(word in text_lower for word in ['free', 'no cost', 'no fee']):
            promises.append('free')
        if any(word in text_lower for word in ['no commitment', 'cancel anytime', 'reversible']):
            promises.append('no_commitment')
        if any(word in text_lower for word in ['personalized', 'tailored', 'for you']):
            promises.append('personalized')
        
        # Infer hidden assumptions
        hidden_assumptions = []
        if any(word in text_lower for word in ['credit score', 'cibil', 'credit history']):
            hidden_assumptions.append('user_understands_credit_score')
        if any(word in text_lower for word in ['pan', 'aadhaar', 'kyc']):
            hidden_assumptions.append('user_has_kyc_documents')
        if any(word in text_lower for word in ['mutual funds', 'stocks', 'portfolio']):
            hidden_assumptions.append('user_understands_investments')
        if any(word in text_lower for word in ['emi', 'interest rate', 'apr']):
            hidden_assumptions.append('user_understands_financial_terms')
        
        # Infer implied effort
        implied_effort = 0.3  # Default
        if any(word in text_lower for word in ['upload', 'scan', 'take photo', 'document']):
            implied_effort = 0.7
        if any(word in text_lower for word in ['fill', 'enter', 'provide', 'details']):
            implied_effort = 0.5
        if any(word in text_lower for word in ['click', 'select', 'choose']):
            implied_effort = 0.2
        
        # Infer implied knowledge
        implied_knowledge = "medium"  # Default
        if any(word in text_lower for word in ['credit score', 'cibil', 'apr', 'emi', 'kyc']):
            implied_knowledge = "high"
        if any(word in text_lower for word in ['simple', 'easy', 'straightforward', 'no knowledge needed']):
            implied_knowledge = "low"
        
        # Infer urgency signals
        urgency_signals = []
        if any(word in text_lower for word in ['limited', 'expires', 'hurry', 'act now', 'today', 'expire']):
            urgency_signals.append('limited_time')
        if any(word in text_lower for word in ['only', 'exclusive', 'special offer']):
            urgency_signals.append('exclusivity')
        
        # Infer risk signals
        risk_signals = []
        if any(word in text_lower for word in ['share', 'provide', 'enter', 'submit']):
            risk_signals.append('data_sharing')
        if any(word in text_lower for word in ['irreversible', 'final', 'cannot undo', 'permanent']):
            risk_signals.append('irreversible_action')
        if any(word in text_lower for word in ['mandate', 'auto-debit', 'authorize']):
            risk_signals.append('financial_commitment')
        
        return CopyInferenceResult(
            micro_intents=micro_intents,
            promises=promises,
            hidden_assumptions=hidden_assumptions,
            implied_effort=implied_effort,
            implied_knowledge=implied_knowledge,
            urgency_signals=urgency_signals,
            risk_signals=risk_signals
        )
    
    def _infer_with_llm(self,
                        cta_text: Optional[str],
                        helper_text: Optional[str],
                        step_description: Optional[str],
                        step_name: Optional[str]) -> CopyInferenceResult:
        """
        LLM-based inference (more accurate, requires API).
        
        Uses structured JSON output from LLM.
        """
        prompt = f"""Analyze the following product step copy and extract semantic meaning.

Step Name: {step_name or 'N/A'}
CTA Text: {cta_text or 'N/A'}
Helper Text: {helper_text or 'N/A'}
Step Description: {step_description or 'N/A'}

Extract:
1. Micro-intents (explore, compare, commit, validate, speed) - provide scores 0-1
2. Psychological promises (fast, safe, free, no commitment, personalized)
3. Hidden assumptions about user knowledge
4. Implied effort level (0-1)
5. Implied knowledge level (low/medium/high)
6. Urgency signals
7. Risk signals

Return ONLY valid JSON in this format:
{{
    "micro_intents": {{"explore": 0.3, "compare": 0.6, "commit": 0.1}},
    "promises": ["fast", "safe"],
    "hidden_assumptions": ["user_understands_credit_score"],
    "implied_effort": 0.4,
    "implied_knowledge": "medium",
    "urgency_signals": ["limited_time"],
    "risk_signals": ["data_sharing"]
}}
"""
        
        try:
            response = self.llm_client.generate(prompt, response_format="json_object")
            result_dict = json.loads(response)
            
            return CopyInferenceResult(
                micro_intents=result_dict.get('micro_intents', {}),
                promises=result_dict.get('promises', []),
                hidden_assumptions=result_dict.get('hidden_assumptions', []),
                implied_effort=result_dict.get('implied_effort', 0.3),
                implied_knowledge=result_dict.get('implied_knowledge', 'medium'),
                urgency_signals=result_dict.get('urgency_signals', []),
                risk_signals=result_dict.get('risk_signals', [])
            )
        except Exception as e:
            # Fallback to rule-based
            return self._infer_rule_based(cta_text, helper_text, step_description, step_name)

