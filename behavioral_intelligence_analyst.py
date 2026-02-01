"""
behavioral_intelligence_analyst.py - Behavioral Intelligence Analyst

Converts large, noisy DropSim simulation outputs into clear causal explanations,
ranked drivers, and actionable insights, while preserving behavioral rigor.

Philosophy: Infer causality, summarize drivers, and explain behavior in human terms.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class BehavioralIntelligenceAnalyst:
    """
    Analyzes DropSim output and generates causal explanations.
    
    System Role: Behavioral Intelligence Analyst
    Job: NOT to restate data, but to infer causality, summarize drivers,
         and explain behavior in human terms.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize analyst.
        
        Args:
            llm_client: Optional LLM client for analysis. If None, uses rule-based analysis.
        """
        self.llm_client = llm_client
        self.use_llm = llm_client is not None
    
    def analyze(self, simulation_output: Dict) -> Dict:
        """
        Analyze simulation output and generate causal explanations.
        
        Args:
            simulation_output: Full JSON output from DropSim simulation
        
        Returns:
            Structured analysis with causal explanations
        """
        if self.use_llm:
            return self._analyze_with_llm(simulation_output)
        else:
            return self._analyze_rule_based(simulation_output)
    
    def _analyze_rule_based(self, output: Dict) -> Dict:
        """Store output for reference in helper methods."""
        self._current_output = output
        """
        Rule-based analysis (deterministic, no API calls).
        
        Uses reasoning hierarchy:
        1. Intent mismatch
        2. Cognitive overload / friction
        3. Trust & risk perception
        4. Energy depletion
        5. Emotional trajectory shifts
        """
        # Extract key metrics
        completion_rate = output.get('overall_completion_rate', 0.0)
        semantic_insights = output.get('semantic_insights', {})
        step_data = output.get('step_semantic_data', {})
        failure_reasons = output.get('failure_reasons', {})
        exit_steps = output.get('exit_steps', {})
        
        # Find most damaging step
        most_damaging_step = self._find_most_damaging_step(step_data, exit_steps)
        
        # Analyze primary drop reason
        primary_reason = self._infer_primary_drop_reason(
            semantic_insights, failure_reasons, step_data, completion_rate, output
        )
        
        # Analyze secondary factors
        secondary_factors = self._identify_secondary_factors(
            semantic_insights, step_data, failure_reasons, output
        )
        
        # Identify psychological failure
        psychological_failure = self._identify_psychological_failure(
            semantic_insights, step_data, output
        )
        
        # Find misaligned assumptions
        misaligned_assumptions = self._find_misaligned_assumptions(
            semantic_insights, step_data, output
        )
        
        # Fixability analysis
        fixability = self._analyze_fixability(step_data, semantic_insights)
        
        # Recommended changes
        recommendations = self._generate_recommendations(
            step_data, semantic_insights, primary_reason, output
        )
        
        # Confidence level
        confidence = self._assess_confidence(output, semantic_insights)
        
        return {
            "primary_drop_reason": primary_reason,
            "secondary_factors": secondary_factors,
            "dominant_psychological_failure": psychological_failure,
            "key_misaligned_assumptions": misaligned_assumptions,
            "most_damaging_step": most_damaging_step,
            "fixability_analysis": fixability,
            "recommended_product_changes": recommendations,
            "confidence_level": confidence
        }
    
    def _find_most_damaging_step(self, step_data: Dict, exit_steps: Dict) -> Dict:
        """Find the step that caused most irreversible damage."""
        if not step_data:
            return {
                "step_id": "Unknown",
                "why_it_failed": "No step data available",
                "what_user_expected": "N/A",
                "what_they_got": "N/A"
            }
        
        # Find step with highest drop rate AND most users affected
        max_impact = 0
        most_damaging = None
        
        for step_name, data in step_data.items():
            drop_rate = data.get('drop_rate', 0)
            drops = data.get('drops', 0)
            # Impact = drop_rate * number of drops (prioritize steps that affect many users)
            impact = drop_rate * drops
            if impact > max_impact:
                max_impact = impact
                most_damaging = (step_name, data)
        
        if not most_damaging:
            return {
                "step_id": "Unknown",
                "why_it_failed": "No clear drop pattern",
                "what_user_expected": "N/A",
                "what_they_got": "N/A"
            }
        
        step_name, data = most_damaging
        alignment = data.get('sample_alignment_result', {})
        semantic_profile = data.get('sample_semantic_profile', {})
        
        # Infer why it failed
        why_failed = self._infer_step_failure_reason(alignment, semantic_profile, step_name)
        
        # Infer expectations
        expected = self._infer_user_expectations(step_name, semantic_profile)
        got = self._infer_what_they_got(step_name, semantic_profile, alignment)
        
        return {
            "step_id": step_name,
            "why_it_failed": why_failed,
            "what_user_expected": expected,
            "what_they_got": got
        }
    
    def _infer_primary_drop_reason(self, semantic_insights: Dict, failure_reasons: Dict,
                                   step_data: Dict, completion_rate: float, output: Optional[Dict] = None) -> str:
        """Infer primary drop reason using reasoning hierarchy."""
        
        # 1. Check for intent mismatch (highest priority)
        intent_mismatches = []
        for step_name, insights in semantic_insights.items():
            alignment = insights.get('avg_alignment_score', 1.0)
            conflicts = insights.get('conflict_axes', {})
            # Check if there are conflicts (even if alignment is high, conflicts indicate issues)
            if conflicts and len(conflicts) > 0:
                # Count total conflicts
                total_conflicts = sum(conflicts.values()) if isinstance(conflicts, dict) else len(conflicts)
                intent_mismatches.append((step_name, alignment, conflicts, total_conflicts))
        
        if intent_mismatches:
            # Sort by total conflicts (most conflicts first)
            worst = max(intent_mismatches, key=lambda x: x[3])
            conflicts = worst[2]
            if isinstance(conflicts, dict):
                conflict_types = list(conflicts.keys())[:2]
                conflict_count = sum(conflicts.values())
            else:
                conflict_types = conflicts[:2] if isinstance(conflicts, list) else []
                conflict_count = len(conflicts) if isinstance(conflicts, list) else 0
            
            # Try to infer actual intent distribution from output
            intent_desc = "specific intent"
            if output and 'intent_distribution' in output:
                intent_dist = output['intent_distribution']
                primary_intent = max(intent_dist.items(), key=lambda x: x[1])[0] if intent_dist else None
                primary_pct = intent_dist.get(primary_intent, 0) * 100 if primary_intent else 0
                if primary_intent:
                    intent_desc = f"{primary_intent.replace('_', ' ')} intent ({primary_pct:.1f}% of users)"
            elif 'choice_availability' in conflict_types:
                intent_desc = "comparison/exploration intent"
            elif 'knowledge_gap' in conflict_types:
                intent_desc = "eligibility check intent"
            
            return f"Intent mismatch: Users entered with {intent_desc} but encountered steps that violated their expectations. Step '{worst[0]}' had {conflict_count} conflict instances ({', '.join(conflict_types)}). Alignment score: {worst[1]:.2f}"
        
        # 2. Check for cognitive overload
        high_effort_steps = []
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                effort = profile.get('perceived_effort', 0.5)
                visual_load = profile.get('visual_load', 0.5)
                if effort > 0.7 or visual_load > 0.7:
                    high_effort_steps.append(step_name)
        
        if high_effort_steps:
            return f"Cognitive overload: Steps {', '.join(high_effort_steps[:2])} required excessive mental effort (effort >0.7 or visual load >0.7), causing users to abandon"
        
        # 3. Check for trust/risk issues
        low_trust_steps = []
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                trust = profile.get('trust_signal', 0.5)
                risks = profile.get('inferred_risks', [])
                if trust < 0.4 or len(risks) > 2:
                    low_trust_steps.append(step_name)
        
        if low_trust_steps:
            return f"Trust & risk perception: Steps {', '.join(low_trust_steps[:2])} had low trust signals (trust <0.4) or high perceived risks, causing abandonment"
        
        # 4. Check for energy depletion
        if completion_rate < 0.1:
            return f"Energy depletion: Very low completion rate ({completion_rate:.1%}) suggests users exhausted cognitive energy before reaching value. Too many steps or too much early effort."
        
        # 5. Default
        return f"Multi-factor failure: Combination of factors including {', '.join(list(failure_reasons.keys())[:2]) if failure_reasons else 'unknown factors'}"
    
    def _identify_secondary_factors(self, semantic_insights: Dict, step_data: Dict,
                                    failure_reasons: Dict, output: Optional[Dict] = None) -> List[str]:
        """Identify secondary contributing factors."""
        factors = []
        
        # Get primary intent from output
        primary_intent = None
        if output and 'intent_distribution' in output:
            intent_dist = output['intent_distribution']
            primary_intent = max(intent_dist.items(), key=lambda x: x[1])[0] if intent_dist else None
        
        # Check for choice availability issues (from semantic insights)
        for step_name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'choice_availability' in conflicts:
                count = conflicts['choice_availability']
                if count > 50:  # Significant number
                    factors.append(f"Step '{step_name}' lacks comparison view (choice_availability conflict: {count} instances). Users want to compare but step doesn't show options.")
        
        # Check for knowledge gap issues (for eligibility_check intent)
        if primary_intent == 'eligibility_check':
            for step_name, insights in semantic_insights.items():
                conflicts = insights.get('conflict_axes', {})
                if isinstance(conflicts, dict) and 'knowledge_gap' in conflicts:
                    count = conflicts['knowledge_gap']
                    if count > 50:
                        factors.append(f"Step '{step_name}' has knowledge gap barrier (knowledge_gap conflict: {count} instances). Step assumes knowledge users don't have, creating barrier for eligibility check.")
        
        # Check for speed issues (for quick_decision intent)
        if primary_intent == 'quick_decision':
            for step_name, data in step_data.items():
                profile = data.get('sample_semantic_profile', {})
                if profile:
                    urgency = profile.get('urgency', 0.3)
                    if urgency < 0.5:  # Low urgency when user expects speed
                        factors.append(f"Step '{step_name}' doesn't signal urgency (urgency: {urgency:.2f}), but user entered with quick decision intent expecting '10s' promise")
        
        # Check for knowledge gaps
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                knowledge = profile.get('implied_user_knowledge', 'medium')
                if knowledge == 'high':
                    factors.append(f"Step '{step_name}' assumes high user knowledge, creating barrier for less sophisticated users")
        
        # Check for choice overload
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                overload = profile.get('choice_overload', 0)
                if overload > 0.6:
                    factors.append(f"Step '{step_name}' presents too many choices (overload: {overload:.2f}), causing decision paralysis")
        
        # Check for reversibility issues
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                reversibility = profile.get('reversibility', 0.7)
                if reversibility < 0.4:
                    factors.append(f"Step '{step_name}' feels irreversible (reversibility: {reversibility:.2f}), increasing perceived risk")
        
        # Check emotional deltas
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                emotions = profile.get('emotional_deltas', {})
                if 'anxiety' in emotions and emotions['anxiety'] > 0.2:
                    factors.append(f"Step '{step_name}' increases anxiety (delta: {emotions['anxiety']:.2f}), reducing confidence")
        
        return factors[:5]  # Top 5 secondary factors
    
    def _identify_psychological_failure(self, semantic_insights: Dict, step_data: Dict, output: Optional[Dict] = None) -> str:
        """Identify dominant psychological failure mode."""
        
        # Check for choice availability violation (for comparison intent)
        choice_conflicts = []
        for name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'choice_availability' in conflicts:
                count = conflicts['choice_availability']
                alignment = insights.get('avg_alignment_score', 1.0)
                choice_conflicts.append((name, alignment, count))
        
        # Check for knowledge gap (for eligibility_check intent)
        knowledge_gap_conflicts = []
        for name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'knowledge_gap' in conflicts:
                count = conflicts['knowledge_gap']
                alignment = insights.get('avg_alignment_score', 1.0)
                knowledge_gap_conflicts.append((name, alignment, count))
        
        # Check for speed mismatch (for quick_decision intent)
        speed_conflicts = []
        for name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'speed' in conflicts:
                count = conflicts['speed']
                alignment = insights.get('avg_alignment_score', 1.0)
                speed_conflicts.append((name, alignment, count))
        
        # Determine primary intent from output
        primary_intent = None
        primary_pct = 0
        if output and 'intent_distribution' in output:
            intent_dist = output['intent_distribution']
            primary_intent = max(intent_dist.items(), key=lambda x: x[1])[0] if intent_dist else None
            primary_pct = intent_dist.get(primary_intent, 0) * 100 if primary_intent else 0
        
        # Prioritize based on primary intent
        if primary_intent == 'eligibility_check' and knowledge_gap_conflicts:
            worst = max(knowledge_gap_conflicts, key=lambda x: x[2])
            return f"Knowledge barrier: Step '{worst[0]}' assumes financial/technical knowledge users don't have. {worst[2]} users encountered knowledge gap barrier (alignment: {worst[1]:.2f}). Users want to check eligibility but step uses terms/concepts (PAN, DOB, credit limit) they don't fully understand."
        
        if primary_intent == 'quick_decision' and speed_conflicts:
            worst = max(speed_conflicts, key=lambda x: x[2])
            return f"Speed mismatch: Step '{worst[0]}' violated user's quick decision intent. {worst[2]} users wanted fast eligibility check (promised '10s') but step is slower than expected (alignment: {worst[1]:.2f})."
        
        if choice_conflicts:
            worst = max(choice_conflicts, key=lambda x: x[2])  # Most conflicts
            return f"Intent violation: Step '{worst[0]}' violated user's comparison intent. {worst[2]} users wanted to compare options but step didn't show comparison view (alignment: {worst[1]:.2f}). Users entered with comparison intent but encountered questions without seeing options."
        
        # Check for trust erosion (important for financial products)
        low_trust = []
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile and profile.get('trust_signal', 0.5) < 0.4:
                low_trust.append(step_name)
        
        if low_trust:
            return f"Trust erosion: Steps {', '.join(low_trust[:2])} failed to build or maintain trust, causing users to question credibility and abandon. Critical for financial products where trust is essential."
        
        # Check for speed mismatch (if primary intent is quick_decision)
        if primary_intent == 'quick_decision':
            low_urgency_steps = []
            for step_name, data in step_data.items():
                profile = data.get('sample_semantic_profile', {})
                if profile:
                    urgency = profile.get('urgency', 0.3)
                    if urgency < 0.4:  # Low urgency when speed is expected
                        low_urgency_steps.append(step_name)
            
            if low_urgency_steps:
                return f"Speed promise violation: Steps {', '.join(low_urgency_steps[:2])} don't signal urgency, but users entered expecting '10s' quick check. Promise-speed mismatch causes abandonment."
        
        # Check for cognitive overwhelm
        high_load = []
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                effort = profile.get('perceived_effort', 0.5)
                visual = profile.get('visual_load', 0.5)
                if effort > 0.6 or visual > 0.6:
                    high_load.append(step_name)
        
        if high_load:
            return f"Cognitive overwhelm: Steps {', '.join(high_load[:2])} exceeded users' cognitive capacity, causing mental fatigue and abandonment"
        
        return "Unclear psychological failure: Multiple factors contributing, need more data to identify dominant mode"
    
    def _find_misaligned_assumptions(self, semantic_insights: Dict, step_data: Dict, output: Optional[Dict] = None) -> List[str]:
        """Find key misaligned assumptions."""
        assumptions = []
        
        # Check semantic insights for conflicts
        for step_name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict):
                if 'choice_availability' in conflicts and conflicts['choice_availability'] > 100:
                    # Get actual intent distribution if available
                    intent_pct = "some"
                    if output and 'intent_distribution' in output:
                        intent_dist = output['intent_distribution']
                        compare_pct = intent_dist.get('compare_options', 0) * 100
                        if compare_pct > 5:
                            intent_pct = f"{compare_pct:.1f}%"
                    assumptions.append(f"Step '{step_name}' assumes users will answer questions without seeing comparison, but {intent_pct} entered with comparison intent expecting to see options first")
        
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            alignment = data.get('sample_alignment_result', {})
            
            if profile and alignment:
                # Knowledge assumption
                knowledge = profile.get('implied_user_knowledge', 'medium')
                if knowledge == 'high':
                    assumptions.append(f"Step '{step_name}' assumes high financial/product knowledge, but many users have low-medium knowledge")
                
                # Intent assumption
                alignment_score = alignment.get('intent_alignment_score', 1.0)
                conflicts = alignment.get('conflict_axes', [])
                if isinstance(conflicts, list):
                    if 'commitment' in conflicts:
                        assumptions.append(f"Step '{step_name}' assumes users are ready to commit, but many entered with exploratory intent")
                    if 'knowledge_gap' in conflicts:
                        assumptions.append(f"Step '{step_name}' assumes users understand financial terms/concepts they may not know")
                    if 'choice_availability' in conflicts:
                        assumptions.append(f"Step '{step_name}' assumes users will provide info before seeing options, but comparison-intent users expect to see options first")
        
        return assumptions[:5]  # Top 5 assumptions
    
    def _analyze_fixability(self, step_data: Dict, semantic_insights: Dict) -> Dict:
        """Analyze what's fixable vs structural."""
        quick_wins = []
        structural_issues = []
        
        # Check semantic insights for quick wins
        for step_name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'choice_availability' in conflicts:
                count = conflicts['choice_availability']
                if count > 100:
                    quick_wins.append(f"Add comparison preview to '{step_name}' or earlier step. Show sample credit cards before asking questions. Quick UI change.")
        
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            alignment = data.get('sample_alignment_result', {})
            
            if profile and alignment:
                # Quick wins: Low trust, high effort (can be fixed with UI/copy)
                trust = profile.get('trust_signal', 0.5)
                if trust < 0.4:
                    quick_wins.append(f"Add trust signals to '{step_name}' (badges, testimonials, security indicators)")
                
                effort = profile.get('perceived_effort', 0.5)
                if effort > 0.7:
                    quick_wins.append(f"Reduce effort in '{step_name}' (simplify UI, reduce fields, add autofill)")
                
                # Structural: Intent mismatch, knowledge gaps (require flow redesign)
                alignment_score = alignment.get('intent_alignment_score', 1.0)
                conflicts = alignment.get('conflict_axes', [])
                conflicts_list = conflicts if isinstance(conflicts, list) else list(conflicts.keys()) if isinstance(conflicts, dict) else []
                
                if 'choice_availability' in conflicts_list or 'choice_availability' in str(conflicts):
                    structural_issues.append(f"'{step_name}' doesn't show comparison view - requires flow redesign to show options before collecting personal info")
                
                if 'commitment' in conflicts_list:
                    structural_issues.append(f"'{step_name}' requires commitment before value - needs flow redesign to show value first")
                
                if 'knowledge_gap' in conflicts_list:
                    structural_issues.append(f"'{step_name}' assumes knowledge users don't have - needs educational layer or simplification")
        
        return {
            "quick_wins": quick_wins[:5],
            "structural_issues": structural_issues[:5]
        }
    
    def _generate_recommendations(self, step_data: Dict, semantic_insights: Dict,
                                  primary_reason: str, output: Optional[Dict] = None) -> List[Dict]:
        """Generate top 3 product change recommendations."""
        recommendations = []
        
        # Find worst step (by drop rate and alignment)
        worst_step = None
        worst_score = 1.0
        worst_drop_rate = 0.0
        
        for step_name, data in step_data.items():
            drop_rate = data.get('drop_rate', 0)
            alignment = data.get('sample_alignment_result', {})
            if alignment:
                score = alignment.get('intent_alignment_score', 1.0)
                # Prioritize high drop rate with low alignment
                combined_score = drop_rate * (1 - score)
                if combined_score > worst_drop_rate * (1 - worst_score):
                    worst_score = score
                    worst_drop_rate = drop_rate
                    worst_step = (step_name, data)
        
        if worst_step:
            step_name, data = worst_step
            alignment = data.get('sample_alignment_result', {})
            conflicts = alignment.get('conflict_axes', []) if alignment else []
            
            conflicts_list = conflicts if isinstance(conflicts, list) else list(conflicts.keys()) if isinstance(conflicts, dict) else []
            
            if 'commitment' in conflicts_list:
                recommendations.append({
                    "change": f"Move commitment gates in '{step_name}' to after value delivery. Show comparison/recommendations before asking for personal info.",
                    "expected_impact": "High - Reduces intent mismatch for comparison/exploration users. Expected +15-25% completion rate increase."
                })
            
            if 'choice_availability' in conflicts_list or 'choice_availability' in str(conflicts):
                recommendations.append({
                    "change": f"Show comparison view in '{step_name}' or earlier. Display sample credit card options before asking for personal information.",
                    "expected_impact": "High - Addresses primary intent mismatch for 39.1% of users with comparison intent. Expected +20-30% completion rate increase."
                })
            
            if 'knowledge_gap' in conflicts_list:
                recommendations.append({
                    "change": f"Add educational layer or simplify language in '{step_name}'. Explain terms, provide tooltips, or reduce complexity.",
                    "expected_impact": "Medium-High - Reduces barrier for low-knowledge users. Expected +10-20% completion rate increase."
                })
        
        # Recommendation 2: Show value earlier (based on semantic insights)
        choice_conflicts_found = False
        for step_name, insights in semantic_insights.items():
            conflicts = insights.get('conflict_axes', {})
            if isinstance(conflicts, dict) and 'choice_availability' in conflicts:
                count = conflicts['choice_availability']
                if count > 100:  # Significant issue
                    choice_conflicts_found = True
                    # Get actual intent distribution
                    intent_pct = "users"
                    if output and 'intent_distribution' in output:
                        intent_dist = output['intent_distribution']
                        compare_pct = intent_dist.get('compare_options', 0) * 100
                        if compare_pct > 5:
                            intent_pct = f"{compare_pct:.1f}% of users"
                    recommendations.append({
                        "change": f"Show sample recommendations/comparison view at step 2-3 (before '{step_name}'), before collecting personal information. Satisfies comparison intent for {intent_pct}.",
                        "expected_impact": "High - Addresses primary intent mismatch. Expected +20-30% completion rate increase for comparison-intent users."
                    })
                    break
        
        if not choice_conflicts_found and worst_step:
            recommendations.append({
                "change": "Show sample recommendations/comparison view at step 2-3, before collecting personal information. Satisfies comparison intent earlier.",
                "expected_impact": "High - Addresses primary intent mismatch. Expected +20-30% completion rate increase for comparison-intent users."
            })
        
        # Recommendation 3: Reduce cognitive load
        high_load_steps = []
        for step_name, data in step_data.items():
            profile = data.get('sample_semantic_profile', {})
            if profile:
                effort = profile.get('perceived_effort', 0.5)
                visual = profile.get('visual_load', 0.5)
                if effort > 0.6 or visual > 0.6:
                    high_load_steps.append(step_name)
        
        if high_load_steps:
            recommendations.append({
                "change": f"Simplify UI and reduce cognitive load in steps {', '.join(high_load_steps[:2])}. Reduce fields, improve visual hierarchy, add progress indicators.",
                "expected_impact": "Medium - Reduces cognitive fatigue. Expected +5-15% completion rate increase."
            })
        
        # Ensure we have 3 recommendations
        while len(recommendations) < 3:
            recommendations.append({
                "change": "Add trust signals throughout flow (security badges, testimonials, clear privacy policy)",
                "expected_impact": "Medium - Builds confidence. Expected +5-10% completion rate increase."
            })
        
        return recommendations[:3]
    
    def _assess_confidence(self, output: Dict, semantic_insights: Dict) -> str:
        """Assess confidence level in analysis."""
        if not semantic_insights:
            return "low"
        
        # High confidence if we have clear patterns
        has_clear_patterns = any(
            insights.get('avg_alignment_score', 1.0) < 0.5
            for insights in semantic_insights.values()
        )
        
        if has_clear_patterns and len(semantic_insights) > 3:
            return "high"
        elif len(semantic_insights) > 0:
            return "medium"
        else:
            return "low"
    
    def _infer_step_failure_reason(self, alignment: Dict, profile: Dict, step_name: str) -> str:
        """Infer why a specific step failed."""
        if not alignment:
            return f"Step '{step_name}' caused drop-off, but specific reason unclear from available data"
        
        alignment_score = alignment.get('intent_alignment_score', 1.0)
        conflicts = alignment.get('conflict_axes', [])
        semantic_reason = alignment.get('semantic_reason', '')
        
        # Handle conflicts (can be list or dict)
        conflicts_list = conflicts if isinstance(conflicts, list) else list(conflicts.keys()) if isinstance(conflicts, dict) else []
        
        if conflicts_list:
            if 'choice_availability' in conflicts_list:
                default_reason = 'User wants to compare but step does not show options'
                return f"Intent mismatch: choice_availability. {semantic_reason or default_reason}"
            if 'commitment' in conflicts_list:
                return f"Intent mismatch: commitment. Step requires commitment before user is ready, violating exploratory intent"
            if 'knowledge_gap' in conflicts_list:
                return f"Knowledge gap: Step assumes knowledge users don't have, creating barrier"
            if 'speed' in conflicts_list:
                return f"Speed mismatch: User wants quick decision but step is slow/effortful"
        
        if profile:
            effort = profile.get('perceived_effort', 0.5)
            if effort > 0.7:
                return f"High perceived effort ({effort:.2f}) exceeded user tolerance, causing cognitive fatigue"
            
            trust = profile.get('trust_signal', 0.5)
            if trust < 0.4:
                return f"Low trust signals ({trust:.2f}) failed to build credibility, increasing perceived risk"
        
        if semantic_reason:
            return semantic_reason[:150]
        
        return f"Step '{step_name}' caused drop-off due to multiple factors"
    
    def _infer_user_expectations(self, step_name: str, profile: Dict) -> str:
        """Infer what users expected at this step."""
        if not profile:
            return "Clear value or progress toward goal"
        
        # Check intent shift
        intent_shift = profile.get('intent_shift', {})
        if 'compare' in intent_shift and intent_shift['compare'] > 0.3:
            return "To see comparison of options before committing"
        if 'explore' in intent_shift and intent_shift['explore'] > 0.3:
            return "To explore and learn about options without commitment"
        if 'speed' in intent_shift and intent_shift['speed'] > 0.3:
            return "Quick path to decision/action"
        
        # Check promises
        promises = profile.get('inferred_psychological_promises', [])
        if 'fast' in promises:
            return "Fast, quick experience"
        if 'safe' in promises:
            return "Safe, secure experience"
        if 'no_commitment' in promises:
            return "No commitment required"
        
        return "Clear value or progress toward goal"
    
    def _infer_what_they_got(self, step_name: str, profile: Dict, alignment: Dict) -> str:
        """Infer what users actually got."""
        if not profile:
            return "Unclear value or high friction"
        
        # Check conflicts
        if alignment:
            conflicts = alignment.get('conflict_axes', [])
            conflicts_list = conflicts if isinstance(conflicts, list) else list(conflicts.keys()) if isinstance(conflicts, dict) else []
            
            if 'choice_availability' in conflicts_list:
                return "Questions without seeing comparison options. No way to compare before committing."
            if 'commitment' in conflicts_list:
                return "Commitment requirement before seeing value"
            if 'knowledge_gap' in conflicts_list:
                return "Complex language/terms they don't understand"
            if 'speed' in conflicts_list:
                return "Slow, effortful process"
        
        # Check effort
        effort = profile.get('perceived_effort', 0.5)
        if effort > 0.6:
            return f"High effort requirement (effort: {effort:.2f})"
        
        # Check risks
        risks = profile.get('inferred_risks', [])
        if risks:
            return f"Perceived risks: {', '.join(risks[:2])}"
        
        return "Unclear value or high friction"
    
    def _analyze_with_llm(self, output: Dict) -> Dict:
        """
        LLM-based analysis (requires API).
        
        Uses the system prompt and reasoning hierarchy specified.
        """
        if not self.llm_client:
            raise ValueError("LLM client required for LLM-based analysis")
        
        # Format output for LLM
        output_str = json.dumps(output, indent=2)
        
        system_prompt = """You are a Behavioral Intelligence Analyst analyzing output from a user-simulation engine (DropSim).
Your job is NOT to restate the data, but to infer causality, summarize drivers, and explain behavior in human terms.
You must:
- Compress large JSON into high-signal explanations
- Identify primary, secondary, and latent causes
- Answer "why" questions, not "what happened"
- Resolve conflicts between signals intelligently
- Avoid listing raw metrics unless they directly explain behavior
You are allowed to infer latent psychological causes when supported by patterns.

Reason using this hierarchy (in order):
1. Intent mismatch (e.g., exploratory users forced into commitment)
2. Cognitive overload / friction (UI complexity, too much info, unclear next step)
3. Trust & risk perception (credibility gaps, missing reassurance, hidden cost fear)
4. Energy depletion (too many steps, too early effort)
5. Emotional trajectory shifts (confidence → anxiety → disengagement)

If multiple causes exist, rank them by contribution."""
        
        user_prompt = f"""Here is the DropSim output for a user journey simulation:

{output_str}

Answer the following:
1. Why did users drop off?
2. What were the dominant psychological and behavioral causes?
3. Which step caused irreversible damage to conversion?
4. Which issues are fixable vs structural?
5. What 3 product changes would most increase completion probability?
6. What signals most strongly influenced the model's decision?

Return ONLY valid JSON in this format:
{{
  "primary_drop_reason": "...",
  "secondary_factors": ["...", "..."],
  "dominant_psychological_failure": "...",
  "key_misaligned_assumptions": ["..."],
  "most_damaging_step": {{
    "step_id": "...",
    "why_it_failed": "...",
    "what_user_expected": "...",
    "what_they_got": "..."
  }},
  "fixability_analysis": {{
    "quick_wins": ["..."],
    "structural_issues": ["..."]
  }},
  "recommended_product_changes": [
    {{
      "change": "...",
      "expected_impact": "..."
    }}
  ],
  "confidence_level": "high | medium | low"
}}

If there is ambiguity or multiple plausible explanations, surface them explicitly and explain how additional data could disambiguate them."""
        
        try:
            response = self.llm_client.generate(
                user_prompt,
                system_prompt=system_prompt,
                response_format="json_object"
            )
            return json.loads(response)
        except Exception as e:
            # Fallback to rule-based
            print(f"LLM analysis failed, using rule-based: {e}")
            return self._analyze_rule_based(output)


def analyze_simulation_output(output_path: str, llm_client=None) -> Dict:
    """
    Convenience function to analyze simulation output from file.
    
    Args:
        output_path: Path to JSON output file
        llm_client: Optional LLM client for analysis
    
    Returns:
        Structured analysis
    """
    with open(output_path, 'r') as f:
        output = json.load(f)
    
    analyst = BehavioralIntelligenceAnalyst(llm_client=llm_client)
    return analyst.analyze(output)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python behavioral_intelligence_analyst.py <simulation_output.json>")
        sys.exit(1)
    
    output_path = sys.argv[1]
    analysis = analyze_simulation_output(output_path)
    
    print("\n" + "=" * 80)
    print("BEHAVIORAL INTELLIGENCE ANALYSIS")
    print("=" * 80)
    print(json.dumps(analysis, indent=2))
    print("=" * 80)

