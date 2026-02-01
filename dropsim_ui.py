#!/usr/bin/env python3
"""
dropsim_ui.py - Simple Streamlit UI for DropSim Wizard

A simple web interface to test the DropSim wizard functionality.
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from dropsim_wizard import WizardInput, run_fintech_wizard
from dropsim_llm_ingestion import OpenAILLMClient

# Page config
st.set_page_config(
    page_title="DropSim Wizard",
    page_icon="🧙",
    layout="wide"
)

st.title("🧙 DropSim Fintech Wizard")
st.markdown("**From Product URL + Screenshots to Behavioral Insights**")

# Sidebar for API key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Enter your OpenAI API key or set OPENAI_API_KEY environment variable"
    )
    
    firecrawl_key = st.text_input(
        "Firecrawl API Key (optional)",
        type="password",
        value=os.environ.get("FIRECRAWL_API_KEY", ""),
        help="Enter Firecrawl API key to fetch content from URLs. Get one at https://firecrawl.dev"
    )
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ OpenAI API key set")
    else:
        st.warning("⚠️ OpenAI API key required")
    
    if firecrawl_key:
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
        st.info("🌐 Firecrawl enabled - URLs will be fetched automatically")
    
    st.markdown("---")
    st.markdown("### How to Use")
    st.markdown("""
    1. Enter product URL (optional)
    2. Upload or paste product text
    3. Upload screenshot texts (separated by `---`)
    4. Add persona notes (optional)
    5. Add target group notes (optional)
    6. Click "Run Wizard"
    """)

# Main form
with st.form("wizard_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Product Information")
        product_url = st.text_input("Product URL (optional)", placeholder="https://example.com")
        
        product_text = st.text_area(
            "Product Description",
            height=200,
            placeholder="Paste your product description, PRD, or website copy here..."
        )
        
        screenshot_file = st.file_uploader(
            "Screenshot Text File (optional)",
            type=["txt"],
            help="Upload a text file with OCR'd screenshots, separated by ---"
        )
        
        screenshot_text = None
        if screenshot_file:
            screenshot_content = screenshot_file.read().decode('utf-8')
            if '---' in screenshot_content:
                screenshot_text = [s.strip() for s in screenshot_content.split('---') if s.strip()]
            else:
                screenshot_text = [s.strip() for s in screenshot_content.split('\n\n') if s.strip()]
            st.info(f"✅ Loaded {len(screenshot_text)} screenshots")
    
    with col2:
        st.subheader("User Information")
        persona_notes = st.text_area(
            "Persona Notes (optional)",
            height=150,
            placeholder="Describe your target users:\n- Age, location, income\n- Digital comfort\n- Risk attitude\n- Intent level"
        )
        
        target_group_notes = st.text_area(
            "Target Group Notes (optional)",
            height=150,
            placeholder="Describe your ICP:\n- Primary target audience\n- Key demographics\n- Behavioral traits"
        )
    
    run_button = st.form_submit_button("🚀 Run Wizard", use_container_width=True)

# Results section
if run_button:
    if not api_key:
        st.error("❌ Please enter your OpenAI API key in the sidebar")
        st.stop()
    
    # Process screenshot inputs
    screenshot_texts = None
    if screenshot_file:
        screenshot_content = screenshot_file.read().decode('utf-8')
        # Split by --- or double newlines
        if '---' in screenshot_content:
            screenshot_texts = [s.strip() for s in screenshot_content.split('---') if s.strip()]
        else:
            screenshot_texts = [s.strip() for s in screenshot_content.split('\n\n') if s.strip()]
    elif screenshot_text_input:
        # Split by --- or double newlines
        if '---' in screenshot_text_input:
            screenshot_texts = [s.strip() for s in screenshot_text_input.split('---') if s.strip()]
        else:
            screenshot_texts = [s.strip() for s in screenshot_text_input.split('\n\n') if s.strip()]
    
    # Validate inputs
    if not product_url and not product_text and not screenshot_texts:
        st.error("❌ Please provide at least one of: Product URL, Product Description, or Screenshots")
        st.stop()
    
    # Show loading
    with st.spinner("🧙 Running wizard... Analyzing screenshots and running simulation..."):
        try:
            # Build wizard input
            wizard_input = WizardInput(
                product_url=product_url if product_url else None,
                product_text=product_text if product_text else None,
                screenshot_texts=screenshot_texts,
                persona_notes=persona_notes if persona_notes else None,
                target_group_notes=target_group_notes if target_group_notes else None
            )
            
            # Initialize LLM client
            llm_client = OpenAILLMClient(api_key=api_key)
            
            # Get Firecrawl key from environment (set in sidebar)
            firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
            
            # Run wizard (use database personas by default)
            wizard_result = run_fintech_wizard(
                wizard_input,
                llm_client,
                simulate=True,
                observed_funnel=None,
                verbose=False,
                firecrawl_api_key=firecrawl_key,
                n_personas=1000,
                use_database_personas=True
            )
            
            # Display results
            st.success("✅ Wizard completed successfully!")
            
            # Show new aggregation format (priority)
            if 'scenario_result' in wizard_result:
                scenario = wizard_result['scenario_result']
                
                if 'aggregated_report_text' in scenario:
                    st.header("📊 Aggregation Results")
                    st.text(scenario['aggregated_report_text'])
                
                # Show step summary table
                if 'aggregated_results' in scenario:
                    agg = scenario['aggregated_results']
                    
                    st.subheader("📈 Step-Level Failure Analysis")
                    step_data = []
                    for step_name, data in agg['step_summary'].items():
                        step_data.append({
                            'Step': step_name,
                            'Variants Failed': data['failure_count'],
                            'Failure Rate %': f"{data['failure_rate']:.1f}",
                            'Personas Affected': data['persona_count'],
                            'Dominant Reason': data['dominant_reason'] or 'None'
                        })
                    
                    if step_data:
                        st.dataframe(pd.DataFrame(step_data), use_container_width=True)
                    
                    # Show interpretations
                    if 'interpretations' in agg:
                        interp = agg['interpretations']
                        st.subheader("🔍 Interpretations")
                        
                        if interp.get('structural_flaws'):
                            st.error("🔴 Structural Product Flaws")
                            for flaw in interp['structural_flaws']:
                                st.write(f"• {flaw['interpretation']}")
                        
                        if interp.get('intent_sensitive_steps'):
                            st.warning("🟡 Intent-Sensitive Steps")
                            for step in interp['intent_sensitive_steps']:
                                st.write(f"• {step['interpretation']}")
                        
                        if interp.get('fatigue_sensitive_steps'):
                            st.info("🟠 Fatigue-Sensitive Steps")
                            for step in interp['fatigue_sensitive_steps']:
                                st.write(f"• {step['interpretation']}")
                        
                        if interp.get('overall_pattern'):
                            st.success(f"📋 Overall Pattern: {interp['overall_pattern']}")
            
            # Summary
            st.header("📋 Wizard Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fintech Archetype", wizard_result.get('fintech_archetype', 'Unknown'))
            with col2:
                st.metric("Personas Inferred", len(wizard_result['lite_scenario'].personas))
            with col3:
                st.metric("Steps Inferred", len(wizard_result['lite_scenario'].steps))
            
            st.metric("LLM Confidence", wizard_result.get('confidence', 'unknown').upper())
            
            # Personas
            st.subheader("👥 Inferred Personas")
            for persona in wizard_result['lite_scenario'].personas:
                with st.expander(f"**{persona.name}**"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**SEC:** {persona.sec}")
                        st.write(f"**Location:** {persona.urban_rural}")
                        st.write(f"**Digital Skill:** {persona.digital_skill}")
                    with col2:
                        st.write(f"**Age:** {persona.age_bucket}")
                        st.write(f"**Intent:** {persona.intent}")
                        st.write(f"**Risk Attitude:** {persona.risk_attitude or 'Not specified'}")
            
            # Steps
            st.subheader("📊 Inferred Steps")
            steps_data = []
            for step in wizard_result['lite_scenario'].steps:
                steps_data.append({
                    "Step": step.name,
                    "Type": step.type,
                    "Mental Complexity": step.mental_complexity,
                    "Effort": step.effort,
                    "Risk": step.risk,
                    "Irreversible": "Yes" if step.irreversible else "No",
                    "Value Visibility": step.value_visibility,
                    "Delay to Value": step.delay_to_value
                })
            st.dataframe(steps_data, use_container_width=True)
            
            # Target Group
            if wizard_result.get('target_group'):
                st.subheader("🎯 Target Group Filters")
                tg_dict = wizard_result['target_group'].to_dict()
                st.json(tg_dict)
            
            # Simulation Results
            if 'scenario_result' in wizard_result:
                st.header("🚀 Simulation Results")
                
                scenario_result = wizard_result['scenario_result']
                full_report = scenario_result['full_report']
                product_steps = scenario_result['product_steps']
                
                # Step-level failure rates
                st.subheader("📊 Failure Mode Analysis")
                failure_data = []
                for step_name in product_steps.keys():
                    step_data = full_report['failure_modes'].get(step_name, {})
                    failure_data.append({
                        "Step": step_name,
                        "Failure Rate": f"{step_data.get('failure_rate', 0):.1f}%",
                        "Primary Cost": step_data.get('primary_cost', 'None'),
                        "Secondary Cost": step_data.get('secondary_cost', 'None')
                    })
                st.dataframe(failure_data, use_container_width=True)
                
                # Narrative Summary
                if 'narrative_summary' in wizard_result:
                    st.subheader("📝 Narrative Summary")
                    st.info(wizard_result['narrative_summary'])
                
                # Download buttons
                st.subheader("💾 Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export lite scenario
                    lite_dict = {
                        'product_type': wizard_result['lite_scenario'].product_type,
                        'personas': [p.__dict__ for p in wizard_result['lite_scenario'].personas],
                        'steps': [s.__dict__ for s in wizard_result['lite_scenario'].steps]
                    }
                    if wizard_result.get('fintech_archetype'):
                        lite_dict['fintech_archetype'] = wizard_result['fintech_archetype']
                    
                    st.download_button(
                        "Download Lite Scenario JSON",
                        data=json.dumps(lite_dict, indent=2),
                        file_name="dropsim_lite_scenario.json",
                        mime="application/json"
                    )
                
                with col2:
                    # Export full traces
                    if 'trajectories' in scenario_result:
                        # Handle product_steps as dicts (from lite_to_scenario)
                        steps_export = {}
                        for k, v in product_steps.items():
                            if isinstance(v, dict):
                                steps_export[k] = {
                                    'name': v.get('name', k),
                                    'cognitive_demand': v.get('cognitive_demand', 0),
                                    'effort_demand': v.get('effort_demand', 0),
                                    'risk_signal': v.get('risk_signal', 0)
                                }
                            else:
                                # If it's an object with attributes
                                steps_export[k] = {
                                    'name': getattr(v, 'name', k),
                                    'cognitive_demand': getattr(v, 'cognitive_demand', 0),
                                    'effort_demand': getattr(v, 'effort_demand', 0),
                                    'risk_signal': getattr(v, 'risk_signal', 0)
                                }
                        
                        traces_json = json.dumps({
                            'personas': scenario_result['personas'],
                            'trajectories': scenario_result['trajectories'],
                            'product_steps': steps_export
                        }, indent=2, default=str)
                        
                        st.download_button(
                            "Download Full Traces JSON",
                            data=traces_json,
                            file_name="dropsim_traces.json",
                            mime="application/json"
                        )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown("**DropSim** - Behavioral Simulation Engine for Product Funnels")
st.markdown("Built with deterministic behavioral models (System 2 fatigue, Loss aversion, Temporal discounting, Low ability)")

