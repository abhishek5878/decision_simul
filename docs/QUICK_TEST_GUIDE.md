# Quick Test Guide - Context Graph for Credigo

## ✅ Verification Complete

All implementation checks passed:
- ✅ Imports working
- ✅ Data structures correct
- ✅ Query functions functional
- ✅ Integration points verified

---

## 🚀 Run Credigo Test

### Option 1: Direct Run

```bash
cd /path/to/decision_simul

export OPENAI_API_KEY="your-openai-api-key"
export FIRECRAWL_API_KEY="your-firecrawl-api-key"

python3 test_credigo_context_graph.py
```

### Option 2: Using Convenience Script

```bash
./run_credigo_test.sh
```

---

## 📊 What to Expect

The test will:

1. **Load Credigo Screenshots** (10 screenshots)
2. **Extract Product Steps** (using direct screenshot extraction)
3. **Load Personas** (1000 from database, filtered by target group)
4. **Run Simulation** (1000 personas × 7 variants = 7,000 trajectories)
5. **Build Context Graph** (from event traces)
6. **Display Results**:
   - Standard aggregation (failure rates)
   - Context Graph insights:
     - Graph statistics
     - Most common paths
     - Fragile steps
     - Energy collapse points
     - Paths leading to failure
     - Successful paths
7. **Export JSON** (`credigo_context_graph.json`)

---

## ⏱️ Expected Runtime

- Persona loading: ~30-60 seconds
- Simulation: ~2-5 minutes (for 1000 personas)
- Context graph building: ~5-10 seconds
- **Total: ~3-6 minutes**

---

## 📋 Output Files

After running, you'll have:

1. **Console Output**: Full simulation results and context graph insights
2. **`credigo_context_graph.json`**: Complete graph structure for inspection
3. **`credigo_test_output.log`**: Full log (if using convenience script)

---

## 🔍 Key Things to Check

### 1. Context Graph is Built
Look for:
```
📊 Building context graph from event traces...
✅ Context graph built:
   Nodes: 10
   Edges: 9
   Total traversals: 7,000
```

### 2. Context Graph Insights Section
Should show:
- Graph statistics
- Most common paths (top 5)
- Fragile steps (top 5)
- Energy collapse points
- Paths leading to failure
- Successful paths

### 3. JSON Export
Check `credigo_context_graph.json` contains:
- `nodes`: Array of step nodes
- `edges`: Array of transition edges
- `dominant_paths`: Most common paths
- `fragile_transitions`: Fragile steps

---

## 🐛 Troubleshooting

### If context graph is missing:

1. **Check event traces are captured**:
   - Look for "Building context graph" message
   - Verify `all_event_traces` is not empty

2. **Check result_df.attrs**:
   ```python
   if hasattr(result_df, 'attrs'):
       print(result_df.attrs.keys())
   ```

3. **Verify simulation completed**:
   - Check for "Simulation complete!" message
   - Verify personas were simulated (should show count)

### If test hangs:

- Check if persona loading is in progress
- Verify API keys are set correctly
- Check network connection (for Hugging Face dataset)

---

## ✅ Success Criteria

The test is successful if:

1. ✅ Simulation completes (1000 personas)
2. ✅ Context graph is built (nodes and edges > 0)
3. ✅ Context Graph insights section appears
4. ✅ JSON export file is created
5. ✅ All query functions return results

---

## 📝 Example Output

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
```

---

**Ready to test!** Run the command above to see Context Graph in action. 🚀

