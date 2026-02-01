#!/usr/bin/env python3
"""
Novelty Wealth - Decision Simulation (Persona-Backed)

Runs an intent-aware behavioral simulation for the Novelty Wealth onboarding /
decision flow using personas from the Nemotron-Personas-India dataset (same
pipeline as Credigo / Currently), then generates a Decision Autopsy JSON
result using the existing engine.

Output: NOVELTY_WEALTH_DECISION_AUTOPSY_RESULT.json

Usage:
  python3 run_novelty_wealth_simulation.py                # default 1000 personas
  python3 run_novelty_wealth_simulation.py --n 500        # custom persona count
"""

import argparse
import json
import sys
from typing import List

import pandas as pd

from decision_autopsy_result_generator import DecisionAutopsyResultGenerator
from decision_graph.decision_trace import (
    DecisionTrace,
    DecisionOutcome,
    CognitiveStateSnapshot,
    IntentSnapshot,
)
from novelty_wealth_steps import NOVELTY_WEALTH_STEPS
from behavioral_engine_intent_aware import run_intent_aware_simulation
from load_dataset import load_and_sample
from derive_features import derive_all_features
from dropsim_intent_model import infer_intent_distribution


class NoveltyWealthResultGenerator(DecisionAutopsyResultGenerator):
    """
    Novelty Wealth–specific result generator with targeted cohort / context.
    """

    def infer_cohort(self, traces):
        return (
            "Founders, startup operators, senior professionals, and early investors "
            "aged roughly 28–45 with first-generation wealth or rapid income "
            "acceleration, who are comfortable with complexity and allergic to fluff."
        )

    def infer_user_context(self):
        return (
            "Users are actively thinking about how to turn volatile or fast-growing "
            "income into long-term, compounding wealth. They are comparing tools, "
            "skeptical of marketing speak, and expect clear, high-signal explanations "
            "before committing serious capital."
        )

    # --- Wealth-specific verdict + sections ---------------------------------

    def _get_drop_stats(self):
        """Utility: compute drop counts by step from stored traces."""
        traces = getattr(self, "_current_traces", []) or []
        step_drop_counts = {}
        for trace in traces:
            if trace.decision.value == "DROP":
                step_id = trace.step_id
                step_drop_counts[step_id] = step_drop_counts.get(step_id, 0) + 1
        return traces, step_drop_counts

    def simplify_verdict(self, autopsy):
        """
        Wealth-specific verdict language using actual drop points.
        """
        traces, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]

            if "Landing & Promise" in most_dropped_step:
                return (
                    "Sophisticated users bounce at the landing page because the message "
                    "feels generic and marketing-led, not like a serious, high-signal "
                    "wealth product worth their attention."
                )
            elif "Profile & Goals" in most_dropped_step:
                return (
                    "Users drop when the profile/goals questionnaire feels like work "
                    "before they have seen even a rough sketch of the wealth plan "
                    "they're signing up for."
                )
            elif "Income & Contributions" in most_dropped_step:
                return (
                    "Users abandon when asked for income and contribution details "
                    "without first seeing a concrete, credible view of how Novelty "
                    "will deploy that money."
                )
            elif "Account / KYC Commitment" in most_dropped_step:
                return (
                    "Users hesitate at the account/KYC step because linking money feels "
                    "like a hard commitment, and they are not yet convinced that this "
                    "is the right vehicle for their wealth."
                )

        # Fallback to generic but still wealth-themed message
        return (
            "Users abandon when the flow asks for meaningful financial information or "
            "commitment before they feel they've seen a clear, high-signal picture of "
            "the wealth strategy on offer."
        )

    def generate_belief_break_section(self, autopsy):
        """
        Wealth-specific belief break based on dominant drop step.
        """
        _, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            actual_irreversible_step = max(
                step_drop_counts.items(), key=lambda x: x[1]
            )[0]
            step_index = None
            for i, step_id in enumerate(self.step_order):
                if step_id == actual_irreversible_step:
                    step_index = i
                    break

            if step_index is not None:
                step_def = self.product_steps.get(actual_irreversible_step, {})
                total_steps = len(self.step_order)
                progress_pct = (
                    int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100
                )

                if "Landing & Promise" in actual_irreversible_step:
                    irreversible_action = (
                        "Users bounce from the first screen after seeing a generic "
                        "wealth promise that does not feel differentiated or credible."
                    )
                    psychology = (
                        "Founders and senior operators arrive from an ad or landing page "
                        "expecting a sharp, differentiated POV on wealth building. "
                        "When the first screen feels like generic marketing rather than "
                        "a serious partner in compounding their capital, they treat it "
                        "as low-signal and leave without engaging."
                    )
                elif "Profile & Goals" in actual_irreversible_step:
                    irreversible_action = (
                        f"User is asked to fill a detailed profile/goals questionnaire "
                        f"at step {step_index + 1} of {total_steps} ({progress_pct}% "
                        f"progress) before seeing even a rough portfolio or plan."
                    )
                    psychology = (
                        "Users are willing to share goals, but only once they have seen "
                        "a glimpse of how Novelty will actually allocate their money. "
                        "A long goals form with no preview feels like unpaid consulting "
                        "for a product they haven't yet chosen."
                    )
                elif "Income & Contributions" in actual_irreversible_step:
                    irreversible_action = (
                        f"User must enter income and contribution numbers at step "
                        f"{step_index + 1} of {total_steps} ({progress_pct}% progress) "
                        f"before seeing how those inputs translate into a real plan."
                    )
                    psychology = (
                        "First‑generation wealth creators are careful about where they "
                        "expose financial details. When asked for income/contribution "
                        "inputs before they see a credible strategy or guardrails, it "
                        "feels like asymmetric disclosure: they give up precision while "
                        "seeing only vague promises."
                    )
                elif "Account / KYC Commitment" in actual_irreversible_step:
                    irreversible_action = (
                        f"User must complete KYC or link money at step {step_index + 1} "
                        f"of {total_steps} ({progress_pct}% progress) to activate the "
                        f"plan."
                    )
                    psychology = (
                        "By the time KYC appears, users have seen value but are still "
                        "running a mental 'manager selection' process. For this cohort, "
                        "linking money is equivalent to hiring a manager. When the "
                        "trust story, downside protection, and exit options are not yet "
                        "clear, they pause instead of wiring funds."
                    )
                else:
                    irreversible_action = (
                        f"User hits a commitment-heavy step at {progress_pct}% progress "
                        f"before feeling fully bought into the strategy."
                    )
                    psychology = (
                        "For wealth products, this cohort expects to understand the "
                        "strategy, risks, and upside before any irreversible step. "
                        "When the flow flips that sequence, they protect downside by "
                        "exiting."
                    )

                return {
                    "screenshot": f"screenshots/novelty_wealth/{step_index + 1}.jpeg",
                    "irreversibleAction": irreversible_action,
                    "callouts": [
                        {
                            "text": "Commitment / friction appears before conviction",
                            "position": "top-left",
                        },
                        {
                            "text": "Sophisticated users protect downside first",
                            "position": "bottom-right",
                        },
                    ],
                    "psychology": psychology,
                }

        # Fallback to base implementation if we can't compute drops
        return super().generate_belief_break_section(autopsy)

    def generate_why_belief_breaks(self, autopsy):
        """
        Wealth-specific 'why belief breaks' narrative.
        """
        _, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]

            if "Landing & Promise" in most_dropped_step:
                return {
                    "userBelieves": [
                        "This will feel like a serious wealth partner, not a generic app",
                        "They will quickly see whether Novelty's philosophy matches their own",
                        "If it looks fluffy, they can safely ignore it",
                    ],
                    "productAsks": [
                        "Treat a marketing-style landing as enough reason to enter the flow",
                        "Trust broad claims without seeing the underlying strategy",
                    ],
                    "whyItFails": [
                        "High-signal users pattern-match generic landing language to low-quality products",
                        "No sharp POV or differentiation appears before asking for attention",
                    ],
                }
            if "Profile & Goals" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They can first see how Novelty thinks about wealth (framework, plan skeleton)",
                        "Goal questions will feel lightweight and obviously tied to the output",
                        "Their time won't be wasted on long forms for an unproven product",
                    ],
                    "productAsks": [
                        "Invest time in a detailed profile before seeing a concrete plan shape",
                        "Trust that giving rich context will be worth it later",
                    ],
                    "whyItFails": [
                        "The goals form feels like work before payoff",
                        "The connection between questions and eventual plan is not visible",
                    ],
                }
            if "Income & Contributions" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They will first see a strategy philosophy and example allocations",
                        "Exact numbers can be tuned later once they trust the approach",
                        "They won't have to expose income details just to kick the tires",
                    ],
                    "productAsks": [
                        "Share income and contribution details early in the flow",
                        "Trust that these numbers will be handled safely and intelligently",
                    ],
                    "whyItFails": [
                        "Precision is demanded before conviction is earned",
                        "Users perceive asymmetric risk: they share details while still unsure if this is their vehicle",
                    ],
                }
            if "Account / KYC Commitment" in most_dropped_step:
                return {
                    "userBelieves": [
                        "They can understand fees, risk management, and exit paths before wiring funds",
                        "KYC and account linking will feel like a natural, low-friction final step",
                        "They can sleep at night with money parked here",
                    ],
                    "productAsks": [
                        "Complete KYC / link accounts when trust is still forming",
                        "Treat a single flow as enough to hand over serious capital",
                    ],
                    "whyItFails": [
                        "KYC/link step feels like a hard commitment rather than an obvious next step",
                        "Risk, downside protection, and governance story are not fully internalized yet",
                    ],
                }

        # Generic wealth fallback
        return {
            "userBelieves": [
                "They'll see a clear wealth strategy before being asked for anything irreversible",
                "The flow will respect their time and sophistication",
            ],
            "productAsks": [
                "Share details or commit before conviction is fully built",
                "Trust generic promises without deep understanding",
            ],
            "whyItFails": [
                "Sequence puts friction before conviction",
                "High-signal users protect downside and simply leave",
            ],
        }

    def generate_one_bet(self, autopsy):
        """
        Wealth-specific one-bet recommendation based on where users drop.
        """
        _, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            most_dropped_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            step_index = self.step_order.index(most_dropped_step)

            if "Landing & Promise" in most_dropped_step:
                return {
                    "headline": "Lead with a sharp, founder-grade memo on your wealth philosophy before any flow.",
                    "support": "If the first screen reads like a serious, opinionated memo rather than generic marketing, this cohort is more likely to give you 5–10 minutes of attention and start the flow.",
                    "confidenceLevel": "medium",
                }
            if "Profile & Goals" in most_dropped_step:
                return {
                    "headline": "Show a rough, example portfolio or plan BEFORE the long goals questionnaire.",
                    "support": "If users see how Novelty structures a 10–20 year wealth plan up front, they'll understand why each goal question matters and be more willing to fill it in.",
                    "confidenceLevel": "high",
                }
            if "Income & Contributions" in most_dropped_step:
                return {
                    "headline": "Let users explore scenarios with ranges/sliders BEFORE asking for exact income numbers.",
                    "support": "If users can play with approximate inputs and see plan shapes first, asking for precise income later feels like calibration, not a blind disclosure.",
                    "confidenceLevel": "high",
                }
            if "Account / KYC Commitment" in most_dropped_step:
                return {
                    "headline": "Add a 'dry run' mode that shows how money would be allocated BEFORE KYC/linking.",
                    "support": "If users can see a simulated allocation and downside scenarios on fake money, KYC becomes a natural step to move from paper to reality.",
                    "confidenceLevel": "medium",
                }

        return {
            "headline": "Separate conviction-building (philosophy + plan preview) from commitment (exact inputs + KYC).",
            "support": "If the flow first earns trust with a clear strategy and only then asks for details and commitment, this cohort is far more willing to move real money.",
            "confidenceLevel": "medium",
        }

    def generate_evidence(self, autopsy, traces):
        """
        Wealth-themed evidence section instead of generic credit-card language.
        """
        _, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            dominant_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
        else:
            dominant_step = self.step_order[0]

        assumptions = [
            "Users discovered Novelty Wealth through founder/operator networks, podcasts, or targeted ads promising a better way to compound wealth.",
            "They already have access to traditional brokers, mutual funds, and direct equity; the bar for 'new' is high.",
            "They think in terms of risk-adjusted compounding and manager selection, not just app UX.",
        ]

        constraints = [
            "Building a credible wealth plan requires some view of income, timeline, and contribution capacity.",
            "Regulation and compliance still require KYC for real money flows.",
            "Novelty must balance transparency with not overwhelming users with raw complexity.",
        ]

        rationale = []
        if "Landing & Promise" in dominant_step:
            rationale.extend(
                [
                    "Most drop happens before users even start the form, indicating a landing/positioning problem more than a form problem.",
                    "Language on the first screen patterns as generic fintech marketing rather than a differentiated wealth philosophy.",
                ]
            )
        if "Profile & Goals" in dominant_step:
            rationale.extend(
                [
                    "Goal questions appear before users see any example of allocations, guardrails, or long-term plan shape.",
                    "For this cohort, long forms with unclear payoff are interpreted as a poor use of attention.",
                ]
            )
        if "Income & Contributions" in dominant_step:
            rationale.extend(
                [
                    "Income/contribution inputs are requested while the product is still in the 'pitch' stage, not yet in 'trusted advisor' territory.",
                    "Users are more sensitive about sharing financial details with products they haven't mentally hired yet.",
                ]
            )
        if "Account / KYC Commitment" in dominant_step:
            rationale.extend(
                [
                    "KYC/link appears as a binary gate rather than a natural final step after a convincing dry run.",
                    "Exit options and risk management are not yet salient, so wiring money feels one-way.",
                ]
            )

        if not rationale:
            rationale.append(
                "Drop-off concentrates around points where friction or commitment appears before conviction is fully built."
            )

        return {
            "assumptions": assumptions,
            "constraints": constraints,
            "rationale": rationale,
        }

    def generate_margin_notes(self, autopsy):
        """
        Wealth-specific margin notes highlighting conviction vs commitment.
        """
        _, step_drop_counts = self._get_drop_stats()
        if step_drop_counts:
            dominant_step = max(step_drop_counts.items(), key=lambda x: x[1])[0]
            step_index = self.step_order.index(dominant_step)
        else:
            step_index = autopsy.irreversible_moment.position_in_flow

        total_steps = len(self.step_order)
        progress_pct = int((step_index + 1) / total_steps * 100) if total_steps > 0 else 100

        notes = {
            "page2": f"Note: Drop concentrates around step {step_index + 1} (~{progress_pct}% of the flow), where conviction has not fully caught up with the level of friction/commitment.",
            "page4": "Pattern: for first-generation wealth creators, conviction must come from a clear philosophy and plan preview before any irreversible step.",
            "page5": "Alternative hypothesis: some users simply prefer self-directed investing and will never hand over allocation decisions, regardless of flow improvements.",
        }

        if step_index > 0:
            notes["page3"] = (
                f"First {step_index} steps are doing some work, but they are not yet strong "
                f"enough to justify the commitment asked at step {step_index + 1}."
            )
        else:
            notes["page3"] = (
                "Landing page bears most of the load: if positioning is off for this cohort, "
                "no amount of downstream UX fixes the bounce."
            )

        return notes


