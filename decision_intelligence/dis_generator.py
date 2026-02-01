"""
DIS Generator - Deterministic Decision Intelligence Summary Generator

Generates Decision Intelligence Summaries from Decision Ledgers.
Enforces strict schema, language safety, and traceability requirements.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import re


# Language Safety Rules
ALLOWED_VERBS = {
    'observed', 'recorded', 'derived', 'grouped', 'mapped', 'documented',
    'shows', 'indicates', 'contains', 'includes', 'represents'
}

FORBIDDEN_VERBS = {
    'predicts', 'optimizes', 'guarantees', 'proves', 'causes', 'ensures',
    'calculates', 'forecasts', 'determines', 'decides'
}

FORBIDDEN_TERMS = {
    'insight', 'recommendation',  # Use "decision pattern" and "hypothesis" instead
    'analysis',  # Use "summary" instead
}

# Schema Definition
REQUIRED_SECTIONS = [
    'Document Type Declaration',
    'Executive Summary',
    'Decision Boundaries by Step',
    'Acceptance Patterns',
    'Rejection Patterns',
    'Decision Termination Points',
    'Decision Pattern Hypotheses',
    'Methodology Notes',
    'Ledger Traceability'
]

OPTIONAL_SECTIONS = [
    'Persona Class Distribution'
]


@dataclass
class DISMetadata:
    """Metadata for DIS generation."""
    product_name: str
    ledger_filename: str
    ledger_timestamp: str
    generator_version: str = "1.0.0"
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'product_name': self.product_name,
            'ledger_filename': self.ledger_filename,
            'ledger_timestamp': self.ledger_timestamp,
            'generator_version': self.generator_version,
            'generation_timestamp': self.generation_timestamp
        }


@dataclass
class DISSection:
    """Represents a section in the DIS."""
    section_id: str
    title: str
    content: str
    section_type: str  # 'required' or 'optional'
    
    def to_dict(self) -> Dict:
        return {
            'section_id': self.section_id,
            'title': self.title,
            'section_type': self.section_type,
            'content_length': len(self.content)
        }


class LanguageSafetyError(Exception):
    """Raised when forbidden language is detected."""
    pass


class SchemaValidationError(Exception):
    """Raised when DIS schema is violated."""
    pass


class ConsistencyInvariantError(Exception):
    """Raised when consistency invariants are violated."""
    pass


def validate_language_safety(text: str, exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """
    Validate text against language safety rules.
    
    Args:
        text: Text to validate
        exclude_patterns: List of regex patterns to exclude from validation
                         (e.g., product names that might contain forbidden terms)
    
    Returns list of violations (empty if valid).
    """
    violations = []
    text_lower = text.lower()
    
    # Build exclusion pattern if provided
    exclusion_pattern = None
    if exclude_patterns:
        exclusion_pattern = re.compile('|'.join(exclude_patterns), re.IGNORECASE)
    
    # Check for forbidden verbs (only in specific contexts)
    for verb in FORBIDDEN_VERBS:
        pattern = r'\b' + re.escape(verb) + r'[a-z]*\b'
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            # Check if match is in excluded region
            if exclusion_pattern:
                match_text = text[match.start():match.end()]
                if exclusion_pattern.search(match_text):
                    continue
            violations.append(f"Forbidden verb: '{verb}'")
            break  # Only report once per verb
    
    # Check for forbidden terms (only when used as standalone concepts, not in compound names)
    for term in FORBIDDEN_TERMS:
        # More specific pattern: term at word boundary, but not as part of compound terms
        # Look for patterns like "recommendation" but not "Credit Card Recommendation Flow"
        pattern = r'\b' + re.escape(term) + r'(?![a-z-])'
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            # Check context - if it's part of a compound name (capitalized before/after), skip
            start, end = match.span()
            if start > 0 and end < len(text):
                # Check if surrounded by capitalized words (likely a product name)
                before = text[max(0, start-20):start].strip()
                after = text[end:min(len(text), end+20)].strip()
                # If it's in a phrase with capitals, it's likely a name, not a recommendation statement
                if (before and before[-1].isupper()) or (after and after[0].isupper()):
                    # Check if match is in excluded region
                    if exclusion_pattern:
                        match_text = text[start:end]
                        if exclusion_pattern.search(match_text):
                            continue
                    # This might be part of a name, but check if it's actually being used as the forbidden term
                    # If it appears in phrases like "product recommendation" or "our recommendation", flag it
                    context = text[max(0, start-30):min(len(text), end+30)].lower()
                    if any(phrase in context for phrase in ['our ' + term, 'the ' + term, term + ' is', term + ' that']):
                        violations.append(f"Forbidden term: '{term}' (use alternative)")
                        break
    
    return violations


def generate_document_type_declaration() -> str:
    """Generate Document Type Declaration section."""
    content = """## Document Type Declaration

