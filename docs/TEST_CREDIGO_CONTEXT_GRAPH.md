# Testing Credigo with Context Graph

## Quick Test

Run the test script:

```bash
export OPENAI_API_KEY="your-key"
export FIRECRAWL_API_KEY="your-key"
python3 test_credigo_context_graph.py
```

Or use the convenience script:

```bash
./run_credigo_test.sh
```

## What the Test Does

1. **Loads Credigo Screenshots**: Reads 10 screenshots from `credigo_screenshots_ordered.txt`
2. **Runs Wizard**: 
   - Extracts product steps from screenshots
   - Loads 1000 personas from database
   - Filters by target group (21-35, tier-1/tier-2, working professionals)
3. **Runs Simulation**: 
   - Simulates each persona × 7 state variants
   - Captures event traces (state_before, state_after, costs, decisions)
4. **Builds Context Graph**:
   - Aggregates all event traces
   - Builds directed graph (nodes=steps, edges=transitions)
   - Computes path frequencies, energy deltas, failure probabilities
5. **Displays Results**:
   - Standard aggregation (failure rates per step)
   - Context Graph insights:
     - Most common paths
     - Fragile steps
     - Energy collapse points
     - Paths leading to failure
     - Successful paths despite risk

## Expected Output

The test will show:

### 1. Standard Aggregation
- Step-level failure analysis
- Dominant failure reasons
- Interpretations (structural, intent-sensitive, fatigue-sensitive)

### 2. Context Graph Insights
- **Graph Statistics**: Nodes, edges, total entries/drops
- **Most Common Paths**: Top 5 paths with traversal counts and failure rates
- **Fragile Steps**: Steps with highest drop rates
- **Energy Collapse Points**: Transitions with highest cognitive energy loss
- **Paths Leading to Failure**: Most common failure paths
- **Successful Paths**: Paths that succeed despite high risk/effort

### 3. Narrative Summary
- Plain-language insights about the simulation

### 4. Export
- Context graph exported to `credigo_context_graph.json` for inspection

## Verification Checklist

After running the test, verify:

- ✅ Event traces are captured (check verbose output for "Building context graph")
- ✅ Context graph is built (should show nodes and edges count)
- ✅ Query functions work (paths, fragile steps, energy loss shown)
- ✅ Output format matches spec (nodes, edges, dominant_paths, fragile_transitions)
- ✅ JSON export is valid (check `credigo_context_graph.json`)

## Troubleshooting

If context graph is missing:
1. Check that `result_df.attrs['context_graph']` exists
2. Verify event traces are being created in simulation loop
3. Check that `build_context_graph()` is being called
4. Ensure `all_event_traces` list is not empty

## Example Output Snippet

```
📊 CONTEXT GRAPH INSIGHTS
================================================================================

📈 Graph Statistics:
   Nodes (steps): 10
   Edges (transitions): 9
   Total entries: 7,000
   Total drops: 2,450
   Overall drop rate: 35.0%

🛤️  Most Common Paths (Top 5):
   1. Landing Page → What kind of perks...
      Traversals: 6,650 | Failure rate: 3.2%
   2. What kind of perks... → Any preference on annual fee?
      Traversals: 6,440 | Failure rate: 2.1%
   ...

⚠️  Most Fragile Steps (Top 5):
   1. Do you have any existing credit cards?
      Drop rate: 37.7% (2,219 drops)
      Dominant factor: System 2 fatigue
   ...

💡 Key Insights from Context Graph:

   🔋 Energy Collapse Points:
      1. Landing Page → What kind of perks...
         Energy loss: -0.152
      ...

   ❌ Paths Leading to Failure:
      1. What kind of perks... → Do you have any existing credit cards?
         Failures: 2,219 | Factor: System 2 fatigue
      ...
```

