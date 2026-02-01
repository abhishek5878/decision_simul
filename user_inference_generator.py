"""
User Inference Generator

Generates different levels of user inference (30%, 60%, 100%) for each product step.
This captures what users actually see, think, and understand at each step - real human behavior.

Uses LLM when available for more realistic, nuanced inferences, falls back to rule-based otherwise.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StepInference:
    """User inference at a specific level for a step."""
    inference_level: str  # "30%", "60%", "100%"
    what_user_sees: str  # What the user actually perceives
    what_user_thinks: str  # What the user thinks is happening
    what_user_understands: str  # What the user understands about value/commitment
    emotional_state: str  # How the user feels at this moment


@dataclass
class StepDecisionSimulation:
    """Complete decision simulation for a step."""
    step_id: str
    step_index: int
    step_description: str
    inferences: List[StepInference]  # 30%, 60%, 100%


class UserInferenceGenerator:
    """
    Generates user inferences at different comprehension levels using LLM or rule-based reasoning.
    """
    
    def __init__(self, product_steps: Dict[str, Dict], product_name: str, llm_client=None):
        """
        Initialize generator.
        
        Args:
            product_steps: Dictionary mapping step_id to step definition
            product_name: Product name for context
            llm_client: Optional LLM client (must implement .complete() method)
        """
        self.product_steps = product_steps
        self.product_name = product_name
        self.step_order = list(product_steps.keys())
        self.llm_client = llm_client
        self.use_llm = llm_client is not None
    
    def generate_inference_30_percent(self, step_id: str, step_def: Dict, step_index: int, total_steps: int) -> StepInference:
        """
        Generate 30% inference level - surface-level, first impression.
        User sees basic elements but doesn't understand deeper implications.
        """
        step_desc = step_def.get('description', step_id)
        delay_to_value = step_def.get('delay_to_value', total_steps)
        explicit_value = step_def.get('explicit_value', 0.0)
        risk_signal = step_def.get('risk_signal', 0.0)
        effort_demand = step_def.get('effort_demand', 0.0)
        
        # What user sees (surface level)
        if step_index == 0:
            what_sees = f"Landing page with {self.product_name} branding and a call-to-action button"
        elif "mobile" in step_id.lower() or "phone" in step_id.lower():
            what_sees = "A form asking for mobile number"
        elif "pan" in step_id.lower() or "dob" in step_id.lower():
            what_sees = "A form asking for PAN and date of birth"
        elif "otp" in step_id.lower():
            what_sees = "A screen asking to enter OTP sent to phone"
        elif "bank" in step_id.lower() or "account" in step_id.lower():
            what_sees = "A screen asking to link bank account"
        elif "eligibility" in step_id.lower() or "result" in step_id.lower():
            what_sees = "A screen showing eligibility or results"
        else:
            what_sees = f"A screen with {step_desc}"
        
        # What user thinks (30% - minimal understanding)
        if step_index == 0:
            what_thinks = "This looks like a financial product. I can explore without commitment."
        elif effort_demand > 0.3:
            what_thinks = "They want some information from me. I'll provide it if it's quick."
        elif risk_signal > 0.3:
            what_thinks = "This seems important. I should be careful about what I share."
        else:
            what_thinks = "I need to fill this out to continue. Seems straightforward."
        
        # What user understands (30% - very limited)
        if delay_to_value > step_index:
            what_understands = "I'm still in the process. I haven't seen what I'll get yet."
        elif explicit_value > 0.5:
            what_understands = "There might be some benefit, but I'm not sure what exactly."
        else:
            what_understands = "I'm providing information, but unclear what happens next."
        
        # Emotional state (30% - initial reaction)
        if risk_signal > 0.4:
            emotional = "Cautious, slightly anxious about sharing information"
        elif effort_demand > 0.4:
            emotional = "Slightly hesitant, wondering if this is worth the effort"
        else:
            emotional = "Neutral, exploring without strong feelings"
        
        return StepInference(
            inference_level="30%",
            what_user_sees=what_sees,
            what_user_thinks=what_thinks,
            what_user_understands=what_understands,
            emotional_state=emotional
        )
    
    def generate_inference_60_percent(self, step_id: str, step_def: Dict, step_index: int, total_steps: int) -> StepInference:
        """
        Generate 60% inference level - moderate understanding.
        User sees patterns and starts connecting dots, but not fully aware of implications.
        """
        step_desc = step_def.get('description', step_id)
        delay_to_value = step_def.get('delay_to_value', total_steps)
        explicit_value = step_def.get('explicit_value', 0.0)
        risk_signal = step_def.get('risk_signal', 0.0)
        irreversibility = step_def.get('irreversibility', 0.0)
        effort_demand = step_def.get('effort_demand', 0.0)
        
        # What user sees (moderate depth)
        if step_index == 0:
            what_sees = f"Landing page promising credit/loan benefits. Progress shows step {step_index + 1} of {total_steps}"
        elif "mobile" in step_id.lower():
            what_sees = "Mobile number entry form. Privacy policy link visible. Progress indicator shows early stage."
        elif "pan" in step_id.lower():
            what_sees = "PAN and DOB form. Security badges visible. Mentions credit check but 'no impact on score'."
        elif "bank" in step_id.lower():
            what_sees = "Bank account linking screen. Mentions 'read-only access' and 'for loan disbursement'."
        elif "eligibility" in step_id.lower():
            what_sees = "Eligibility results screen showing loan amount/limit. Clear value proposition visible."
        else:
            what_sees = f"{step_desc}. Progress shows {step_index + 1}/{total_steps}"
        
        # What user thinks (60% - pattern recognition)
        if step_index == 0:
            what_thinks = "This is a credit/loan product. I'll need to provide some information to see if I qualify."
        elif delay_to_value > step_index and step_index > 0:
            what_thinks = "I've answered several questions but haven't seen my results yet. I'm getting closer."
        elif risk_signal > 0.4:
            what_thinks = "They're asking for sensitive financial information. I should understand what I'm committing to."
        elif irreversibility > 0.3:
            what_thinks = "This feels like a commitment. I should make sure I want to proceed."
        else:
            what_thinks = "This is part of the process. I'll continue if it's not too complicated."
        
        # What user understands (60% - partial understanding)
        if delay_to_value > step_index:
            what_understands = f"I'm {step_index + 1} steps in. I expect to see results in {delay_to_value - step_index} more steps. Value is coming but not yet shown."
        elif explicit_value > 0.5:
            what_understands = "I can see some value proposition, but I'm not sure if it's personalized to me yet."
        else:
            what_understands = "I'm providing information that will help determine my eligibility or options."
        
        # Emotional state (60% - developing feelings)
        if risk_signal > 0.4 and delay_to_value > step_index:
            emotional = "Growing concern - sharing sensitive info without seeing value yet"
        elif irreversibility > 0.3:
            emotional = "Hesitant - this feels like a commitment I can't easily undo"
        elif delay_to_value > step_index and step_index > 2:
            emotional = "Impatient - I've invested time but haven't seen results"
        else:
            emotional = "Engaged but cautious - proceeding with moderate trust"
        
        return StepInference(
            inference_level="60%",
            what_user_sees=what_sees,
            what_user_thinks=what_thinks,
            what_user_understands=what_understands,
            emotional_state=emotional
        )
    
    def generate_inference_100_percent(self, step_id: str, step_def: Dict, step_index: int, total_steps: int) -> StepInference:
        """
        Generate 100% inference level - full understanding.
        User sees the complete picture, understands implications, and makes informed decision.
        """
        step_desc = step_def.get('description', step_id)
        delay_to_value = step_def.get('delay_to_value', total_steps)
        explicit_value = step_def.get('explicit_value', 0.0)
        risk_signal = step_def.get('risk_signal', 0.0)
        irreversibility = step_def.get('irreversibility', 0.0)
        effort_demand = step_def.get('effort_demand', 0.0)
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
        
        # What user sees (full context)
        if step_index == 0:
            what_sees = f"Landing page: {step_desc}. Value proposition visible but generic. No personalized eligibility shown. Progress: {progress_pct}%"
        elif "mobile" in step_id.lower():
            what_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): Mobile number entry. Privacy policy mentions data sharing. No value shown yet. {delay_to_value - step_index} steps until value."
        elif "pan" in step_id.lower():
            what_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): PAN/DOB form. Security badges present. 'No credit score impact' mentioned. Still {delay_to_value - step_index} steps from seeing eligibility."
        elif "bank" in step_id.lower():
            what_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): Bank linking required. 'For disbursement' mentioned. Read-only access promised. Value still {delay_to_value - step_index} steps away."
        elif "eligibility" in step_id.lower():
            what_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): Eligibility results shown. Personalized loan amount/limit displayed. FIRST VALUE MOMENT."
        else:
            what_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): {step_desc}. Irreversibility: {irreversibility:.1f}. Value delay: {delay_to_value - step_index} steps."
        
        # What user thinks (100% - complete understanding)
        if step_index == 0:
            what_thinks = "This is a credit/loan product. They want me to start a process that will require personal information. I haven't seen if I qualify yet, but they're asking me to begin."
        elif delay_to_value > step_index and risk_signal > 0.3:
            what_thinks = f"I'm at step {step_index + 1} and they're asking for {step_desc.lower()}. I've shared information but haven't seen my personalized results. I'm {delay_to_value - step_index} steps away from value, but they want more sensitive data now."
        elif delay_to_value <= step_index:
            what_thinks = "I'm finally seeing my eligibility/results. This is what I came for. Now I understand what I qualify for."
        elif irreversibility > 0.3:
            what_thinks = "This step requires irreversible commitment. I'm being asked to commit before I've seen my personalized value. This feels like a bait-and-switch."
        else:
            what_thinks = f"I understand this is step {step_index + 1} of {total_steps}. I'm providing information to get personalized results, but value hasn't been shown yet."
        
        # What user understands (100% - complete picture)
        if delay_to_value > step_index:
            what_understands = f"VALUE MISMATCH: I'm at step {step_index + 1} but value appears at step {delay_to_value + 1}. I'm being asked to share {step_desc.lower()} {delay_to_value - step_index} steps BEFORE seeing what I'll get. This violates value-before-trust principle."
        elif explicit_value > 0.5:
            what_understands = "I can see value now (eligibility/loan amount). This justifies the information I've shared. Trust is established because value was shown."
        elif irreversibility > 0.3:
            what_understands = f"COMMITMENT MISMATCH: This step has irreversibility {irreversibility:.1f} but I haven't seen personalized value. I'm being asked to commit permanently without knowing what I'm committing to."
        else:
            what_understands = "I understand the process flow. I'm providing information that will lead to personalized results. The sequence makes sense."
        
        # Emotional state (100% - full awareness of implications)
        if delay_to_value > step_index and risk_signal > 0.3:
            emotional = "Frustrated and suspicious - being asked for sensitive data without value demonstration feels like a trap"
        elif delay_to_value > step_index and step_index > 2:
            emotional = "Impatient and losing trust - I've invested multiple steps but value keeps being delayed"
        elif irreversibility > 0.3 and delay_to_value > step_index:
            emotional = "Anxious and resistant - irreversible commitment without value feels like exploitation"
        elif delay_to_value <= step_index:
            emotional = "Relieved and engaged - finally seeing value justifies the process"
        else:
            emotional = "Cautiously optimistic - proceeding but aware of the trust-value gap"
        
        return StepInference(
            inference_level="100%",
            what_user_sees=what_sees,
            what_user_thinks=what_thinks,
            what_user_understands=what_understands,
            emotional_state=emotional
        )
    
    def generate_inference_with_llm(self, step_id: str, step_def: Dict, step_index: int, total_steps: int, inference_level: str) -> StepInference:
        """
        Generate inference using LLM for more realistic, nuanced understanding.
        """
        if not self.llm_client:
            # Fallback to rule-based
            if inference_level == "30%":
                return self.generate_inference_30_percent(step_id, step_def, step_index, total_steps)
            elif inference_level == "60%":
                return self.generate_inference_60_percent(step_id, step_def, step_index, total_steps)
            else:
                return self.generate_inference_100_percent(step_id, step_def, step_index, total_steps)
        
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
        delay_to_value = step_def.get('delay_to_value', total_steps)
        steps_until_value = delay_to_value - step_index
        
        prompt = f"""You are analyzing a user's mental state at step {step_index + 1} of {total_steps} ({progress_pct}% progress) in the {self.product_name} onboarding flow.

