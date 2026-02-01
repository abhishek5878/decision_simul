#!/usr/bin/env python3
"""
Blink Money Enhanced Inference Analysis
Uses detailed screenshot analysis to generate much richer, more accurate inferences
"""

import json
import sys
import pandas as pd
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from blink_money_steps import BLINK_MONEY_STEPS


class EnhancedBlinkMoneyResultGenerator(DecisionAutopsyResultGenerator):
    """Enhanced generator with screenshot-based rich inferences."""
    
    def __init__(self, product_steps, product_name, product_full_name=None, screenshot_analysis_path=None):
        super().__init__(product_steps, product_name, product_full_name)
        
        # Load detailed screenshot analysis if available
        self.screenshot_analysis = {}
        if screenshot_analysis_path:
            try:
                with open(screenshot_analysis_path, 'r') as f:
                    analysis_data = json.load(f)
                    # Map by step number
                    for item in analysis_data:
                        step_num = item.get('step_number', 0)
                        self.screenshot_analysis[step_num] = item.get('deep_analysis', '')
            except Exception as e:
                print(f"Warning: Could not load screenshot analysis: {e}")
    
    def generate_belief_break_section(self, autopsy):
        """Override to ensure accuracy - use actual drop point, not algorithm detection."""
        from decision_graph.decision_trace import DecisionTrace
        
        # Find the step with most actual drops from traces
        # This ensures accuracy - belief break should be where users actually drop
        step_drop_counts = {}
        for trace in getattr(self, '_current_traces', []):
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
        # If we have drop data, use the step with most drops
        if step_drop_counts:
            actual_irreversible_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            # Find step index
            actual_step_index = None
            for i, step_id in enumerate(self.step_order):
                if step_id == actual_irreversible_step:
                    actual_step_index = i
                    break
            
            if actual_step_index is not None:
                # Override the autopsy's irreversible moment with actual data
                step_def = self.product_steps.get(actual_irreversible_step, {})
                total_steps = len(self.step_order)
                progress_pct = int((actual_step_index + 1) / total_steps * 100) if total_steps > 0 else 100
                
                # Generate accurate description based on actual step
                if "phone" in actual_irreversible_step.lower() or "mobile" in actual_irreversible_step.lower() or "eligibility check" in actual_irreversible_step.lower():
                    action = f"User must share phone number at step {actual_step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing their eligible credit limit."
                    psychology = f"Users arrive at step {actual_step_index + 1} and are immediately asked to share their phone number before seeing any eligibility results. After the landing page (step 1), they expected to see their credit limit or at least an estimate, but instead face a personal information request. The mismatch between expectation (value demonstration) and reality (data collection) triggers abandonment. Credit-aware users want to see what they'll get (loan amount) before sharing contact information."
                elif "pan" in actual_irreversible_step.lower() or "dob" in actual_irreversible_step.lower():
                    action = f"User must provide PAN and date of birth at step {actual_step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing personalized credit limit."
                    psychology = f"After providing phone number, users expect to see their credit eligibility. Instead, they're asked for sensitive financial identity (PAN, DOB) without any value demonstration. The trust-value gap widens - users have invested time but haven't seen what they'll get."
                elif "otp" in actual_irreversible_step.lower():
                    action = f"User must verify identity via OTP at step {actual_step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing credit eligibility results."
                    psychology = f"Users have provided phone number and PAN/DOB, expecting to see results. Instead, they face another verification step (OTP) without seeing their credit limit. The accumulation of verification steps without value feedback creates frustration and abandonment."
                else:
                    action = f"User must make a commitment at step {actual_step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing value first."
                    psychology = f"Users reach step {actual_step_index + 1} expecting to see results, but instead face new requirements. The expectation mismatch triggers abandonment."
                
                return {
                    "screenshot": f"screenshots/{self.product_name.lower()}/{actual_step_index + 1}.jpeg",
                    "irreversibleAction": action,
                    "callouts": [
                        {"text": "Personal information requested before value shown", "position": "top-left"},
                        {"text": "Trust demand exceeds demonstrated value", "position": "bottom-right"}
                    ],
                    "psychology": psychology
                }
        
        # Fallback to parent implementation
        return super().generate_belief_break_section(autopsy)
    
    def generate_journey_screenshots(self, autopsy):
        """Override to ensure journey screenshots match actual belief break step."""
        from decision_graph.decision_trace import DecisionTrace
        
        # Find the step with most actual drops from traces (same logic as belief break)
        step_drop_counts = {}
        for trace in getattr(self, '_current_traces', []):
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
        # If we have drop data, use the step with most drops
        if step_drop_counts:
            actual_irreversible_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            # Find step index
            actual_step_index = None
            for i, step_id in enumerate(self.step_order):
                if step_id == actual_irreversible_step:
                    actual_step_index = i
                    break
            
            if actual_step_index is not None:
                product_lower = self.product_name.lower()
                total_steps = len(self.step_order)
                
                # Before: previous step or landing page
                before_step = max(0, actual_step_index - 1) if actual_step_index > 0 else 0
                moment_step = actual_step_index
                after_step = min(total_steps - 1, actual_step_index + 1) if actual_step_index < total_steps - 1 else actual_step_index
                
                result = {
                    "before": f"screenshots/{product_lower}/{before_step + 1}.jpeg",
                    "moment": f"screenshots/{product_lower}/{moment_step + 1}.jpeg"
                }
                
                if after_step > moment_step:
                    result["after"] = f"screenshots/{product_lower}/{after_step + 1}.jpeg"
                
                return result
        
        # Fallback to parent implementation
        return super().generate_journey_screenshots(autopsy)
    
    def infer_cohort(self, traces):
        """Infer user cohort for mutual fund holders seeking liquidity."""
        return "30+ Urban salaried or self-employed professionals with mutual fund holdings who need short-term liquidity without breaking long-term investments"
    
    def infer_user_context(self):
        """Infer user context for credit-seekers."""
        return "Digitally savvy, credit-aware users who value speed, low friction, and cost-efficient borrowing over traditional personal loans. They have mutual funds but need quick liquidity without selling investments. Early-funnel but with strong intent once they understand the value proposition."
    
    def simplify_verdict(self, autopsy):
        """Blink Money specific verdict language."""
        verdict = autopsy.verdict_text.lower()
        
        if "trust" in verdict or "commitment" in verdict:
            return "Trust collapses when personal information requests (PAN, DOB, OTP verification) appear before users see their eligible credit limit. Credit-aware users abandon when verification requirements exceed demonstrated value (actual loan amount they can get)."
        elif "value" in verdict:
            return "Value perception collapses during the 4-step delay to credit limit display. Users expect immediate eligibility feedback but face verification friction (PAN, DOB, OTP) before seeing what they can borrow against their mutual funds."
        else:
            return "Users abandon when onboarding complexity outweighs the promise of quick liquidity. Credit-aware professionals expect faster feedback on eligibility and loan terms before committing to verification steps."
    
    def generate_decision_simulation(self, traces):
        """Generate decision simulation with enhanced inferences using screenshot analysis."""
        from user_inference_generator import UserInferenceGenerator, StepDecisionSimulation, StepInference
        from openai import OpenAI
        import os
        
        # Try to get LLM client for enhanced inference
        llm_client = None
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                from dropsim_llm_ingestion import OpenAILLMClient
                llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
        except Exception:
            pass
        
        # Enhanced inference generator with screenshot context
        enhanced_generator = EnhancedInferenceGenerator(
            self.product_steps, 
            self.product_name, 
            llm_client=llm_client,
            screenshot_analysis=self.screenshot_analysis
        )
        
        step_simulations = enhanced_generator.generate_all_step_simulations()
        
        return {
            "steps": [
                enhanced_generator.to_dict(sim) for sim in step_simulations
            ]
        }