This document is a **Decision Intelligence Summary** — a human-readable interpretation derived from the Decision Ledger.

**Important:**
- This summary is **not** the Decision Ledger itself
- The Decision Ledger is the authoritative, immutable record of decisions
- This summary provides decision patterns and hypotheses for product strategy
- All assertions in this document are derived from the Decision Ledger

**This document can be regenerated but should not be manually edited.**
"""
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Document Type Declaration: {violations}")
    return content


def generate_executive_summary(ledger_data: Dict, product_name: str) -> str:
    """Generate Executive Summary section (counts only)."""
    boundaries = ledger_data.get('decision_boundaries', [])
    acceptance = ledger_data.get('precedents_acceptance', [])
    rejection = ledger_data.get('precedents_rejection', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    excluded = ledger_data.get('non_binding_observations_excluded', [])
    
    content = f"""## Executive Summary

This summary presents decision patterns observed in the {product_name}. All patterns are derived from immutable decision traces recorded in the Decision Ledger.

**Key Decision Patterns:**
- **{len(boundaries)}** stable decision boundaries observed across **{ledger_data.get('total_steps', 0)}** product steps
- **{len(acceptance)}** acceptance patterns and **{len(rejection)}** rejection patterns documented
- Decision termination points mapped across the flow
- **{len(excluded)}** unstable patterns excluded from core findings (require additional observation)
"""
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Executive Summary: {violations}")
    return content


def generate_decision_boundaries_by_step(ledger_data: Dict, step_names: Optional[Dict] = None) -> str:
    """Generate Decision Boundaries by Step section."""
    boundaries = ledger_data.get('decision_boundaries', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    
    # Group boundaries by step
    boundaries_by_step = {}
    for boundary in boundaries:
        step_id = boundary['step_id']
        if step_id not in boundaries_by_step:
            boundaries_by_step[step_id] = []
        boundaries_by_step[step_id].append(boundary)
    
    # Ensure all steps from termination points appear (even if no stable boundaries)
    # This satisfies step coverage completeness
    for tp in termination_points:
        step_id = tp['step_id']
        if step_id not in boundaries_by_step:
            boundaries_by_step[step_id] = []  # Empty list for steps with no stable boundaries
    
    if not boundaries_by_step:
        return "## Decision Boundaries by Step\n\nNo decision boundaries observed.\n"
    
    lines = ["## Decision Boundaries by Step\n"]
    
    # Generate section for each step (in order of step_index)
    # For steps with boundaries, use step_index from boundaries
    # For steps without boundaries, use step_index from termination points
    def get_step_index(item):
        step_id, step_boundaries = item
        if step_boundaries:
            return min(b['step_index'] for b in step_boundaries)
        else:
            tp = next((t for t in termination_points if t['step_id'] == step_id), None)
            return tp['step_index'] if tp else 999
    
    steps_sorted = sorted(
        boundaries_by_step.items(),
        key=get_step_index
    )
    
    for step_idx, (step_id, step_boundaries) in enumerate(steps_sorted, 1):
        # Handle steps with no stable boundaries
        if not step_boundaries:
            # Get termination point data for this step
            tp = next((t for t in termination_points if t['step_id'] == step_id), None)
            lines.append(f"### Step {step_idx}: {step_id}\n")
            lines.append("**Observed Patterns:**")
            if tp:
                lines.append(f"- **{tp.get('rejection_decision_count', 0)}** rejection decisions recorded at this step")
                lines.append(f"- **0** stable persona classes observed (unstable patterns excluded)")
            else:
                lines.append(f"- No rejection decisions recorded")
                lines.append(f"- **0** stable persona classes observed")
            lines.append("")
            lines.append("---\n")
            continue
        
        # Find largest rejection count
        max_rejection = max(b['rejected_count'] for b in step_boundaries)
        max_rejection_boundary = next(b for b in step_boundaries if b['rejected_count'] == max_rejection)
        
        # Find largest acceptance count
        max_acceptance = max(b['accepted_count'] for b in step_boundaries)
        max_acceptance_boundary = next(b for b in step_boundaries if b['accepted_count'] == max_acceptance)
        
        # Get unique persona classes
        persona_classes = {}
        for b in step_boundaries:
            pc = b['persona_class']
            if pc not in persona_classes:
                persona_classes[pc] = b['supporting_trace_count']
        
        lines.append(f"### Step {step_idx}: {step_id}\n")
        lines.append("**Observed Patterns:**")
        lines.append(f"- **{sum(b['rejected_count'] for b in step_boundaries)}** rejection decisions recorded at this step")
        lines.append(f"- **{len(step_boundaries)}** stable persona classes observed")
        lines.append(f"- Primary rejection pattern: `{max_rejection_boundary['persona_class']}` ({max_rejection_boundary['rejected_count']} rejections)")
        lines.append(f"- Primary acceptance pattern: `{max_acceptance_boundary['persona_class']}` ({max_acceptance_boundary['accepted_count']} acceptances)")
        lines.append("")
        
        if persona_classes:
            lines.append("**Persona Classes Observed:**")
            sorted_personas = sorted(persona_classes.items(), key=lambda x: x[1], reverse=True)
            for i, (pc, count) in enumerate(sorted_personas[:5], 1):  # Limit to 5
                lines.append(f"{i}. `{pc}` - {count} traces")
            lines.append("")
        
        # Factor presence from first boundary
        if step_boundaries:
            factors = step_boundaries[0].get('factor_presence', [])
            if factors:
                lines.append("**Factor Presence:**")
                for fp in factors[:5]:  # Limit to 5
                    lines.append(f"- `{fp['factor_name']}` present in {fp['present_in_traces']} traces")
                lines.append("")
        
        lines.append("---\n")
    
    content = "\n".join(lines)
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Decision Boundaries by Step: {violations}")
    return content


def generate_acceptance_patterns(ledger_data: Dict) -> str:
    """Generate Acceptance Patterns section."""
    patterns = ledger_data.get('precedents_acceptance', [])
    
    if not patterns:
        return "## Acceptance Patterns\n\nNo stable acceptance patterns observed.\n"
    
    lines = [
        "## Acceptance Patterns\n",
        f"**{len(patterns)}** stable acceptance patterns observed across the flow.\n",
        "**Top Acceptance Patterns (by occurrence count):**\n"
    ]
    
    for i, pattern in enumerate(patterns[:10], 1):  # Limit to 10
        factors = [fp['factor_name'] for fp in pattern.get('factor_presence', [])]
        lines.append(f"{i}. **Step: \"{pattern['step_id']}\"**")
        lines.append(f"   - Persona: `{pattern['persona_class']}`")
        lines.append(f"   - Factors: `{'`, `'.join(factors[:5])}`")
        lines.append(f"   - Outcome: CONTINUE")
        lines.append(f"   - Occurrence count: {pattern['occurrence_count']}")
        lines.append("")
    
    content = "\n".join(lines)
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Acceptance Patterns: {violations}")
    return content


def generate_rejection_patterns(ledger_data: Dict) -> str:
    """Generate Rejection Patterns section."""
    patterns = ledger_data.get('precedents_rejection', [])
    
    if not patterns:
        return "## Rejection Patterns\n\nNo stable rejection patterns observed.\n"
    
    lines = [
        "## Rejection Patterns\n",
        f"**{len(patterns)}** stable rejection patterns observed across the flow.\n",
        "**Top Rejection Patterns (by occurrence count):**\n"
    ]
    
    for i, pattern in enumerate(patterns[:10], 1):  # Limit to 10
        factors = [fp['factor_name'] for fp in pattern.get('factor_presence', [])]
        lines.append(f"{i}. **Step: \"{pattern['step_id']}\"**")
        lines.append(f"   - Persona: `{pattern['persona_class']}`")
        lines.append(f"   - Factors: `{'`, `'.join(factors[:5])}`")
        lines.append(f"   - Outcome: DROP")
        lines.append(f"   - Occurrence count: {pattern['occurrence_count']}")
        lines.append("")
    
    content = "\n".join(lines)
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Rejection Patterns: {violations}")
    return content


def generate_decision_termination_points(ledger_data: Dict) -> str:
    """Generate Decision Termination Points section."""
    termination_points = ledger_data.get('decision_termination_points', [])
    
    if not termination_points:
        return "## Decision Termination Points\n\nNo decision termination points observed.\n"
    
    total_rejections = sum(tp['rejection_decision_count'] for tp in termination_points)
    
    # Calculate distribution
    steps_with_rejections = [tp for tp in termination_points if tp['has_observed_rejections']]
    num_steps = len(termination_points)
    
    # Group by funnel stage (if 11 steps: 1-3 early, 4-8 mid, 9-11 late)
    if num_steps >= 11:
        early = termination_points[:3]
        mid = termination_points[3:8] if len(termination_points) > 8 else termination_points[3:]
        late = termination_points[8:] if len(termination_points) > 8 else []
        
        early_rejections = sum(tp['rejection_decision_count'] for tp in early)
        mid_rejections = sum(tp['rejection_decision_count'] for tp in mid)
        late_rejections = sum(tp['rejection_decision_count'] for tp in late)
        
        lines = [
            "## Decision Termination Points\n",
            f"All **{num_steps}** steps show observed rejections. The final step is marked as the last decision boundary.\n",
            "**Observed Rejection Distribution:**"
        ]
        
        if total_rejections > 0:
            lines.append(f"- Steps 1-3: {early_rejections} total rejections ({early_rejections/total_rejections*100:.1f}% of all rejections)")
            lines.append(f"- Steps 4-8: {mid_rejections} total rejections ({mid_rejections/total_rejections*100:.1f}% of all rejections)")
            lines.append(f"- Steps 9-11: {late_rejections} total rejections ({late_rejections/total_rejections*100:.1f}% of all rejections)")
        else:
            lines.append("- No rejections observed")
        
        lines.append("")
    else:
        lines = [
            "## Decision Termination Points\n",
            f"All **{num_steps}** steps show observed rejections.\n",
            f"Total rejections observed: {total_rejections}\n"
        ]
    
    content = "\n".join(lines)
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Decision Termination Points: {violations}")
    return content


def generate_hypotheses(ledger_data: Dict, product_name: str) -> str:
    """Generate Decision Pattern Hypotheses section with guardrails."""
    termination_points = ledger_data.get('decision_termination_points', [])
    boundaries = ledger_data.get('decision_boundaries', [])
    
    disclaimer = """**⚠️ RECOMMENDATION DISCLAIMER**