Step: {step_id}
Description: {step_def.get('description', 'N/A')}
Step Attributes:
- Cognitive demand: {step_def.get('cognitive_demand', 0.0):.1f}
- Effort demand: {step_def.get('effort_demand', 0.0):.1f}
- Risk signal: {step_def.get('risk_signal', 0.0):.1f}
- Irreversibility: {step_def.get('irreversibility', 0.0):.1f}
- Explicit value: {step_def.get('explicit_value', 0.0):.1f}
- Steps until value: {steps_until_value}
- Reassurance signal: {step_def.get('reassurance_signal', 0.0):.1f}

Generate what a user with {inference_level} comprehension level would:
1. **See** (surface-level perception - what they actually notice on screen)
2. **Think** (their immediate mental model - what they believe is happening)
3. **Understand** (deeper comprehension - what they realize about value, commitment, trust)
4. **Feel** (emotional state - how they feel at this moment)

Inference Level Guidelines:
- **30%**: Surface-level, first impression. User sees basic elements but doesn't understand deeper implications. Minimal pattern recognition.
- **60%**: Moderate understanding. User sees patterns and connects some dots, but not fully aware of all implications. Partial trust/value awareness.
- **100%**: Full understanding. User sees complete picture, understands all implications, makes informed decision. Aware of value-trust gaps, commitment risks.