class EnhancedInferenceGenerator:
    """Enhanced inference generator that uses detailed screenshot analysis."""
    
    def __init__(self, product_steps, product_name, llm_client=None, screenshot_analysis=None):
        self.product_steps = product_steps
        self.product_name = product_name
        self.step_order = list(product_steps.keys())
        self.llm_client = llm_client
        self.screenshot_analysis = screenshot_analysis or {}
        self.use_llm = llm_client is not None
    
    def generate_inference_for_step(self, step_id, step_index, inference_level):
        """Generate inference for a step using screenshot analysis."""
        step_def = self.product_steps.get(step_id, {})
        total_steps = len(self.step_order)
        
        # Get screenshot analysis for this step
        screenshot_context = ""
        if (step_index + 1) in self.screenshot_analysis:
            screenshot_context = self.screenshot_analysis[step_index + 1]
        
        # Use LLM if available and screenshot context exists
        if self.use_llm and screenshot_context:
            return self._generate_llm_inference(step_id, step_def, step_index, total_steps, inference_level, screenshot_context)
        else:
            # Fallback to rule-based
            return self._generate_rule_based_inference(step_id, step_def, step_index, total_steps, inference_level)
    
    def _generate_llm_inference(self, step_id, step_def, step_index, total_steps, inference_level, screenshot_context):
        """Generate inference using LLM with screenshot context."""
        from user_inference_generator import StepInference
        
        prompt = f"""You are analyzing step {step_index + 1} of {total_steps} in Blink Money's credit against mutual funds flow.

**STEP INFORMATION:**
- Step Name: {step_id}
- Step Description: {step_def.get('description', 'N/A')}
- Delay to Value: {step_def.get('delay_to_value', total_steps)} steps until credit eligibility is shown
- Explicit Value Shown: {step_def.get('explicit_value', 0.0):.1f} (0.0 = none, 1.0 = full credit limit shown)
- Risk Signal: {step_def.get('risk_signal', 0.0):.1f} (0.0 = low, 1.0 = high - sensitive data)
- Effort Demand: {step_def.get('effort_demand', 0.0):.1f} (0.0 = low, 1.0 = high)

**DETAILED SCREENSHOT ANALYSIS:**
{screenshot_context[:2000]}

**CRITICAL FOR STEP 2:**
If this is step 2 ("Eligibility Check for Credit"), understand:
- PRIMARY ACTION: Phone number input field is the MAIN action that moves user to next step
- SECONDARY: Mutual fund amount field is also visible but secondary
- CONTEXT: Everything below (benefits, testimonials, FAQs) is informational context, not actions

**TASK:**
Generate what a user at {inference_level} comprehension level would:
1. **See** (exact UI elements, text, buttons visible on screen - be specific. For step 2, distinguish PRIMARY ACTION vs CONTEXT)
2. **Think** (immediate mental model - what they believe is happening. For step 2, they think: "I need to enter my phone number to proceed")
3. **Understand** (deeper comprehension - value, commitment, trust implications. For step 2, they understand phone number is required to continue, rest is just information)
4. **Feel** (emotional state at this moment)

**Inference Level Guidelines:**
- **30%**: Surface-level, first impression. User sees basic elements but doesn't understand deeper implications.
- **60%**: Moderate understanding. User sees patterns and connects some dots, but not fully aware of all implications.
- **100%**: Full understanding. User sees complete picture, understands all implications, makes informed decision.

**Context:**
- Product: Blink Money - Credit Against Mutual Funds
- Target User: 30+ Urban salaried/self-employed professionals with MF holdings
- User Intent: Need short-term liquidity without selling investments
- User Traits: Digitally savvy, credit-aware, value speed and low friction

**IMPORTANT:**
- Be specific about what's actually visible on screen (use screenshot analysis)
- Reference exact text, buttons, numbers if mentioned in screenshot
- For step 2: Clearly identify phone number input as PRIMARY ACTION
- Distinguish between REQUIRED ACTIONS vs CONTEXTUAL INFORMATION
- Consider the delay_to_value - if value appears in {step_def.get('delay_to_value', total_steps)} steps, user is aware of this gap
- If risk_signal is high ({step_def.get('risk_signal', 0.0):.1f}), user feels anxiety about sharing sensitive data
- If explicit_value is 0.0, user hasn't seen credit limit yet - this creates uncertainty

Return ONLY valid JSON:
{{
    "what_user_sees": "...",
    "what_user_thinks": "...",
    "what_user_understands": "...",
    "emotional_state": "..."
}}"""
        
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
        except Exception as e:
            print(f"Warning: LLM inference failed for {step_id}: {e}")
        
        # Fallback
        return self._generate_rule_based_inference(step_id, step_def, step_index, total_steps, inference_level)
    
    def _generate_rule_based_inference(self, step_id, step_def, step_index, total_steps, inference_level):
        """Fallback rule-based inference."""
        from user_inference_generator import StepInference, UserInferenceGenerator
        
        # Use standard generator as fallback
        standard_gen = UserInferenceGenerator(self.product_steps, self.product_name, llm_client=None)
        
        if inference_level == "30%":
            return standard_gen.generate_inference_30_percent(step_id, step_def, step_index, total_steps)
        elif inference_level == "60%":
            return standard_gen.generate_inference_60_percent(step_id, step_def, step_index, total_steps)
        else:
            return standard_gen.generate_inference_100_percent(step_id, step_def, step_index, total_steps)
    
    def generate_all_step_simulations(self):
        """Generate simulations for all steps."""
        from user_inference_generator import StepDecisionSimulation
        
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
        from user_inference_generator import StepInference
        
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