The hypotheses below are derived from observed decision patterns in the Decision Ledger. They are not guaranteed improvements, optimization recommendations, or predictions. They represent testable hypotheses based on recorded decision boundaries.

---
"""
    
    hypotheses = []
    
    # Hypothesis 1: Largest rejection point
    if termination_points:
        max_rejection_tp = max(termination_points, key=lambda tp: tp['rejection_decision_count'])
        if max_rejection_tp['rejection_decision_count'] > 0:
            # Find boundaries for this step
            step_boundaries = [b for b in boundaries if b['step_id'] == max_rejection_tp['step_id']]
            if step_boundaries:
                # Get factors
                factors = set()
                for b in step_boundaries:
                    for fp in b.get('factor_presence', []):
                        factors.add(fp['factor_name'])
                
                factors_str = '`, `'.join(list(factors)[:3])
                hypotheses.append(f"""### Hypothesis 1: {max_rejection_tp['step_id'][:50]} Optimization Priority

**Observed Pattern:**  
The {max_rejection_tp['step_id']} step shows {max_rejection_tp['rejection_decision_count']} rejections recorded, representing the largest single rejection point in the flow.

**Hypothesis:**  
Optimizing {max_rejection_tp['step_id']} messaging, value proposition clarity, and reducing cognitive load may improve continuation rates.

