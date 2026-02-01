#!/usr/bin/env python3
"""
Generate founder-readable narrative about Credigo's decision system.
"""

import json
import re
from typing import Dict, List


def generate_narrative(analysis_file: str) -> str:
    """Generate founder-readable narrative."""
    
    with open(analysis_file, 'r') as f:
        analysis = json.load(f)
    
    lines = []
    
    # Title
    lines.append("# What Credigo Decides About Its Users")
    lines.append("")
    lines.append("**Analysis Date:** Generated from decision traces")
    lines.append("**Methodology:** Decision gate analysis from behavioral simulation traces")
    lines.append("**Purpose:** Understand Credigo as a decision-making system, not a UX problem")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 1: The kind of user Credigo is built for
    lines.append("## 1. The Kind of User Credigo is Built For")
    lines.append("")
    
    user_contract = analysis.get('user_contract', [])
    if user_contract:
        lines.append("Based on survival patterns in the decision traces, Credigo is built for users who:")
        lines.append("")
        for requirement in user_contract:
            lines.append(f"- {requirement}")
    else:
        lines.append("Analysis of completing users reveals the implicit contract Credigo enforces.")
    
    lines.append("")
    
    # Section 2: The kind of user Credigo filters out
    lines.append("## 2. The Kind of User Credigo Filters Out")
    lines.append("")
    
    filtering_patterns = analysis.get('filtering_patterns', {})
    gates = analysis.get('decision_gates', [])
    
    lines.append("### What Credigo is Hostile To")
    lines.append("")
    intolerances = filtering_patterns.get('intolerances', [])
    if intolerances:
        for intolerance in intolerances:
            lines.append(f"- **{intolerance['description']}**")
            lines.append(f"  Evidence: {intolerance['evidence']}")
            lines.append("")
    else:
        # Infer from gates
        if gates:
            first_gate = gates[0]
            failing_chars = first_gate['failing_persona_characteristics']
            failing_forces = first_gate['avg_forces_fail']
            
            if failing_chars.get('avg_intent_strength', 1.0) < 0.6:
                lines.append(f"- **Users who are uncertain about their intent**")
                lines.append(f"  Evidence: {first_gate['fails_count']} users filtered at {first_gate['step_id']} with avg intent strength {failing_chars.get('avg_intent_strength', 0):.2f}")
                lines.append("")
            
            if failing_forces.get('risk', 0) > 0.2:
                lines.append(f"- **Users who hesitate due to perceived risk**")
                lines.append(f"  Evidence: Avg risk force for failures: {failing_forces.get('risk', 0):.2f}")
                lines.append("")
    
    lines.append("### What Credigo Refuses to Spend Time On")
    lines.append("")
    
    # Analyze from gates
    if gates:
        first_gate = gates[0]
        failing_chars = first_gate['failing_persona_characteristics']
        
        refusals_list = []
        if failing_chars.get('avg_intent_strength', 1.0) < 0.5:
            refusals_list.append("Users who need education or convincing before starting")
        if failing_chars.get('avg_risk_tolerance', 1.0) < 0.4:
            refusals_list.append("Users who require reassurance before sharing information")
        if failing_chars.get('avg_effort_tolerance', 1.0) < 0.5:
            refusals_list.append("Users who want to browse before committing effort")
        
        for refusal in refusals_list:
            lines.append(f"- {refusal}")
        lines.append("")
    
    # Section 3: Decision gates table
    lines.append("## 3. The Decisions That Matter Most")
    lines.append("")
    
    gates = analysis.get('decision_gates', [])
    # Filter out gates with 0% pass rate (no passes)
    meaningful_gates = [g for g in gates if g['pass_rate'] > 0 or g['fails_count'] > 10]
    
    if meaningful_gates:
        lines.append("| Decision Gate | Signal Demanded | Who Passes | Who Fails | Pass Rate |")
        lines.append("|---------------|-----------------|------------|-----------|-----------|")
        
        for gate in meaningful_gates[:5]:  # Top 5 meaningful gates
            step_id = gate['step_id'].replace('step_', 'Step ').replace('_', ' ').title()
            signal = gate['signal_demanded'][:45]
            
            # Who passes (from characteristics)
            passing_chars = gate['passing_persona_characteristics']
            who_passes = describe_persona_group_decision_focused(passing_chars, gate, passing=True)
            
            # Who fails
            failing_chars = gate['failing_persona_characteristics']
            who_fails = describe_persona_group_decision_focused(failing_chars, gate, passing=False)
            
            pass_rate = gate['pass_rate']
            
            lines.append(f"| {step_id} | {signal} | {who_passes} | {who_fails} | {pass_rate:.1%} |")
        
        lines.append("")
        
        # Add key finding
        if len(meaningful_gates) >= 2:
            first_gate = meaningful_gates[0]
            second_gate = meaningful_gates[1]
            lines.append(f"**Key Finding:** {first_gate['step_id'].replace('step_', 'Step ')} filters out {1-first_gate['pass_rate']:.1%} of users immediately. {second_gate['step_id'].replace('step_', 'Step ')} is the major filtering point where {1-second_gate['pass_rate']:.1%} of remaining users fail.")
            lines.append("")
    
    # Section 4: Tradeoffs
    lines.append("## 4. The Irreversible Tradeoffs in the Current Design")
    lines.append("")
    
    tradeoffs = analysis.get('tradeoffs', [])
    # Filter out tradeoffs with no gains/losses
    meaningful_tradeoffs = [t for t in tradeoffs if t.get('gains') or t.get('losses')]
    
    for tradeoff in meaningful_tradeoffs:
        # Clean up decision title - extract signal and step info
        decision_text = tradeoff['decision']
        # Format: "Ask for [signal] at step_X (step N)" -> "Ask for [signal] at Step N"
        match = re.search(r'Ask for (.+?) at (step_\d+) \(step (\d+)\)', decision_text)
        if match:
            signal = match.group(1)
            step_num = match.group(3)
            decision_title = f'Ask for "{signal}" at Step {step_num}'
        else:
            decision_title = decision_text.replace('Ask for ', '')
        lines.append(f"### Decision: {decision_title}")
        lines.append("")
        
        if tradeoff.get('gains'):
            lines.append("**Gain:**")
            for gain in tradeoff['gains']:
                lines.append(f"- {gain}")
            lines.append("")
        
        if tradeoff.get('losses'):
            lines.append("**Loss:**")
            for loss in tradeoff['losses']:
                lines.append(f"- {loss}")
            lines.append("")
        
        lines.append(f"Evidence: {tradeoff['evidence']['passes']} passed, {tradeoff['evidence']['fails']} failed ({tradeoff['evidence']['pass_rate']:.1%} pass rate)")
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("**Note:** This analysis is derived entirely from decision traces. ")
    lines.append("Every claim is backed by observable patterns in how users were accepted or rejected at each step. ")
    lines.append("No optimization advice is provided — only a clear picture of what decisions the product makes.")
    lines.append("")
    
    return "\n".join(lines)


