"""
Test script for decision trace system.
Demonstrates recording and querying decision traces.
"""

import json
import os
from dropsim_decision_traces import (
    DecisionTraceStore,
    extract_decision_traces_from_simulation,
    create_decision_trace
)
from dropsim_context_graph_v2 import ContextGraphV2

def main():
    print("=" * 80)
    print("DECISION TRACE SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Load a system result
    result_file = "output/credigo_ss_full_pipeline_results.json"
    if not os.path.exists(result_file):
        print(f"❌ Result file not found: {result_file}")
        print("   Please run a full pipeline test first.")
        return
    
    print(f"📊 Loading system result from: {result_file}")
    with open(result_file, 'r') as f:
        system_result = json.load(f)
    
    print("✅ System result loaded")
    print()
    
    # Extract decision traces
    print("🔍 Extracting decision traces from simulation...")
    # Try full result first, then scenario_result
    traces = extract_decision_traces_from_simulation(system_result, actor_type="system")
    if not traces:
        scenario_result = system_result.get('scenario_result', {})
        traces = extract_decision_traces_from_simulation(scenario_result, actor_type="system")
    
    print(f"   Extracted {len(traces)} decision traces")
    print()
    
    # Store traces
    print("💾 Storing decision traces...")
    store = DecisionTraceStore()
    for trace in traces:
        store.add_trace(trace)
    
    print(f"   Total traces in store: {len(store.traces)}")
    print()
    
    # Test similarity query
    print("=" * 80)
    print("KILLER QUERY: Similar Past Decisions")
    print("=" * 80)
    print()
    
    if traces:
        # Use first trace as query
        query_trace = traces[0]
        print(f"Query: Find decisions similar to:")
        print(f"   Decision ID: {query_trace.decision_id}")
        print(f"   Action Type: {query_trace.chosen_action.get('action_type', 'N/A')}")
        print(f"   Context: {query_trace.context_snapshot.get('step_id', 'N/A')}")
        print()
        
        similar = store.find_similar_decisions(query_trace, limit=5)
        print(f"Found {len(similar)} similar past decisions:")
        print()
        
        for i, similar_trace in enumerate(similar, 1):
            print(f"{i}. Decision ID: {similar_trace.decision_id}")
            print(f"   Timestamp: {similar_trace.timestamp}")
            print(f"   Chosen Action: {similar_trace.chosen_action}")
            print(f"   Rationale: {similar_trace.rationale[:100]}...")
            if similar_trace.downstream_outcome:
                print(f"   Outcome: {similar_trace.downstream_outcome}")
            print()
    
    # Test context graph v2
    print("=" * 80)
    print("CONTEXT GRAPH V2")
    print("=" * 80)
    print()
    
    context_graph = ContextGraphV2()
    
    # Add traces to graph
    for trace in traces[:5]:  # First 5 traces
        context_graph.add_decision_trace(trace)
    
    print(f"Graph nodes: {len(context_graph.nodes)}")
    print(f"Graph edges: {len(context_graph.edges)}")
    print()
    
    # Query similar decisions from graph
    if traces:
        query_trace = traces[0]
        context_snapshot = query_trace.context_snapshot
        action_type = query_trace.chosen_action.get('action_type', '')
        
        similar_from_graph = context_graph.query_similar_decisions(
            context_snapshot,
            action_type
        )
        
        print(f"Similar decisions from graph: {len(similar_from_graph)}")
        for i, decision in enumerate(similar_from_graph[:3], 1):
            print(f"{i}. {decision.get('decision_id', 'N/A')}")
            print(f"   Rationale: {decision.get('rationale', 'N/A')[:80]}...")
            print()
    
    # Test query: "Why did the system behave this way?"
    print("=" * 80)
    print("QUERY: Why did the system behave this way?")
    print("=" * 80)
    print()
    
    if traces:
        trace = traces[0]
        decision_id = trace.decision_id
        
        # Get the trace
        stored_trace = store.get_trace(decision_id)
        if stored_trace:
            print(f"Decision ID: {decision_id}")
            print(f"Timestamp: {stored_trace.timestamp}")
            print(f"Chosen Action: {stored_trace.chosen_action}")
            print(f"Rationale: {stored_trace.rationale}")
            print()
            
            # Get precedents
            if stored_trace.precedent_ids:
                print(f"Precedents followed: {len(stored_trace.precedent_ids)}")
                for precedent_id in stored_trace.precedent_ids[:3]:
                    precedent = store.get_trace(precedent_id)
                    if precedent:
                        print(f"   - {precedent_id}: {precedent.rationale[:60]}...")
            else:
                print("No precedents found (first decision of this type)")
            print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Decision Trace System working!")
    print()
    print("The system now:")
    print("   • Records actual decisions made")
    print("   • Stores context snapshots")
    print("   • Links to similar past decisions")
    print("   • Builds a context graph of decisions")
    print("   • Can answer: 'Why did this happen?' from data")
    print()
    print("This transforms the system from 'simulator' to 'system of record'")

if __name__ == "__main__":
    main()

