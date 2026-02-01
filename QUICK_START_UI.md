# DropSim Wizard UI - Quick Start

## 🚀 Run the UI

```bash
streamlit run dropsim_ui.py
```

The UI will open automatically in your browser at `http://localhost:8501`

## 📋 What You'll See

1. **Sidebar**: Enter your OpenAI API key
2. **Main Form**: 
   - Product URL (optional)
   - Product Description (paste your product copy)
   - Screenshot Text File (upload OCR'd screenshots)
   - Persona Notes (describe your users)
   - Target Group Notes (describe your ICP)
3. **Results**: 
   - Inferred personas and steps
   - Simulation results with failure rates
   - Narrative summary
   - Download buttons for JSON exports

## 💡 Example Input

**Product Description:**
```
QuickCredit - Instant personal loans for salaried professionals
Up to ₹5 lakhs, no collateral, funds in 24 hours
```

**Persona Notes:**
```
Young professionals, 25-35, metro cities
Medium to high income, comfortable with digital apps
Moderate to high risk tolerance
```

**Target Group Notes:**
```
Primary: Young to middle-aged (25-45), metro/tier2 cities
Medium to high digital skill, high intent
```

## 🎯 Try It Now

1. Run: `streamlit run dropsim_ui.py`
2. Enter your OpenAI API key
3. Paste the example inputs above
4. Click "Run Wizard"
5. View results in 30-60 seconds!

