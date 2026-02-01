#!/usr/bin/env python3
"""
Quick verification script to check Context Graph implementation

This script verifies that:
1. Context Graph module is importable
2. All required functions exist
3. Data structures are correct
4. Integration points are in place
"""

import sys

def verify_imports():
    """Verify all required modules can be imported."""
    print("🔍 Verifying imports...")
    try:
        from dropsim_context_graph import (
            Event, EventTrace, ContextGraph,
            StepNode, EdgeStats,
            build_context_graph,
            get_most_common_paths,
            get_highest_loss_transitions,
            get_most_fragile_steps,
            get_paths_leading_to_drop,
            get_successful_paths,
            summarize_context_graph
        )
        print("   ✅ All Context Graph imports successful")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def verify_data_structures():
    """Verify data structures match spec."""
    print("\n🔍 Verifying data structures...")
    from dropsim_context_graph import Event, EventTrace, ContextGraph
    
    # Check Event
    try:
        event = Event(
            step_id="test_step",
            persona_id="test_persona",
            variant_id="test_variant",
            state_before={"cognitive_energy": 0.8},
            state_after={"cognitive_energy": 0.7},
            cost_components={"cognitive_cost": 0.1},
            decision="continue",
            dominant_factor="none",
            timestep=0
        )
        assert hasattr(event, 'cost_components'), "Event missing cost_components"
        assert hasattr(event, 'timestep'), "Event missing timestep"
        assert event.timestep == 0, "Event timestep incorrect"
        print("   ✅ Event dataclass correct")
    except Exception as e:
        print(f"   ❌ Event verification failed: {e}")
        return False
    
    # Check EventTrace
    try:
        trace = EventTrace(
            persona_id="test_persona",
            variant_id="test_variant",
            events=[event],
            final_outcome="completed"
        )
        assert len(trace.events) == 1, "EventTrace events incorrect"
        print("   ✅ EventTrace dataclass correct")
    except Exception as e:
        print(f"   ❌ EventTrace verification failed: {e}")
        return False
    
    # Check ContextGraph
    try:
        graph = ContextGraph(nodes={}, edges={})
        assert hasattr(graph, 'nodes'), "ContextGraph missing nodes"
        assert hasattr(graph, 'edges'), "ContextGraph missing edges"
        print("   ✅ ContextGraph dataclass correct")
    except Exception as e:
        print(f"   ❌ ContextGraph verification failed: {e}")
        return False
    
    return True

def verify_query_functions():
    """Verify all query functions exist and are callable."""
    print("\n🔍 Verifying query functions...")
    from dropsim_context_graph import (
        get_most_common_paths,
        get_highest_loss_transitions,
        get_most_fragile_steps,
        get_paths_leading_to_drop,
        get_successful_paths,
        ContextGraph
    )
    
    # Create empty graph for testing
    graph = ContextGraph(nodes={}, edges={})
    
    functions = [
        ("get_most_common_paths", get_most_common_paths),
        ("get_highest_loss_transitions", get_highest_loss_transitions),
        ("get_most_fragile_steps", get_most_fragile_steps),
        ("get_paths_leading_to_drop", get_paths_leading_to_drop),
        ("get_successful_paths", get_successful_paths),
    ]
    
    for name, func in functions:
        try:
            result = func(graph)
            assert isinstance(result, list), f"{name} should return list"
            print(f"   ✅ {name}() works correctly")
        except Exception as e:
            print(f"   ❌ {name}() failed: {e}")
            return False
    
    return True

def verify_integration():
    """Verify integration points exist."""
    print("\n🔍 Verifying integration points...")
    
    # Check simulation runner
    try:
        from dropsim_simulation_runner import run_simulation_with_database_personas
        import inspect
        source = inspect.getsource(run_simulation_with_database_personas)
        assert 'Event' in source or 'event_trace' in source, "Event capture not found in simulation runner"
        assert 'build_context_graph' in source, "build_context_graph not found in simulation runner"
        print("   ✅ Simulation runner integration verified")
    except Exception as e:
        print(f"   ❌ Simulation runner check failed: {e}")
        return False
    
    # Check wizard
    try:
        from dropsim_wizard import run_fintech_wizard
        import inspect
        source = inspect.getsource(run_fintech_wizard)
        assert 'context_graph' in source, "Context graph not found in wizard"
        print("   ✅ Wizard integration verified")
    except Exception as e:
        print(f"   ❌ Wizard check failed: {e}")
        return False
    
    return True

def main():
    print("=" * 80)
    print("🔍 CONTEXT GRAPH VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        ("Imports", verify_imports),
        ("Data Structures", verify_data_structures),
        ("Query Functions", verify_query_functions),
        ("Integration", verify_integration),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ {name} check crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All checks passed! Context Graph implementation is ready.")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

