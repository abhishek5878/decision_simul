#!/usr/bin/env python3
"""
CirclePe Enhanced Inference Generator
Uses LLM to generate rich, specific inferences about WhatsApp onboarding flow
"""

import json
import os
from typing import Dict, List
from user_inference_generator import UserInferenceGenerator, StepDecisionSimulation, StepInference


class CirclePeEnhancedInferenceGenerator(UserInferenceGenerator):
    """Enhanced inference generator for CirclePe WhatsApp flow using LLM."""
    
    def __init__(self, product_steps, product_name, llm_client=None):
        super().__init__(product_steps, product_name)
        self.llm_client = llm_client
        self.use_llm = llm_client is not None
    
    def generate_inference_for_step(self, step_id, step_index, inference_level):
        """Generate CirclePe-specific inference using LLM."""
        step_def = self.product_steps.get(step_id, {})
        total_steps = len(self.step_order)
        
        if self.use_llm:
            return self._generate_llm_inference(step_id, step_def, step_index, total_steps, inference_level)
        else:
            return self._generate_rule_based_inference(step_id, step_def, step_index, total_steps, inference_level)
    
    def _generate_llm_inference(self, step_id, step_def, step_index, total_steps, inference_level):
        """Generate inference using LLM with CirclePe-specific context."""
        
        prompt = f"""You are analyzing CirclePe's WhatsApp onboarding flow for zero security deposit rental platform.

**PRODUCT CONTEXT:**
- CirclePe helps tenants move in without paying 2-6 months security deposit
- Landlords receive 8-10 months advance rent (non-refundable) + additional security deposit
- Target users: 22-35 year old professionals in Tier-1 cities (Bengaluru, Mumbai, Delhi-NCR)
- User intent: Need quick move-in without large upfront cash, seeking zero deposit rental solutions

**CURRENT STEP: {step_id} (Step {step_index + 1} of {total_steps})**
**Step Description:** {step_def.get('description', '')}

**STEP ATTRIBUTES:**
- Risk Signal: {step_def.get('risk_signal', 0.0):.1f}
- Value Shown: {step_def.get('explicit_value', 0.0):.1f}
- Delay to Value: {step_def.get('delay_to_value', total_steps)} steps remaining
- Effort Demand: {step_def.get('effort_demand', 0.0):.1f}
- Irreversibility: {step_def.get('irreversibility', 0.0):.1f}
- Reassurance Signal: {step_def.get('reassurance_signal', 0.0):.1f}
- Authority Signal: {step_def.get('authority_signal', 0.0):.1f}

**CIRCLEPE WHATSAPP FLOW SPECIFICS:**
- Step 0 (Entry): User clicks wa.me link, bot triggers immediately
- Step 1 (Welcome): Greeting with IIT-IIM branding, partner logos (Paytm, BharatPe, OYO, Uni), "ONE STEP AWAY" message
- Step 2 (User Type Selection): Tenant vs Landlord choice - THIS IS A COMMITMENT POINT
- Step 3 (Path-Specific): Tenant sees eligibility prompt, Landlord sees benefits/calculator - APP REDIRECT REQUIRED HERE
- Step 4 (App/Agent): Final step - app download or agent handover - VALUE SHOWN HERE BUT FRICTION HIGH

**CRITICAL FOR CIRCLEPE:**
- WhatsApp creates low-friction expectation - users expect quick answers in chat
- App redirect breaks the WhatsApp experience - creates friction
- Value (eligibility estimate, advance rent calculation) is delayed until app or agent
- Users want to see value BEFORE committing to app download or agent wait

**TASK:**
Generate what a user at {inference_level} comprehension level would:
1. **See** (exact UI elements, text, buttons visible in WhatsApp - be specific about WhatsApp interface)
2. **Think** (immediate mental model - what they believe is happening in this WhatsApp step)
3. **Understand** (deeper comprehension - value, commitment, trust implications for zero deposit rental)
4. **Feel** (emotional state - urgency for move-in, anxiety about security deposit, trust in zero deposit model)

**Inference Level Guidelines:**
- **30%**: Surface-level, first impression. User sees basic WhatsApp message but doesn't understand deeper implications.
- **60%**: Moderate understanding. User sees patterns and connects some dots about zero deposit model, but not fully aware of all implications.
- **100%**: Full understanding. User sees complete picture, understands zero deposit model, app redirect requirement, and makes informed decision.

**CIRCLEPE-SPECIFIC CONSIDERATIONS:**
- If delay_to_value is {step_def.get('delay_to_value', total_steps)}, user knows they won't see eligibility/calculator for {step_def.get('delay_to_value', total_steps)} more steps
- If risk_signal is {step_def.get('risk_signal', 0.0):.1f}, user feels anxiety about zero deposit model or commitment
- If explicit_value is {step_def.get('explicit_value', 0.0):.1f}, user hasn't seen eligibility/calculator yet - this creates uncertainty
- If this is Step 2 (User Type Selection), user is being asked to commit to Tenant/Landlord path - this is a key decision point
- If this is Step 3 (Path-Specific), user is about to be redirected to app - this breaks WhatsApp low-friction expectation
- WhatsApp interface means: quick replies, list buttons, carousel images, minimal typing

Return ONLY valid JSON:
{{
    "what_user_sees": "...",
    "what_user_thinks": "...",
    "what_user_understands": "...",
    "emotional_state": "..."
}}"""
        
        try:
            response = self.llm_client.complete(prompt)
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                inference_data = json.loads(json_match.group())
                return StepInference(
                    inference_level=inference_level,
                    what_user_sees=inference_data.get('what_user_sees', ''),
                    what_user_thinks=inference_data.get('what_user_thinks', ''),
                    what_user_understands=inference_data.get('what_user_understands', ''),
                    emotional_state=inference_data.get('emotional_state', '')
                )
        except Exception as e:
            print(f"   ⚠️  LLM inference failed for {step_id}: {e}")
        
        # Fallback to rule-based
        return self._generate_rule_based_inference(step_id, step_def, step_index, total_steps, inference_level)
    
    def _generate_rule_based_inference(self, step_id, step_def, step_index, total_steps, inference_level):
        """Fallback rule-based inference for CirclePe."""
        delay = step_def.get('delay_to_value', total_steps)
        value = step_def.get('explicit_value', 0.0)
        risk = step_def.get('risk_signal', 0.0)
        
        if step_id == "Entry":
            sees = "WhatsApp message from CirclePe bot. Low-friction entry via familiar WhatsApp interface."
            thinks = "This is a rental platform. They want me to explore zero deposit options."
            understands = f"Value (eligibility/calculator) is {delay} steps away. This is just entry."
            feels = "Curious, low commitment, expecting quick WhatsApp interaction"
        elif "Welcome" in step_id:
            sees = "Welcome message with IIT-IIM branding, partner logos (Paytm, BharatPe, OYO, Uni), 'ONE STEP AWAY' text, Services button"
            thinks = "They're showing trust signals but I haven't seen my eligibility or calculator yet."
            understands = f"Branding shown but value delayed {delay} steps. Need to proceed to see eligibility."
            feels = "Slightly anxious - want to see value, not just branding"
        elif "User Type Selection" in step_id:
            sees = "Services list: Tenant or Landlord options. This is a choice that commits me to a path."
            thinks = "I need to choose Tenant or Landlord but I don't know what I'll get yet."
            understands = f"Commitment required before seeing value. Still {delay} steps from eligibility/calculator."
            feels = "Anxious about committing without seeing value first"
        elif "Path-Specific" in step_id:
            sees = "Tenant: Eligibility prompt with app redirect button. Landlord: Benefits/calculator with app redirect."
            thinks = "They want me to download the app or wait for agent. I wanted to see this in WhatsApp."
            understands = f"Value is shown but requires app download or agent wait. This breaks WhatsApp low-friction expectation."
            feels = "Frustrated - WhatsApp was supposed to be quick, now I need app or agent"
        else:  # App Redirect or Agent Handover
            sees = "App download prompt or agent connecting message. Eligibility/calculator shown but in app or via agent."
            thinks = "Finally I see value but I have to download app or wait for agent."
            understands = "Value delivered but friction is high. WhatsApp promise of low-friction is broken."
            feels = "Mixed - value shown but friction is high"
        
        return StepInference(
            inference_level=inference_level,
            what_user_sees=sees,
            what_user_thinks=thinks,
            what_user_understands=understands,
            emotional_state=feels
        )
    
    def generate_all_step_simulations(self):
        """Generate simulations for all steps."""
        simulations = []
        for step_index, step_id in enumerate(self.step_order):
            step_def = self.product_steps[step_id]
            
            inferences = [
                self.generate_inference_for_step(step_id, step_index, "30%"),
                self.generate_inference_for_step(step_id, step_index, "60%"),
                self.generate_inference_for_step(step_id, step_index, "100%")
            ]
            
            sim = StepDecisionSimulation(
                step_id=step_id,
                step_index=step_index,
                step_description=step_def.get('description', ''),
                inferences=inferences
            )
            simulations.append(sim)
        
        return simulations
    
    def to_dict(self, simulation):
        """Convert to dict format."""
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
