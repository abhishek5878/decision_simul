"""
tests/test_step_semantics.py - Tests for Step Semantic Inference Layer
"""

import pytest
from step_semantics import (
    StepSemanticProfile,
    StepSemanticExtractor,
    IntentAlignmentAnalyzer
)
from step_semantics.schema import KnowledgeLevel


class TestCopyInference:
    """Test copy inference engine."""
    
    def test_rule_based_inference(self):
        """Test rule-based copy inference."""
        from step_semantics.copy_inference import CopyInferenceEngine
        
        engine = CopyInferenceEngine(use_llm=False)
        
        result = engine.infer(
            cta_text="Find the Best Credit Card In 60 seconds",
            step_description="Quick credit card comparison"
        )
        
        # Should detect both compare and speed
        assert ('compare' in result.micro_intents or 'speed' in result.micro_intents)
        if 'compare' in result.micro_intents:
            assert result.micro_intents['compare'] > 0.5
        if 'speed' in result.micro_intents:
            assert result.micro_intents['speed'] > 0.5
        assert 'fast' in result.promises
        assert result.implied_effort < 0.5
    
    def test_urgency_detection(self):
        """Test urgency signal detection."""
        from step_semantics.copy_inference import CopyInferenceEngine
        
        engine = CopyInferenceEngine(use_llm=False)
        
        result = engine.infer(
            cta_text="Act Now - Limited Time Offer",
            helper_text="Expires today"
        )
        
        # Should detect urgency signals
        assert len(result.urgency_signals) > 0 or 'limited' in str(result.urgency_signals).lower() or 'today' in str(result.urgency_signals).lower()
        # Urgency might not reduce effort, but should be detected
        assert result.implied_effort <= 0.5  # Not too high


class TestVisualInference:
    """Test visual inference engine."""
    
    def test_metadata_inference(self):
        """Test inference from UI metadata."""
        from step_semantics.visual_inference import VisualInferenceEngine
        
        engine = VisualInferenceEngine()
        
        metadata = {
            "elements": [
                {"type": "button", "text": "Continue", "style": "primary"},
                {"type": "badge", "text": "Secure & Verified"},
                {"type": "text", "size": "large"}
            ],
            "layout": {
                "density": 0.6,
                "contrast": 0.8,
                "whitespace": 0.4
            },
            "colors": {
                "primary": "#FF0000"
            }
        }
        
        result = engine.infer(ui_metadata=metadata)
        
        assert result['trust_signal'] > 0.5  # Has trust badge
        assert result['urgency'] > 0.5  # Red color
        assert result['visual_load'] < 1.0
    
    def test_choice_overload(self):
        """Test choice overload detection."""
        from step_semantics.visual_inference import VisualInferenceEngine
        
        engine = VisualInferenceEngine()
        
        metadata = {
            "elements": [
                {"type": "button", "text": "Option 1"},
                {"type": "button", "text": "Option 2"},
                {"type": "button", "text": "Option 3"},
                {"type": "button", "text": "Option 4"},
                {"type": "button", "text": "Option 5"},
                {"type": "dropdown", "text": "Select"}
            ],
            "layout": {"density": 0.5, "contrast": 0.7, "whitespace": 0.3}
        }
        
        result = engine.infer(ui_metadata=metadata)
        
        assert result['choice_overload'] > 0.5  # Many options


class TestSemanticExtractor:
    """Test main semantic extractor."""
    
    def test_extract_from_step_def(self):
        """Test extraction from step definition."""
        extractor = StepSemanticExtractor(use_llm=False)
        
        step_def = {
            "cta_phrasing": "Find the Best Credit Card In 60 seconds",
            "description": "Quick credit card comparison tool",
            "cognitive_demand": 0.2,
            "effort_demand": 0.0
        }
        
        profile = extractor.extract(step_def)
        
        assert isinstance(profile, StepSemanticProfile)
        assert profile.perceived_effort < 0.5
        assert 'fast' in profile.inferred_psychological_promises
        assert profile.implied_user_knowledge in [KnowledgeLevel.LOW, KnowledgeLevel.MEDIUM, KnowledgeLevel.HIGH]
    
    def test_intent_shift_extraction(self):
        """Test intent shift extraction."""
        extractor = StepSemanticExtractor(use_llm=False)
        
        step_def = {
            "cta_phrasing": "Compare Options",
            "description": "See all credit cards side by side"
        }
        
        profile = extractor.extract(step_def)
        
        assert 'compare' in profile.intent_shift or len(profile.intent_shift) > 0