Return ONLY valid JSON in this format:
{{
    "what_user_sees": "...",
    "what_user_thinks": "...",
    "what_user_understands": "...",
    "emotional_state": "..."
}}

Be specific, realistic, and capture real human psychology. Use Indian fintech context if relevant."""
        
        try:
            response = self.llm_client.complete(prompt)
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                result = json.loads(json_str)
                
                return StepInference(
                    inference_level=inference_level,
                    what_user_sees=result.get('what_user_sees', ''),
                    what_user_thinks=result.get('what_user_thinks', ''),
                    what_user_understands=result.get('what_user_understands', ''),
                    emotional_state=result.get('emotional_state', '')
                )
        except Exception as e:
            # Fallback to rule-based on error
            pass
        
        # Fallback to rule-based
        if inference_level == "30%":
            return self.generate_inference_30_percent(step_id, step_def, step_index, total_steps)
        elif inference_level == "60%":
            return self.generate_inference_60_percent(step_id, step_def, step_index, total_steps)
        else:
            return self.generate_inference_100_percent(step_id, step_def, step_index, total_steps)
    
    def generate_step_simulation(self, step_id: str) -> StepDecisionSimulation:
        """
        Generate complete decision simulation for a step with all inference levels.
        """
        step_def = self.product_steps.get(step_id, {})
        step_index = self.step_order.index(step_id) if step_id in self.step_order else 0
        total_steps = len(self.step_order)
        
        if self.use_llm:
            inferences = [
                self.generate_inference_with_llm(step_id, step_def, step_index, total_steps, "30%"),
                self.generate_inference_with_llm(step_id, step_def, step_index, total_steps, "60%"),
                self.generate_inference_with_llm(step_id, step_def, step_index, total_steps, "100%")
            ]
        else:
            inferences = [
                self.generate_inference_30_percent(step_id, step_def, step_index, total_steps),
                self.generate_inference_60_percent(step_id, step_def, step_index, total_steps),
                self.generate_inference_100_percent(step_id, step_def, step_index, total_steps)
            ]
        
        return StepDecisionSimulation(
            step_id=step_id,
            step_index=step_index,
            step_description=step_def.get('description', step_id),
            inferences=inferences
        )
    
    def generate_all_step_simulations(self) -> List[StepDecisionSimulation]:
        """
        Generate decision simulations for all steps.
        """
        simulations = []
        for step_id in self.step_order:
            simulation = self.generate_step_simulation(step_id)
            simulations.append(simulation)
        return simulations
    
    def generate_persona_inference_for_step(self, step_id: str, step_def: Dict, step_index: int, total_steps: int, persona_id: str, inference_level: str) -> StepInference:
        """
        Generate persona-specific inference for a step at a given inference level.
        This creates personalized inferences based on the persona's characteristics.
        """
        # Extract persona characteristics from persona_id
        persona_lower = persona_id.lower()
        
        # Determine persona traits
        is_distrustful = 'distrustful' in persona_lower
        is_tired = 'tired' in persona_lower
        is_casual = 'browsing' in persona_lower or 'casual' in persona_lower
        is_price_sensitive = 'price' in persona_lower
        is_motivated = 'motivated' in persona_lower
        is_tech_savvy = 'tech' in persona_lower or 'savvy' in persona_lower
        is_urgent = 'urgent' in persona_lower
        
        # Adjust inference based on persona traits
        if self.use_llm:
            # Use LLM with persona context
            progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
            delay_to_value = step_def.get('delay_to_value', total_steps)
            steps_until_value = delay_to_value - step_index
            
            persona_context = []
            if is_distrustful:
                persona_context.append("distrustful and skeptical")
            if is_tired:
                persona_context.append("tired and low on cognitive energy")
            if is_casual:
                persona_context.append("casually browsing without strong intent")
            if is_price_sensitive:
                persona_context.append("highly price-sensitive and deal-focused")
            if is_motivated:
                persona_context.append("fresh and motivated")
            if is_tech_savvy:
                persona_context.append("tech-savvy and optimistic about digital products")
            if is_urgent:
                persona_context.append("has urgent need and is willing to move quickly")
            
            persona_desc = ", ".join(persona_context) if persona_context else "typical user"
            
            prompt = f"""You are analyzing a {persona_desc} user's mental state at step {step_index + 1} of {total_steps} ({progress_pct}% progress) in the {self.product_name} onboarding flow.