def describe_persona_group_decision_focused(characteristics: Dict[str, float], gate: Dict, passing: bool = True) -> str:
    """Describe a persona group in decision-focused language."""
    if not characteristics:
        return "Various"
    
    energy = characteristics.get('avg_cognitive_energy', 0.5)
    risk = characteristics.get('avg_risk_tolerance', 0.5)
    effort = characteristics.get('avg_effort_tolerance', 0.5)
    intent = characteristics.get('avg_intent_strength', 0.5)
    
    # Use forces to understand what matters
    forces = gate['avg_forces_pass'] if passing else gate['avg_forces_fail']
    
    descriptors = []
    
    # Decision-focused: what capability/signal do they have?
    if gate['step_index'] == 0:
        # Landing page: trust/commitment matters
        if passing:
            descriptors.append("sufficient trust to proceed")
        else:
            descriptors.append("low trust, need reassurance")
    elif gate['step_index'] == 4:
        # Financial info: effort tolerance and risk matter
        if passing:
            if effort > 0.45:
                descriptors.append("high effort tolerance")
            if risk > 0.35:
                descriptors.append("low risk sensitivity")
            if not descriptors:
                descriptors.append("can tolerate effort without value")
        else:
            descriptors.append("cannot tolerate effort without value signal")
    else:
        # Generic
        if effort > 0.5:
            descriptors.append("effort-tolerant")
        elif effort < 0.35:
            descriptors.append("effort-sensitive")
        
        if risk > 0.5:
            descriptors.append("risk-tolerant")
        elif risk < 0.4:
            descriptors.append("risk-averse")
    
    if descriptors:
        return ", ".join(descriptors[:2])  # Limit to 2 descriptors
    else:
        return "moderate characteristics"


if __name__ == '__main__':
    import sys
    
    analysis_file = sys.argv[1] if len(sys.argv) > 1 else 'credigo_decision_system_analysis.json'
    
    narrative = generate_narrative(analysis_file)
    
    output_file = 'what_credigo_decides_about_its_users.md'
    with open(output_file, 'w') as f:
        f.write(narrative)
    
    print(f"✓ Narrative generated: {output_file}")