def create_fallback_traces(num_traces: int = 50, seed: int = 42) -> List[DecisionTrace]:
    """
    Fallback: synthetic traces if persona-based simulation fails.
    """
    import random

    random.seed(seed)

    step_names = list(NOVELTY_WEALTH_STEPS.keys())
    traces: List[DecisionTrace] = []

    # Drop-off distribution: built from current steps (ss1..ss6) so it stays in sync
    # Heavier on middle steps (goals, income, plan); lighter on landing and final KYC
    default_probs = [0.08, 0.12, 0.18, 0.25, 0.22, 0.15]  # 6 steps
    n_steps = len(step_names)
    probs = (default_probs[:n_steps] if n_steps <= len(default_probs) else [1.0 / n_steps] * n_steps)
    scale = sum(probs)
    step_distribution = {step_names[i]: probs[i] / scale for i in range(n_steps)}

    for i in range(num_traces):
        rand = random.random()
        cumulative = 0.0
        selected_step = step_names[0]

        for step_id, prob in step_distribution.items():
            cumulative += prob
            if rand <= cumulative:
                selected_step = step_id
                break

        step_index = step_names.index(selected_step)
        step_def = NOVELTY_WEALTH_STEPS.get(selected_step, {})

        traces.append(
            DecisionTrace(
                persona_id=f"persona_{i}",
                step_id=selected_step,
                step_index=step_index,
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.4 + random.uniform(-0.1, 0.1),
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=0.5 + random.uniform(-0.1, 0.1),
                    risk=step_def.get("risk_signal", 0.3) + random.uniform(-0.1, 0.1),
                    effort=step_def.get("effort_demand", 0.3)
                    + random.uniform(-0.1, 0.1),
                    value=step_def.get("explicit_value", 0.5)
                    + random.uniform(-0.1, 0.1),
                    control=0.5 + random.uniform(-0.1, 0.1),
                ),
                intent=IntentSnapshot(
                    inferred_intent="build_wealth_over_time",
                    alignment_score=0.6 + random.uniform(-0.1, 0.1),
                ),
                dominant_factors=["value_perception", "risk_perception"],
            )
        )

    return traces