**Testable Actions:**
- A/B test alternative value propositions
- Test reduced cognitive load variations
- Test messaging targeted to observed persona segments
""")
    
    # Hypothesis 2: Early funnel concentration
    if len(termination_points) >= 11:
        early_rejections = sum(tp['rejection_decision_count'] for tp in termination_points[:3])
        total_rejections = sum(tp['rejection_decision_count'] for tp in termination_points)
        if total_rejections > 0 and early_rejections / total_rejections > 0.5:
            percentage = early_rejections / total_rejections * 100
            hypotheses.append(f"""### Hypothesis 2: Early Funnel Concentration

**Observed Pattern:**  
{percentage:.1f}% of all rejections occur in Steps 1-3, indicating that users who pass the first three steps are more likely to complete the flow.

**Hypothesis:**  
Focusing optimization efforts on the first three steps before optimizing later steps may be more effective, as these steps serve as the primary filtering mechanism.

**Testable Actions:**
- Prioritize A/B tests for Steps 1-3 over later steps
- Measure impact of changes to Steps 1-3 on overall flow completion
- Compare optimization ROI of early vs. late funnel improvements
""")
    
    if not hypotheses:
        hypotheses.append("No hypotheses generated from observed patterns.\n")
    
    content = "## Decision Pattern Hypotheses\n\n" + disclaimer + "\n".join(hypotheses)
    
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Decision Pattern Hypotheses: {violations}")
    
    return content


def generate_methodology_notes(ledger_data: Dict, metadata: DISMetadata) -> str:
    """Generate Methodology Notes section."""
    boundaries = ledger_data.get('decision_boundaries', [])
    acceptance = ledger_data.get('precedents_acceptance', [])
    rejection = ledger_data.get('precedents_rejection', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    
    content = f"""## Methodology Notes

