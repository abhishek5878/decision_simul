#!/usr/bin/env python3
"""
dropsim_wizard.py - Input Wizard for DropSim

Provides a high-level, user-friendly interface for PMs to input product information
(URL, screenshots, notes) and get behavioral simulation results automatically.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from dropsim_llm_ingestion import (
    infer_lite_scenario_and_target_from_llm,
    LLMClient
)
from dropsim_lite_input import lite_to_scenario
from dropsim_target_filter import TargetGroup
from dropsim_narrative import generate_narrative_summary
# Legacy calibration imports (if needed)
try:
    from dropsim_calibration import ObservedFunnel, compare_scenario_to_observed, format_calibration_report
except ImportError:
    # New calibration module doesn't have these - they're optional
    ObservedFunnel = None
    compare_scenario_to_observed = None
    format_calibration_report = None
from dropsim_visualization_data import build_step_level_series
from dropsim_simulation_runner import run_simulation_with_database_personas
from dropsim_aggregation_v2 import aggregate_simulation_results, format_aggregated_results
import json
import re


# ============================================================================
# Wizard Input Schema
# ============================================================================

@dataclass
class WizardInput:
    """User-level input for the wizard - no engine-level schemas."""
    product_url: Optional[str] = None
    product_text: Optional[str] = None
    screenshot_texts: Optional[List[str]] = None
    persona_notes: Optional[str] = None
    target_group_notes: Optional[str] = None


# ============================================================================
# Firecrawl Integration
# ============================================================================

def fetch_product_content_with_firecrawl(url: str, api_key: str) -> str:
    """
    Fetch product content from URL using Firecrawl.
    
    Args:
        url: Product URL
        api_key: Firecrawl API key
    
    Returns:
        Extracted text content from the website
    """
    try:
        from firecrawl import FirecrawlApp
        
        app = FirecrawlApp(api_key=api_key)
        
        # Scrape the URL
        result = app.scrape_url(url, params={
            'formats': ['markdown', 'html'],
            'onlyMainContent': True,
            'removeTags': ['nav', 'footer', 'header', 'script', 'style']
        })
        
        # Extract text content
        if isinstance(result, dict):
            content = result.get('markdown', '') or result.get('content', '') or result.get('text', '')
        else:
            content = str(result)
        
        # Clean up content (remove excessive whitespace)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        return content if content else f"Unable to extract content from {url}"
    
    except ImportError:
        raise ValueError("firecrawl-py package not installed. Install with: pip install firecrawl-py")
    except Exception as e:
        # Fallback: return URL as reference
        return f"Error fetching content from {url}: {str(e)}\n\nUsing URL as reference only."


def analyze_screenshots_with_llm(
    screenshot_texts: List[str],
    llm_client: LLMClient,
    verbose: bool = False
) -> str:
    """
    Use LLM to analyze screenshots and extract product flow.
    
    Args:
        screenshot_texts: List of screenshot descriptions/OCR text
        llm_client: LLM client for analysis
        verbose: Print debug info
    
    Returns:
        Analyzed and structured content summary
    """
    if not screenshot_texts or len(screenshot_texts) == 0:
        return ""
    
    # Combine all screenshots with clear numbering
    screenshots_combined = "\n\n".join([
        f"## SCREENSHOT {i+1}\n{text}" 
        for i, text in enumerate(screenshot_texts)
    ])
    
    analysis_prompt = f"""You are analyzing screenshots from a fintech product to extract the exact user onboarding flow.

 **CRITICAL INSTRUCTION: Extract ALL screenshots as separate steps. DO NOT consolidate or interpret. Each screenshot = one step.**

Your task is to analyze the screenshots in chronological order and produce a structured summary of the product flow.

## SCREENSHOTS (in order)

{screenshots_combined[:15000]}  # Limit to avoid token limits

## ANALYSIS TASK

Analyze the screenshots and produce a structured summary in the following format:

### PRODUCT OVERVIEW
- Product name: [name from screenshots]
- Primary value proposition: [what problem does it solve?]
- Product archetype: [one of: payments_wallet, neo_bank, lending_bnpl, trading_investing, insurance, personal_finance_manager]
- Archetype confidence: [high/medium/low] and reasoning

### EXACT USER FLOW FROM SCREENSHOTS
**MANDATORY: Extract ONE step per screenshot. If there are 10 screenshots, you MUST extract 10 steps.**

List steps in the EXACT order shown, one per screenshot:

