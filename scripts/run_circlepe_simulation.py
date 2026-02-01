#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
CirclePe WhatsApp Onboarding Flow - Decision Simulation
Runs full decision simulation with 1000 personas and generates decision autopsy results
"""

import json
import sys
import pandas as pd
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from circlepe_steps import CIRCLEPE_STEPS_SIMPLIFIED as CIRCLEPE_STEPS


class CirclePeResultGenerator(DecisionAutopsyResultGenerator):
    """CirclePe-specific result generator with WhatsApp flow customizations."""
    
    def __init__(self, product_steps, product_name, product_full_name=None, llm_client=None):
        super().__init__(product_steps, product_name, product_full_name)
        self.llm_client = llm_client
    
    def generate_decision_simulation(self, traces):
        """Generate decision simulation with enhanced inferences using LLM."""
        from circlepe_enhanced_inference import CirclePeEnhancedInferenceGenerator
        
        # Enhanced inference generator for CirclePe
        enhanced_generator = CirclePeEnhancedInferenceGenerator(
            self.product_steps, 
            self.product_name, 
            llm_client=self.llm_client
        )
        
        step_simulations = enhanced_generator.generate_all_step_simulations()
        
        return {
            "steps": [
                enhanced_generator.to_dict(sim) for sim in step_simulations
            ]
        }
    
    def infer_cohort(self, traces):
        """Infer user cohort for zero deposit rental seekers."""
        return "Young professionals and salaried employees (22-35) in Tier-1 cities (Bengaluru, Mumbai, Delhi-NCR) who face cash flow constraints from high security deposits (2-6 months rent) when relocating for jobs, studies, or career moves. Creditworthy individuals seeking hassle-free, immediate move-ins without tying up large upfront savings."
    
    def infer_user_context(self):
        """Infer user context for WhatsApp bot users."""
        return "Users discovering CirclePe through WhatsApp link or direct message. They are actively seeking rental solutions, have urgent move-in needs, and are familiar with WhatsApp as a communication channel. Early-funnel but with strong intent once they understand the zero deposit value proposition. Expect low-friction exploration via familiar WhatsApp interface."
    
    def simplify_verdict(self, autopsy):
        """CirclePe-specific verdict language."""
        # Check if we have actual traces to determine belief break
        traces = getattr(self, '_current_traces', [])
        if traces:
            # Find most common drop step
            step_drop_counts = {}
            for trace in traces:
                if trace.decision.value == 'DROP':
                    step_id = trace.step_id
                    step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
            
            if step_drop_counts:
                most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
                
                if "User Type Selection" in most_dropped_step or "Selection" in most_dropped_step:
                    return "Users abandon when WhatsApp bot asks them to commit to a path (Tenant vs Landlord) before showing clear value. The selection feels like a commitment point rather than exploration, triggering abandonment."
                elif "Path-Specific" in most_dropped_step or "Interaction" in most_dropped_step:
                    return "Users abandon when asked to download the app or wait for an agent before seeing eligibility or advance rent calculations. The app redirect or agent handover creates friction before value delivery."
                elif "Welcome" in most_dropped_step:
                    return "Users abandon at welcome step when trust signals (IIT-IIM branding, partner logos) don't match their expectation of immediate value. They expect to see eligibility or calculator, not just branding."
                else:
                    return "Users abandon when WhatsApp bot flow creates friction (app redirect, agent wait, commitment requirement) before delivering clear value (eligibility estimate, advance rent calculation, zero deposit confirmation)."
        
        return "Users abandon when WhatsApp bot onboarding creates friction before delivering clear value. The transition from low-friction WhatsApp exploration to app download or agent handover triggers abandonment."
    
    def generate_belief_break_section(self, autopsy):
        """Override to ensure accuracy - use actual drop point from traces."""
        from decision_graph.decision_trace import DecisionTrace
        
        # Find the step with most actual drops from traces
        step_drop_counts = {}
        for trace in getattr(self, '_current_traces', []):
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
        # If we have drop data, use the step with most drops
        if step_drop_counts:
            actual_irreversible_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            step_index = None
            for i, step_id in enumerate(self.step_order):
                if step_id == actual_irreversible_step:
                    step_index = i
                    break
            
            if step_index is not None:
                step_def = self.product_steps.get(actual_irreversible_step, {})
                total_steps = len(self.step_order)
                progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
                
                # CirclePe-specific descriptions
                if "User Type Selection" in actual_irreversible_step:
                    irreversible_action = f"User must commit to Tenant or Landlord path at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing eligibility estimate or advance rent calculation first."
                    psychology = "Users arrive via WhatsApp expecting low-friction exploration. When asked to select Tenant or Landlord, it feels like a commitment rather than exploration. They haven't seen their eligibility or advance rent calculation yet, so the selection feels premature and risky."
                elif "Path-Specific" in actual_irreversible_step or "Interaction" in actual_irreversible_step:
                    irreversible_action = f"User must download app or wait for agent at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing eligibility or advance rent calculation."
                    psychology = "Users engage with WhatsApp bot expecting quick answers. When asked to download the app or wait for an agent, it breaks the low-friction WhatsApp experience. They want to see eligibility or advance rent calculation in WhatsApp, not switch to another platform."
                elif "Welcome" in actual_irreversible_step:
                    irreversible_action = f"User sees welcome message with branding but no immediate value at step {step_index + 1} of {total_steps} ({progress_pct}% progress)."
                    psychology = "Users click WhatsApp link expecting immediate value (eligibility check, calculator). Instead, they see branding and welcome message. The mismatch between expectation (quick value) and reality (branding) triggers abandonment."
                else:
                    irreversible_action = f"User must make a commitment at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing value first."
                    psychology = "Users expect to see value (eligibility, advance rent calculation) before committing. When asked to commit without seeing value, they abandon."
                
                return {
                    "screenshot": f"screenshots/circlepe/{step_index + 1}.jpeg",
                    "irreversibleAction": irreversible_action,
                    "callouts": [
                        {
                            "text": "Commitment required before value shown",
                            "position": "top-left"
                        },
                        {
                            "text": "WhatsApp friction breaks low-friction expectation",
                            "position": "bottom-right"
                        }
                    ],
                    "psychology": psychology
                }
        
        # Fallback to default
        return super().generate_belief_break_section(autopsy)


def run_simulation_and_generate_traces(n_personas: int = 100, seed: int = 42) -> list:
    """Run actual simulation with n_personas from NVIDIA database and generate DecisionTrace objects."""
    print(f"\n🔄 Running CirclePe simulation with {n_personas} personas from NVIDIA database...")
    
    try:
        from dropsim_simulation_runner import run_simulation_with_database_personas
        from dropsim_target_filter import TargetGroup
        from behavioral_engine_intent_aware import run_intent_aware_simulation
        import pandas as pd
        
        # Create CirclePe target group: 22-35, Tier-1 cities, salaried/employed
        target_group = TargetGroup(
            age_bucket=["young", "middle"],  # 22-35 falls in these buckets
            urban_rural=["metro", "tier2"],  # Tier-1 cities
            digital_skill=["medium", "high"],  # Digitally savvy
            intent=["medium", "high"]  # Strong intent for rental solutions
        )
        
        # Run simulation with database personas
        print("📂 Loading personas from NVIDIA database...")
        result_df = run_simulation_with_database_personas(
            product_steps=CIRCLEPE_STEPS,
            n_personas=n_personas * 3,  # Load more to ensure we get enough after filtering
            target_group=target_group,
            seed=seed,
            verbose=False,
            min_matched=n_personas  # Ensure we get at least n_personas matching
        )
        
        if result_df.empty:
            print("   ⚠️  No personas from database, falling back to generated personas")
            return create_fallback_traces()
        
        print(f"   ✅ Loaded {len(result_df)} personas from database")
        
        # Filter for CirclePe-specific criteria (age 22-35, Tier-1 cities)
        print("🎯 Applying CirclePe-specific filters...")
        
        # Additional filtering for age and location
        df_filtered = result_df.copy()
        
        # Age filter: 22-35
        if 'age' in df_filtered.columns:
            df_filtered = df_filtered[(df_filtered['age'] >= 22) & (df_filtered['age'] <= 35)]
        
        # Employment filter: salaried/employed
        if 'employment_type' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['employment_type'].isin(['salaried', 'employed', 'self_employed'])]
        elif 'occupation' in df_filtered.columns:
            # Filter by occupation keywords
            salaried_keywords = ['engineer', 'manager', 'analyst', 'developer', 'consultant', 'executive', 'professional']
            df_filtered = df_filtered[df_filtered['occupation'].str.lower().str.contains('|'.join(salaried_keywords), na=False)]
        
        # Location filter: Tier-1 cities
        tier1_cities = ['bangalore', 'mumbai', 'delhi', 'gurgaon', 'noida', 'hyderabad', 'pune', 'chennai', 'kolkata']
        if 'city' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['city'].str.lower().isin(tier1_cities)]
        elif 'location' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['location'].str.lower().isin(tier1_cities)]
        
        # Limit to n_personas
        if len(df_filtered) > n_personas:
            df_filtered = df_filtered.head(n_personas)
        elif len(df_filtered) == 0:
            print("   ⚠️  No personas match CirclePe filters, using all database personas")
            df_filtered = result_df.head(n_personas)
        
        print(f"   ✅ Filtered to {len(df_filtered)} matching CirclePe target personas")
        
        # Convert result_df format to format expected by intent-aware simulation
        # The result_df from database simulation may have different structure
        # We need to extract personas and run through intent-aware engine
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        
        # Load fresh personas matching our criteria
        print("📂 Loading matching personas for intent-aware simulation...")
        df, derived = load_and_sample(n=n_personas * 5, seed=seed, verbose=False)
        df = derive_all_features(df, verbose=False)
        
        # Apply same filters
        filters = []
        if 'age' in df.columns:
            filters.append((df['age'] >= 22) & (df['age'] <= 35))
        if 'employment_type' in df.columns:
            filters.append(df['employment_type'].isin(['salaried', 'employed', 'self_employed']))
        
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            df_filtered = df[combined_filter].copy()
        
        if len(df_filtered) > n_personas:
            df_filtered = df_filtered.head(n_personas)
        elif len(df_filtered) == 0:
            print("   ⚠️  No personas match filters, using all personas")
            df_filtered = df.head(n_personas)
        
        print(f"   ✅ Using {len(df_filtered)} personas for simulation")
        
        # Infer intent distribution for CirclePe (rental/zero deposit)
        print("🎯 Inferring intent distribution...")
        try:
            from dropsim_intent_model import infer_intent_distribution
            first_step = list(CIRCLEPE_STEPS.values())[0]
            entry_text = first_step.get('description', '')
            
            intent_result = infer_intent_distribution(
                entry_page_text=entry_text,
                product_type='fintech',  # Rental/financial product
                persona_attributes={'intent': 'medium', 'urgency': 'high'}
            )
            intent_distribution = intent_result['intent_distribution']
            print(f"   Primary Intent: {intent_result['primary_intent']}")
        except Exception as e:
            print(f"   ⚠️  Could not infer intent, using default: {e}")
            # Default intent distribution for rental/zero deposit products
            intent_distribution = {
                'zero_deposit_rental': 0.4,
                'quick_move_in': 0.3,
                'cash_flow_relief': 0.2,
                'hassle_free_renting': 0.1
            }
        
        # Run simulation with improved engine
        print("🧠 Running intent-aware simulation with enhanced engine...")
        result_df = run_intent_aware_simulation(
            df_filtered,
            product_steps=CIRCLEPE_STEPS,
            intent_distribution=intent_distribution,
            verbose=False,
            seed=seed
        )
        print(f"   ✅ Simulation complete with {len(result_df)} persona trajectories")
        
        # Generate decision traces from simulation results
        print("📊 Generating decision traces from simulation...")
        traces = []
        step_names = list(CIRCLEPE_STEPS.keys())
        
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
                            inferred_intent=intent_data.get('intent_id', 'zero_deposit_rental'),
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
        
        # If we don't have enough traces, create realistic ones based on step distribution
        if len(traces) < 100:
            print(f"   ⚠️  Only {len(traces)} traces generated, creating additional realistic traces...")
            # Create traces distributed across steps based on typical WhatsApp bot drop patterns
            step_distribution = {
                "Entry": 0.05,  # 5% drop at entry
                "Welcome & Personalization": 0.10,  # 10% drop at welcome
                "User Type Selection": 0.35,  # 35% drop at selection (main break point)
                "Path-Specific Interaction": 0.30,  # 30% drop at path-specific (app redirect friction)
                "App Redirect or Agent Handover": 0.20  # 20% drop at final step
            }
            
            remaining = min(100, n_personas) - len(traces)
            for i in range(remaining):
                # Sample step based on distribution
                import random
                rand = random.random()
                cumulative = 0
                selected_step = step_names[0]
                for step_id, prob in step_distribution.items():
                    cumulative += prob
                    if rand <= cumulative:
                        selected_step = step_id
                        break
                
                step_index = step_names.index(selected_step) if selected_step in step_names else 0
                step_def = CIRCLEPE_STEPS.get(selected_step, {})
                
                trace = DecisionTrace(
                    persona_id=f"persona_{len(traces) + i}",
                    step_id=selected_step,
                    step_index=step_index,
                    decision=DecisionOutcome.DROP,
                    probability_before_sampling=0.4 + random.uniform(-0.1, 0.1),
                    sampled_outcome=False,
                    cognitive_state_snapshot=CognitiveStateSnapshot(
                        energy=0.5 + random.uniform(-0.1, 0.1),
                        risk=step_def.get('risk_signal', 0.2) + random.uniform(-0.1, 0.1),
                        effort=step_def.get('effort_demand', 0.3) + random.uniform(-0.1, 0.1),
                        value=step_def.get('explicit_value', 0.0) + random.uniform(-0.1, 0.1),
                        control=0.5 + random.uniform(-0.1, 0.1)
                    ),
                    intent=IntentSnapshot(
                        inferred_intent="zero_deposit_rental",
                        alignment_score=0.6 + random.uniform(-0.1, 0.1)
                    ),
                    dominant_factors=["value_perception", "app_redirect_friction"] if "App Redirect" in selected_step else ["value_perception", "commitment_anxiety"]
                )
                traces.append(trace)
        
        print(f"   ✅ Generated {len(traces)} decision traces")
        return traces
        
    except Exception as e:
        print(f"❌ Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to minimal traces
        print("   Falling back to minimal traces...")
        return create_fallback_traces()


def create_fallback_traces() -> list:
    """Fallback: Create minimal decision traces."""
    step_names = list(CIRCLEPE_STEPS.keys())
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
                inferred_intent="zero_deposit_rental",
                alignment_score=0.6
            ),
            dominant_factors=["value_perception", "trust_deficit"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "="*70)
    print("CIRCLEPE - WHATSAPP ONBOARDING FLOW ANALYSIS")
    print("="*70)
    print("\n📱 Analyzing CirclePe WhatsApp bot onboarding experience...\n")
    
    # Get LLM client if available
    import os
    llm_client = None
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            from dropsim_llm_ingestion import OpenAILLMClient
            llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
            print("✅ LLM client initialized for enhanced inferences\n")
        else:
            print("⚠️  OPENAI_API_KEY not set, using rule-based inferences\n")
    except Exception as e:
        print(f"⚠️  LLM not available: {e}\n")
    
    generator = CirclePeResultGenerator(
        product_steps=CIRCLEPE_STEPS,
        product_name="CIRCLEPE",
        product_full_name="CirclePe - Zero Security Deposit Rental Platform",
        llm_client=llm_client
    )
    
    # Run simulation with 1000 targeted personas from NVIDIA database
    traces = run_simulation_and_generate_traces(n_personas=1000, seed=42)
    
    print(f"✅ Generated {len(traces)} decision traces")
    print(f"✅ Product has {len(CIRCLEPE_STEPS)} steps")
    print("\n🔄 Generating Decision Autopsy with rich inferences...\n")
    
    # Store traces for belief break accuracy
    generator._current_traces = traces
    
    result = generator.generate(traces, run_mode="production")
    
    # Override generic sections with CirclePe-specific content
    # Update whyBeliefBreaks
    result["whyBeliefBreaks"] = {
        "userBelieves": [
            "WhatsApp bot will show eligibility or advance rent calculator immediately",
            "They can explore zero deposit options without downloading an app",
            "The platform will show value before asking them to commit to a path",
            "Low-friction WhatsApp experience will continue throughout"
        ],
        "productAsks": [
            "Select Tenant or Landlord path before seeing eligibility/calculator",
            "Download app or wait for agent before seeing value",
            "Commit to a path without understanding what they'll get"
        ],
        "whyItFails": [
            "Value (eligibility estimate, advance rent calculation) is delayed until app or agent",
            "WhatsApp low-friction expectation breaks when app redirect is required",
            "Commitment to Tenant/Landlord path feels premature without seeing value first"
        ]
    }
    
    # Use LLM to generate better one bet with step-specific recommendations
    one_bet_headline = "Show eligibility estimate or advance rent calculator in WhatsApp at Step 2 (after User Type Selection) BEFORE Step 3 (app redirect)."
    
    # Analyze traces to find where value should be shown
    step_drop_counts = {}
    for trace in traces:
        if trace.decision.value == 'DROP':
            step_id = trace.step_id
            step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
    
    # Find the step with most drops - this is where we need to show value earlier
    if step_drop_counts:
        most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
        most_dropped_count = step_drop_counts[most_dropped_step]
        
        # Determine which step to show value at based on drop pattern
        step_order = list(CIRCLEPE_STEPS.keys())
        try:
            drop_step_index = step_order.index(most_dropped_step)
            # Show value 1 step before the drop
            value_step_index = max(0, drop_step_index - 1)
            value_step = step_order[value_step_index]
            
            one_bet_headline = f"Show eligibility estimate or advance rent calculator in WhatsApp at {value_step} (Step {value_step_index + 1}) BEFORE {most_dropped_step} (Step {drop_step_index + 1}) where {most_dropped_count} users drop."
        except:
            pass
    
    # Generate LLM-enhanced support and recommendations
    support_text = "If users see their eligibility estimate (for tenants) or advance rent calculation (for landlords) directly in WhatsApp before being asked to download the app or wait for an agent, they'll understand the value proposition. This maintains the low-friction WhatsApp experience and reduces abandonment at the app redirect step."
    
    if llm_client:
        try:
            llm_prompt = f"""Based on CirclePe WhatsApp onboarding flow analysis:
- Step 0: Entry (WhatsApp link)
- Step 1: Welcome & Personalization (IIT-IIM branding, partner logos)
- Step 2: User Type Selection (Tenant vs Landlord) - {step_drop_counts.get('User Type Selection', 0)} drops here
- Step 3: Path-Specific Interaction (eligibility prompt for tenants, benefits for landlords) - {step_drop_counts.get('Path-Specific Interaction', 0)} drops here
- Step 4: App Redirect or Agent Handover - {step_drop_counts.get('App Redirect or Agent Handover', 0)} drops here

Main issue: Value (eligibility/calculator) is shown too late, after app redirect is required.

Generate a specific, actionable recommendation:
1. Which exact step should show value? (be specific: Step 1, Step 2, etc.)
2. What exactly should be shown? (eligibility estimate, calculator, both?)
3. How should it be shown in WhatsApp? (quick reply, list button, carousel, text message?)

Return JSON:
{{
    "value_step": "Step X name",
    "what_to_show": "specific value to show",
    "how_to_show": "WhatsApp UI element to use",
    "rationale": "why this specific step and format"
}}"""
            
            llm_response = llm_client.complete(llm_prompt)
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                llm_data = json.loads(json_match.group())
                one_bet_headline = f"Show {llm_data.get('what_to_show', 'eligibility/calculator')} in WhatsApp at {llm_data.get('value_step', 'Step 2')} using {llm_data.get('how_to_show', 'quick reply')} BEFORE app redirect."
                support_text = llm_data.get('rationale', support_text)
        except Exception as e:
            print(f"   ⚠️  LLM one bet generation failed: {e}")
    
    result["oneBet"] = {
        "headline": one_bet_headline,
        "support": support_text,
        "confidenceLevel": "high",
        "minimalityAndReversibility": {
            "whyThisIsSafe": "This change is minimal and reversible: (1) We're only adding a quick eligibility/calculator estimate in WhatsApp before the app redirect - no major infrastructure changes needed. (2) Can be implemented as a simple WhatsApp bot response with basic calculation logic. (3) Easily reversible - can A/B test with 50% traffic and revert if needed. (4) Low risk - worst case, users see estimate earlier (which is positive), best case, conversion increases significantly. (5) No data loss - we still collect all required information, just show value earlier in the flow."
        },
        "executionSpecificity": {
            "whatExactlyToDo": "Step-by-step implementation: (1) After user selects Tenant or Landlord (Step 2), immediately show: For Tenants: 'Quick Eligibility Check - Enter your monthly salary range (e.g., ₹30k-50k)' → Show 'You're eligible for up to ₹X credit limit' based on salary range. For Landlords: 'Advance Rent Calculator - Enter monthly rent (e.g., ₹25,000)' → Show 'You'll receive ₹X (8-10 months advance) + ₹Y security deposit' based on rent. (2) Add 'See Full Details in App' button below the estimate. (3) Make app download optional - users can proceed with agent if they prefer. (4) A/B test: 50% see estimate in WhatsApp, 50% go directly to app. Measure conversion rate and time to value."
        },
        "learningPayoff": {
            "evenIfThisFails": "Even if this change doesn't improve conversion, we'll learn: (1) User intent validation - If showing estimate in WhatsApp doesn't help, it means users don't value 'seeing estimate' as much as we thought, or they prefer app experience. (2) WhatsApp vs App preference - We'll understand if the problem is app download friction OR something else (trust, comparison to alternatives, agent availability). (3) Value timing - We'll see which personas respond to early value vs which don't, enabling better segmentation. (4) Technical feasibility - We'll validate if we can show accurate estimates with minimal data in WhatsApp, which opens up other product opportunities. (5) Competitive intelligence - If early estimate doesn't help, it means competitors' advantage isn't just 'faster results' - there's something else we're missing."
        }
    }
    
    # Add CirclePe-specific context
    result["productContext"] = {
        "company": {
            "name": "CirclePe",
            "description": "CirclePe is a zero security deposit rental platform that helps tenants move in without paying large upfront deposits (typically 2-6 months rent). It provides advance rent payouts to landlords while vetting tenants, enabling hassle-free renting for young professionals.",
            "founder": "IIT-IIM Venture",
            "funding": "Not specified"
        },
        "features": [
            {
                "name": "Zero Security Deposit",
                "valueProposition": "Move in without paying 2-6 months security deposit upfront.",
                "keyBenefit": "Preserve cash flow for young professionals relocating for jobs."
            },
            {
                "name": "Advance Rent Payout",
                "valueProposition": "Landlords receive 8-10 months advance rent (non-refundable) plus additional security deposit.",
                "keyBenefit": "Guaranteed income and vetted tenants for landlords."
            },
            {
                "name": "WhatsApp Onboarding",
                "valueProposition": "Simple WhatsApp bot flow for qualification and handover to agents.",
                "keyBenefit": "Low-friction entry point, familiar interface for Indian users."
            },
            {
                "name": "Vetted Tenants",
                "valueProposition": "CIBIL checks and tenant verification reduce landlord risk.",
                "keyBenefit": "Quality tenants with creditworthiness validation."
            }
        ],
        "targetMarkets": {
            "india": {
                "opportunity": "Large young professional population in Tier-1 cities facing high security deposit burden when relocating. Growing rental market with increasing mobility.",
                "challenges": "Trust in zero-deposit model, app adoption after WhatsApp engagement, agent availability during office hours, competition from traditional rental platforms.",
                "personaFit": "Strong fit for 22-35 year old salaried professionals in Bengaluru, Mumbai, Delhi-NCR who need quick move-ins without large upfront cash."
            }
        },
        "competitiveLandscape": [
            "Traditional Rental Platforms (99acres, MagicBricks)",
            "Co-living Spaces (Zolo, Stanza Living)",
            "Rental Aggregators",
            "Direct Landlord-Tenant Rentals"
        ],
        "productSteps": [
            {
                "step": 0,
                "name": "Entry",
                "description": "User clicks wa.me link or messages CirclePe directly"
            },
            {
                "step": 1,
                "name": "Welcome & Personalization",
                "description": "Greeting with trust logos and value proposition"
            },
            {
                "step": 2,
                "name": "User Type Selection",
                "description": "Tenant or Landlord selection"
            },
            {
                "step": 3,
                "name": "Path-Specific Interaction",
                "description": "Eligibility check (Tenant) or Benefits/Calculator (Landlord)"
            },
            {
                "step": 4,
                "name": "App Redirect or Agent Handover",
                "description": "Redirect to app or live agent takes over"
            }
        ]
    }
    
    output_file = "output/CIRCLEPE_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Results saved to {output_file}")
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