def run_simulation_and_generate_traces(
    n_personas: int = 1000, seed: int = 42
) -> List[DecisionTrace]:
    """
    Run persona-backed simulation using Nemotron personas and return DecisionTrace objects.
    """
    print(
        f"\n🔄 Running Novelty Wealth simulation with {n_personas} personas from NVIDIA dataset..."
    )

    try:
        # 1) Load personas from Nemotron-Personas-India
        print("📂 Loading personas from NVIDIA dataset...")
        personas_df_raw, _ = load_and_sample(
            n=n_personas * 5,  # over-sample then filter
            seed=seed,
            language="en_IN",
            verbose=False,
            use_huggingface=True,
        )
        print(f"   ✅ Loaded {len(personas_df_raw)} personas from database")

        # 2) Apply simple Novelty-Wealth–oriented filters
        print("🎯 Applying Novelty Wealth–specific filters...")
        df_filtered = personas_df_raw.copy()

        # Focus on working-age adults 25-55
        if "age" in df_filtered.columns:
            df_filtered = df_filtered[(df_filtered["age"] >= 25) & (df_filtered["age"] <= 55)]

        # Prefer metro / tier-1 / tier-2 cities (wealth & investing context)
        tier_cities = [
            "bangalore",
            "bengaluru",
            "mumbai",
            "delhi",
            "gurgaon",
            "noida",
            "hyderabad",
            "pune",
            "chennai",
            "kolkata",
            "ahmedabad",
            "surat",
        ]
        for city_col in ["city", "district", "location"]:
            if city_col in df_filtered.columns:
                df_filtered = df_filtered[
                    df_filtered[city_col].str.lower().isin(tier_cities)
                ]
                break

        # Ensure we have at least n_personas
        if len(df_filtered) < n_personas:
            print(
                f"   ⚠️  Only {len(df_filtered)} personas match Novelty Wealth filters, "
                "using all available and supplementing from the raw sample."
            )
            if len(df_filtered) == 0:
                df_filtered = personas_df_raw.head(n_personas)
            else:
                remaining_needed = n_personas - len(df_filtered)
                if remaining_needed > 0:
                    supplement = personas_df_raw.drop(df_filtered.index).sample(
                        n=min(remaining_needed, len(personas_df_raw.drop(df_filtered.index))),
                        random_state=seed,
                    )
                    df_filtered = pd.concat([df_filtered, supplement]).head(n_personas)
        else:
            df_filtered = df_filtered.head(n_personas)

        print(f"   ✅ Using {len(df_filtered)} personas for simulation")

        # 3) Derive behavioral & psychographic features
        df_filtered = derive_all_features(df_filtered, verbose=False)

        # 4) Infer intent distribution for a wealth / investing product
        print("🎯 Inferring intent distribution for wealth product...")
        try:
            first_step = list(NOVELTY_WEALTH_STEPS.values())[0]
            entry_text = first_step.get("description", "")

            intent_result = infer_intent_distribution(
                entry_page_text=entry_text,
                product_type="fintech",  # wealth/investing is still fintech
                persona_attributes={"intent": "medium", "wealth_focus": "high"},
                product_steps=NOVELTY_WEALTH_STEPS,
            )
            intent_distribution = intent_result["intent_distribution"]
            print(
                f"   Primary Intent: {intent_result.get('primary_intent', 'build_wealth_over_time')}"
            )
        except Exception as e:
            print(f"   ⚠️  Could not infer intent, using default: {e}")
            intent_distribution = {
                "build_wealth_over_time": 0.5,
                "save_for_goals": 0.3,
                "optimize_existing_investments": 0.2,
            }

        # 5) Run intent-aware simulation
        print("🧠 Running intent-aware simulation with enhanced engine...")
        result_df = run_intent_aware_simulation(
            df_filtered,
            product_steps=NOVELTY_WEALTH_STEPS,
            intent_distribution=intent_distribution,
            verbose=False,
            seed=seed,
        )
        print(f"   ✅ Simulation complete with {len(result_df)} persona rows")

        # 6) Convert simulation output into DecisionTrace objects
        print("📊 Generating decision traces from simulation...")
        traces: List[DecisionTrace] = []
        step_names = list(NOVELTY_WEALTH_STEPS.keys())

        # We use the dominant exit step (like Currently) to create one DROP trace per persona
        for idx, row in result_df.iterrows():
            exit_step = row.get("dominant_exit_step") or "Landing & Promise (ss1)"
            try:
                step_index = step_names.index(exit_step) if exit_step in step_names else 0
            except ValueError:
                step_index = 0

            # Try to pull a representative trajectory for cognitive/intent snapshot
            trajs = row.get("trajectories", [])
            traj = trajs[0] if trajs else {}
            final_state = traj.get("final_state", {})
            intent_info = {}
            if traj:
                # Each trajectory has a fixed intent_id and alignment info per step;
                # for now we just use the global intent_id and an average alignment.
                intent_info["intent_id"] = traj.get("intent_id", "build_wealth_over_time")
                # Best-effort: use alignment from the last step in the journey
                journey = traj.get("journey", [])
                if journey:
                    intent_info["alignment_score"] = journey[-1].get("intent_alignment", 0.6)
                else:
                    intent_info["alignment_score"] = 0.6

            trace = DecisionTrace(
                persona_id=str(row.get("uuid", f"persona_{idx}")),
                step_id=exit_step,
                step_index=step_index,
                decision=DecisionOutcome.DROP,
                probability_before_sampling=0.4,
                sampled_outcome=False,
                cognitive_state_snapshot=CognitiveStateSnapshot(
                    energy=final_state.get("cognitive_energy", 0.5),
                    risk=final_state.get("perceived_risk", 0.5),
                    effort=final_state.get("perceived_effort", 0.5),
                    value=final_state.get("perceived_value", 0.5),
                    control=final_state.get("perceived_control", 0.5),
                ),
                intent=IntentSnapshot(
                    inferred_intent=intent_info.get("intent_id", "build_wealth_over_time"),
                    alignment_score=intent_info.get("alignment_score", 0.6),
                ),
                dominant_factors=["value_perception", "risk_perception"],
            )
            traces.append(trace)

            if len(traces) >= n_personas:
                break

        if len(traces) < n_personas:
            print(
                f"   ⚠️  Only {len(traces)} traces generated, supplementing with fallback traces..."
            )
            fallback_needed = n_personas - len(traces)
            traces.extend(create_fallback_traces(num_traces=fallback_needed, seed=seed + 1))

        print(f"   ✅ Generated {len(traces)} decision traces")
        return traces

    except Exception as e:
        print(f"❌ Error running persona-backed simulation: {e}")
        import traceback

        traceback.print_exc()
        print("   Falling back to synthetic traces...")
        return create_fallback_traces(num_traces=n_personas, seed=seed)


