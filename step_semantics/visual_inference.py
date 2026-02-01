"""
step_semantics/visual_inference.py - Visual & Layout Semantic Inference

Infers semantic meaning from visual elements, layout, and UI structure.
Rule-based initially, with hooks for CV models later.
"""

from typing import Dict, List, Optional
from .schema import StepSemanticProfile


class VisualInferenceEngine:
    """
    Infers semantic meaning from visual elements and layout.
    
    Currently rule-based, but designed to be extended with CV models.
    Philosophy: We are not predicting clicks — we are modeling cognition.
    """
    
    def __init__(self):
        """Initialize visual inference engine."""
        pass
    
    def infer(self,
              ui_metadata: Optional[Dict] = None,
              screenshot_path: Optional[str] = None) -> Dict:
        """
        Infer visual semantics from UI metadata or screenshot.
        
        Args:
            ui_metadata: Structured UI metadata (preferred):
                {
                    "elements": [
                        {"type": "button", "text": "Continue", "style": "primary"},
                        {"type": "text", "size": "large"},
                        {"type": "badge", "text": "Secure"}
                    ],
                    "layout": {
                        "density": 0.6,  # 0-1
                        "contrast": 0.8,  # 0-1
                        "whitespace": 0.4  # 0-1
                    },
                    "colors": {
                        "primary": "#FF0000",  # Urgency
                        "background": "#FFFFFF"
                    }
                }
            screenshot_path: Path to screenshot (for future CV integration)
        
        Returns:
            Dict with visual semantic scores
        """
        if ui_metadata:
            return self._infer_from_metadata(ui_metadata)
        elif screenshot_path:
            # Future: Use CV model
            return self._infer_from_screenshot(screenshot_path)
        else:
            return self._default_inference()
    
    def _infer_from_metadata(self, metadata: Dict) -> Dict:
        """
        Infer from structured UI metadata (rule-based).
        """
        elements = metadata.get('elements', [])
        layout = metadata.get('layout', {})
        colors = metadata.get('colors', {})
        
        # Visual load (cognitive load from visual complexity)
        density = layout.get('density', 0.5)
        contrast = layout.get('contrast', 0.5)
        num_elements = len(elements)
        visual_load = min(1.0, (density * 0.4 + (num_elements / 10) * 0.3 + (1 - contrast) * 0.3))
        
        # Trust signals
        trust_signal = 0.5  # Default
        for elem in elements:
            if elem.get('type') == 'badge':
                badge_text = elem.get('text', '').lower()
                if any(word in badge_text for word in ['secure', 'safe', 'verified', 'trusted', 'rbi', 'sebi']):
                    trust_signal = min(1.0, trust_signal + 0.2)
            if elem.get('type') == 'logo':
                trust_signal = min(1.0, trust_signal + 0.1)
        
        # Urgency (from colors, button styles)
        urgency = 0.3  # Default
        primary_color = colors.get('primary', '').upper()
        if primary_color in ['#FF0000', '#FF4500', '#FF6347']:  # Red/orange
            urgency = 0.7
        elif primary_color in ['#FFD700', '#FFA500']:  # Gold/orange
            urgency = 0.6
        
        for elem in elements:
            if elem.get('type') == 'button':
                style = elem.get('style', '').lower()
                if style == 'primary' and 'now' in elem.get('text', '').lower():
                    urgency = min(1.0, urgency + 0.2)
        
        # Choice overload
        choice_overload = 0.0
        buttons = [e for e in elements if e.get('type') == 'button']
        dropdowns = [e for e in elements if e.get('type') == 'dropdown']
        if len(buttons) > 3:
            choice_overload = min(1.0, (len(buttons) - 3) * 0.2)
        if len(dropdowns) > 0:
            choice_overload = min(1.0, choice_overload + len(dropdowns) * 0.3)
        
        # Reversibility (from UI cues)
        reversibility = 0.7  # Default (most steps feel reversible)
        for elem in elements:
            if elem.get('type') == 'button' and 'cancel' in elem.get('text', '').lower():
                reversibility = 1.0
            if 'irreversible' in elem.get('text', '').lower() or 'final' in elem.get('text', '').lower():
                reversibility = 0.2
        
        return {
            'visual_load': visual_load,
            'trust_signal': trust_signal,
            'urgency': urgency,
            'choice_overload': choice_overload,
            'reversibility': reversibility
        }
    
    def _infer_from_screenshot(self, screenshot_path: str) -> Dict:
        """
        Infer from screenshot (future: CV model integration).
        
        For now, returns default values.
        """
        # TODO: Integrate CV model (CLIP, image embeddings, etc.)
        return self._default_inference()
    
    def _default_inference(self) -> Dict:
        """Default inference when no data available."""
        return {
            'visual_load': 0.5,
            'trust_signal': 0.5,
            'urgency': 0.3,
            'choice_overload': 0.2,
            'reversibility': 0.7
        }