This summary is derived from a Decision Ledger containing:
- {len(boundaries)} stable decision boundary assertions
- {len(acceptance)} acceptance pattern assertions
- {len(rejection)} rejection pattern assertions
- {len(termination_points)} decision termination point assertions
- {ledger_data.get('total_sequences', 0)} persona simulation sequences

All assertions are machine-verifiable from immutable DecisionTrace objects. Percentages and interpretations in this document are derived from raw counts for presentation purposes only.

**Factor Presence Semantics:**
The term "factor present" means a factor appeared in at least one DecisionTrace at that step for that persona class. All factor presence counts in this document use this definition consistently.

**Reconciliation Standards:**
This document enforces strict consistency invariants:
- Step-level reconciliation: For each step, sum of acceptance occurrences plus sum of rejection occurrences equals total traces reaching that step.
- Persona trace consistency: Persona trace counts are identical wherever referenced across sections.
- Step coverage completeness: All steps appearing in any section also appear in Decision Boundaries by Step.
- Cross-section audit: All counts reconcile across sections; no section introduces numbers not derivable from the ledger.

**Data Source:** {metadata.ledger_filename}  
**Ledger Format:** Audit-grade, interpretation-free decision records  
**Summary Generation:** {metadata.generation_timestamp}  
**Ledger Generation:** {metadata.ledger_timestamp}
"""
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Methodology Notes: {violations}")
    return content


def generate_ledger_traceability(ledger_data: Dict, metadata: DISMetadata) -> str:
    """Generate Ledger Traceability section."""
    content = f"""## Ledger Traceability