Persona: {persona_id}
Step: {step_id}
Description: {step_def.get('description', 'N/A')}
Step Attributes:
- Cognitive demand: {step_def.get('cognitive_demand', 0.0):.1f}
- Effort demand: {step_def.get('effort_demand', 0.0):.1f}
- Risk signal: {step_def.get('risk_signal', 0.0):.1f}
- Irreversibility: {step_def.get('irreversibility', 0.0):.1f}
- Explicit value: {step_def.get('explicit_value', 0.0):.1f}
- Steps until value: {steps_until_value}
- Reassurance signal: {step_def.get('reassurance_signal', 0.0):.1f}

Generate what this specific user (with {inference_level} comprehension level) would:
1. **See** (surface-level perception - what they actually notice on screen)
2. **Think** (their immediate mental model - what they believe is happening, considering their persona traits)
3. **Understand** (deeper comprehension - what they realize about value, commitment, trust)
4. **Feel** (emotional state - how they feel at this moment, reflecting their persona characteristics)

Inference Level Guidelines:
- **30%**: Surface-level, first impression. User sees basic elements but doesn't understand deeper implications. Minimal pattern recognition.
- **60%**: Moderate understanding. User sees patterns and connects some dots, but not fully aware of all implications. Partial trust/value awareness.
- **100%**: Full understanding. User sees complete picture, understands all implications, makes informed decision. Aware of value-trust gaps, commitment risks.