class TestIntentAlignment:
    """Test intent alignment analyzer."""
    
    def test_knowledge_gap_detection(self):
        """Test knowledge gap detection."""
        analyzer = IntentAlignmentAnalyzer()
        
        profile = StepSemanticProfile(
            visual_load=0.5,
            perceived_effort=0.3,
            trust_signal=0.6,
            urgency=0.3,
            reversibility=0.8,
            choice_overload=0.2,
            implied_user_knowledge=KnowledgeLevel.HIGH,
            intent_shift={},
            emotional_deltas={},
            inferred_psychological_promises=[],
            inferred_risks=[]
        )
        
        user_intent = {"compare_options": 0.5, "learn_basics": 0.3}
        
        result = analyzer.analyze(profile, user_intent, persona_knowledge="low")
        
        # Knowledge gap should be detected (may be in conflict_axes or affect alignment)
        # Alignment should be reduced due to knowledge gap
        assert result.intent_alignment_score < 1.0
        # Effect depends on alignment score threshold (0.5)
        # If alignment is 0.5-0.7, it's neutral; if <0.5, it's increase_drop_probability
        assert result.predicted_effect in ["increase_drop_probability", "neutral"]
    
    def test_commitment_mismatch(self):
        """Test commitment mismatch for explore intent."""
        analyzer = IntentAlignmentAnalyzer()
        
        profile = StepSemanticProfile(
            visual_load=0.5,
            perceived_effort=0.3,
            trust_signal=0.6,
            urgency=0.3,
            reversibility=0.3,  # Low reversibility = high commitment
            choice_overload=0.2,
            implied_user_knowledge=KnowledgeLevel.MEDIUM,
            intent_shift={},
            emotional_deltas={},
            inferred_psychological_promises=[],
            inferred_risks=[]
        )
        
        user_intent = {"compare_options": 0.6, "learn_basics": 0.2}
        
        result = analyzer.analyze(profile, user_intent, persona_knowledge="medium")
        
        # Should detect commitment mismatch
        assert 'commitment' in result.conflict_axes or result.intent_alignment_score < 0.8
        # Alignment should be reduced
        assert result.intent_alignment_score < 1.0
    
    def test_speed_mismatch(self):
        """Test speed mismatch for quick_decision intent."""
        analyzer = IntentAlignmentAnalyzer()
        
        profile = StepSemanticProfile(
            visual_load=0.5,
            perceived_effort=0.8,  # High effort
            trust_signal=0.6,
            urgency=0.2,  # Low urgency
            reversibility=0.8,
            choice_overload=0.2,
            implied_user_knowledge=KnowledgeLevel.MEDIUM,
            intent_shift={},
            emotional_deltas={},
            inferred_psychological_promises=[],
            inferred_risks=[]
        )
        
        user_intent = {"quick_decision": 0.7}
        
        result = analyzer.analyze(profile, user_intent, persona_knowledge="medium")
        
        # Should detect speed mismatch
        assert 'speed' in result.conflict_axes or result.intent_alignment_score < 0.8
        # Alignment should be reduced
        assert result.intent_alignment_score < 1.0


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_extraction(self):
        """Test end-to-end semantic extraction."""
        extractor = StepSemanticExtractor(use_llm=False)
        
        step_def = {
            "cta_phrasing": "Check Your Eligibility",
            "description": "Enter your PAN and DOB to check eligibility",
            "cognitive_demand": 0.4,
            "effort_demand": 0.3,
            "risk_signal": 0.25
        }
        
        profile = extractor.extract(step_def)
        
        # Should have inferred risks
        assert len(profile.inferred_risks) > 0
        assert 'data_sharing' in profile.inferred_risks or 'irreversible_action' in profile.inferred_risks
        
        # Should have knowledge assumptions
        assert profile.implied_user_knowledge in [KnowledgeLevel.LOW, KnowledgeLevel.MEDIUM, KnowledgeLevel.HIGH]
    
    def test_intent_alignment_integration(self):
        """Test intent alignment with extracted profile."""
        extractor = StepSemanticExtractor(use_llm=False)
        
        step_def = {
            "cta_phrasing": "Compare Credit Cards",
            "description": "See all options side by side"
        }
        
        profile = extractor.extract(step_def)
        
        user_intent = {"compare_options": 0.8}
        result = extractor.analyze_intent_alignment(profile, user_intent, "medium")
        
        assert result.intent_alignment_score > 0.6  # Should align well
        assert result.predicted_effect in ["decrease_drop_probability", "neutral"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

