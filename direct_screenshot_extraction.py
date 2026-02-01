"""
Direct screenshot extraction - maps each screenshot to a step without LLM consolidation.
"""

from dropsim_lite_input import LiteStep
from typing import List
import re


def extract_steps_directly_from_screenshots(screenshot_texts: List[str]) -> List[LiteStep]:
    """
    Directly extract one step per screenshot without LLM consolidation.
    
    Args:
        screenshot_texts: List of screenshot analysis texts (one per screenshot)
    
    Returns:
        List of LiteStep objects (one per screenshot)
    """
    steps = []
    
    for i, screenshot_text in enumerate(screenshot_texts, 1):
        # Extract step name from screenshot analysis
        step_name = None
        step_type = "other"
        
        # Try to extract the main question or heading
        # Priority: Look for quoted questions first, then unquoted questions
        patterns = [
            (r'Main Question[:\s]+"([^"]+)"', 1),
            (r'Main question[:\s]+"([^"]+)"', 1),
            (r'question is[:\s]+"([^"]+)"', 1),
            (r'question is[:\s]+([^\n\.\?]+)', 1),
            (r'"([^"]+\?)"', 1),  # Quoted question with ?
            (r'"([^"]+)"', 1),  # Any quoted text
            (r'Main Question[:\s]+([^\n\.]+)', 1),
            (r'Main question[:\s]+([^\n\.]+)', 1),
            (r'(What is[^\.\?\n]+[\.\?]?)', 1),  # What is... question
            (r'(What are[^\.\?\n]+[\.\?]?)', 1),  # What are... question
            (r'(Enter[^\.\?\n]+[\.\?]?)', 1),
            (r'(Input[^\.\?\n]+[\.\?]?)', 1),
            (r'(Select[^\.\?\n]+[\.\?]?)', 1),
            (r'(Choose[^\.\?\n]+[\.\?]?)', 1),
        ]
        
        for pattern, group_num in patterns:
            match = re.search(pattern, screenshot_text, re.IGNORECASE)
            if match and match.lastindex >= group_num:
                step_name = match.group(group_num).strip()
                # Clean up - remove trailing periods if it's a question
                if step_name.endswith('.') and '?' not in step_name:
                    step_name = step_name[:-1]
                # Limit length to reasonable question length
                if len(step_name) > 150:
                    # Try to find sentence boundary
                    sentences = step_name.split('.')
                    if sentences:
                        step_name = sentences[0].strip()
                break
        
        # If no question found, try to extract from description
        if not step_name:
            # Look for "What is..." or similar question patterns in the text (more specific)
            question_match = re.search(r'(What is[^\.\?\n]+[\.\?]?|What are[^\.\?\n]+[\.\?]?|Enter[^\.\?\n]+[\.\?]?|Input[^\.\?\n]+[\.\?]?|Select[^\.\?\n]+[\.\?]?|Choose[^\.\?\n]+[\.\?]?)', screenshot_text, re.IGNORECASE)
            if question_match:
                step_name = question_match.group(0).strip()
                # Clean up - remove trailing periods if it's a question
                if step_name.endswith('.') and '?' not in step_name:
                    step_name = step_name[:-1]
                # Limit to reasonable length
                if len(step_name) > 100:
                    step_name = step_name[:100].rsplit(' ', 1)[0]  # Cut at word boundary
            else:
                # Look for quoted text (often questions) - prefer shorter quotes
                quoted_matches = re.findall(r'"([^"]+)"', screenshot_text)
                if quoted_matches:
                    # Prefer shorter quotes (likely questions)
                    step_name = min(quoted_matches, key=len)
                    if len(step_name) > 100:
                        step_name = step_name[:100]
                else:
                    # Fallback: use first meaningful sentence (but limit length)
                    sentences = screenshot_text.split('.')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 10 and len(sentence) < 100 and not sentence.startswith('Screenshot') and not sentence.startswith('**'):
                            step_name = sentence
                            break
        
        # Clean up step name - remove markdown formatting
        if step_name:
            step_name = step_name.replace('**', '').replace('*', '').strip()
            # Remove common prefixes
            step_name = re.sub(r'^(is:\s*|question is:\s*|Main Question:\s*|Main question:\s*)', '', step_name, flags=re.IGNORECASE)
            step_name = step_name.strip()
        
        # Final fallback
        if not step_name:
            step_name = f"Step {i}"
        
        # Determine step type
        name_lower = step_name.lower()
        screenshot_lower = screenshot_text.lower()
        
        # Detect commitment gates: landing pages with CTAs that require action
        # Check for CTA indicators in screenshot text
        has_cta = any(phrase in screenshot_lower for phrase in [
            'cta', 'button', 'click', 'find my', 'find the', 'get started', 'start', 'begin',
            'apply now', 'proceed', 'next', 'continue', 'sign up', 'register', 'perfect card',
            'best credit card', '60 seconds', 'quiz'
        ])
        # First step is almost always a landing page
        is_passive_landing = (
            i == 1 and 
            not ('question' in screenshot_lower or 'step' in screenshot_lower or 'progress' in screenshot_lower)
        )
        # Commitment gate: landing page (step 1) with CTA
        is_commitment_gate = is_passive_landing and has_cta
        
        if is_commitment_gate:
            step_type = "landing"
        elif i == 1 or 'landing' in name_lower or 'welcome' in name_lower:
            step_type = "landing"
        elif 'email' in name_lower or 'phone' in name_lower or 'otp' in name_lower:
            step_type = "signup"
        elif 'kyc' in name_lower or 'pan' in name_lower or 'aadhaar' in name_lower:
            step_type = "kyc"
        elif 'payment' in name_lower or 'pay' in name_lower:
            step_type = "payment"
        elif 'consent' in name_lower or 'terms' in name_lower:
            step_type = "consent"
        else:
            step_type = "other"
        
        # Infer attributes from screenshot description
        mental_complexity = "medium"
        effort = "medium"
        risk = "low"
        irreversible = False
        value_visibility = "low"
        delay_to_value = "later"
        reassurance = "medium"
        authority = "medium"
        
        # Special handling for commitment gates (landing pages with CTAs)
        if is_commitment_gate:
            # Landing pages with CTAs require commitment to proceed
            # The CTA click is a commitment decision, not just passive browsing
            effort = "high"  # Clicking CTA requires commitment (activation energy)
            risk = "medium"  # Starting a quiz feels like commitment (loss of optionality)
            mental_complexity = "low"  # Low cognitive load (just reading)
            value_visibility = "low"  # Value is promised, not shown
            delay_to_value = "later"  # Value comes after quiz completion
            reassurance = "medium"  # Some reassurance signals (No PAN, No sensitive data)
            authority = "medium"  # Moderate authority signals
        elif 'input' in screenshot_lower or 'enter' in screenshot_lower or 'question' in screenshot_lower:
            # Active input/question steps
            effort = "medium"
            mental_complexity = "medium"
        elif 'financial' in screenshot_lower or 'salary' in screenshot_lower or 'payout' in screenshot_lower:
            risk = "medium"
            mental_complexity = "high"
        elif 'email' in screenshot_lower:
            risk = "low"
            effort = "low"
        elif 'calculation' in screenshot_lower or 'graph' in screenshot_lower:
            mental_complexity = "high"
        elif 'quiz' in screenshot_lower or 'question' in screenshot_lower:
            # Quiz/question steps are active
            effort = "medium"
            mental_complexity = "medium"
            risk = "low"  # Quiz is low risk
        elif i == len(screenshot_texts):  # Last step
            value_visibility = "high"
            delay_to_value = "instant"
        
        step = LiteStep(
            name=step_name,
            type=step_type,
            mental_complexity=mental_complexity,
            effort=effort,
            risk=risk,
            irreversible=irreversible,
            value_visibility=value_visibility,
            delay_to_value=delay_to_value,
            reassurance=reassurance,
            authority=authority
        )
        
        steps.append(step)
    
    return steps