Persona Traits to Consider:
- Distrustful users: More suspicious, need more reassurance
- Tired users: Lower cognitive capacity, more likely to abandon
- Casual browsers: Less committed, easily distracted
- Price-sensitive: Focus on costs and deals
- Motivated: Higher engagement, more willing to proceed
- Tech-savvy: More comfortable with digital processes
- Urgent: Willing to move fast but also need quick value

Return ONLY valid JSON in this format:
{{
    "what_user_sees": "...",
    "what_user_thinks": "...",
    "what_user_understands": "...",
    "emotional_state": "..."
}}

Be specific, realistic, and capture real human psychology. Use Indian fintech context if relevant."""
            
            try:
                response = self.llm_client.complete(prompt)
                if "{" in response and "}" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    
                    return StepInference(
                        inference_level=inference_level,
                        what_user_sees=result.get('what_user_sees', ''),
                        what_user_thinks=result.get('what_user_thinks', ''),
                        what_user_understands=result.get('what_user_understands', ''),
                        emotional_state=result.get('emotional_state', '')
                    )
            except Exception:
                pass
        
        # Fallback to step-level inference (not persona-specific)
        if inference_level == "30%":
            return self.generate_inference_30_percent(step_id, step_def, step_index, total_steps)
        elif inference_level == "60%":
            return self.generate_inference_60_percent(step_id, step_def, step_index, total_steps)
        else:
            return self.generate_inference_100_percent(step_id, step_def, step_index, total_steps)
    
    def to_dict(self, simulation: StepDecisionSimulation) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "step_id": simulation.step_id,
            "step_index": simulation.step_index,
            "step_description": simulation.step_description,
            "inferences": [
                {
                    "inference_level": inf.inference_level,
                    "what_user_sees": inf.what_user_sees,
                    "what_user_thinks": inf.what_user_thinks,
                    "what_user_understands": inf.what_user_understands,
                    "emotional_state": inf.emotional_state
                }
                for inf in simulation.inferences
            ]
        }

