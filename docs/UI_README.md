# DropSim Wizard UI

A simple web interface to test the DropSim wizard functionality.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install streamlit
   ```

2. **Run the UI:**
   ```bash
   streamlit run dropsim_ui.py
   ```
   
   Or use the helper script:
   ```bash
   ./run_ui.sh
   ```

3. **Open your browser:**
   - The UI will automatically open at `http://localhost:8501`
   - If not, navigate to that URL manually

## Using the UI

1. **Enter OpenAI API Key** (in the sidebar)
   - Or set `OPENAI_API_KEY` environment variable

2. **Fill in the form:**
   - **Product URL** (optional): Your product website URL
   - **Product Description**: Paste product copy, PRD, or website text
   - **Screenshot Text File** (optional): Upload a text file with OCR'd screenshots
   - **Persona Notes** (optional): Describe your target users
   - **Target Group Notes** (optional): Describe your ICP

3. **Click "Run Wizard"**
   - Wait 30-60 seconds for LLM processing
   - View results: personas, steps, simulation results
   - Download generated scenarios as JSON

## Screenshot Text Format

When preparing screenshot text files, separate each screen with `---`:

```
SCREENSHOT 1: Landing Page
Welcome to QuickCredit
[Get Started] button
---

SCREENSHOT 2: Phone Verification
Enter your mobile number
[Continue] button
---
```

## Example Workflow

1. Copy product description from your website/PRD
2. Paste into "Product Description" field
3. (Optional) Upload screenshot texts
4. (Optional) Add persona notes: "Young professionals, 25-35, metro cities, high digital skill"
5. Click "Run Wizard"
6. Review inferred personas and steps
7. Download Lite Scenario JSON
8. Edit and re-run with `simulate-lite` command

## Features

- ✅ Simple form-based input
- ✅ Real-time wizard execution
- ✅ Visual results display
- ✅ JSON export for scenarios and traces
- ✅ Step-level failure analysis
- ✅ Narrative summary
- ✅ Target group visualization

## Troubleshooting

- **"API key required"**: Enter your OpenAI API key in the sidebar
- **"No product context"**: Provide at least one input (URL, text, or screenshots)
- **LLM errors**: Check that your API key is valid and has credits

