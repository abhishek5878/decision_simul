"""
Decision Autopsy Result Generator (Simplified)

Generates founder-friendly, easy-to-understand results in the exact schema format.
Language is simplified and comprehensible.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

from decision_autopsy_generator import DecisionAutopsyGenerator, DecisionAutopsy
from decision_graph.decision_trace import DecisionTrace
from dominant_belief_break_analyzer import DominantBeliefBreakAnalyzer
from user_inference_generator import UserInferenceGenerator
import os


class DecisionAutopsyResultGenerator:
    """
    Generates simplified, founder-friendly Decision Autopsy results.
    """
    
    def __init__(self, product_steps: Dict[str, Dict], product_name: str, product_full_name: str = None):
        """
        Initialize generator.
        
        Args:
            product_steps: Dictionary mapping step_id to step definition
            product_name: Product identifier (e.g., "CREDIGO", "BLINK_MONEY")
            product_full_name: Full product name for display
        """
        self.product_steps = product_steps
        self.product_name = product_name.upper()
        self.product_full_name = product_full_name or f"{product_name.title()} Product"
        self.autopsy_generator = DecisionAutopsyGenerator(product_steps)
        self.break_analyzer = DominantBeliefBreakAnalyzer(product_steps)
        
        # Try to initialize LLM client if available
        llm_client = None
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                from dropsim_llm_ingestion import OpenAILLMClient
                llm_client = OpenAILLMClient(api_key=openai_key, model="gpt-4o-mini")
        except Exception:
            pass  # Fall back to rule-based
        
        self.inference_generator = UserInferenceGenerator(product_steps, product_name, llm_client=llm_client)
        self.step_order = list(product_steps.keys())
    
    def generate_simulation_id(self) -> str:
        """Generate unique simulation ID in format CRG-2025-01."""
        now = datetime.now()
        # Use first 3 letters of product + year + month
        prefix = self.product_name[:3]
        return f"{prefix}-{now.year}-{now.month:02d}"
    
    def infer_cohort(self, traces: List[DecisionTrace]) -> str:
        """Infer user cohort in plain language."""
        return "First-time credit seekers (₹0 history)"
    
    def infer_user_context(self) -> str:
        """Infer user context in plain language."""
        if "CREDIGO" in self.product_name or "CREDIT" in self.product_name:
            return "Users seeking personalized credit card recommendations, mid-funnel"
        elif "BLINK" in self.product_name:
            return "Users seeking credit against mutual funds, early-funnel"
        else:
            return "Users exploring financial products, mid-funnel"
    
    def simplify_verdict(self, autopsy: DecisionAutopsy) -> str:
        """Convert technical verdict to plain language."""
        verdict = autopsy.verdict_text.lower()
        
        # Map technical terms to plain language
        if "trust collapses" in verdict:
            if "commitment" in verdict and "before trust" in verdict:
                return "Trust collapses precisely when personal financial data requests appear without established credibility."
            else:
                return "Trust collapses when sensitive information is requested before users understand the value."
        elif "value perception collapses" in verdict or "value" in verdict:
            if "distant" in verdict:
                return "Users abandon when asked to share personal information before seeing what they'll get in return."
            else:
                return "Value perception collapses when commitment is demanded while value remains distant."
        elif "risk perception" in verdict:
            return "Users abandon when risk feels too high relative to demonstrated value."
        else:
            # Generic simplification
            return verdict.replace("commitment is demanded", "personal information is requested").capitalize()
    
    def generate_belief_break_section(self, autopsy: DecisionAutopsy) -> Dict:
        """Generate beliefBreak section with simplified language."""
        step_id = autopsy.irreversible_moment.step_id
        step_index = autopsy.irreversible_moment.position_in_flow
        total_steps = len(self.step_order)
        step_def = self.product_steps.get(step_id, {})
        
        # Generate irreversible action in plain language
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
        
        # Infer what's being asked based on step definition
        if "credit score" in step_id.lower() or "income" in step_id.lower() or "financial" in step_id.lower():
            action = f"User must disclose credit score range and annual income at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without prior value demonstration."
        elif "bank account" in step_id.lower() or "account" in step_id.lower():
            action = f"User must link bank account at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before seeing any results."
        elif "pan" in step_id.lower() or "dob" in step_id.lower():
            action = f"User must provide PAN and date of birth at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing personalized recommendations."
        elif "mobile" in step_id.lower() or "phone" in step_id.lower():
            action = f"User must share mobile number at step {step_index + 1} of {total_steps} ({progress_pct}% progress) before understanding what they'll receive."
        else:
            action = f"User must make a commitment at step {step_index + 1} of {total_steps} ({progress_pct}% progress) without seeing value first."
        
        # Generate callouts
        callouts = [
            {"text": "Sensitive data requested at peak commitment", "position": "top-left"},
            {"text": "No established trust before financial disclosure", "position": "bottom-right"}
        ]
        
        # Generate psychology in narrative form
        delay_to_value = step_def.get('delay_to_value', total_steps)
        irreversibility = step_def.get('irreversibility', 0.0)
        
        if step_index == 0:
            psychology = f"Users arrive expecting to explore options, but immediately encounter a request for personal information. The mismatch between initial expectations and actual requirements triggers immediate abandonment."
        elif delay_to_value >= step_index and step_index > 0:
            psychology = f"After investing {step_index} steps into preference questions, users encounter unexpected financial disclosure requirements at {progress_pct}% completion. The cognitive mismatch between 'exploration' framing and 'application' reality triggers abandonment. Users experience bait-and-switch perception when casual engagement suddenly demands sensitive financial data."
        elif irreversibility > 0.3:
            psychology = f"At step {step_index + 1}, users face an irreversible commitment without having seen any personalized value. The combination of high commitment and low demonstrated value creates a trust deficit that triggers abandonment."
        else:
            psychology = f"Users reach step {step_index + 1} expecting to see results, but instead face new requirements for personal information. The expectation mismatch between progress shown ({progress_pct}%) and actual friction triggers abandonment."
        
        return {
            "screenshot": f"screenshots/{self.product_name.lower()}/{step_index + 1}.jpeg",
            "irreversibleAction": action,
            "callouts": callouts,
            "psychology": psychology
        }
    
    def generate_journey_screenshots(self, autopsy: DecisionAutopsy) -> Dict:
        """Generate journeyScreenshots section."""
        step_index = autopsy.irreversible_moment.position_in_flow
        product_lower = self.product_name.lower()
        total_steps = len(self.step_order)
        
        # Before: previous step or landing page
        before_step = max(0, step_index - 1) if step_index > 0 else 0
        moment_step = step_index
        after_step = min(total_steps - 1, step_index + 1) if step_index < total_steps - 1 else step_index
        
        result = {
            "before": f"screenshots/{product_lower}/{before_step + 1}.jpeg",
            "moment": f"screenshots/{product_lower}/{moment_step + 1}.jpeg"
        }
        
        if after_step > moment_step:
            result["after"] = f"screenshots/{product_lower}/{after_step + 1}.jpeg"
        
        return result
    
    def generate_why_belief_breaks(self, autopsy: DecisionAutopsy) -> Dict:
        """Generate whyBeliefBreaks section in plain language."""
        step_def = self.product_steps.get(autopsy.irreversible_moment.step_id, {})
        step_index = autopsy.irreversible_moment.position_in_flow
        total_steps = len(self.step_order)
        
        # Infer user beliefs based on step position and type
        if step_index == 0:
            user_believes = [
                "This is a quick exploration tool",
                "They can browse options without commitment",
                "The platform will show value before asking for data"
            ]
        elif step_index < total_steps * 0.5:
            user_believes = [
                "This is a low-stakes preference quiz",
                "Recommendations based on spending patterns only",
                "Can explore options without commitment"
            ]
        else:
            user_believes = [
                "They're almost done and will see results soon",
                "The hard questions are behind them",
                "They'll see personalized recommendations now"
            ]
        
        # Infer product asks based on step definition
        step_id_lower = autopsy.irreversible_moment.step_id.lower()
        product_asks = []
        
        if "credit score" in step_id_lower or "score" in step_id_lower:
            product_asks.append("Disclose exact credit score range")
        if "income" in step_id_lower or "salary" in step_id_lower:
            product_asks.append("Reveal annual income bracket")
        if "bank" in step_id_lower or "account" in step_id_lower:
            product_asks.append("Link bank account for verification")
        if "pan" in step_id_lower:
            product_asks.append("Provide PAN number")
        if "mobile" in step_id_lower or "phone" in step_id_lower:
            product_asks.append("Share mobile number")
        
        if not product_asks:
            product_asks.append("Make a commitment without seeing value")
            product_asks.append("Trust platform with personal information")
        
        # Infer why it fails
        delay_to_value = step_def.get('delay_to_value', total_steps)
        why_it_fails = []
        
        if delay_to_value > step_index:
            why_it_fails.append("Value not demonstrated before data request")
        if step_index > 0 and step_index < total_steps * 0.7:
            why_it_fails.append("Quiz framing mismatches application reality")
        why_it_fails.append("Trust demand exceeds relationship depth")
        
        return {
            "userBelieves": user_believes,
            "productAsks": product_asks,
            "whyItFails": why_it_fails
        }
    
    def generate_one_bet(self, autopsy: DecisionAutopsy) -> Dict:
        """Generate oneBet section with actionable headline."""
        step_index = autopsy.irreversible_moment.position_in_flow
        step_def = self.product_steps.get(autopsy.irreversible_moment.step_id, {})
        delay_to_value = step_def.get('delay_to_value', len(self.step_order))
        total_steps = len(self.step_order)
        
        # Generate actionable headline based on step position
        if delay_to_value > step_index and step_index < total_steps - 1:
            # Value comes later - show value first
            headline = "Show personalized recommendations BEFORE requesting financial disclosure."
            support = "If users see tailored results based solely on preferences, establishing value before trust demands, completion rates should increase."
        elif step_index == 0:
            # First step - show value on landing
            headline = "Show value proposition and sample results on the landing page."
            support = "If users understand what they'll get before sharing any information, trust builds naturally and completion rates increase."
        elif step_index >= total_steps - 1:
            # Last step - move commitment earlier or show value first
            headline = "Show eligibility results BEFORE final confirmation step."
            support = "If users see their personalized loan amount and eligibility before being asked to commit, completion rates should increase."
        else:
            # Middle step - generic fix
            headline = "Show personalized matches BEFORE asking for sensitive information."
            support = "If users see value first, they're more willing to share information to refine results."
        
        # Determine confidence level
        confidence_level = "high" if autopsy.confidence_level > 0.7 else "medium" if autopsy.confidence_level > 0.5 else "low"
        
        return {
            "headline": headline,
            "support": support,
            "confidenceLevel": confidence_level
        }
    
    def generate_how_wrong(self, autopsy: DecisionAutopsy) -> List[Dict]:
        """Generate howWrong section with descriptive test names."""
        step_index = autopsy.irreversible_moment.position_in_flow
        step_def = self.product_steps.get(autopsy.irreversible_moment.step_id, {})
        delay_to_value = step_def.get('delay_to_value', len(self.step_order))
        
        tests = []
        
        # Test 1: Value-First Sequencing
        if delay_to_value > step_index:
            tests.append({
                "name": "Value-First Sequencing Test",
                "hypothesis": "Users abandon due to premature data request, not data request itself",
                "measure": "Completion rate when financial questions move to post-recommendation vs current placement",
                "falsifier": "If post-recommendation placement shows equal abandonment, timing isn't the blocker."
            })
        
        # Test 2: Progressive Disclosure
        tests.append({
            "name": "Progressive Disclosure Test",
            "hypothesis": "Users need gradual trust building through value demonstration",
            "measure": "Engagement with initial recommendations (no financial data) vs refined recommendations (with data)",
            "falsifier": "If users don't engage with initial recommendations, they don't value the output."
        })
        
        # Test 3: Framing Transparency
        tests.append({
            "name": "Framing Transparency Test",
            "hypothesis": "Bait-and-switch perception drives exit more than data request",
            "measure": "Completion rate when step 1 explicitly mentions 'financial info needed' vs silent",
            "falsifier": "If transparency reduces starts, users actively avoid financial disclosure regardless of timing."
        })
        
        return tests[:3]
    
    def generate_evidence(self, autopsy: DecisionAutopsy, traces: List[DecisionTrace]) -> Dict:
        """Generate evidence section with specific observations."""
        step_index = autopsy.irreversible_moment.position_in_flow
        total_steps = len(self.step_order)
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
        
        assumptions = [
            f"Users discovered {self.product_full_name} through organic search or ads promising 'instant recommendations'",
            "Competing platforms offer immediate results without financial disclosure",
            "Users have not yet established relationship with the brand"
        ]
        
        constraints = [
            "Accurate matching requires some financial data",
            "Lending partners require minimum qualification criteria",
            "Regulatory compliance mandates certain disclosures"
        ]
        
        # Generate specific rationale from flow observations
        rationale = []
        
        step_id = autopsy.irreversible_moment.step_id
        step_id_lower = step_id.lower()
        
        # Progress indicator observation
        if progress_pct >= 80:
            rationale.append(f"Progress bar shows {progress_pct}% at financial disclosure step — signals 'almost done' but introduces highest-friction requirement")
        elif progress_pct >= 50:
            rationale.append(f"Progress shows {progress_pct}% completion — users expect to see results soon, not new requirements")
        
        # Previous steps observation
        if step_index > 0:
            if step_index <= 3:
                rationale.append(f"Steps 1-{step_index} establish comfort through low-stakes questions (preferences, categories)")
            else:
                rationale.append(f"Steps 1-{step_index} establish comfort through low-stakes preference questions (perks, fees, categories)")
        
        # Privacy/trust signals
        rationale.append("Privacy reassurance appears only AFTER request — too late for trust building")
        
        # Step-specific observations
        if "pan" in step_id_lower or "dob" in step_id_lower:
            rationale.append("PAN and DOB requested without showing eligibility results first — users don't know if they qualify")
            rationale.append("Credit limit check promise appears, but users must share sensitive financial identity before seeing limit")
        elif "bank" in step_id_lower or "account" in step_id_lower:
            rationale.append("Bank account linking required before showing loan amount — users commit without knowing what they'll get")
            rationale.append("Read-only access mentioned, but users don't see loan terms before linking account")
        elif "mobile" in step_id_lower or "phone" in step_id_lower:
            rationale.append("Mobile number requested early without value demonstration — users hesitate to share contact info")
            rationale.append("Free vouchers mentioned as incentive, but value not personalized to user's needs")
        elif step_index == 0:
            rationale.append("Landing page shows value proposition (9.99% p.a., up to ₹1 Crore) but doesn't show personalized eligibility")
            rationale.append("Users see generic benefits but must start process to learn if they qualify")
        
        # Final step observation
        if step_index == total_steps - 1 or step_index >= total_steps - 2:
            rationale.append("Final step promises results but requires sensitive data — expectation mismatch")
        
        # Competitive context
        rationale.append("Competing platforms show initial matches without credit score disclosure")
        
        # Ensure we have at least 4-5 rationale items
        if len(rationale) < 4:
            rationale.append("Users expect to see eligibility estimate before sharing financial information")
            rationale.append("Progress indicators create false sense of completion when high-friction steps remain")
        
        return {
            "assumptions": assumptions,
            "constraints": constraints,
            "rationale": rationale
        }
    
    def generate_margin_notes(self, autopsy: DecisionAutopsy) -> Dict:
        """Generate marginNotes section."""
        step_index = autopsy.irreversible_moment.position_in_flow
        total_steps = len(self.step_order)
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
        
        margin_notes = {
            "page2": f"Note: {progress_pct}% progress indicator creates expectation of completion, not new high-friction requirement.",
            "page4": f"High confidence: Pattern observed across fintech onboarding where value-before-trust sequencing improves conversion.",
            "page5": "Alternative hypothesis: Users lack credit score knowledge, not willingness to share. Test 'Don't know my score' option."
        }
        
        if step_index > 0:
            margin_notes["page3"] = f"First {step_index} steps train users for 'preference quiz' experience. Step {step_index + 1} breaks pattern with financial application requirements."
        else:
            margin_notes["page3"] = "Landing page promises exploration, but immediately requires personal information — expectation mismatch from the start."
        
        return margin_notes
    
    def generate_decision_simulation(self, traces: List[DecisionTrace]) -> Dict:
        """
        Generate decision simulation for all steps with pre-defined inference levels (30%, 60%, 100%).
        
        These are step-level inferences, NOT persona-specific. Generated once per step.
        """
        # Generate step-level simulations (30%, 60%, 100% per step)
        # This calls LLM only once per step (3 calls per step = 21 total calls for 7 steps)
        step_simulations = self.inference_generator.generate_all_step_simulations()
        
        return {
            "steps": [
                self.inference_generator.to_dict(sim) for sim in step_simulations
            ]
        }
    
    def generate(self, traces: List[DecisionTrace], run_mode: str = "production",
                 config: Optional[Dict] = None) -> Dict:
        """
        Generate complete Decision Autopsy result in simplified, founder-friendly format.
        """
        start_time = time.time()
        
        # Generate base autopsy
        autopsy = self.autopsy_generator.generate(
            product_id=self.product_name.lower(),
            traces=traces,
            run_mode=run_mode,
            config=config or {}
        )
        
        latency = f"{time.time() - start_time:.2f}s"
        confidence = f"{autopsy.confidence_level * 100:.1f}%"
        
        result = {
            "simulationId": self.generate_simulation_id(),
            "latency": latency,
            "confidence": confidence,
            "cohort": self.infer_cohort(traces),
            "productName": self.product_full_name,
            "userContext": self.infer_user_context(),
            "verdict": self.simplify_verdict(autopsy),
            "beliefBreak": self.generate_belief_break_section(autopsy),
            "journeyScreenshots": self.generate_journey_screenshots(autopsy),
            "whyBeliefBreaks": self.generate_why_belief_breaks(autopsy),
            "oneBet": self.generate_one_bet(autopsy),
            "howWrong": self.generate_how_wrong(autopsy),
            "evidence": self.generate_evidence(autopsy, traces),
            "marginNotes": self.generate_margin_notes(autopsy),
            "decisionSimulation": self.generate_decision_simulation(traces)
        }
        
        # Remove None values from journeyScreenshots
        if "after" in result["journeyScreenshots"] and result["journeyScreenshots"]["after"] is None:
            del result["journeyScreenshots"]["after"]
        
        return result