1. [Step name from screenshot 1] - [Brief description] - [Step number if shown] - [Key attributes: risk level, effort level, cognitive complexity]
2. [Step name from screenshot 2] - [Brief description] - [Step number if shown] - [Key attributes]
3. [Step name from screenshot 3] - [Brief description] - [Step number if shown] - [Key attributes]
... (continue for ALL screenshots)

**CRITICAL RULES**: 
- Extract EXACTLY as many steps as there are screenshots (if 10 screenshots, extract 10 steps)
- Use the EXACT step names, questions, or screen purposes from each screenshot
- DO NOT consolidate similar steps - each screenshot is a separate step
- DO NOT interpret or simplify - extract what the user actually sees
- Note step numbers if visible (e.g., "Step 1 of 10", "Step 2 of 10")
- Extract the actual questions/inputs shown in each screenshot
- If a screenshot shows a question, use that exact question as the step name

### KEY FEATURES MENTIONED
- [Feature 1 from screenshots]
- [Feature 2 from screenshots]
...

### TARGET AUDIENCE INDICATORS
- Demographics mentioned: [age groups, income levels, location]
- Use cases mentioned: [primary use cases]
- User types mentioned: [types of users the product targets]

## INSTRUCTIONS

1. Be precise about the product archetype - look for:
   - Credit card recommendation/comparison tools (quiz-based) → personal_finance_manager
   - Lending/credit products → lending_bnpl
   - Payment/wallet apps → payments_wallet
   - Investment/trading platforms → trading_investing
   - Insurance products → insurance
   - Banking accounts → neo_bank

2. Extract the EXACT flow from screenshots:
   - Look for step numbers (Step X of Y)
   - Identify each screen's purpose (landing, quiz question, results, etc.)
   - Note the progression from first screenshot to last
   - Identify the final value delivery point (results page, recommendations, etc.)

3. For each step, note:
   - What the user is asked to do
   - What information is collected
   - Risk indicators (data sharing, financial info, etc.)
   - Effort indicators (form complexity, number of fields, etc.)
   - Cognitive complexity (simple choice vs complex decision)

Output your analysis in the structured format above. Be precise and use the exact step names from screenshots.
"""

    try:
        if verbose:
            print("🔍 Analyzing screenshots with LLM...")
        
        analyzed_content = llm_client.complete(analysis_prompt)
        
        if verbose:
            print("✅ Screenshot analysis complete")
        
        return analyzed_content
    
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: LLM analysis failed: {e}")
        return ""


def analyze_crawled_content_with_llm(
    crawled_content: str,
    llm_client: LLMClient,
    verbose: bool = False
) -> str:
    """
    Use LLM to analyze and structure crawled content for better extraction.
    
    This step helps:
    1. Identify the product type and value proposition
    2. Extract key user flows and steps mentioned
    3. Identify user personas and target groups
    4. Structure the content for downstream extraction
    
    Args:
        crawled_content: Raw content from Firecrawl
        llm_client: LLM client for analysis
        verbose: Print debug info
    
    Returns:
        Analyzed and structured content summary
    """
    if not crawled_content or len(crawled_content.strip()) < 50:
        return crawled_content  # Too short to analyze
    
    analysis_prompt = f"""You are analyzing a fintech product website to extract structured information for behavioral simulation.

Your task is to analyze the crawled website content and produce a structured summary that will be used to extract:
1. Product archetype (payments_wallet, neo_bank, lending_bnpl, trading_investing, insurance, personal_finance_manager)
2. User onboarding flow steps (in chronological order)
3. Key user personas
4. Target audience

## CRAWLED WEBSITE CONTENT

{crawled_content[:8000] if len(crawled_content) > 8000 else crawled_content}

## ANALYSIS TASK

Analyze the content and produce a structured summary in the following format:

### PRODUCT OVERVIEW
- Product name: [name]
- Primary value proposition: [what problem does it solve?]
- Product archetype: [one of: payments_wallet, neo_bank, lending_bnpl, trading_investing, insurance, personal_finance_manager]
- Archetype confidence: [high/medium/low] and reasoning

### USER FLOW ANALYSIS
Identify the complete user onboarding journey from first visit to first value. List steps in chronological order:

1. [Step name] - [Brief description] - [Key attributes: risk level, effort level, cognitive complexity]
2. [Step name] - [Brief description] - [Key attributes]
...

Focus on:
- Steps that require user action (not just browsing)
- Steps that involve data sharing, verification, or financial transactions
- Steps that represent decision points or commitment moments
- The complete flow from landing to first value delivery