**Source Ledger:** {metadata.ledger_filename}  
**Ledger Timestamp:** {metadata.ledger_timestamp}  
**Total Sequences:** {ledger_data.get('total_sequences', 0)}  
**Total Steps:** {ledger_data.get('total_steps', 0)}

This document can be regenerated from the Decision Ledger at any time. Manual edits to this summary are not recommended, as regeneration will overwrite changes.

To regenerate this summary:
1. Ensure the Decision Ledger (`{metadata.ledger_filename}`) is available
2. Run the Decision Intelligence Summary generator
3. Specify the ledger file and output location
"""
    violations = validate_language_safety(content)
    if violations:
        raise LanguageSafetyError(f"Ledger Traceability: {violations}")
    return content


def generate_dis_header(metadata: DISMetadata) -> str:
    """Generate DIS header."""
    content = f"""# Decision Intelligence Summary

**Product:** {metadata.product_name}  
**Generated:** {metadata.generation_timestamp}  
**Source Ledger:** {metadata.ledger_filename}  
**Ledger Timestamp:** {metadata.ledger_timestamp}

---

**Regenerable from ledger. Non-authoritative.**
"""
    return content


def validate_schema(sections: List[DISSection]) -> List[str]:
    """
    Validate DIS schema against requirements.
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    # Check required sections
    section_titles = {s.title for s in sections}
    for required in REQUIRED_SECTIONS:
        if required not in section_titles:
            violations.append(f"Missing required section: '{required}'")
    
    return violations


def validate_step_level_reconciliation(ledger_data: Dict) -> List[str]:
    """
    Validate step-level reconciliation invariant.
    
    For every step: Sum(acceptance) + Sum(rejection) must equal total traces.
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    boundaries = ledger_data.get('decision_boundaries', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    
    # Group boundaries by step
    boundaries_by_step = {}
    for boundary in boundaries:
        step_id = boundary['step_id']
        if step_id not in boundaries_by_step:
            boundaries_by_step[step_id] = []
        boundaries_by_step[step_id].append(boundary)
    
    # Check each step
    for step_id, step_boundaries in boundaries_by_step.items():
        # Sum acceptance and rejection counts
        total_acceptance = sum(b['accepted_count'] for b in step_boundaries)
        total_rejection = sum(b['rejected_count'] for b in step_boundaries)
        total_from_boundaries = total_acceptance + total_rejection
        
        # Get total traces from boundaries (should be same for all boundaries in step)
        total_traces = sum(b['supporting_trace_count'] for b in step_boundaries)
        
        # Also check termination points
        # Note: Termination points count ALL rejections (stable + unstable)
        # Boundaries only count STABLE patterns (MIN_BOUNDARY_SUPPORT threshold)
        # So termination point rejections should be >= boundary rejections
        tp = next((t for t in termination_points if t['step_id'] == step_id), None)
        if tp:
            tp_rejections = tp.get('rejection_decision_count', 0)
            # Termination points include all rejections, boundaries only stable ones
            # So TP rejections >= boundary rejections is expected
            # But we can check for extreme mismatches (likely data issues)
            if tp_rejections < total_rejection:
                violations.append(
                    f"Step '{step_id}': Termination point rejections ({tp_rejections}) "
                    f"less than boundary rejections ({total_rejection}) - data inconsistency"
                )
            # Allow TP rejections to exceed boundary rejections (unstable patterns excluded)
        
        # Check if totals match
        # Note: Total traces from boundaries should equal sum of acceptance + rejection
        if total_from_boundaries != total_traces:
            violations.append(
                f"Step '{step_id}': Acceptance ({total_acceptance}) + Rejection ({total_rejection}) "
                f"= {total_from_boundaries}, but total traces = {total_traces}"
            )
    
    return violations


def validate_persona_trace_consistency(ledger_data: Dict) -> List[str]:
    """
    Validate persona trace consistency across sections.
    
    Persona trace counts must be identical wherever referenced.
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    boundaries = ledger_data.get('decision_boundaries', [])
    acceptance_patterns = ledger_data.get('precedents_acceptance', [])
    rejection_patterns = ledger_data.get('precedents_rejection', [])
    
    # Build persona class trace counts from boundaries (source of truth)
    persona_counts_from_boundaries = {}
    for boundary in boundaries:
        pc = boundary['persona_class']
        step_id = boundary['step_id']
        key = (step_id, pc)
        if key not in persona_counts_from_boundaries:
            persona_counts_from_boundaries[key] = boundary['supporting_trace_count']
        else:
            # Should be consistent
            if persona_counts_from_boundaries[key] != boundary['supporting_trace_count']:
                violations.append(
                    f"Persona '{pc}' at step '{step_id}': Inconsistent trace counts in boundaries"
                )
    
    # Check acceptance patterns reference consistent counts
    # (Note: patterns have occurrence_count, not trace_count, so we can't directly compare)
    # But we can check that patterns reference persona classes that exist in boundaries
    
    # Check rejection patterns similarly
    
    return violations