def main():
    print("\n" + "=" * 70)
    print("NOVELTY WEALTH - ONBOARDING / DECISION FLOW ANALYSIS")
    print("=" * 70)

    parser = argparse.ArgumentParser(
        description="Run Novelty Wealth decision simulation and generate Decision Autopsy output."
    )
    parser.add_argument(
        "-n",
        "--n_personas",
        type=int,
        default=1000,
        help="Number of synthetic personas to simulate (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    n_personas = args.n_personas
    print(
        "\n🎯 Target Persona: Users exploring wealth-building / investing products, mid-funnel,"
        " comparing options and sensitive to risk vs. returns."
    )
    print(f"📊 Running simulation with {n_personas} personas (seed={args.seed})...")

    traces = run_simulation_and_generate_traces(
        n_personas=n_personas, seed=args.seed
    )
    if not traces:
        print("❌ No traces generated. Exiting.")
        sys.exit(1)

    # Generate decision autopsy
    print("\n📋 Generating decision autopsy results...")
    generator = NoveltyWealthResultGenerator(
        product_steps=NOVELTY_WEALTH_STEPS,
        product_name="NOVELTY_WEALTH",
        product_full_name="Novelty Wealth - Investing & Wealth Building",
    )

    # Store traces so wealth-specific generator can use real drop points
    generator._current_traces = traces

    autopsy = generator.generate(traces)

    # Save to JSON
    output_file = "NOVELTY_WEALTH_DECISION_AUTOPSY_RESULT.json"
    with open(output_file, "w") as f:
        json.dump(autopsy, f, indent=2)

    print(f"\n✅ Decision autopsy saved to {output_file}")

    # Print concise summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Product: Novelty Wealth")
    print(f"Personas Simulated: {len(traces)}")
    print(f"Core Verdict: {autopsy.get('verdict', 'N/A')}")
    if "beliefBreak" in autopsy:
        print(
            f"Belief Break: {autopsy['beliefBreak'].get('irreversibleAction', 'N/A')}"
        )
    if "oneBet" in autopsy:
        print(f"One Bet: {autopsy['oneBet'].get('headline', 'N/A')}")
    print("=" * 70)

    return autopsy


if __name__ == "__main__":
    main()

