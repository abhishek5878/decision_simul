"""
simulation_pipeline.py - Canonical Execution Pipeline

This is the ONLY supported entry point for running simulations.
All other execution paths are deprecated.

Usage:
    from simulation_pipeline import run_simulation
    
    result = run_simulation(
        product_config="credigo",
        data_source="default",
        mode="production"
    )
"""

import json
import numpy as np
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import warnings

# ============================================================================
# CANONICAL ENGINE SELECTION
# ============================================================================

CANONICAL_ENGINE = "behavioral_engine_intent_aware"

# Deprecated engines - should not be used directly
DEPRECATED_ENGINES = [
    "behavioral_engine",
    "behavioral_engine_improved",
    "behavioral_engine_semantic_aware",
    "behavioral_engine_stabilized"
]


# ============================================================================
# EXECUTION MODES
# ============================================================================

ExecutionMode = Literal["research", "evaluation", "production"]


# ============================================================================
# PIPELINE STAGES
# ============================================================================

@dataclass
class PipelineResult:
    """
    Unified output from canonical pipeline.
    
    NOW DECISION-FIRST (not metrics-first).
    This enables answering:
    - "Which user types does this product work for?"
    - "Which user types does it reject?"
    - "What decisions caused that outcome?"
    """
    entry: Dict
    behavioral: Dict
    intent: Dict
    calibration: Optional[Dict]
    evaluation: Optional[Dict]
    drift: Optional[Dict]
    final_metrics: Dict
    # NEW: Decision-first data
    decision_traces: Optional[List[Dict]] = None  # List of DecisionTrace dicts
    context_graph_summary: Optional[Dict] = None  # Context graph summary
    model_version: str = "v1.0"
    execution_mode: str = "production"
    timestamp: str = ""
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        import numpy as np
        
        def convert_numpy_types(obj):
            """Recursively convert numpy types to native Python types."""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        result = {
            'entry': convert_numpy_types(self.entry),
            'behavioral': convert_numpy_types(self.behavioral),
            'intent': convert_numpy_types(self.intent),
            'calibration': convert_numpy_types(self.calibration) if self.calibration else None,
            'evaluation': convert_numpy_types(self.evaluation) if self.evaluation else None,
            'drift': convert_numpy_types(self.drift) if self.drift else None,
            'final_metrics': convert_numpy_types(self.final_metrics),
            'model_version': self.model_version,
            'execution_mode': self.execution_mode,
            'timestamp': self.timestamp
        }
        # Add decision-first data if available
        if self.decision_traces is not None:
            result['decision_traces'] = convert_numpy_types(self.decision_traces)
        if self.context_graph_summary is not None:
            result['context_graph_summary'] = convert_numpy_types(self.context_graph_summary)
        return result
    
    def export(self, filepath: str = 'simulation_result.json'):
        """Export to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        return filepath


# ============================================================================
# CANONICAL PIPELINE
# ============================================================================

def run_simulation(
    product_config: str,
    data_source: str = "default",
    mode: ExecutionMode = "production",
    n_personas: int = 1000,
    seed: int = 42,
    calibration_file: Optional[str] = None,
    baseline_file: Optional[str] = None,
    verbose: bool = True
) -> PipelineResult:
    """
    Canonical simulation pipeline - THE ONLY WAY TO RUN SIMULATIONS.
    
    Args:
        product_config: Product identifier ("credigo", "blink_money", etc.)
        data_source: Data source identifier
        mode: Execution mode ("research", "evaluation", "production")
        n_personas: Number of personas to simulate
        seed: Random seed for reproducibility
        calibration_file: Path to calibration summary JSON (optional)
        baseline_file: Path to baseline JSON for drift monitoring (optional)
        verbose: Print progress
    
    Returns:
        PipelineResult with all outputs
    
    Raises:
        ValueError: If invariants are violated
        RuntimeError: If pipeline stage fails
    """
    if verbose:
        print("\n" + "=" * 80)
        print("CANONICAL SIMULATION PIPELINE")
        print("=" * 80)
        print(f"Product: {product_config}")
        print(f"Mode: {mode}")
        print(f"Engine: {CANONICAL_ENGINE}")
        print(f"Personas: {n_personas}")
        print("=" * 80)
    
    # ========================================================================
    # STAGE 1: Load Product + Persona Data
    # ========================================================================
    if verbose:
        print("\n[1/7] Loading product and persona data...")
    
    product_steps = _load_product_config(product_config)
    df, derived = _load_persona_data(n_personas, seed, data_source)
    
    if verbose:
        print(f"   ✓ Loaded {len(df)} personas")
        print(f"   ✓ Loaded {len(product_steps)} product steps")
    
    # ========================================================================
    # STAGE 2: Run Entry Model
    # ========================================================================
    if verbose:
        print("\n[2/7] Running entry model...")
    
    entry_result = _run_entry_model(product_config, product_steps, verbose)
    entry_probability = entry_result.get('entry_probability', 0.5)
    
    if verbose:
        print(f"   ✓ Entry probability: {entry_probability:.2%}")
    
    # ========================================================================
    # STAGE 3: Run Behavioral + Intent Engine (CANONICAL ONLY)
    # ========================================================================
    if verbose:
        print(f"\n[3/7] Running behavioral engine ({CANONICAL_ENGINE})...")
    
    behavioral_result = _run_canonical_engine(
        df, derived, product_steps, entry_probability, seed, verbose, product_config
    )
    
    completion_rate = behavioral_result.get('completion_rate', 0.0)
    total_conversion = entry_probability * completion_rate
    
    if verbose:
        print(f"   ✓ Completion rate: {completion_rate:.2%}")
        print(f"   ✓ Total conversion: {total_conversion:.2%}")
    
    # ========================================================================
    # STAGE 4: Apply Calibrated Parameters (if available)
    # ========================================================================
    calibration_data = None
    if mode in ["evaluation", "production"]:
        if verbose:
            print("\n[4/7] Applying calibrated parameters...")
        
        calibration_data = _apply_calibration(
            calibration_file, product_config, verbose
        )
        
        if calibration_data:
            # Re-run behavioral engine with calibrated parameters
            behavioral_result = _run_canonical_engine(
                df, derived, product_steps, entry_probability, seed, verbose,
                product_config, parameters=calibration_data.get('calibrated_parameters')
            )
            completion_rate = behavioral_result.get('completion_rate', 0.0)
            total_conversion = entry_probability * completion_rate
            
            if verbose:
                print(f"   ✓ Applied calibrated parameters")
                print(f"   ✓ Re-computed completion: {completion_rate:.2%}")
    else:
        if verbose:
            print("\n[4/7] Skipping calibration (research mode)")
    
    # ========================================================================
    # STAGE 5: Compute Full Funnel Metrics
    # ========================================================================
    if verbose:
        print("\n[5/7] Computing full funnel metrics...")
    
    final_metrics = _compute_final_metrics(
        entry_probability, behavioral_result, product_steps
    )
    
    if verbose:
        print(f"   ✓ Entry rate: {final_metrics['entry_rate']:.2%}")
        print(f"   ✓ Completion rate: {final_metrics['completion_rate']:.2%}")
        print(f"   ✓ Total conversion: {final_metrics['total_conversion']:.2%}")
    
    # ========================================================================
    # STAGE 6: Run Evaluation (if mode allows)
    # ========================================================================
    evaluation_data = None
    if mode in ["evaluation", "production"]:
        if verbose:
            print("\n[6/7] Running evaluation...")
        
        evaluation_data = _run_evaluation(
            df, derived, product_steps, entry_probability, seed, verbose, product_config
        )
        
        if verbose:
            if evaluation_data:
                print(f"   ✓ Confidence intervals computed")
                print(f"   ✓ Sensitivity analysis complete")
    else:
        if verbose:
            print("\n[6/7] Skipping evaluation (research mode)")
    
    # ========================================================================
    # STAGE 7: Run Drift Monitoring (production only)
    # ========================================================================
    drift_data = None
    if mode == "production":
        if verbose:
            print("\n[7/7] Running drift monitoring...")
        
        drift_data = _run_drift_monitoring(
            entry_probability, behavioral_result, calibration_data,
            baseline_file, product_config, verbose
        )
        
        if verbose:
            if drift_data:
                status = drift_data.get('overall_status', 'unknown')
                print(f"   ✓ Drift status: {status}")
            else:
                print(f"   ℹ️  No baseline found (skipping drift check)")
    else:
        if verbose:
            print("\n[7/7] Skipping drift monitoring (not production mode)")
    
    # ========================================================================
    # Build Unified Output (NOW DECISION-FIRST)
    # ========================================================================
    result = PipelineResult(
        entry=entry_result,
        behavioral=behavioral_result,
        intent=behavioral_result.get('intent_analysis', {}),
        calibration=calibration_data,
        evaluation=evaluation_data,
        drift=drift_data,
        final_metrics=final_metrics,
        # NEW: Decision-first data
        decision_traces=behavioral_result.get('decision_traces'),
        context_graph_summary=behavioral_result.get('context_graph_summary'),
        model_version="v1.0",
        execution_mode=mode,
        timestamp=datetime.now().isoformat()
    )
    
    if verbose:
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Mode: {mode}")
        print(f"Entry rate: {final_metrics['entry_rate']:.2%}")
        print(f"Completion rate: {final_metrics['completion_rate']:.2%}")
        print(f"Total conversion: {final_metrics['total_conversion']:.2%}")
        if drift_data:
            print(f"Drift status: {drift_data.get('overall_status', 'unknown')}")
        print("=" * 80)
    
    return result


# ============================================================================
# PIPELINE STAGE IMPLEMENTATIONS
# ============================================================================

def _get_fixed_intent_for_product(product_config: str):
    """
    Get fixed intent for product (helper to avoid duplication).
    
    This function is used by both _run_canonical_engine and _run_evaluation.
    """
    # Try to get product-specific intent
    if product_config in ["credigo", "credigo_ss"]:
        try:
            from dropsim_intent_model import CREDIGO_GLOBAL_INTENT
            return CREDIGO_GLOBAL_INTENT
        except ImportError:
            pass
    elif product_config == "keeper":
        try:
            from dropsim_intent_model import KEEPER_SS_GLOBAL_INTENT
            return KEEPER_SS_GLOBAL_INTENT
        except ImportError:
            pass
    elif product_config == "trial1":
        try:
            from dropsim_intent_model import TRIAL1_GLOBAL_INTENT
            return TRIAL1_GLOBAL_INTENT
        except ImportError:
            pass
    
    # Fallback: create generic intent frame
    from dropsim_intent_model import IntentFrame
    return IntentFrame(
        intent_id="generic_recommendation",
        description="User wants product recommendations",
        primary_goal="get_recommendations",
        commitment_threshold=0.7,
        tolerance_for_effort=0.6,
        tolerance_for_risk=0.5,
        expected_value_type="comparison",
        expected_reward="Product recommendations",
        acceptable_friction=0.5,
        typical_exit_triggers=["Too much friction", "Unclear value"],
        expected_completion_behavior="Evaluates options and decides"
    )


def _load_product_config(product_config: str) -> Dict:
    """Load product configuration."""
    product_configs = {
        "credigo": "credigo_ss_steps_improved",
        "credigo_ss": "credigo_ss_steps_improved",
        "blink_money": "blink_money_steps",
        "keeper": "keeper_ss_steps",
        "trial1": "trial1_steps"
    }
    
    if product_config not in product_configs:
        raise ValueError(f"Unknown product config: {product_config}")
    
    module_name = product_configs[product_config]
    
    # Import product steps
    if module_name == "credigo_ss_steps_improved":
        from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
        return CREDIGO_SS_11_STEPS
    elif module_name == "blink_money_steps":
        from blink_money_steps import BLINK_MONEY_STEPS
        return BLINK_MONEY_STEPS
    elif module_name == "keeper_ss_steps":
        from keeper_ss_steps import KEEPER_SS_STEPS
        return KEEPER_SS_STEPS
    elif module_name == "trial1_steps":
        from trial1_steps import TRIAL1_STEPS
        return TRIAL1_STEPS
    else:
        raise ValueError(f"Unknown product steps module: {module_name}")


def _load_persona_data(n_personas: int, seed: int, data_source: str):
    """Load persona data."""
    from load_dataset import load_and_sample
    from derive_features import derive_all_features
    
    df, _ = load_and_sample(n=n_personas, seed=seed, verbose=False)
    df = derive_all_features(df, verbose=False)
    
    # Extract derived features dict for compatibility
    derived = {}  # Could extract if needed
    
    return df, derived


def _run_entry_model(product_config: str, product_steps: Dict, verbose: bool) -> Dict:
    """Run entry model."""
    from entry_model import estimate_entry_probability
    
    # Get first step for entry signals
    first_step = list(product_steps.values())[0]
    landing_page_text = first_step.get('description', '')
    cta_text = first_step.get('cta_phrasing', '')
    
    # Default entry signals (can be customized per product)
    entry_signals = {
        'referrer': 'direct',
        'intent_frame': {'commitment_threshold': 0.7, 'tolerance_for_effort': 0.6},
        'landing_page_text': landing_page_text or cta_text
    }
    
    result = estimate_entry_probability(**entry_signals)
    
    return {
        'entry_probability': result.entry_probability,
        'confidence': result.confidence,
        'drivers': result.drivers,
        'signals': {
            'traffic_source': result.signals.traffic_source.value,
            'intent_strength': result.signals.intent_strength.value,
            'promise_strength': result.signals.landing_page_promise_strength
        }
    }


def _run_canonical_engine(
    df, derived, product_steps: Dict,
    entry_probability: float,
    seed: int,
    verbose: bool,
    product_config: str = "credigo",
    parameters: Optional[Dict] = None
) -> Dict:
    """Run canonical behavioral engine (ONLY behavioral_engine_intent_aware)."""
    # ENFORCE: Only canonical engine allowed
    if CANONICAL_ENGINE != "behavioral_engine_intent_aware":
        raise RuntimeError(f"Canonical engine mismatch: {CANONICAL_ENGINE}")
    
    from behavioral_engine_intent_aware import run_intent_aware_simulation
    
    # Use fixed global intent for consistency (can be customized per product)
    fixed_intent = _get_fixed_intent_for_product(product_config)
    
    # Apply calibrated parameters if provided
    if parameters:
        from calibration.calibrator import inject_parameters_into_engine
        with inject_parameters_into_engine(parameters, 'behavioral_engine_intent_aware'):
            result_df = run_intent_aware_simulation(
                df,
                product_steps=product_steps,
                fixed_intent=fixed_intent,
                verbose=False,
                seed=seed
            )
    else:
        result_df = run_intent_aware_simulation(
            df,
            product_steps=product_steps,
            fixed_intent=fixed_intent,
            verbose=False,
            seed=seed
        )
    
    # Extract metrics
    from calibration.loss_functions import extract_simulated_metrics_from_results
    
    metrics = extract_simulated_metrics_from_results(result_df, product_steps)
    
    # Get intent analysis
    intent_analysis = {}
    try:
        from dropsim_intent_analysis import generate_intent_analysis
        intent_analysis = generate_intent_analysis(result_df, product_steps)
        # Convert to dict if needed
        if hasattr(intent_analysis, 'to_dict'):
            intent_analysis = intent_analysis.to_dict()
    except:
        pass
    
    # NEW: Build decision sequences and context graph from traces
    decision_traces_all = []
    decision_sequences = []
    context_graph_summary = None
    
    try:
        from decision_graph.decision_trace import DecisionSequence, DecisionOutcome, DecisionTrace
        from decision_graph.context_graph import build_context_graph_from_traces, ContextGraphSummary
        
        # Collect traces from trajectories (they're stored in 'trajectories' column)
        if 'trajectories' in result_df.columns:
            for idx, row in result_df.iterrows():
                trajectories = row.get('trajectories', [])
                
                # Each trajectory has decision_traces and other info
                for traj in trajectories:
                    traces = traj.get('decision_traces', [])
                    persona_id = traj.get('persona_id', f"persona_{idx}")
                    variant_name = traj.get('variant', 'default')
                    
                    if traces:
                        # Convert DecisionTrace objects to dicts if needed
                        trace_dicts = []
                        for trace in traces:
                            if hasattr(trace, 'to_dict'):
                                trace_dict = trace.to_dict()
                                trace_dicts.append(trace_dict)
                                decision_traces_all.append(trace_dict)
                            elif isinstance(trace, dict):
                                trace_dicts.append(trace)
                                decision_traces_all.append(trace)
                        
                        # Convert back to DecisionTrace objects for sequence building
                        trace_objects = [DecisionTrace.from_dict(td) for td in trace_dicts]
                        
                        # Determine final outcome
                        final_outcome = DecisionOutcome.CONTINUE if traj.get('completed', False) else DecisionOutcome.DROP
                        exit_step = traj.get('exit_step', None)
                        
                        # Build sequence
                        sequence = DecisionSequence(
                            persona_id=persona_id,
                            variant_name=variant_name,
                            traces=trace_objects,
                            final_outcome=final_outcome,
                            exit_step=exit_step
                        )
                        decision_sequences.append(sequence)
        
        # Build context graph from sequences
        if decision_sequences:
            context_graph = build_context_graph_from_traces(decision_sequences, product_steps)
            context_graph_summary = ContextGraphSummary(
                dominant_failure_paths=context_graph.dominant_failure_paths,
                persona_step_rejection_map=context_graph.persona_step_rejection_map,
                repeated_precedents=context_graph.repeated_precedents,
                total_nodes=len(context_graph.nodes),
                total_edges=len(context_graph.edges)
            ).to_dict()
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Warning: Could not build context graph: {e}")
            import traceback
            traceback.print_exc()
        # Continue without graph
    
    return {
        'completion_rate': metrics.get('completion_rate', 0.0),
        'step_completion_rates': metrics.get('step_completion_rates', {}),
        'dropoff_by_step': metrics.get('dropoff_by_step', {}),
        'avg_steps_completed': metrics.get('avg_steps_completed', 0.0),
        'intent_analysis': intent_analysis,
        'result_dataframe': None,  # Don't include full DF in output
        # NEW: Decision-first data
        'decision_traces': decision_traces_all if decision_traces_all else None,
        'context_graph_summary': context_graph_summary
    }


def _apply_calibration(
    calibration_file: Optional[str],
    product_config: str,
    verbose: bool
) -> Optional[Dict]:
    """Apply calibrated parameters if available."""
    # Try to find calibration file
    if calibration_file and Path(calibration_file).exists():
        calib_path = calibration_file
    else:
        # Try default location
        default_path = f'{product_config}_calibration_summary.json'
        if Path(default_path).exists():
            calib_path = default_path
        else:
            if verbose:
                print(f"   ℹ️  No calibration file found (using defaults)")
            return None
    
    try:
        with open(calib_path, 'r') as f:
            calibration_data = json.load(f)
        return calibration_data
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Error loading calibration: {e}")
        return None


def _compute_final_metrics(
    entry_probability: float,
    behavioral_result: Dict,
    product_steps: Dict
) -> Dict:
    """Compute final funnel metrics."""
    completion_rate = behavioral_result.get('completion_rate', 0.0)
    total_conversion = entry_probability * completion_rate
    
    return {
        'entry_rate': entry_probability,
        'completion_rate': completion_rate,
        'total_conversion': total_conversion,
        'step_completion_rates': behavioral_result.get('step_completion_rates', {}),
        'dropoff_by_step': behavioral_result.get('dropoff_by_step', {})
    }


def _run_evaluation(
    df, derived, product_steps: Dict,
    entry_probability: float,
    seed: int,
    verbose: bool,
    product_config: str = "credigo"
) -> Optional[Dict]:
    """Run evaluation (confidence, sensitivity, stability)."""
    try:
        from calibration.evaluator import evaluate_model
        from behavioral_engine_intent_aware import run_intent_aware_simulation
        
        # Use the product's fixed intent instead of creating a new one
        fixed_intent = _get_fixed_intent_for_product(product_config)
        
        def simulation_fn(df, seed):
            return run_intent_aware_simulation(
                df, product_steps=product_steps, fixed_intent=fixed_intent,
                verbose=False, seed=seed
            )
        
        evaluation_report = evaluate_model(
            simulation_function=simulation_fn,
            simulation_args={'df': df, 'seed': seed},
            product_steps=product_steps,
            n_simulations=10,  # Reduced for speed
            verbose=False
        )
        
        return evaluation_report.to_dict() if hasattr(evaluation_report, 'to_dict') else {}
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Evaluation failed: {e}")
        return None


def _run_drift_monitoring(
    entry_probability: float,
    behavioral_result: Dict,
    calibration_data: Optional[Dict],
    baseline_file: Optional[str],
    product_config: str,
    verbose: bool
) -> Optional[Dict]:
    """Run drift monitoring (production mode only)."""
    try:
        from calibration.model_health_monitor import ModelHealthMonitor
        
        # Try to find baseline file
        if baseline_file and Path(baseline_file).exists():
            baseline_path = baseline_file
        else:
            default_path = f'{product_config}_baseline.json'
            if Path(default_path).exists():
                baseline_path = default_path
            else:
                if verbose:
                    print(f"   ℹ️  No baseline file found (skipping drift check)")
                return None
        
        monitor = ModelHealthMonitor(baseline_file=baseline_path)
        
        if monitor.baseline is None:
            if verbose:
                print(f"   ℹ️  Baseline not loaded (skipping drift check)")
            return None
        
        # Get current parameters
        current_params = {}
        if calibration_data:
            current_params = calibration_data.get('calibrated_parameters', {})
        
        # Monitor drift
        drift_report = monitor.monitor_drift(
            current_entry_rate=entry_probability,
            current_completion_rate=behavioral_result.get('completion_rate', 0.0),
            current_total_conversion=entry_probability * behavioral_result.get('completion_rate', 0.0),
            current_step_completion_rates=behavioral_result.get('step_completion_rates', {}),
            current_parameters=current_params,
            current_dropoff_distribution=behavioral_result.get('dropoff_by_step', {})
        )
        
        return drift_report.to_dict()
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Drift monitoring failed: {e}")
        return None


# ============================================================================
# DEPRECATION WARNINGS
# ============================================================================

def _check_deprecated_import(module_name: str):
    """Check if deprecated module is being imported."""
    if any(dep in module_name for dep in DEPRECATED_ENGINES):
        warnings.warn(
            f"⚠️  {module_name} is DEPRECATED. Use simulation_pipeline.run_simulation() instead.",
            DeprecationWarning,
            stacklevel=2
        )