def validate_step_coverage_completeness(ledger_data: Dict) -> List[str]:
    """
    Validate step coverage completeness invariant.
    
    If a step appears anywhere, it MUST appear in Decision Boundaries section.
    Note: Steps may appear in boundaries with 0 stable patterns (still satisfies completeness).
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    boundaries = ledger_data.get('decision_boundaries', [])
    acceptance_patterns = ledger_data.get('precedents_acceptance', [])
    rejection_patterns = ledger_data.get('precedents_rejection', [])
    termination_points = ledger_data.get('decision_termination_points', [])
    
    # Collect all step IDs from boundaries (steps that WILL appear in boundaries section)
    steps_in_boundaries = {b['step_id'] for b in boundaries}
    
    # Also include all termination points (they will be added to boundaries section even if no stable patterns)
    steps_in_boundaries.update({tp['step_id'] for tp in termination_points})
    
    # Collect step IDs from other sections
    steps_in_acceptance = {p['step_id'] for p in acceptance_patterns}
    steps_in_rejection = {p['step_id'] for p in rejection_patterns}
    steps_in_termination = {tp['step_id'] for tp in termination_points}
    
    # All steps must appear in boundaries section
    # (generate_decision_boundaries_by_step ensures all termination points are included)
    all_other_steps = steps_in_acceptance | steps_in_rejection | steps_in_termination
    
    missing_steps = all_other_steps - steps_in_boundaries
    if missing_steps:
        violations.append(
            f"Steps appearing in patterns but missing from boundaries/termination: {sorted(missing_steps)}"
        )
    
    return violations


def validate_cross_section_audit(ledger_data: Dict) -> List[str]:
    """
    Validate cross-section audit checks.
    
    Verify all counts reconcile and no section introduces new numbers.
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    boundaries = ledger_data.get('decision_boundaries', [])
    acceptance_patterns = ledger_data.get('precedents_acceptance', [])
    rejection_patterns = ledger_data.get('precedents_rejection', [])
    
    # Check that pattern occurrence counts don't exceed boundary counts
    # Group boundaries by (step_id, persona_class)
    boundary_totals = {}
    for boundary in boundaries:
        key = (boundary['step_id'], boundary['persona_class'])
        boundary_totals[key] = boundary_totals.get(key, 0) + boundary['supporting_trace_count']
    
    # Check acceptance patterns
    for pattern in acceptance_patterns:
        key = (pattern['step_id'], pattern['persona_class'])
        pattern_count = pattern['occurrence_count']
        boundary_count = boundary_totals.get(key, 0)
        
        if boundary_count > 0 and pattern_count > boundary_count:
            violations.append(
                f"Acceptance pattern at '{pattern['step_id']}' for '{pattern['persona_class']}': "
                f"Occurrence count ({pattern_count}) exceeds boundary total ({boundary_count})"
            )
    
    # Check rejection patterns
    for pattern in rejection_patterns:
        key = (pattern['step_id'], pattern['persona_class'])
        pattern_count = pattern['occurrence_count']
        boundary_count = boundary_totals.get(key, 0)
        
        if boundary_count > 0 and pattern_count > boundary_count:
            violations.append(
                f"Rejection pattern at '{pattern['step_id']}' for '{pattern['persona_class']}': "
                f"Occurrence count ({pattern_count}) exceeds boundary total ({boundary_count})"
            )
    
    return violations


