#!/usr/bin/env python3
"""
Run drift monitoring for Credigo SS.

Monitors model health by detecting drift between current predictions
and historical baseline.
"""

import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibration.model_health_monitor import ModelHealthMonitor
from calibration.real_world_calibration import get_default_parameters


def main():
    print("\n" + "=" * 80)
    print("MODEL HEALTH MONITORING: Credigo SS")
    print("=" * 80)
    
    try:
        # Import dependencies
        from load_dataset import load_and_sample
        from derive_features import derive_all_features
        from behavioral_engine_improved import run_behavioral_simulation_improved
        from credigo_ss_steps_improved import CREDIGO_SS_11_STEPS
        from calibration.loss_functions import extract_simulated_metrics_from_results
        from entry_model import estimate_entry_probability
        
        # Load personas
        print("\n📂 Loading dataset...")
        n_personas = 500
        df, _ = load_and_sample(n=n_personas, seed=42, verbose=False)
        print(f"   Loaded {len(df)} personas")
        
        print("\n🔧 Deriving features...")
        df = derive_all_features(df, verbose=False)
        print(f"   Derived features")
        
        # Initialize monitor
        baseline_file = 'credigo_ss_baseline.json'
        monitor = ModelHealthMonitor(
            baseline_file=baseline_file if __import__('os').path.exists(baseline_file) else None,
            threshold_warning=5.0,
            threshold_critical=15.0
        )
        
        # Check if baseline exists
        if monitor.baseline is None:
            print("\n📊 Creating baseline from current simulation...")
            print("   (This will be used as the reference for future drift detection)")
            
            # Try to load calibrated parameters if they exist (preferred for baseline)
            baseline_params = get_default_parameters()
            try:
                import json
                with open('credigo_ss_calibration_summary.json', 'r') as f:
                    calib_data = json.load(f)
                    baseline_params = calib_data.get('calibrated_parameters', baseline_params)
                    print("   ✓ Using calibrated parameters for baseline")
            except FileNotFoundError:
                print("   ℹ️  Using default parameters for baseline (no calibration found)")
            
            # Run simulation with baseline parameters
            from calibration.calibrator import run_simulation_with_parameters
            import numpy as np
            np.random.seed(42)  # Ensure reproducibility
            result_df = run_simulation_with_parameters(
                baseline_params,
                run_behavioral_simulation_improved,
                {
                    'df': df,
                    'verbose': False,
                    'product_steps': CREDIGO_SS_11_STEPS,
                    'seed': 42
                },
                engine_module='behavioral_engine_improved'
            )
            
            # Extract metrics
            simulated_metrics = extract_simulated_metrics_from_results(
                result_df,
                CREDIGO_SS_11_STEPS
            )
            
            # Get entry probability
            entry_signals = {
                'referrer': 'direct',
                'intent_frame': {'commitment_threshold': 0.7},
                'landing_page_text': 'Find the Best Credit Card In 60 seconds'
            }
            entry_result = estimate_entry_probability(**entry_signals)
            # Apply entry scale if present
            entry_scale = baseline_params.get('ENTRY_PROBABILITY_SCALE', 1.0)
            entry_rate = np.clip(entry_result.entry_probability * entry_scale, 0.01, 0.95)
            completion_rate = simulated_metrics.get('completion_rate', 0.0)
            total_conversion = entry_rate * completion_rate
            
            # Create baseline
            baseline = monitor.create_baseline_from_simulation(
                entry_rate=entry_rate,
                completion_rate=completion_rate,
                total_conversion=total_conversion,
                step_completion_rates=simulated_metrics.get('step_completion_rates', {}),
                parameters=baseline_params,
                dropoff_distribution=simulated_metrics.get('dropoff_by_step', {}),
                sample_size=n_personas
            )
            
            # Save baseline
            monitor.save_baseline(baseline, baseline_file)
            print(f"   ✓ Baseline saved to {baseline_file}")
            print(f"   Entry rate: {entry_rate:.2%}")
            print(f"   Completion rate: {completion_rate:.2%}")
            print(f"   Total conversion: {total_conversion:.2%}")
            
            print("\n✅ Baseline created. Run this script again to monitor drift.")
            return
        
        # Baseline exists - monitor drift
        print(f"\n📊 Monitoring drift against baseline from {monitor.baseline.timestamp}")
        
        # Get current parameters (could be calibrated) - must be before simulation
        current_params = get_default_parameters()
        
        # Try to load calibrated parameters if they exist
        try:
            import json
            with open('credigo_ss_calibration_summary.json', 'r') as f:
                calib_data = json.load(f)
                current_params = calib_data.get('calibrated_parameters', current_params)
                print("\n🔄 Running current simulation...")
                print("   ✓ Using calibrated parameters")
        except FileNotFoundError:
            print("\n🔄 Running current simulation...")
            print("   ℹ️  Using default parameters (no calibration found)")
        
        # Run current simulation with current parameters
        from calibration.calibrator import run_simulation_with_parameters
        import numpy as np
        np.random.seed(42)  # Ensure reproducibility
        result_df = run_simulation_with_parameters(
            current_params,
            run_behavioral_simulation_improved,
            {
                'df': df,
                'verbose': False,
                'product_steps': CREDIGO_SS_11_STEPS,
                'seed': 42
            },
            engine_module='behavioral_engine_improved'
        )
        
        # Extract current metrics
        current_metrics = extract_simulated_metrics_from_results(
            result_df,
            CREDIGO_SS_11_STEPS
        )
        
        # Get current entry probability
        entry_signals = {
            'referrer': 'direct',
            'intent_frame': {'commitment_threshold': 0.7},
            'landing_page_text': 'Find the Best Credit Card In 60 seconds'
        }
        entry_result = estimate_entry_probability(**entry_signals)
        # Apply entry scale if present in current parameters
        entry_scale = current_params.get('ENTRY_PROBABILITY_SCALE', 1.0)
        current_entry_rate = np.clip(entry_result.entry_probability * entry_scale, 0.01, 0.95)
        current_completion_rate = current_metrics.get('completion_rate', 0.0)
        current_total_conversion = current_entry_rate * current_completion_rate
        
        # Monitor drift
        print("\n🔍 Detecting drift...")
        report = monitor.monitor_drift(
            current_entry_rate=current_entry_rate,
            current_completion_rate=current_completion_rate,
            current_total_conversion=current_total_conversion,
            current_step_completion_rates=current_metrics.get('step_completion_rates', {}),
            current_parameters=current_params,
            current_dropoff_distribution=current_metrics.get('dropoff_by_step', {})
        )
        
        # Print report
        monitor.print_drift_report(report)
        
        # Export report
        report_file = 'credigo_ss_drift_report.json'
        monitor.export_drift_report(report, report_file)
        print(f"\n💾 Drift report exported to: {report_file}")
        
        return report
        
    except Exception as e:
        print(f"\n❌ Error during drift monitoring: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

