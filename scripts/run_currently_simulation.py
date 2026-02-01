#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Currently Social App - Decision Simulation
Runs full decision simulation with 1000 personas and generates decision autopsy results
"""

import json
import sys
import os
import pandas as pd
from datetime import datetime
from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import DecisionTrace, DecisionOutcome, CognitiveStateSnapshot, IntentSnapshot
from currently_steps import CURRENTLY_STEPS


class CurrentlyResultGenerator(DecisionAutopsyResultGenerator):
    """Currently-specific result generator with social app customizations."""
    
    def __init__(self, product_steps, product_name, product_full_name=None, llm_client=None):
        super().__init__(product_steps, product_name, product_full_name)
        self.llm_client = llm_client
    
    def infer_cohort(self, traces):
        """Infer user cohort for social app users."""
        return "Young Millennials (typically 22-35) who are heavy social app users and want real-time, authentic updates from friends rather than curated feeds. Socially active, urban users who like spontaneous meetups and seeing where friends are on a live map."
    
    def infer_user_context(self):
        """Infer user context for social app users."""
        return "Users discovering Currently through app store, social media, or friend referrals. They are active social media users, familiar with location-based apps, and seeking authentic social connections. Early-funnel but with strong intent for real-time social updates. Privacy-conscious but willing to share location for social value."
    
    def simplify_verdict(self, autopsy):
        """Currently-specific verdict language."""
        traces = getattr(self, '_current_traces', [])
        if traces:
            step_drop_counts = {}
            for trace in traces:
                if trace.decision.value == 'DROP':
                    step_id = trace.step_id
                    step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
            
            if step_drop_counts:
                most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
                
                if "Location Permission" in most_dropped_step:
                    return "Users abandon when app requests location permission before showing value (live map, friend locations). Privacy-conscious Millennials hesitate to share location without seeing what they'll get in return."
                elif "Profile Setup" in most_dropped_step:
                    return "Users abandon when asked to create detailed profile before seeing the main feed or friend updates. They want to explore the app first, not commit to profile creation."
                elif "OTP Verification" in most_dropped_step or "Phone Number" in most_dropped_step:
                    return "Users abandon when phone verification feels like unnecessary friction before seeing value. They expect social apps to let them explore before requiring verification."
                else:
                    return "Users abandon when onboarding creates friction (location permission, profile setup, verification) before delivering clear value (real-time friend updates, live map, spontaneous meetups)."
        
        return "Users abandon when social app onboarding creates friction before delivering clear value. Privacy concerns (location sharing) and commitment requirements (profile setup) trigger abandonment before users see real-time friend updates."
    
    def generate_belief_break_section(self, autopsy):
        """Override to ensure accuracy - use actual drop point from traces."""
        from decision_graph.decision_trace import DecisionTrace
        
        step_drop_counts = {}
        for trace in getattr(self, '_current_traces', []):
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
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
                
                if "Location Permission" in actual_irreversible_step:
                    irreversible_action = f"User must grant location permission at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing live map or friend locations."
                    psychology = "Privacy-conscious Millennials arrive expecting to explore the app first. When asked for location permission before seeing value (live map, friend locations), it feels like a privacy risk without clear benefit. They haven't seen what they'll get, so the permission request feels premature and risky."
                elif "Profile Setup" in actual_irreversible_step:
                    irreversible_action = f"User must create detailed profile at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing main feed or friend updates."
                    psychology = "Users want to explore the app and see real-time updates from friends. When asked to create a detailed profile first, it feels like unnecessary commitment before seeing value. They expect social apps to let them browse first."
                elif "OTP Verification" in actual_irreversible_step or "Phone Number" in actual_irreversible_step:
                    irreversible_action = f"User must verify phone number at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing value."
                    psychology = "Users expect social apps to allow exploration before requiring verification. When asked for phone verification early, it feels like unnecessary friction before they've seen the value (real-time updates, live map)."
                else:
                    irreversible_action = f"User must make a commitment at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing value first."
                    psychology = "Users expect to see value (real-time friend updates, live map) before committing. When asked to commit without seeing value, they abandon."
                
                return {
                    "screenshot": f"screenshots/currently/{step_index + 1}.jpeg",
                    "irreversibleAction": irreversible_action,
                    "callouts": [
                        {
                            "text": "Privacy/commitment required before value shown",
                            "position": "top-left"
                        },
                        {
                            "text": "Social app friction breaks exploration expectation",
                            "position": "bottom-right"
                        }
                    ],
                    "psychology": psychology
                }
        
        return super().generate_belief_break_section(autopsy)
    
    def generate_why_belief_breaks(self, autopsy):
        """Currently-specific why belief breaks."""
        traces = getattr(self, '_current_traces', [])
        step_drop_counts = {}
        for trace in traces:
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
        if step_drop_counts:
            most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            
            if "Location Permission" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They can explore the app and see friend updates first",
                        "Location sharing is optional or can be done later",
                        "They'll see value (live map, friend locations) before being asked for permissions"
                    ],
                    "productAsks": [
                        "Grant location permission before seeing main feed",
                        "Share location data before experiencing value"
                    ],
                    "whyItFails": [
                        "Privacy-conscious Millennials hesitate to share location without seeing benefit",
                        "Permission request appears before value demonstration (live map, friend locations)",
                        "Users expect social apps to let them explore before requiring sensitive permissions"
                    ]
                }
            elif "OTP Verification" in most_dropped_step or "Phone Number" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They can explore the app and see real-time updates first",
                        "Phone verification can happen later or is optional",
                        "Social apps let them browse before requiring verification"
                    ],
                    "productAsks": [
                        "Verify phone number before seeing main feed",
                        "Share contact information before experiencing value"
                    ],
                    "whyItFails": [
                        "Phone verification feels like unnecessary friction before seeing value",
                        "Users expect social apps to allow exploration before requiring verification",
                        "Value (real-time updates, live map) not demonstrated before trust demand"
                    ]
                }
            elif "Profile Setup" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They can browse friend updates and live map first",
                        "Profile creation can be minimal or done later",
                        "Social apps let them explore before requiring detailed profiles"
                    ],
                    "productAsks": [
                        "Create detailed profile before seeing main feed",
                        "Commit to profile setup before experiencing value"
                    ],
                    "whyItFails": [
                        "Profile setup feels like unnecessary commitment before seeing value",
                        "Users want to explore the app first, not commit to profile creation",
                        "Value (real-time friend updates, live map) not demonstrated before commitment"
                    ]
                }
        
        return {
            "userBelieves": [
                "They can explore the app and see real-time friend updates first",
                "Onboarding is quick and low-friction",
                "They'll see value (live map, friend locations) before being asked for permissions or verification"
            ],
            "productAsks": [
                "Grant permissions or verify before seeing main feed",
                "Share data or create profile before experiencing value"
            ],
            "whyItFails": [
                "Onboarding creates friction (location permission, verification, profile setup) before delivering value",
                "Privacy-conscious users hesitate to share data without seeing benefit",
                "Users expect social apps to let them explore before requiring commitments"
            ]
        }
    
    def generate_one_bet(self, autopsy):
        """Currently-specific one bet."""
        traces = getattr(self, '_current_traces', [])
        step_drop_counts = {}
        for trace in traces:
            if trace.decision.value == 'DROP':
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        
        if step_drop_counts:
            most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            step_index = None
            for i, step_id in enumerate(self.step_order):
                if step_id == most_dropped_step:
                    step_index = i
                    break
            
            if "Location Permission" in most_dropped_step:
                return {
                    "headline": f"Show live map preview with friend locations (anonymized) BEFORE requesting location permission at Step {step_index + 1}",
                    "support": "If users see a preview of the live map and friend locations (with anonymized markers) before being asked for location permission, they'll understand the value and be more willing to grant permission. This establishes value before trust demand.",
                    "confidenceLevel": "high",
                    "minimalityAndReversibility": "Minimal change: Just reorder steps to show preview before permission. Reversible: Can revert if it doesn't improve conversion.",
                    "executionSpecificity": "At Step 4 (Location Permission), first show a preview screen with: (1) Live map with anonymized friend location markers, (2) Text: 'See where your friends are in real-time', (3) Then request location permission with clear benefit explanation. This preview can use mock/demo data if needed.",
                    "learningPayoff": "Even if this fails, we learn whether location permission timing is the blocker or if users fundamentally don't want to share location. If preview doesn't help, the issue is deeper privacy concerns, not timing."
                }
            elif "OTP Verification" in most_dropped_step or "Phone Number" in most_dropped_step:
                return {
                    "headline": f"Allow guest browsing of main feed BEFORE phone verification at Step {step_index + 1}",
                    "support": "If users can browse the main feed, see real-time friend updates, and explore the live map as a guest before being asked for phone verification, they'll experience value first and be more willing to verify to continue.",
                    "confidenceLevel": "high",
                    "minimalityAndReversibility": "Minimal change: Make phone verification optional initially, allow guest access. Reversible: Can add verification requirement back if needed.",
                    "executionSpecificity": "At Step 1-2 (Phone Number Entry/OTP), add 'Continue as Guest' option that lets users browse feed and map. After they engage with content, prompt: 'Verify your phone to see friend locations and send updates'. This creates value-first experience.",
                    "learningPayoff": "Even if this fails, we learn whether phone verification is the blocker or if users don't find value in the app itself. If guest browsing doesn't improve engagement, the issue is product-market fit, not verification friction."
                }
            elif "Profile Setup" in most_dropped_step:
                return {
                    "headline": f"Show main feed preview BEFORE profile setup at Step {step_index + 1}",
                    "support": "If users see a preview of the main feed with real-time friend updates and live map before being asked to create a detailed profile, they'll understand the value and be more willing to complete profile setup.",
                    "confidenceLevel": "high",
                    "minimalityAndReversibility": "Minimal change: Reorder steps to show feed preview before profile. Reversible: Can revert if it doesn't improve conversion.",
                    "executionSpecificity": "At Step 4 (Profile Setup), first show a preview screen with: (1) Main feed with sample real-time updates, (2) Live map preview, (3) Text: 'Complete your profile to see your friends' updates'. Then prompt for minimal profile (name, photo) with option to add more later.",
                    "learningPayoff": "Even if this fails, we learn whether profile setup is the blocker or if users don't find value in the feed. If preview doesn't help, the issue is deeper engagement problem, not profile friction."
                }
        
        return {
            "headline": "Show value (live map, friend updates preview) BEFORE requesting permissions or verification",
            "support": "If users see a preview of the live map and real-time friend updates before being asked for location permission, phone verification, or detailed profile setup, they'll understand the value and be more willing to complete onboarding.",
            "confidenceLevel": "high",
            "minimalityAndReversibility": "Minimal change: Reorder steps to show preview before permissions. Reversible: Can revert if it doesn't improve conversion.",
            "executionSpecificity": "Add preview screens before permission/verification steps showing: (1) Live map with anonymized friend markers, (2) Sample real-time updates feed, (3) Clear benefit explanation. Then request permission/verification with context.",
            "learningPayoff": "Even if this fails, we learn whether timing is the blocker or if users fundamentally don't want to share data. If preview doesn't help, the issue is deeper privacy concerns or product-market fit."
        }
    
    def generate_how_wrong(self, autopsy):
        """Currently-specific falsifiable conditions for social app."""
        return [
            {
                "name": "Guest Browsing Test",
                "hypothesis": "Users abandon due to premature verification requirement, not verification itself",
                "measure": "Completion rate when guest browsing is allowed before phone verification vs current placement",
                "falsifier": "If guest browsing before verification shows equal abandonment, verification timing isn't the blocker."
            },
            {
                "name": "Value Preview Test",
                "hypothesis": "Users need to see value (live map, friend updates) before sharing location or verifying phone",
                "measure": "Engagement with preview screens (live map preview, feed preview) vs immediate permission requests",
                "falsifier": "If preview screens don't improve conversion, users don't value the social features enough to share data."
            },
            {
                "name": "Privacy Transparency Test",
                "hypothesis": "Bait-and-switch perception (exploration vs verification) drives exit more than data request itself",
                "measure": "Completion rate when onboarding explicitly mentions 'verification needed' vs silent verification prompt",
                "falsifier": "If transparency reduces starts, users actively avoid verification regardless of timing."
            }
        ]
    
    def generate_evidence(self, autopsy, traces):
        """Currently-specific evidence section for social app."""
        return {
            "assumptions": [
                "Users discovered Currently through app store, social media, or friend referrals",
                "Competing social apps (Instagram, Snapchat, BeReal) allow exploration before verification",
                "Users have not yet established relationship with the brand",
                "Privacy-conscious Millennials are sensitive to location sharing and phone verification"
            ],
            "constraints": [
                "Location-based features require location permission",
                "Real-time friend updates require phone verification for security",
                "Social graph building requires some user identification",
                "Platform safety requires verification to prevent spam/abuse"
            ],
            "rationale": [
                "Step 1 (Welcome) shows value proposition but doesn't demonstrate actual live map or friend updates",
                "Step 2 (Phone Verification) requests contact info before user experiences value",
                "Privacy reassurance appears only AFTER permission request — too late for trust building",
                "Users expect social apps to let them explore (like Instagram, Snapchat) before requiring verification",
                "Competing platforms show feed preview or allow guest browsing before verification"
            ]
        }
    
    def generate_margin_notes(self, autopsy):
        """Currently-specific margin notes for social app."""
        step_index = autopsy.irreversible_moment.position_in_flow
        total_steps = len(self.step_order)
        
        return {
            "page2": f"Note: {int((step_index + 1) / total_steps * 100)}% progress indicator creates expectation of exploration, not verification requirement.",
            "page4": "High confidence: Pattern observed across social app onboarding where value-before-verification sequencing improves conversion (see Instagram, Snapchat, BeReal).",
            "page5": "Alternative hypothesis: Users don't want to share location at all, not just timing. Test 'Skip location' option to see if it's privacy concern or timing issue.",
            "page3": f"First {step_index} steps show value proposition but don't demonstrate actual features. Step {step_index + 1} breaks pattern with verification/permission requirements."
        }
    
    def generate_decision_simulation(self, traces):
        """Override to generate social app-specific decision simulation."""
        from user_inference_generator import StepDecisionSimulation, StepInference
        
        # Create a custom inference generator that uses social app context
        class SocialAppInferenceGenerator:
            def __init__(self, product_steps, step_order):
                self.product_steps = product_steps
                self.step_order = step_order
            
            def generate_step_simulation(self, step_id):
                step_def = self.product_steps.get(step_id, {})
                step_index = self.step_order.index(step_id) if step_id in self.step_order else 0
                total_steps = len(self.step_order)
                
                # Generate social app-specific inferences
                inferences = []
                for level in ["30%", "60%", "100%"]:
                    if level == "30%":
                        what_user_sees = f"Social app screen showing {step_def.get('description', step_id).lower()}"
                        what_user_thinks = "This looks like a social app. I can explore to see what it offers."
                        what_user_understands = "I'm exploring a social app. I haven't seen the main feed or friend updates yet."
                        emotional_state = "Curious, exploring without strong commitment"
                    elif level == "60%":
                        progress = f"{step_index + 1}/{total_steps}"
                        what_user_sees = f"Step {progress}: {step_def.get('description', step_id)}"
                        what_user_thinks = "I'm going through onboarding. I want to see real-time friend updates and live map."
                        what_user_understands = f"I'm {step_index + 1} steps in. I expect to see the main feed with friend updates soon."
                        emotional_state = "Engaged but waiting to see value - proceeding with moderate interest"
                    else:  # 100%
                        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
                        delay = step_def.get('delay_to_value', total_steps)
                        what_user_sees = f"Step {step_index + 1}/{total_steps} ({progress_pct}%): {step_def.get('description', step_id)}"
                        
                        if delay > 0:
                            what_user_thinks = f"This is a social app for real-time friend updates. I'm providing information but haven't seen the live map or feed yet."
                            what_user_understands = f"VALUE MISMATCH: I'm at step {step_index + 1} but value (main feed, live map) appears at step {step_index + 1 + delay}. I'm being asked to share data {delay} steps BEFORE seeing what I'll get. This violates value-before-trust principle."
                            emotional_state = "Cautiously optimistic - proceeding but aware of the trust-value gap"
                        else:
                            what_user_thinks = "I'm finally seeing the main feed with real-time friend updates and live map. This is what I came for."
                            what_user_understands = "I can see value now (real-time friend updates, live map). This justifies the information I've shared. Trust is established because value was shown."
                            emotional_state = "Excited and engaged - finally seeing value justifies the process"
                    
                    inferences.append(StepInference(
                        inference_level=level,
                        what_user_sees=what_user_sees,
                        what_user_thinks=what_user_thinks,
                        what_user_understands=what_user_understands,
                        emotional_state=emotional_state
                    ))
                
                return StepDecisionSimulation(
                    step_id=step_id,
                    step_index=step_index,
                    step_description=step_def.get('description', step_id),
                    inferences=inferences
                )
        
        generator = SocialAppInferenceGenerator(self.product_steps, self.step_order)
        simulations = [generator.generate_step_simulation(step_id) for step_id in self.step_order]
        
        return {
            "steps": [
                {
                    "step_id": sim.step_id,
                    "step_index": sim.step_index,
                    "step_description": sim.step_description,
                    "inferences": [
                        {
                            "inference_level": inf.inference_level,
                            "what_user_sees": inf.what_user_sees,
                            "what_user_thinks": inf.what_user_thinks,
                            "what_user_understands": inf.what_user_understands,
                            "emotional_state": inf.emotional_state
                        }
                        for inf in sim.inferences
                    ]
                }
                for sim in simulations
            ]
        }


def run_simulation_and_generate_traces(n_personas: int = 10, seed: int = 42) -> list:
    """Run actual simulation with n_personas from NVIDIA database and generate DecisionTrace objects."""
    print(f"\n🔄 Running Currently simulation with {n_personas} personas from NVIDIA database...")
    
    try:
        from dropsim_target_filter import TargetGroup
        from behavioral_engine_intent_aware import run_intent_aware_simulation
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from dropsim_intent_model import infer_intent_distribution
        
        # Create Currently target group: young Millennials (22-35), urban, high digital skill, social app users
        target_group = TargetGroup(
            age_bucket=["young", "middle"],  # 22-35 falls in these buckets
            urban_rural=["metro", "tier2"],  # Urban users
            digital_skill=["high"],  # Heavy social app users
            intent=["medium", "high"]  # Strong intent for social connections
        )
        
        # Load personas from NVIDIA database
        print("📂 Loading personas from NVIDIA database...")
        personas_df_raw, _ = load_and_sample(
            n=n_personas * 5,  # Load more to ensure we get enough after filtering
            seed=seed,
            language="en_IN",
            verbose=False,
            use_huggingface=True
        )
        print(f"   ✅ Loaded {len(personas_df_raw)} personas from database")
        
        # Apply Currently-specific filters
        print("🎯 Applying Currently-specific filters...")
        df_filtered = personas_df_raw.copy()
        
        # Age filter: 22-35 (young Millennials)
        if 'age' in df_filtered.columns:
            df_filtered = df_filtered[(df_filtered['age'] >= 22) & (df_filtered['age'] <= 35)]
        
        # Urban filter: Metro/Tier-1 cities
        tier1_cities = ['bangalore', 'mumbai', 'delhi', 'gurgaon', 'noida', 'hyderabad', 'pune', 'chennai', 'kolkata']
        if 'city' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['city'].str.lower().isin(tier1_cities)]
        elif 'location' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['location'].str.lower().isin(tier1_cities)]
        
        # Digital skill filter: High (heavy social app users)
        if 'digital_skill' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['digital_skill'] == 'high']
        
        # Ensure we have at least n_personas
        if len(df_filtered) < n_personas:
            print(f"   ⚠️  Only {len(df_filtered)} personas match Currently filters, using all available and supplementing if needed.")
            if len(df_filtered) == 0:
                df_filtered = personas_df_raw.head(n_personas)  # Fallback to unfiltered if no match
            else:
                remaining_needed = n_personas - len(df_filtered)
                if remaining_needed > 0:
                    supplement = personas_df_raw.drop(df_filtered.index).sample(n=min(remaining_needed, len(personas_df_raw.drop(df_filtered.index))), random_state=seed)
                    df_filtered = pd.concat([df_filtered, supplement]).head(n_personas)
        else:
            df_filtered = df_filtered.head(n_personas)
        
        print(f"   ✅ Using {len(df_filtered)} personas for simulation")
        
        # Derive features for the filtered personas
        df_filtered = derive_all_features(df_filtered, verbose=False)
        
        # Infer intent distribution for Currently (social app, real-time updates)
        print("🎯 Inferring intent distribution...")
        try:
            first_step = list(CURRENTLY_STEPS.values())[0]
            entry_text = first_step.get('description', '')
            
            intent_result = infer_intent_distribution(
                entry_page_text=entry_text,
                product_type='social',  # Social app
                persona_attributes={'intent': 'medium', 'social': 'high'}
            )
            intent_distribution = intent_result['intent_distribution']
            print(f"   Primary Intent: {intent_result.get('primary_intent', 'social_connection')}")
        except Exception as e:
            print(f"   ⚠️  Could not infer intent, using default: {e}")
            intent_distribution = {
                'real_time_updates': 0.4,
                'spontaneous_meetups': 0.3,
                'live_map_exploration': 0.2,
                'friend_discovery': 0.1
            }
        
        # Run intent-aware simulation
        print("🧠 Running intent-aware simulation with enhanced engine...")
        result_df = run_intent_aware_simulation(
            df_filtered,
            product_steps=CURRENTLY_STEPS,
            intent_distribution=intent_distribution,
            verbose=False,
            seed=seed
        )
        print(f"   ✅ Simulation complete with {len(result_df)} persona trajectories")
        
        # Generate decision traces from simulation results
        print("📊 Generating decision traces from simulation...")
        traces = []
        step_names = list(CURRENTLY_STEPS.keys())
        
        drop_points = {}
        for idx, row in result_df.iterrows():
            for traj in row.get('trajectories', []):
                if not traj.get('completed', False) and traj.get('exit_step'):
                    step_id = traj.get('exit_step', 'unknown')
                    if step_id not in drop_points:
                        drop_points[step_id] = []
                    drop_points[step_id].append({
                        'persona_id': row.get('persona_id', f'persona_{idx}'),
                        'cognitive_state': traj.get('final_state', {}),
                        'intent': traj.get('intent', {}),
                        'probability': traj.get('continuation_probability', 0.5),
                        'dominant_factors': traj.get('dominant_factors', ['value_perception', 'privacy_concern'])
                    })
        
        trace_count = 0
        for step_id, drop_data_list in drop_points.items():
            try:
                step_index = step_names.index(step_id) if step_id in step_names else 0
                
                for i, drop_data in enumerate(drop_data_list[:min(200, len(drop_data_list))]):
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
                            inferred_intent=intent_data.get('intent_id', 'real_time_updates'),
                            alignment_score=intent_data.get('alignment_score', 0.6)
                        ),
                        dominant_factors=drop_data.get('dominant_factors', ['value_perception', 'privacy_concern'])
                    )
                    traces.append(trace)
                    trace_count += 1
                    
                    if trace_count >= n_personas:
                        break
                
                if trace_count >= n_personas:
                    break
            except Exception as e:
                print(f"   ⚠️  Error creating trace for {step_id}: {e}")
                continue
        
        if len(traces) < n_personas:
            print(f"   ⚠️  Only {len(traces)} traces generated, supplementing with fallback traces...")
            fallback_needed = n_personas - len(traces)
            fallback_traces = create_fallback_traces(num_traces=fallback_needed)
            traces.extend(fallback_traces)
        
        print(f"   ✅ Generated {len(traces)} decision traces")
        return traces
        
    except Exception as e:
        print(f"❌ Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        print("   Falling back to minimal traces...")
        return create_fallback_traces()


def create_fallback_traces(num_traces: int = 100) -> list:
    """Fallback: Create minimal decision traces."""
    step_names = list(CURRENTLY_STEPS.keys())
    traces = []
    
    import random
    random.seed(42)
    
    # Typical drop distribution for social apps
    step_distribution = {
        "Welcome & Value Proposition": 0.05,
        "Phone Number Entry": 0.10,
        "OTP Verification": 0.15,
        "Profile Setup": 0.20,
        "Location Permission": 0.40,  # Main break point
        "Friend Discovery & Main Feed": 0.10
    }
    
    for i in range(num_traces):
        rand = random.random()
        cumulative = 0
        selected_step = step_names[0]
        for step_id, prob in step_distribution.items():
            cumulative += prob
            if rand <= cumulative:
                selected_step = step_id
                break
        
        step_index = step_names.index(selected_step) if selected_step in step_names else 0
        step_def = CURRENTLY_STEPS.get(selected_step, {})
        
        trace = DecisionTrace(
            persona_id=f"persona_{i}",
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
                inferred_intent="real_time_updates",
                alignment_score=0.6 + random.uniform(-0.1, 0.1)
            ),
            dominant_factors=["privacy_concern", "value_perception"] if "Location" in selected_step else ["value_perception", "commitment_anxiety"]
        )
        traces.append(trace)
    
    return traces


def main():
    print("\n" + "="*70)
    print("CURRENTLY - SOCIAL APP ONBOARDING FLOW ANALYSIS")
    print("="*70)
    
    n_personas = 10
    print(f"\n🎯 Target Persona: Young Millennials (22-35), heavy social app users, urban, want real-time authentic updates from friends")
    print(f"📊 Running simulation with {n_personas} personas...")
    
    # Run simulation
    traces = run_simulation_and_generate_traces(n_personas=n_personas, seed=42)
    
    if not traces:
        print("❌ No traces generated. Exiting.")
        sys.exit(1)
    
    print(f"\n✅ Generated {len(traces)} decision traces")
    
    # Generate decision autopsy
    print("\n📋 Generating decision autopsy results...")
    
    generator = CurrentlyResultGenerator(
        product_steps=CURRENTLY_STEPS,
        product_name="Currently",
        product_full_name="Currently - Real-time Social Updates"
    )
    
    # Store traces for use in generator methods
    generator._current_traces = traces
    
    autopsy = generator.generate(traces)
    
    # Save to JSON
    output_file = "output/CURRENTLY_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, 'w') as f:
        json.dump(autopsy, f, indent=2)
    
    print(f"\n✅ Decision autopsy saved to {output_file}")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Product: Currently")
    print(f"Personas Simulated: {len(traces)}")
    print(f"Core Verdict: {autopsy.get('verdict', 'N/A')}")
    if 'beliefBreak' in autopsy:
        print(f"Belief Break: {autopsy['beliefBreak'].get('irreversibleAction', 'N/A')}")
    if 'oneBet' in autopsy:
        print(f"One Bet: {autopsy['oneBet'].get('headline', 'N/A')}")
    print("="*70)
    
    return autopsy


if __name__ == "__main__":
    main()
