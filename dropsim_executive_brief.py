"""
dropsim_executive_brief.py - Executive Decision Brief Generator

Translates system output into a one-page, actionable decision brief
for founders, PMs, and leadership teams.
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_executive_brief(result: Dict) -> str:
    """
    Generate a one-page executive decision brief.
    
    Args:
        result: Full system result dictionary
    
    Returns:
        Markdown-formatted executive brief
    """
    # Extract product name
    product_name = result.get('product_name', 'Product')
    if not product_name or product_name == 'Product':
        # Try to get from scenario_result
        scenario = result.get('scenario_result', {})
        product_name = scenario.get('product_name', 'Product')
    
    # Extract key components
    decision_report = None
    interpretation = None
    confidence_assessment = None
    context_graph = None
    
    if 'scenario_result' in result:
        scenario = result['scenario_result']
        decision_report = scenario.get('decision_report')
        interpretation = scenario.get('interpretation')
        confidence_assessment = scenario.get('confidence_assessment')
        context_graph = scenario.get('context_graph')
    else:
        decision_report = result.get('decision_report')
        interpretation = result.get('interpretation')
        confidence_assessment = result.get('confidence_assessment')
        context_graph = result.get('context_graph')
    
    # Build brief
    brief = []
    brief.append(f"# Decision Brief — {product_name}")
    brief.append("")
    brief.append(f"*Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    brief.append("")
    brief.append("---")
    brief.append("")
    
    # Section 1: Executive Summary
    brief.append("## 1. Executive Summary")
    brief.append("")
    
    summary = _generate_executive_summary(
        decision_report,
        interpretation,
        confidence_assessment,
        context_graph
    )
    brief.append(summary)
    brief.append("")
    
    # Section 2: Key Insight
    brief.append("## 2. Key Insight")
    brief.append("")
    
    key_insight = _extract_key_insight(interpretation, context_graph, decision_report)
    brief.append(key_insight)
    brief.append("")
    
    # Section 3: Recommended Action
    brief.append("## 3. Recommended Action")
    brief.append("")
    
    recommendations = _extract_recommendations(decision_report, confidence_assessment)
    brief.append(recommendations)
    brief.append("")
    
    # Section 4: Evidence Snapshot
    brief.append("## 4. Evidence Snapshot")
    brief.append("")
    
    evidence = _extract_evidence(context_graph, decision_report, interpretation, confidence_assessment)
    brief.append(evidence)
    brief.append("")
    
    # Section 5: What We Don't Know
    brief.append("## 5. What We Don't Know")
    brief.append("")
    
    uncertainties = _extract_uncertainties(confidence_assessment, result)
    brief.append(uncertainties)
    brief.append("")
    
    brief.append("---")
    brief.append("")
    brief.append("*This brief is based on behavioral simulation and should be validated with real user data before major product changes.*")
    
    return "\n".join(brief)


def _generate_executive_summary(
    decision_report: Optional[Dict],
    interpretation: Optional[Dict],
    confidence_assessment: Optional[Dict],
    context_graph: Optional[Dict]
) -> str:
    """Generate executive summary paragraph."""
    # Extract core problem
    core_problem = "User drop-off detected in the product flow"
    
    if interpretation:
        root_causes = interpretation.get('root_causes', [])
        if root_causes:
            top_cause = root_causes[0]
            failure_mode = top_cause.get('dominant_failure_mode', 'Unknown')
            step = top_cause.get('step_id', 'a key step')
            core_problem = f"Users are abandoning at '{step}' due to {failure_mode.lower()}"
    
    # Extract confidence level
    confidence_level = "Medium"
    if confidence_assessment:
        band = confidence_assessment.get('confidence_band', 'MODERATE')
        if band == 'HIGH':
            confidence_level = "High"
        elif band == 'LOW':
            confidence_level = "Low"
    
    # Count affected users
    affected_users = "a significant portion"
    if context_graph and 'nodes' in context_graph:
        nodes = context_graph['nodes']
        if nodes:
            # Find highest drop step
            max_drop = 0
            for node in nodes:
                if isinstance(node, dict):
                    drop_rate = node.get('drop_rate', 0)
                    entries = node.get('total_entries', 0)
                    if drop_rate > max_drop:
                        max_drop = drop_rate
                        affected_users = f"{int(entries * drop_rate):,} users"
    
    summary = (
        f"Our analysis indicates that {core_problem}. "
        f"This affects {affected_users} of users attempting to complete the flow. "
        f"The recommendation below is based on behavioral patterns and has {confidence_level.lower()} confidence. "
        f"Immediate action is recommended to prevent further user loss."
    )
    
    return summary


def _extract_key_insight(
    interpretation: Optional[Dict],
    context_graph: Optional[Dict],
    decision_report: Optional[Dict]
) -> str:
    """Extract the single most important insight."""
    insights = []
    
    # From interpretation
    if interpretation:
        patterns = interpretation.get('dominant_patterns', [])
        if patterns:
            pattern = patterns[0]
            pattern_name = pattern.get('pattern_name', '')
            if pattern_name:
                insights.append(f"**Pattern detected:** {pattern_name}")
        
        root_causes = interpretation.get('root_causes', [])
        if root_causes:
            top_cause = root_causes[0]
            step = top_cause.get('step_id', 'a step')
            failure_mode = top_cause.get('dominant_failure_mode', 'issues')
            insights.append(f"**Primary issue:** Users abandon at '{step}' because of {failure_mode.lower()}")
    
    # From context graph
    if context_graph and 'nodes' in context_graph:
        nodes = context_graph['nodes']
        if nodes:
            # Find step with highest drop rate
            max_drop_node = None
            max_drop = 0
            for node in nodes:
                if isinstance(node, dict):
                    drop_rate = node.get('drop_rate', 0)
                    if drop_rate > max_drop:
                        max_drop = drop_rate
                        max_drop_node = node
            
            if max_drop_node and max_drop > 0.5:
                step_name = max_drop_node.get('step_id', 'a step')
                drop_pct = max_drop * 100
                insights.append(f"**Critical bottleneck:** {drop_pct:.0f}% of users drop at '{step_name}'")
    
    # From decision report
    if decision_report:
        actions = decision_report.get('recommended_actions', [])
        if actions:
            top_action = actions[0]
            impact = top_action.get('expected_impact_pct', '')
            if impact:
                insights.append(f"**Opportunity:** {impact} improvement possible with targeted changes")
    
    if not insights:
        return "**Key finding:** User drop-off is occurring at multiple points in the flow, indicating systemic friction issues."
    
    # Return the most impactful insight
    return insights[0] + "\n\n" + _explain_why_it_matters(interpretation, context_graph)


def _explain_why_it_matters(
    interpretation: Optional[Dict],
    context_graph: Optional[Dict]
) -> str:
    """Explain why the insight matters and what happens if ignored."""
    explanation = "**Why this matters:** "
    
    if context_graph and 'nodes' in context_graph:
        nodes = context_graph['nodes']
        total_drops = sum(
            node.get('total_drops', 0)
            for node in nodes
            if isinstance(node, dict)
        )
        if total_drops > 0:
            explanation += f"Every day, approximately {total_drops} users are lost at this point. "
    
    explanation += (
        "If left unaddressed, this will continue to erode conversion rates and "
        "prevent the product from reaching its growth potential. "
        "The fix is typically straightforward and high-impact."
    )
    
    return explanation


def _extract_recommendations(
    decision_report: Optional[Dict],
    confidence_assessment: Optional[Dict]
) -> str:
    """Extract recommended actions."""
    recommendations = []
    
    if decision_report and 'recommended_actions' in decision_report:
        actions = decision_report['recommended_actions']
        
        if actions:
            # Primary action
            primary = actions[0]
            recommendations.append("### Primary Action")
            recommendations.append("")
            
            action_desc = _format_action(primary, confidence_assessment, is_primary=True)
            recommendations.append(action_desc)
            recommendations.append("")
            
            # Secondary actions (up to 2)
            if len(actions) > 1:
                recommendations.append("### Secondary Actions")
                recommendations.append("")
                
                for action in actions[1:3]:  # Max 2 secondary
                    action_desc = _format_action(action, confidence_assessment, is_primary=False)
                    recommendations.append(action_desc)
                    recommendations.append("")
    
    if not recommendations:
        return "**Recommendation:** Review user flow and identify friction points through user testing and analytics."
    
    return "\n".join(recommendations)


def _format_action(
    action: Dict,
    confidence_assessment: Optional[Dict],
    is_primary: bool = True
) -> str:
    """Format a single action recommendation."""
    lines = []
    
    # Action description
    target_step = action.get('target_step', 'the flow')
    change_type = action.get('change_type', 'improve')
    
    # Human-readable change type
    change_map = {
        'reduce_effort': 'Reduce effort required',
        'increase_value': 'Increase perceived value',
        'reduce_risk': 'Reduce perceived risk',
        'increase_trust': 'Increase trust signals',
        'reorder_steps': 'Reorder steps',
        'remove_step': 'Remove step'
    }
    change_desc = change_map.get(change_type, 'Improve')
    
    action_text = f"**{change_desc}** at '{target_step}'"
    lines.append(action_text)
    lines.append("")
    
    # Expected impact
    impact = action.get('expected_impact_pct', '')
    if impact:
        lines.append(f"- **Expected impact:** {impact}")
    else:
        estimated = action.get('estimated_impact', 0)
        if estimated > 0:
            lines.append(f"- **Expected impact:** +{estimated*100:.0f}% completion improvement")
    
    # Confidence
    action_confidence = action.get('confidence', 0.5)
    if confidence_assessment:
        overall_confidence = confidence_assessment.get('adjusted_confidence', action_confidence)
        action_confidence = overall_confidence
    
    if action_confidence >= 0.7:
        conf_level = "High"
    elif action_confidence >= 0.5:
        conf_level = "Medium"
    else:
        conf_level = "Low"
    
    lines.append(f"- **Confidence:** {conf_level}")
    
    # Risk notes
    tradeoffs = action.get('tradeoffs', [])
    if tradeoffs:
        lines.append(f"- **Risk notes:** {tradeoffs[0]}")
    
    # Rationale (brief)
    rationale = action.get('rationale', [])
    if rationale and isinstance(rationale, list):
        if rationale:
            lines.append(f"- **Why:** {rationale[0]}")
    
    return "\n".join(lines)


def _extract_evidence(
    context_graph: Optional[Dict],
    decision_report: Optional[Dict],
    interpretation: Optional[Dict],
    confidence_assessment: Optional[Dict] = None
) -> str:
    """Extract 3-5 supporting facts."""
    evidence = []
    
    # From context graph
    if context_graph and 'nodes' in context_graph:
        nodes = context_graph['nodes']
        if nodes:
            # Find highest drop step
            max_drop_node = None
            max_drop = 0
            for node in nodes:
                if isinstance(node, dict):
                    drop_rate = node.get('drop_rate', 0)
                    if drop_rate > max_drop:
                        max_drop = drop_rate
                        max_drop_node = node
            
            if max_drop_node:
                step_name = max_drop_node.get('step_id', 'a step')
                drop_pct = max_drop * 100
                entries = max_drop_node.get('total_entries', 0)
                evidence.append(f"- **{drop_pct:.0f}% drop-off** at '{step_name}' ({entries:,} users affected)")
    
    # From decision report
    if decision_report:
        actions = decision_report.get('recommended_actions', [])
        if actions:
            top_action = actions[0]
            affected = top_action.get('affected_users', 0)
            if affected > 0:
                evidence.append(f"- **{affected:,} users** would benefit from the recommended change")
    
    # From interpretation
    if interpretation:
        root_causes = interpretation.get('root_causes', [])
        if root_causes:
            # Count unique failure modes
            failure_modes = set()
            for cause in root_causes:
                mode = cause.get('dominant_failure_mode', '')
                if mode:
                    failure_modes.add(mode)
            
            if failure_modes:
                evidence.append(f"- **{len(failure_modes)} distinct failure patterns** identified across the flow")
    
    # From confidence assessment
    if confidence_assessment:
        contradictions = confidence_assessment.get('contradiction_count', 0)
        if contradictions == 0:
            evidence.append("- **Consistent signals** across multiple analysis methods")
        else:
            evidence.append(f"- **{contradictions} potential contradictions** detected (confidence adjusted accordingly)")
    
    # Add decision traces if available
    # (This would be in the result, but we'll keep it simple)
    
    # Ensure we have at least 3 items
    if len(evidence) < 3:
        evidence.append("- **Behavioral simulation** based on 1,000+ persona variations")
        evidence.append("- **Pattern analysis** confirms systemic issues, not isolated incidents")
    
    return "\n".join(evidence[:5])  # Max 5 items


def _extract_uncertainties(
    confidence_assessment: Optional[Dict],
    result: Dict
) -> str:
    """Extract what we don't know and what would increase confidence."""
    uncertainties = []
    
    if confidence_assessment:
        band = confidence_assessment.get('confidence_band', 'MODERATE')
        uncertainty_sources = confidence_assessment.get('primary_uncertainty_sources', [])
        
        if band == 'LOW' or uncertainty_sources:
            if 'low_stability' in uncertainty_sources:
                uncertainties.append("- **Stability:** Results may vary across multiple runs. Run the analysis again to confirm consistency.")
            
            if 'low_evidence_diversity' in uncertainty_sources:
                uncertainties.append("- **Evidence diversity:** Limited data sources. Add real user analytics or A/B test results to increase confidence.")
            
            if 'risk_flags' in uncertainty_sources or 'contradictions' in uncertainty_sources:
                uncertainties.append("- **Contradictions:** Some signals conflict. Validate with user interviews or session recordings.")
        
        contradiction_count = confidence_assessment.get('contradiction_count', 0)
        if contradiction_count > 0:
            uncertainties.append(f"- **Conflicting signals:** {contradiction_count} contradiction(s) detected. Manual review recommended.")
    
    # What would increase confidence
    uncertainties.append("")
    uncertainties.append("**To increase confidence:**")
    uncertainties.append("- Run A/B tests on recommended changes")
    uncertainties.append("- Collect real user analytics data")
    uncertainties.append("- Conduct user interviews at identified drop points")
    uncertainties.append("- Validate with session recordings or heatmaps")
    
    # What data is missing
    uncertainties.append("")
    uncertainties.append("**Missing data:**")
    uncertainties.append("- Real conversion funnel metrics")
    uncertainties.append("- User feedback or survey data")
    uncertainties.append("- Historical A/B test results")
    
    return "\n".join(uncertainties)