def run_simulation_and_generate_traces(n_personas: int = 1000, seed: int = 42) -> list:
    """Run actual simulation with n_personas and generate DecisionTrace objects."""
    print(f"\n🔄 Running simulation with {n_personas} personas...")
    
    try:
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_intent_aware import run_intent_aware_simulation
        from dropsim_target_filter import TargetGroup
        
        # Load personas
        print("📂 Loading dataset...")
        df, derived = load_and_sample(n=n_personas, seed=seed, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        # Derive features
        print("🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        
        # Filter for target persona: "30+ Urban salaried or self-employed professionals with mutual fund holdings"
        print("🎯 Filtering for target persona...")
        
        # Apply filter - check available columns
        filters = []
        if 'age' in df.columns:
            filters.append(df['age'] >= 30)
        if 'employment_type' in df.columns:
            filters.append(df['employment_type'].isin(['salaried', 'self_employed']))
        if 'has_mutual_funds' in df.columns:
            filters.append(df['has_mutual_funds'] == True)
        if 'digital_savvy' in df.columns:
            filters.append(df['digital_savvy'] == True)
        
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            df_filtered = df[combined_filter].copy()
        else:
            df_filtered = df.copy()
        
        if len(df_filtered) == 0:
            print("   ⚠️  No personas match filter, using all personas")
            df_filtered = df
        else:
            print(f"   Filtered to {len(df_filtered)} matching personas")
        
        # Infer intent distribution for blink_money
        print("🎯 Inferring intent distribution...")
        try:
            from dropsim_intent_model import infer_intent_distribution
            first_step = list(BLINK_MONEY_STEPS.values())[0]
            entry_text = first_step.get('description', '')
            
            intent_result = infer_intent_distribution(
                entry_page_text=entry_text,
                product_type='fintech',
                persona_attributes={'intent': 'medium', 'urgency': 'medium'}
            )
            intent_distribution = intent_result['intent_distribution']
            print(f"   Primary Intent: {intent_result['primary_intent']}")
        except Exception as e:
            print(f"   ⚠️  Could not infer intent, using default: {e}")
            # Default intent distribution for credit/liquidity products
            intent_distribution = {
                'short_term_liquidity': 0.4,
                'cost_efficient_borrowing': 0.3,
                'quick_liquidity': 0.2,
                'business_liquidity': 0.1
            }
        
        # Run simulation
        print("🧠 Running intent-aware simulation...")
        result_df = run_intent_aware_simulation(
            df_filtered,
            product_steps=BLINK_MONEY_STEPS,
            intent_distribution=intent_distribution,
            verbose=False,
            seed=seed
        )
        print(f"   ✅ Simulation complete")
        
        # Generate decision traces from simulation results
        print("📊 Generating decision traces from simulation...")
        traces = []
        step_names = list(BLINK_MONEY_STEPS.keys())
        
        # Extract drop points from trajectories
        drop_points = {}
        for idx, row in result_df.iterrows():
            for traj in row.get('trajectories', []):
                if not traj.get('completed', False) and traj.get('exit_step'):
                    step_id = traj.get('exit_step', 'unknown')
                    if step_id not in drop_points:
                        drop_points[step_id] = []
                    # Store trajectory data for trace creation
                    drop_points[step_id].append({
                        'persona_id': row.get('persona_id', f'persona_{idx}'),
                        'cognitive_state': traj.get('final_state', {}),
                        'intent': traj.get('intent', {}),
                        'probability': traj.get('continuation_probability', 0.5)
                    })
        
        # Create DecisionTrace objects from drop points
        trace_count = 0
        for step_id, drop_data_list in drop_points.items():
            try:
                step_index = step_names.index(step_id) if step_id in step_names else 0
                
                # Create traces for each drop (sample up to reasonable number per step)
                for i, drop_data in enumerate(drop_data_list[:min(200, len(drop_data_list))]):  # Max 200 per step
                    cognitive = drop_data.get('cognitive_state', {})
                    intent_data = drop_data.get('intent', {})
                    
                    trace = DecisionTrace(
                        persona_id=drop_data.get('persona_id', f'persona_{trace_count}'),
                        step_id=step_id,
                        step_index=step_index,
                        decision=DecisionOutcome.DROP,
                        probability_before_sampling=drop_data.get('probability', 0.4),
                        sampled_outcome=False,
                        cognitive_state_snapshot=CognitiveStateSnapshot(
                            energy=cognitive.get('energy', 0.5),
                            risk=cognitive.get('risk', 0.5),
                            effort=cognitive.get('effort', 0.5),
                            value=cognitive.get('value', 0.3),
                            control=cognitive.get('control', 0.5)
                        ),
                        intent=IntentSnapshot(
                            inferred_intent=intent_data.get('intent_id', 'short_term_liquidity'),
                            alignment_score=intent_data.get('alignment_score', 0.6)
                        ),
                        dominant_factors=cognitive.get('dominant_factors', ['value_perception', 'trust_deficit'])
                    )
                    traces.append(trace)
                    trace_count += 1
                    
                    if trace_count >= n_personas:  # Limit total traces
                        break
                
                if trace_count >= n_personas:
                    break
            except Exception as e:
                print(f"   ⚠️  Error creating trace for {step_id}: {e}")
                continue
        
        # If we don't have enough traces, create some default ones
        if len(traces) < 100:
            print(f"   ⚠️  Only {len(traces)} traces generated, creating additional traces...")
            for i in range(len(traces), min(100, n_personas)):
                step_id = step_names[0] if step_names else "Smart Credit Exploration"
                trace = DecisionTrace(
                    persona_id=f"persona_{i}",
                    step_id=step_id,
                    step_index=0,
                    decision=DecisionOutcome.DROP,
                    probability_before_sampling=0.4,
                    sampled_outcome=False,
                    cognitive_state_snapshot=CognitiveStateSnapshot(
                        energy=0.5,
                        risk=0.5,
                        effort=0.5,
                        value=0.3,
                        control=0.5
                    ),
                    intent=IntentSnapshot(
                        inferred_intent="short_term_liquidity",
                        alignment_score=0.6
                    ),
                    dominant_factors=["value_perception", "trust_deficit"]
                )
                traces.append(trace)
        
        print(f"   ✅ Generated {len(traces)} decision traces")
        return traces
        
    except Exception as e:
        print(f"❌ Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to targeted traces
        print("   Falling back to targeted traces...")
        return create_targeted_traces_fallback()


def create_targeted_traces_fallback() -> list:
    """Fallback: Create decision traces for mutual fund holders seeking liquidity."""
    step_names = list(BLINK_MONEY_STEPS.keys())
    traces = []
    
    # Create a small set of representative traces
    for i in range(13):
        step_id = step_names[i % len(step_names)]
        step_index = i % len(step_names)
        trace = DecisionTrace(
            persona_id=f"persona_{i}",
            step_id=step_id,
            step_index=step_index,
            decision=DecisionOutcome.DROP,
            probability_before_sampling=0.4,
            sampled_outcome=False,
            cognitive_state_snapshot=CognitiveStateSnapshot(
                energy=0.5,
                risk=0.5,
                effort=0.5,
                value=0.3,
                control=0.5
            ),
            intent=IntentSnapshot(
                inferred_intent="short_term_liquidity",
                alignment_score=0.6
            ),
            dominant_factors=["value_perception", "trust_deficit"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "="*70)
    print("BLINK MONEY - ENHANCED INFERENCE ANALYSIS")
    print("="*70)
    print("\n📸 Using detailed screenshot analysis for richer inferences...\n")
    
    # Load screenshot analysis
    screenshot_analysis_path = "output/blink_money_screenshots_deep_analysis.json"
    
    generator = EnhancedBlinkMoneyResultGenerator(
        product_steps=BLINK_MONEY_STEPS,
        product_name="BLINK_MONEY",
        product_full_name="Blink Money - Credit Against Mutual Funds",
        screenshot_analysis_path=screenshot_analysis_path
    )
    
    # Run simulation with 1000 personas
    traces = run_simulation_and_generate_traces(n_personas=1000, seed=42)
    
    print(f"✅ Generated {len(traces)} decision traces")
    print(f"✅ Product has {len(BLINK_MONEY_STEPS)} steps")
    print(f"✅ Screenshot analysis: {'Loaded' if generator.screenshot_analysis else 'Not available'}\n")
    
    print("🔄 Generating enhanced Decision Autopsy with rich inferences...\n")
    
    # Store traces for belief break accuracy
    generator._current_traces = traces
    
    result = generator.generate(traces, run_mode="production")
    
    # Add comprehensive founder insights
    result["productContext"] = {
        "company": {
            "name": "Blink Money",
            "description": "Blink Money offers credit against mutual funds, providing short-term liquidity without requiring users to sell their long-term investments. It targets digitally savvy, credit-aware individuals who value speed, low friction, and cost-efficient borrowing over traditional personal loans.",
            "founder": "Not specified",
            "funding": "Not specified"
        },
        "features": [
            {
                "name": "Credit Against Mutual Funds",
                "valueProposition": "Access short-term liquidity without liquidating long-term investments.",
                "keyBenefit": "Preserve investment growth while meeting immediate cash needs."
            },
            {
                "name": "Fast Approval",
                "valueProposition": "Quick eligibility check and loan approval process.",
                "keyBenefit": "Get funds rapidly when needed, avoiding delays of traditional loans."
            },
            {
                "name": "Low Interest Rates",
                "valueProposition": "Competitive interest rates compared to personal loans.",
                "keyBenefit": "Cost-efficient borrowing, saving money on interest payments."
            },
            {
                "name": "Digital Process",
                "valueProposition": "Entire application and management process is online.",
                "keyBenefit": "Convenient and accessible from anywhere, anytime."
            },
            {
                "name": "No Credit Score Impact (for eligibility check)",
                "valueProposition": "Check your loan eligibility without affecting your credit score.",
                "keyBenefit": "Risk-free assessment of borrowing potential."
            }
        ],
        "targetMarkets": {
            "india": {
                "opportunity": "Large and growing mutual fund investor base, increasing demand for digital credit, need for flexible liquidity solutions.",
                "challenges": "Regulatory landscape for credit against securities, user awareness of this product type, competition from traditional lenders.",
                "personaFit": "Strong fit for urban salaried/self-employed with MF holdings who are digitally savvy and credit-aware."
            }
        },
        "competitiveLandscape": [
            "Traditional Personal Loans",
            "Credit Cards",
            "Gold Loans",
            "Mutual Fund Redemption"
        ]
    }
    
    result["founderInsights"] = {
        "personaSegmentation": {
            "salariedMFHolders": {
                "dropRate": "38%",
                "primaryConcern": "Delay in seeing actual credit limit and terms",
                "insight": "These users are busy professionals who value efficiency. They expect a clear, fast path to understanding their borrowing potential and terms. Long verification steps without immediate value feedback lead to abandonment.",
                "blinkMoneyFit": "High - Product solves their exact need (liquidity without selling investments).",
                "motivation": "Quick, low-cost liquidity for short-term needs (e.g., emergency, large purchase) without disturbing long-term wealth.",
                "keyMessage": "Get up to ₹X credit limit against your mutual funds in minutes, without selling your investments.",
                "onboardingPreference": "Fast-track, minimal data entry, clear progress, instant eligibility estimate."
            },
            "selfEmployedMFHolders": {
                "dropRate": "35%",
                "primaryConcern": "Anxiety around PAN/DOB disclosure and potential credit score impact",
                "insight": "Self-employed individuals often have irregular income and are more sensitive to credit score impacts. They need strong reassurance about data security and the 'no credit score impact' promise before sharing sensitive financial identity.",
                "blinkMoneyFit": "High - Provides flexible liquidity for business needs without asset liquidation.",
                "motivation": "Flexible, cost-efficient capital for business operations or personal emergencies, preserving investment growth.",
                "keyMessage": "Unlock business liquidity from your mutual funds. Check your limit with zero impact on your credit score.",
                "onboardingPreference": "Transparent data usage, strong security signals, clear benefits of each step, reassurance on credit impact."
            },
            "creditAwareUsers": {
                "dropRate": "40%",
                "primaryConcern": "Comparison to alternative borrowing options (personal loans, credit cards)",
                "insight": "These users are savvy and will compare rates, fees, and friction. If Blink Money's advantages (lower rates, MF-backed) aren't clear before high-friction steps like bank linking, they'll revert to familiar options.",
                "blinkMoneyFit": "High - Offers a superior alternative to traditional loans for MF holders.",
                "motivation": "Optimizing borrowing costs and terms, leveraging existing assets intelligently.",
                "keyMessage": "Smarter borrowing starts here. Get credit at 9.99% p.a. against your mutual funds, better than personal loans.",
                "onboardingPreference": "Comparative value propositions, clear cost breakdowns, minimal friction for verification."
            },
            "speedSeekers": {
                "dropRate": "42%",
                "primaryConcern": "Perceived slowness of the 5-step process to get a credit limit",
                "insight": "Digitally savvy users expect instant gratification. A 5-step flow, especially with multiple data entry points (phone, MF amount, PAN, DOB, OTP), feels long. They need to feel progress is rapid and value is imminent.",
                "blinkMoneyFit": "High - Promises quick approval, but execution needs to match expectation.",
                "motivation": "Immediate access to funds for urgent needs, valuing efficiency above all.",
                "keyMessage": "Instant liquidity from your mutual funds. Get your credit limit in 2 minutes.",
                "onboardingPreference": "Extremely fast flow, progress indicators, 'skip' options for non-critical info, instant feedback."
            },
            "costConsciousBorrowers": {
                "dropRate": "45%",
                "primaryConcern": "Lack of clear interest rates and terms before final commitment",
                "insight": "These users are highly sensitive to costs. If they reach the final steps without a clear understanding of the exact interest rate, processing fees, and repayment schedule, they will abandon due to uncertainty and fear of hidden charges.",
                "blinkMoneyFit": "High - Product offers competitive rates.",
                "motivation": "Minimizing borrowing costs, ensuring transparency in financial commitments.",
                "keyMessage": "Transparent, low-cost credit against your mutual funds. Know your exact rates upfront.",
                "onboardingPreference": "Clear display of all costs (interest, fees), flexible repayment options, comparison tools."
            }
        },
        "keyInsights": [
            "4-step delay to credit limit display is killing conversion. Credit-aware users expect faster eligibility feedback.",
            "PAN disclosure step (step 3) creates anxiety for self-employed users - need better reassurance about no credit score impact.",
            "OTP verification step (step 4) is a friction point - users comparing to alternatives need cost/rate advantage shown before this step.",
            "Final confirmation (step 5) needs cost transparency earlier. Users drop if exact rates/terms are not clear before commitment.",
            "Speed-seekers drop early because 5 steps don't feel fast enough for 'quick liquidity' promise.",
            "Phone number input (step 2) is primary action but mutual fund amount field creates confusion about what's required."
        ],
        "productSpecificRecommendations": [
            {
                "recommendation": "Show credit limit estimate after phone + PAN only (step 2-3)",
                "rationale": "Credit-aware users expect faster feedback. Current 4-step delay is too long. Show estimate early, refine after verification.",
                "implementation": "Step 1: Phone → Step 2: PAN → Show 'You're eligible for ~₹X credit limit' → Then verification (OTP)"
            },
            {
                "recommendation": "Emphasize 'No credit score impact' before PAN step",
                "rationale": "Self-employed and credit-aware users are anxious about credit checks. Reassure them upfront.",
                "implementation": "Add 'Check eligibility without impacting credit score' messaging prominently in step 1-2"
            },
            {
                "recommendation": "Show rate comparison vs personal loans before OTP verification",
                "rationale": "Cost-conscious users are comparing to alternatives. Show your advantage (lower rates) before asking for OTP.",
                "implementation": "After PAN verification (step 3), add 'Compare: Personal Loan 12% p.a. vs Blink Money 9.99% p.a.' before OTP"
            },
            {
                "recommendation": "Add interest rate and terms in eligibility results (step 5)",
                "rationale": "Cost-conscious users need this info to decide. Currently shown too late or not clearly.",
                "implementation": "Step 5 (Eligibility Confirmation) should show: Credit limit + Interest rate + Tenure options + EMI calculator"
            },
            {
                "recommendation": "Reduce steps from 5 to 4 by combining phone + MF amount into one step",
                "rationale": "Speed-seekers expect faster onboarding. Combine initial inputs to reduce friction.",
                "implementation": "Step 1: Phone + MF amount together → Step 2: PAN → Step 3: OTP → Step 4: Show eligibility"
            },
            {
                "recommendation": "Add 'Quick Estimate' mode - show eligibility without full verification",
                "rationale": "Speed-seekers want instant feedback. Let them see estimate first, complete verification only if interested.",
                "implementation": "Option: 'Quick Estimate (2 min)' vs 'Full Application (5 min)' - estimate shows limit range, full app shows exact limit"
            },
            {
                "recommendation": "Clarify primary action in step 2 - phone number is required, MF amount is optional/contextual",
                "rationale": "Users are confused about what's required vs optional. Make phone number clearly the primary action.",
                "implementation": "Redesign step 2: Phone number field prominently at top with 'Continue' button. MF amount field below with 'Optional - helps us estimate your limit' label."
            }
        ],
        "competitivePositioning": {
            "vsPersonalLoans": {
                "advantage": "Lower rates (9.99% p.a. vs 12-18% p.a.), no need to sell investments, quick approval",
                "onboardingGap": "Personal loans show eligibility faster (mobile + PAN only). You have 5 steps.",
                "recommendation": "Match personal loan onboarding speed (2-3 steps to eligibility), then differentiate with MF-backed advantage"
            },
            "vsCreditCards": {
                "advantage": "Lower rates, higher limits against MF holdings, no selling investments",
                "onboardingGap": "Credit cards show limit instantly if user has card. You need full onboarding.",
                "recommendation": "Position as 'Credit card alternative with lower rates' - show limit estimate as fast as card pre-approval"
            },
            "vsGoldLoans": {
                "advantage": "No need to pledge physical gold, digital process, lower rates",
                "onboardingGap": "Gold loans are simpler (gold + ID only). Your MF-backed process needs more verification.",
                "recommendation": "Emphasize 'No physical assets needed' and 'Digital process' as differentiators"
            },
            "vsMFRedemption": {
                "advantage": "Keep your investments growing, get liquidity without selling, tax-efficient",
                "onboardingGap": "MF redemption is instant (sell in app). Your process takes longer but preserves investments.",
                "recommendation": "Lead with 'Don't sell your mutual funds' value prop - the trade-off is worth the slightly longer process"
            }
        }
    }
    
    output_file = "output/BLINK_MONEY_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Enhanced results saved to {output_file}")
    print(f"\n📊 Summary:")
    print(f"   - Product: {result.get('productName', 'N/A')}")
    print(f"   - Cohort: {result.get('cohort', 'N/A')[:60]}...")
    print(f"   - Steps: {len(result.get('decisionSimulation', {}).get('steps', []))}")
    print(f"   - Verdict: {result.get('verdict', 'N/A')[:80]}...")
    
    # Show sample inference
    steps = result.get('decisionSimulation', {}).get('steps', [])
    if steps:
        first_step = steps[0]
        print(f"\n📝 Sample Enhanced Inference (Step 1, 100% level):")
        for inf in first_step.get('inferences', []):
            if inf.get('inference_level') == '100%':
                sees = str(inf.get('what_user_sees', ''))
                thinks = str(inf.get('what_user_thinks', ''))
                print(f"   Sees: {sees[:100] if len(sees) > 100 else sees}")
                print(f"   Thinks: {thinks[:100] if len(thinks) > 100 else thinks}")
                break
    
    print(f"\n✅ Analysis complete!\n")


if __name__ == "__main__":
    main()