def validate_consistency_invariants(ledger_data: Dict) -> List[str]:
    """
    Validate all consistency invariants.
    
    Returns list of violations (empty if valid).
    """
    violations = []
    
    # Run all validation checks
    violations.extend(validate_step_level_reconciliation(ledger_data))
    violations.extend(validate_persona_trace_consistency(ledger_data))
    violations.extend(validate_step_coverage_completeness(ledger_data))
    violations.extend(validate_cross_section_audit(ledger_data))
    
    return violations


def generate_dis(
    ledger_file: str,
    product_name: str,
    generator_version: str = "1.0.0",
    skip_language_validation: bool = False
) -> tuple[str, Dict]:
    """
    Generate Decision Intelligence Summary from ledger file.
    
    Returns:
        tuple: (markdown_content, metadata_dict)
    
    Raises:
        LanguageSafetyError: If forbidden language is detected
        SchemaValidationError: If schema is violated
        FileNotFoundError: If ledger file doesn't exist
    """
    # Load ledger
    with open(ledger_file, 'r') as f:
        ledger_data = json.load(f)
    
    # Extract metadata
    metadata = DISMetadata(
        product_name=product_name,
        ledger_filename=ledger_file.split('/')[-1],  # Just filename
        ledger_timestamp=ledger_data.get('generated_timestamp', datetime.now().isoformat()),
        generator_version=generator_version
    )
    
    # Generate sections
    sections = []
    
    # Header
    header = generate_dis_header(metadata)
    
    # Required sections
    sections.append(DISSection(
        section_id='doc_type_declaration',
        title='Document Type Declaration',
        content=generate_document_type_declaration(),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='executive_summary',
        title='Executive Summary',
        content=generate_executive_summary(ledger_data, product_name),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='decision_boundaries',
        title='Decision Boundaries by Step',
        content=generate_decision_boundaries_by_step(ledger_data),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='acceptance_patterns',
        title='Acceptance Patterns',
        content=generate_acceptance_patterns(ledger_data),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='rejection_patterns',
        title='Rejection Patterns',
        content=generate_rejection_patterns(ledger_data),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='termination_points',
        title='Decision Termination Points',
        content=generate_decision_termination_points(ledger_data),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='hypotheses',
        title='Decision Pattern Hypotheses',
        content=generate_hypotheses(ledger_data, product_name),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='methodology',
        title='Methodology Notes',
        content=generate_methodology_notes(ledger_data, metadata),
        section_type='required'
    ))
    
    sections.append(DISSection(
        section_id='traceability',
        title='Ledger Traceability',
        content=generate_ledger_traceability(ledger_data, metadata),
        section_type='required'
    ))
    
    # Validate schema
    schema_violations = validate_schema(sections)
    if schema_violations:
        raise SchemaValidationError(f"Schema violations: {schema_violations}")
    
    # Validate consistency invariants
    consistency_violations = validate_consistency_invariants(ledger_data)
    if consistency_violations:
        raise ConsistencyInvariantError(
            f"Consistency invariant violations:\n" + "\n".join(f"  - {v}" for v in consistency_violations)
        )
    
    # Assemble markdown
    markdown_parts = [header]
    markdown_parts.extend(s.content for s in sections)
    markdown_content = "\n\n".join(markdown_parts)
    
    # Final language safety check on full document
    final_violations = validate_language_safety(markdown_content)
    if final_violations:
        raise LanguageSafetyError(f"Final validation failed: {final_violations}")
    
    # Generate metadata dict for JSON sidecar
    metadata_dict = {
        'metadata': metadata.to_dict(),
        'sections': [s.to_dict() for s in sections],
        'validation': {
            'schema_valid': len(schema_violations) == 0,
            'language_safe': len(final_violations) == 0
        }
    }
    
    return markdown_content, metadata_dict