### KEY FEATURES MENTIONED
- [Feature 1]
- [Feature 2]
...

### TARGET AUDIENCE INDICATORS
- Demographics mentioned: [age groups, income levels, location]
- Use cases mentioned: [primary use cases]
- User types mentioned: [types of users the product targets]

### PERSONA HINTS
Based on the content, what types of users would use this product?
- [Persona 1 description]
- [Persona 2 description]
...

## INSTRUCTIONS

1. Be precise about the product archetype - look for:
   - Lending/credit products → lending_bnpl
   - Payment/wallet apps → payments_wallet
   - Investment/trading platforms → trading_investing
   - Insurance products → insurance
   - Banking accounts → neo_bank
   - Expense tracking/savings goals → personal_finance_manager

2. Extract the actual user flow from the website - look for:
   - "Get started" flows
   - Onboarding sequences
   - Step-by-step guides
   - Signup/registration processes
   - First transaction/value delivery points

3. Identify concrete steps, not vague descriptions:
   - Good: "Phone number + OTP verification"
   - Bad: "User signs up"

4. Note risk, effort, and complexity indicators:
   - Risk: mentions of security, data sharing, financial transactions
   - Effort: document uploads, form filling, verification processes
   - Complexity: multiple choices, financial decisions, complex forms

Output your analysis in the structured format above. Be concise but complete.
"""

    try:
        if verbose:
            print("🔍 Analyzing crawled content with LLM...")
        
        analyzed_content = llm_client.complete(analysis_prompt)
        
        if verbose:
            print("✅ Content analysis complete")
        
        return analyzed_content
    
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: LLM analysis failed: {e}")
        # Fallback to original content
        return crawled_content


# ============================================================================
# Context Consolidation
# ============================================================================

def consolidate_product_context(
    input: WizardInput, 
    firecrawl_api_key: Optional[str] = None,
    llm_client: Optional[LLMClient] = None,
    verbose: bool = False
) -> str:
    """
    Deterministically merges URL, product_text, and screenshot_texts
    into one LLM-ready 'product_context' string with clear section headers.
    
    Uses LLM to analyze Firecrawl content for better extraction.
    
    Args:
        input: WizardInput object
        firecrawl_api_key: Optional Firecrawl API key for URL fetching
        llm_client: Optional LLM client for content analysis
        verbose: Print debug info
    
    Returns:
        Consolidated product context string
    """
    parts = []
    
    # Product URL - fetch content if Firecrawl key provided
    if input.product_url:
        parts.append("## PRODUCT_URL")
        parts.append(input.product_url)
        parts.append("")
        
        # Fetch content from URL if Firecrawl key is available
        if firecrawl_api_key:
            try:
                fetched_content = fetch_product_content_with_firecrawl(input.product_url, firecrawl_api_key)
                if fetched_content and not fetched_content.startswith("Error"):
                    # Analyze crawled content with LLM if client provided
                    if llm_client:
                        analyzed_content = analyze_crawled_content_with_llm(
                            fetched_content,
                            llm_client,
                            verbose=verbose
                        )
                        parts.append("## PRODUCT_WEBSITE_ANALYSIS")
                        parts.append("(LLM-analyzed content from Firecrawl crawl)")
                        parts.append(analyzed_content)
                        parts.append("")
                        parts.append("## PRODUCT_WEBSITE_RAW_CONTENT")
                        parts.append("(Original crawled content for reference)")
                        parts.append(fetched_content[:2000])  # Include first 2000 chars as reference
                        parts.append("")
                    else:
                        parts.append("## PRODUCT_WEBSITE_CONTENT")
                        parts.append("(Content fetched from URL using Firecrawl)")
                        parts.append(fetched_content)
                        parts.append("")
            except Exception as e:
                # Continue without fetched content if there's an error
                parts.append(f"## NOTE: Could not fetch content from URL ({str(e)})")
                parts.append("")
    
    # Product text (main description)
    if input.product_text:
        parts.append("## PRODUCT_TEXT")
        parts.append(input.product_text.strip())
        parts.append("")
    
    # Screenshot texts (analyze with LLM if provided and LLM client available)
    if input.screenshot_texts and llm_client:
        # Analyze screenshots with LLM first
        analyzed_screenshots = analyze_screenshots_with_llm(
            input.screenshot_texts,
            llm_client,
            verbose=verbose
        )
        if analyzed_screenshots:
            parts.append("## PRODUCT_SCREENSHOT_ANALYSIS")
            parts.append("(LLM-analyzed flow from screenshots)")
            parts.append(analyzed_screenshots)
            parts.append("")
    
    # Also include raw screenshot texts for reference
    if input.screenshot_texts:
        for i, screenshot_text in enumerate(input.screenshot_texts, 1):
            if screenshot_text and screenshot_text.strip():
                parts.append(f"## SCREENSHOT_{i}_RAW")
                parts.append("(Original screenshot text for reference)")
                parts.append(screenshot_text.strip())
                parts.append("")
    
    # Persona notes
    if input.persona_notes:
        parts.append("## PERSONA_NOTES")
        parts.append(input.persona_notes.strip())
        parts.append("")
    
    # Target group notes
    if input.target_group_notes:
        parts.append("## TARGET_GROUP_NOTES")
        parts.append(input.target_group_notes.strip())
        parts.append("")
    
    return "\n".join(parts)


# ============================================================================
# Confidence Heuristics
# ============================================================================

def estimate_llm_confidence(
    lite_scenario,
    target_group: Optional[TargetGroup],
    num_screenshots: int,
    has_product_text: bool,
    has_persona_notes: bool,
    has_target_notes: bool
) -> str:
    """
    Estimate confidence level based on input richness and extraction quality.
    
    Returns:
        "high", "medium", or "low"
    """
    score = 0
    
    # Input richness
    if has_product_text:
        score += 2
    if num_screenshots >= 3:
        score += 3
    elif num_screenshots >= 1:
        score += 1
    if has_persona_notes:
        score += 1
    if has_target_notes:
        score += 1
    
    # Extraction quality
    if len(lite_scenario.personas) >= 2:
        score += 1
    if len(lite_scenario.steps) >= 5:
        score += 1
    if target_group:
        score += 1
    
    # Confidence bands
    if score >= 8:
        return "high"
    elif score >= 5:
        return "medium"
    else:
        return "low"


# ============================================================================
# Wizard Orchestrator
# ============================================================================

def run_fintech_wizard(
    wizard_input: WizardInput,
    llm_client: LLMClient,
    simulate: bool = True,
    observed_funnel: Optional[ObservedFunnel] = None,
    verbose: bool = False,
    firecrawl_api_key: Optional[str] = None,
    n_personas: int = 1000,
    use_database_personas: bool = True,
    explicit_target_group: Optional[TargetGroup] = None,
) -> Dict:
    """
    Main wizard orchestrator: consolidates input, extracts scenario, runs simulation.
    
    Pipeline:
      1) Consolidate context from all inputs
      2) Call infer_lite_scenario_and_target_from_llm(...) to get LiteScenario + TargetGroup
      3) Optionally run DropSim (lite_to_scenario + simulate_persona_trajectories)
      4) Return a dict containing:
         - lite_scenario
         - target_group
         - fintech_archetype
         - scenario_result (if simulate=True)
         - narrative_summary (if simulate=True)
         - confidence (heuristic)
    
    Args:
        wizard_input: WizardInput object
        llm_client: LLM client instance
        simulate: Whether to run simulation (default: True)
        observed_funnel: Optional observed funnel for calibration
        verbose: Print debug info
        firecrawl_api_key: Optional Firecrawl API key for URL fetching
        n_personas: Number of personas to load from database (default: 1000)
        use_database_personas: Use database personas instead of preset (default: True)
    
    Returns:
        Dict with extracted scenario, results, and metadata
    """
    # Step 1: Consolidate context (with Firecrawl if URL provided, analyzed with LLM)
    product_context = consolidate_product_context(
        wizard_input, 
        firecrawl_api_key=firecrawl_api_key,
        llm_client=llm_client,
        verbose=verbose
    )
    
    if not product_context.strip():
        raise ValueError("No product context provided. At least one of: product_url, product_text, or screenshot_texts must be provided.")
    
    # Step 2: Extract scenario via LLM
    # Note: persona_notes and target_group_notes are already in product_context if provided
    # Pass None to avoid duplication (the function will extract them from product_context)
    
    # If explicit_target_group is provided, use it instead of LLM extraction
    if explicit_target_group is not None:
        if verbose:
            print("🎯 Using explicit target group (overriding LLM extraction)")
            print(f"   Target: {explicit_target_group.to_dict()}")
    
    # If we have screenshots, try direct extraction first to ensure we get all steps
    use_direct_extraction = False
    if wizard_input.screenshot_texts and len(wizard_input.screenshot_texts) > 0:
        # Check if we should use direct extraction (bypass LLM step consolidation)
        use_direct_extraction = True
        if verbose:
            print(f"📸 Using direct screenshot extraction to ensure all {len(wizard_input.screenshot_texts)} steps are captured")
    
    if use_direct_extraction:
        # Extract steps directly from screenshots
        from direct_screenshot_extraction import extract_steps_directly_from_screenshots
        direct_steps = extract_steps_directly_from_screenshots(wizard_input.screenshot_texts)
        
        if verbose:
            print(f"✅ Directly extracted {len(direct_steps)} steps from {len(wizard_input.screenshot_texts)} screenshots")
        
        # Still use LLM for personas and archetype, but inject our direct steps
        lite_scenario, target_group, fintech_archetype = infer_lite_scenario_and_target_from_llm(
            product_context,
            persona_notes=None,
            target_group_notes=None,
            llm_client=llm_client,
            verbose=verbose,
            dry_run=not simulate,
            force_steps=direct_steps  # Inject our directly extracted steps
        )
    else:
        lite_scenario, target_group, fintech_archetype = infer_lite_scenario_and_target_from_llm(
            product_context,
            persona_notes=None,  # Already in consolidated context
            target_group_notes=None,  # Already in consolidated context
            llm_client=llm_client,
            verbose=verbose,
            dry_run=not simulate
        )
    
    # Override target_group if explicit_target_group is provided
    if explicit_target_group is not None:
        target_group = explicit_target_group
    
    # Estimate confidence
    num_screenshots = len(wizard_input.screenshot_texts) if wizard_input.screenshot_texts else 0
    confidence = estimate_llm_confidence(
        lite_scenario,
        target_group,
        num_screenshots,
        bool(wizard_input.product_text),
        bool(wizard_input.persona_notes),
        bool(wizard_input.target_group_notes)
    )
    
    result = {
        "lite_scenario": lite_scenario,
        "target_group": target_group,
        "fintech_archetype": fintech_archetype,
        "confidence": confidence,
        "product_context_preview": product_context[:200] + "..." if len(product_context) > 200 else product_context
    }
    
    if not simulate:
        return result
    
    # Step 3: Run DropSim
    from behavioral_aggregator import generate_full_report
    
    # Convert to full scenario
    scenario = lite_to_scenario(lite_scenario)
    product_steps_raw = scenario['steps']  # Could be dict or list
    
    # Get state variants (default to STATE_VARIANTS if not in scenario)
    if 'state_variants' in scenario and scenario['state_variants']:
        state_variants = scenario['state_variants']
    else:
        from behavioral_engine import STATE_VARIANTS
        state_variants = STATE_VARIANTS
    
    # Ensure product_steps is a dict keyed by step name
    # This is required by generate_full_report and the simulation runner
    if isinstance(product_steps_raw, list):
        # Convert list to dict
        product_steps = {}
        for step in product_steps_raw:
            if isinstance(step, dict):
                step_name = step.get('name')
                if step_name:
                    product_steps[step_name] = step
            else:
                # If it's a ProductStep object, use its name attribute
                step_name = getattr(step, 'name', None)
                if step_name:
                    product_steps[step_name] = step
    elif isinstance(product_steps_raw, dict):
        product_steps = product_steps_raw  # Already a dict
    else:
        # Fallback: create empty dict
        product_steps = {}
        if verbose:
            print(f"⚠️  Warning: Unexpected product_steps type: {type(product_steps_raw)}")
    
    # Run simulation with database personas or preset personas
    personas = None  # Initialize personas variable
    if use_database_personas:
        # Use 1000 personas from database
        from dropsim_target_filter import TargetGroup as TG
        target_group_obj = None
        if target_group:
            if isinstance(target_group, dict):
                target_group_obj = TG.from_dict(target_group)
            else:
                target_group_obj = target_group
        
        result_df = run_simulation_with_database_personas(
            product_steps=product_steps,
            n_personas=n_personas,
            target_group=target_group_obj,
            state_variants=state_variants,
            verbose=verbose,
            min_matched=n_personas  # Ensure we get exactly the requested number of personas
        )
        
        # Extract personas from result_df for reporting
        # When using database personas, we don't have a separate personas list
        # but we can extract them from result_df if needed
        personas = []  # Empty list for database personas (not used in reporting)
    else:
        # Use preset personas (original behavior)
        from fintech_demo import run_fintech_demo_simulation
        personas = scenario['personas']
        
        # Normalize persona structure (ensure 'priors' key exists)
        for persona in personas:
            if 'compiled_priors' in persona and 'priors' not in persona:
                persona['priors'] = persona['compiled_priors']
        
        # Filter personas by target group if provided
        if target_group:
            from dropsim_target_filter import filter_personas_by_target
            personas = filter_personas_by_target(personas, target_group)
        
        # Run simulation
        result_df = run_fintech_demo_simulation(
            personas,
            state_variants,
            product_steps,
            verbose=verbose
        )
    
    # Extract trajectories from result_df (they're stored in the 'trajectories' column)
    trajectories = []
    if 'trajectories' in result_df.columns:
        for traj_list in result_df['trajectories']:
            if isinstance(traj_list, list):
                trajectories.extend(traj_list)
    
    # Generate report using new aggregation format
    try:
        aggregated_results = aggregate_simulation_results(result_df, product_steps, verbose=verbose)
        aggregated_report_text = format_aggregated_results(aggregated_results, verbose=verbose)
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: New aggregation format failed: {e}")
            import traceback
            traceback.print_exc()
        aggregated_results = None
        aggregated_report_text = None
    
    # Also generate legacy report for compatibility
    from behavioral_aggregator import generate_full_report
    full_report = generate_full_report(result_df, product_steps=product_steps)
    
    # Generate narrative
    narrative = generate_narrative_summary(
        scenario_result=full_report,
        product_steps=product_steps,
        calibration_report=None,
        result_df=result_df
    )
    
    # Extract context graph and counterfactuals from result_df if available
    context_graph = None
    context_graph_summary = None
    counterfactuals = None
    context_graph_obj = None
    if hasattr(result_df, 'attrs'):
        context_graph = result_df.attrs.get('context_graph')
        context_graph_summary = result_df.attrs.get('context_graph_summary')
        counterfactuals = result_df.attrs.get('counterfactuals')
        context_graph_obj = result_df.attrs.get('_context_graph_obj')  # For calibration
    
    # Note: Calibration requires observed_metrics (real-world data)
    # This will be added when calibration is run separately with observed data
    # For now, we just prepare the structure
    
    result["scenario_result"] = {
        "result_df": result_df,
        "trajectories": trajectories,
        "full_report": full_report,
        "aggregated_results": aggregated_results,  # New format
        "aggregated_report_text": aggregated_report_text,  # New format text
        "personas": personas if personas is not None else [],
        "product_steps": product_steps,
        "state_variants": state_variants,
        "context_graph": context_graph,  # Context graph data
        "context_graph_summary": context_graph_summary,  # Context graph insights
        "counterfactuals": counterfactuals,  # Counterfactual analysis
        "_context_graph_obj": context_graph_obj  # Internal: for calibration
    }
    result["narrative_summary"] = narrative
    
    # Decision Engine: Generate recommendations from analysis
    # Only runs if we have both counterfactuals and context graph
    decision_report = None
    if counterfactuals and context_graph:
        try:
            from dropsim_decision_engine import generate_decision_report
            
            # Check if calibration is available (may be None if not run)
            calibration_report = None
            if hasattr(result_df, 'attrs') and 'calibration' in result_df.attrs:
                calibration_report = result_df.attrs.get('calibration')
            
            # If calibration is available, use it; otherwise use context graph for basic recommendations
            if calibration_report:
                decision_report = generate_decision_report(
                    calibration_report,
                    counterfactuals,
                    context_graph,
                    top_n=5
                )
            else:
                # Generate basic recommendations from counterfactuals and context graph only
                # Create a minimal calibration report structure
                minimal_calibration = {
                    'calibration_score': 0.5,  # Unknown without real data
                    'stability_score': 0.5,
                    'bias_summary': {},
                    'step_metrics': []
                }
                
                # Extract step metrics from context graph
                if context_graph and 'nodes' in context_graph:
                    for node in context_graph['nodes']:
                        if isinstance(node, dict):
                            step_id = node.get('step_id')
                            drop_rate = node.get('drop_rate', 0.0)
                            if step_id and drop_rate > 0:
                                minimal_calibration['step_metrics'].append({
                                    'step_id': step_id,
                                    'predicted_drop_rate': drop_rate,
                                    'observed_drop_rate': drop_rate,  # Assume accurate without calibration
                                    'absolute_error': 0.0,
                                    'error_direction': 'accurate'
                                })
                
                decision_report = generate_decision_report(
                    minimal_calibration,
                    counterfactuals,
                    context_graph,
                    top_n=5
                )
            
            if decision_report:
                result["scenario_result"]["decision_report"] = decision_report.to_dict()
                
                # Deployment Guard: Validate recommendations for deployment
                try:
                    from dropsim_deployment_guard import validate_all_recommendations
                    
                    # Get calibration data if available
                    calibration_data = None
                    if hasattr(result_df, 'attrs') and 'calibration' in result_df.attrs:
                        calibration_data = result_df.attrs.get('calibration')
                    
                    # Validate all recommendations
                    deployment_reports = validate_all_recommendations(
                        decision_report.to_dict(),
                        calibration_data,
                        counterfactuals,
                        context_graph
                    )
                    
                    # Add deployment validation to result
                    result["scenario_result"]["deployment_validation"] = [
                        report.to_dict() for report in deployment_reports
                    ]
                    
                    if verbose and deployment_reports:
                        safe_count = sum(1 for r in deployment_reports if r.evaluation.rollout_recommendation == "safe")
                        caution_count = sum(1 for r in deployment_reports if r.evaluation.rollout_recommendation == "caution")
                        blocked_count = sum(1 for r in deployment_reports if r.evaluation.rollout_recommendation == "do_not_deploy")
                        print(f"✅ Deployment validation complete:")
                        print(f"   Safe to deploy: {safe_count}")
                        print(f"   Caution: {caution_count}")
                        print(f"   Blocked: {blocked_count}")
                except Exception as e:
                    # Deployment guard is optional, don't fail if it errors
                    if verbose:
                        print(f"⚠️  Warning: Deployment guard failed: {e}")
                    pass
        except Exception as e:
            # Decision engine is optional, don't fail if it errors
            if verbose:
                print(f"⚠️  Warning: Decision engine failed: {e}")
            pass
    
    # Interpretation Layer: Convert findings into high-level insights
    interpretation = None
    if context_graph and (counterfactuals or decision_report):
        try:
            from dropsim_interpreter import interpret_results
            
            # Get calibration if available
            calibration_data = None
            if hasattr(result_df, 'attrs') and 'calibration' in result_df.attrs:
                calibration_data = result_df.attrs.get('calibration')
            
            # Run interpretation
            interpretation = interpret_results(
                context_graph,
                calibration_data,
                counterfactuals,
                decision_report.to_dict() if decision_report else None
            )
            
            if interpretation:
                result["scenario_result"]["interpretation"] = interpretation.to_dict()
                
                if verbose:
                    print(f"✅ Interpretation complete:")
                    print(f"   Root causes identified: {len(interpretation.root_causes)}")
                    print(f"   Structural patterns: {len(interpretation.dominant_patterns)}")
                    print(f"   Design shifts recommended: {len(interpretation.recommended_design_shifts)}")
        except Exception as e:
            # Interpretation is optional, don't fail if it errors
            if verbose:
                print(f"⚠️  Warning: Interpretation failed: {e}")
            pass
    
    # Signal Quality Evaluation: Assess epistemic quality of outputs
    signal_quality_evaluation = None
    if context_graph and (counterfactuals or decision_report):
        try:
            from dropsim_signal_quality import evaluate_signal_quality
            
            # Run signal quality evaluation on scenario_result
            signal_quality_evaluation = evaluate_signal_quality(
                result["scenario_result"],
                comparison_results=None,  # Could add multiple runs for stability
                perturbed_result=None,  # Could add perturbation tests
                perturbed_results=None  # Could add multiple perturbation tests
            )
            
            if signal_quality_evaluation:
                result["scenario_result"]["signal_quality"] = signal_quality_evaluation['final_evaluation']
                
                if verbose:
                    trust_index = signal_quality_evaluation['final_evaluation']['signal_quality']['overall_trust_index']
                    print(f"✅ Signal quality evaluation complete:")
                    print(f"   Trust Index: {trust_index:.1%}")
                    print(f"   Classification: {signal_quality_evaluation['judgment']['classification']}")
                    if signal_quality_evaluation['confidence_calibration']['overconfidence_detected']:
                        print(f"   ⚠️  Overconfidence detected: {signal_quality_evaluation['confidence_calibration']['original_confidence']:.1%} → {signal_quality_evaluation['confidence_calibration']['calibrated_confidence']:.1%}")
        except Exception as e:
            # Signal quality evaluation is optional, don't fail if it errors
            if verbose:
                print(f"⚠️  Warning: Signal quality evaluation failed: {e}")
            pass
    
    # Confidence Calibration: Adjust confidence based on contradictions
    try:
        from dropsim_confidence_calibrator import apply_confidence_calibration
        
        # Apply confidence calibration to scenario result
        result["scenario_result"] = apply_confidence_calibration(result["scenario_result"])
        
        if verbose:
            confidence_assessment = result["scenario_result"].get('confidence_assessment', {})
            if confidence_assessment:
                raw_conf = confidence_assessment.get('raw_confidence', 0.5)
                adj_conf = confidence_assessment.get('adjusted_confidence', 0.5)
                band = confidence_assessment.get('confidence_band', 'UNKNOWN')
                contradictions = confidence_assessment.get('contradiction_count', 0)
                
                print(f"✅ Confidence calibration complete:")
                print(f"   Raw Confidence: {raw_conf:.1%}")
                print(f"   Adjusted Confidence: {adj_conf:.1%}")
                print(f"   Confidence Band: {band}")
                if contradictions > 0:
                    print(f"   ⚠️  {contradictions} contradiction(s) detected → confidence reduced")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Confidence calibration failed: {e}")
        pass
    
    # Reference Signal Calibration: Anchor to real-world signals
    try:
        from dropsim_reference_signals import ReferenceSignalStore, check_reference_signals
        
        # Check against reference signals
        store = ReferenceSignalStore()
        result["scenario_result"] = check_reference_signals(result["scenario_result"], store)
        
        if verbose:
            ref_calibration = result["scenario_result"].get('reference_calibration', {})
            if ref_calibration:
                match_score = ref_calibration.get('match_score')
                trend = ref_calibration.get('calibration_trend')
                if match_score is not None:
                    print(f"✅ Reference signal calibration:")
                    print(f"   Match Score: {match_score:.1%}")
                    if trend:
                        print(f"   Calibration Trend: {trend}")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Reference signal calibration failed: {e}")
        pass
    
    # Decision Trace Recording: Record actual decisions made
    decision_traces = []
    context_graph_delta = {}
    learned_precedents = []
    
    try:
        from dropsim_decision_traces import (
            DecisionTraceStore,
            extract_decision_traces_from_simulation
        )
        from dropsim_context_graph_v2 import ContextGraphV2
        
        # Extract decision traces from simulation
        decision_traces = extract_decision_traces_from_simulation(
            result["scenario_result"],
            actor_type="system"
        )
        
        # Store traces
        trace_store = DecisionTraceStore()
        for trace in decision_traces:
            trace_store.add_trace(trace)
            learned_precedents.extend(trace.precedent_ids)
        
        # Add to context graph v2
        context_graph = ContextGraphV2()
        for trace in decision_traces:
            context_graph.add_decision_trace(trace)
        
        # Get graph delta (new nodes/edges)
        # Use timestamp from start of run if available, otherwise use 24 hours ago
        import datetime
        since_time = (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
        context_graph_delta = context_graph.get_graph_delta(since_time)
        
        # Add to result
        result["decision_traces"] = [t.to_dict() for t in decision_traces]
        result["context_graph_delta"] = context_graph_delta
        result["learned_precedents"] = list(set(learned_precedents))  # Unique precedents
        
        if verbose:
            print(f"✅ Decision traces recorded:")
            print(f"   Total traces: {len(decision_traces)}")
            print(f"   Precedents found: {len(set(learned_precedents))}")
            print(f"   Graph nodes added: {len(context_graph_delta.get('nodes', []))}")
            print(f"   Graph edges added: {len(context_graph_delta.get('edges', []))}")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Decision trace recording failed: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # Executive Brief: Generate one-page decision brief
    try:
        from dropsim_executive_brief import generate_executive_brief
        
        executive_brief = generate_executive_brief(result)
        result["executive_brief"] = executive_brief
        
        if verbose:
            print(f"✅ Executive brief generated")
            print(f"   Brief length: {len(executive_brief)} characters")
            print(f"   Ready for leadership review")
    except Exception as e:
        if verbose:
            print(f"⚠️  Warning: Executive brief generation failed: {e}")
        pass
    
    # Calibration if provided (legacy support)
    if observed_funnel and compare_scenario_to_observed:
        try:
            calibration_report = compare_scenario_to_observed(
                {
                    "full_report": full_report,
                    "product_steps": product_steps
                },
                observed_funnel,
                product_steps
            )
            result["calibration_report"] = calibration_report
            result["narrative_summary"] = generate_narrative_summary(
                scenario_result=full_report,
                product_steps=product_steps,
                calibration_report=calibration_report,
                result_df=result_df
            )
        except Exception as e:
            if verbose:
                print(f"⚠️  Warning: Legacy calibration failed: {e}")
    
    return result

