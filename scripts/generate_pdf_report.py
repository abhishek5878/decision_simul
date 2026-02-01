"""
Generate comprehensive PDF report from simulation results JSON.
Explains what's not working, why, and what we've been solving.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def load_json_data(filepath: str) -> Dict:
    """Load JSON simulation results."""
    print(f"Loading JSON from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded JSON successfully")
    return data


def analyze_trajectories(data: Dict) -> Dict:
    """Analyze trajectories to extract key insights."""
    print("Analyzing trajectories...")
    
    scenario_result = data.get('scenario_result', {})
    trajectories = scenario_result.get('trajectories', [])
    
    # Extract aggregated results if available
    aggregated_results = scenario_result.get('aggregated_results', {})
    aggregated_report_text = scenario_result.get('aggregated_report_text', '')
    full_report = scenario_result.get('full_report', {})
    
    # Statistics
    total_trajectories = len(trajectories)
    completed_count = sum(1 for t in trajectories if t.get('completed', False))
    completion_rate = (completed_count / total_trajectories * 100) if total_trajectories > 0 else 0
    
    # Step-level analysis
    step_stats = defaultdict(lambda: {
        'entered': 0,
        'exited': 0,
        'failure_reasons': Counter(),
        'avg_cognitive_energy': [],
        'avg_perceived_risk': [],
        'avg_perceived_effort': [],
        'avg_perceived_value': []
    })
    
    # Failure reason analysis
    failure_reasons = Counter()
    
    # Persona-level analysis
    persona_exits = defaultdict(lambda: {
        'exit_steps': Counter(),
        'failure_reasons': Counter(),
        'completed': 0
    })
    
    for traj in trajectories:
        variant = traj.get('variant', 'unknown')
        journey = traj.get('journey', [])
        exit_step = traj.get('exit_step', 'Unknown')
        failure_reason = traj.get('failure_reason', 'None')
        completed = traj.get('completed', False)
        
        # Track failure reasons
        if not completed:
            failure_reasons[failure_reason] += 1
        
        # Track step progression
        for i, step_data in enumerate(journey):
            step_name = step_data.get('step', 'Unknown')
            step_stats[step_name]['entered'] += 1
            
            # Collect metrics
            if 'cognitive_energy' in step_data:
                step_stats[step_name]['avg_cognitive_energy'].append(step_data['cognitive_energy'])
            if 'perceived_risk' in step_data:
                step_stats[step_name]['avg_perceived_risk'].append(step_data['perceived_risk'])
            if 'perceived_effort' in step_data:
                step_stats[step_name]['avg_perceived_effort'].append(step_data['perceived_effort'])
            if 'perceived_value' in step_data:
                step_stats[step_name]['avg_perceived_value'].append(step_data['perceived_value'])
            
            # Check if this is where they exited
            continue_flag = step_data.get('continue', 'True')
            if continue_flag == 'False' or (i == len(journey) - 1 and not completed):
                step_stats[step_name]['exited'] += 1
                step_stats[step_name]['failure_reasons'][failure_reason] += 1
    
    # Calculate averages
    for step_name in step_stats:
        stats = step_stats[step_name]
        stats['drop_rate'] = (stats['exited'] / stats['entered'] * 100) if stats['entered'] > 0 else 0
        stats['avg_cognitive_energy'] = sum(stats['avg_cognitive_energy']) / len(stats['avg_cognitive_energy']) if stats['avg_cognitive_energy'] else 0
        stats['avg_perceived_risk'] = sum(stats['avg_perceived_risk']) / len(stats['avg_perceived_risk']) if stats['avg_perceived_risk'] else 0
        stats['avg_perceived_effort'] = sum(stats['avg_perceived_effort']) / len(stats['avg_perceived_effort']) if stats['avg_perceived_effort'] else 0
        stats['avg_perceived_value'] = sum(stats['avg_perceived_value']) / len(stats['avg_perceived_value']) if stats['avg_perceived_value'] else 0
        stats['dominant_failure_reason'] = stats['failure_reasons'].most_common(1)[0][0] if stats['failure_reasons'] else 'None'
    
    # Identify top problem steps
    problem_steps = sorted(
        [(name, stats) for name, stats in step_stats.items()],
        key=lambda x: x[1]['drop_rate'],
        reverse=True
    )[:10]
    
    print(f"✓ Analyzed {total_trajectories} trajectories")
    print(f"✓ Completion rate: {completion_rate:.1f}%")
    
    return {
        'total_trajectories': total_trajectories,
        'completed_count': completed_count,
        'completion_rate': completion_rate,
        'step_stats': dict(step_stats),
        'problem_steps': problem_steps,
        'failure_reasons': failure_reasons,  # Keep as Counter for .most_common()
        'scenario_info': {
            'product_type': data.get('fintech_archetype', 'Unknown'),
            'confidence': data.get('confidence', 'Unknown'),
            'target_group': data.get('target_group', 'Unknown')
        },
        'aggregated_results': aggregated_results,
        'aggregated_report_text': aggregated_report_text,
        'full_report': full_report
    }


def create_pdf_report(analysis: Dict, output_path: str, json_data: Dict):
    """Create comprehensive PDF report."""
    print(f"Generating PDF report: {output_path}...")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Behavioral Simulation Analysis Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Credigo.club Product Journey Analysis", styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary Box
    story.append(Paragraph("Executive Summary", heading1_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Trajectories Simulated', f"{analysis['total_trajectories']:,}"],
        ['Completed Journeys', f"{analysis['completed_count']:,}"],
        ['Overall Completion Rate', f"{analysis['completion_rate']:.1f}%"],
        ['Product Type', analysis['scenario_info']['product_type']],
        ['Analysis Confidence', analysis['scenario_info']['confidence'].title()],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(summary_table)
    story.append(PageBreak())
    
    # Section 1: What's Not Working
    story.append(Paragraph("1. What's Not Working in the Current Product", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "This section identifies the critical failure points in the user journey where users "
        "are abandoning the product. These are not just numbers—they represent real behavioral "
        "barriers preventing users from completing their goals.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    # Top Problem Steps
    story.append(Paragraph("Critical Drop-Off Points", heading2_style))
    
    problem_steps = analysis['problem_steps']
    if problem_steps:
        step_data = [
            ['Step Name', 'Drop Rate', 'Users Exited', 'Dominant Failure Reason']
        ]
        
        for step_name, stats in problem_steps[:8]:
            drop_rate = stats['drop_rate']
            exited = stats['exited']
            reason = stats['dominant_failure_reason']
            
            # Truncate long step names
            display_name = step_name[:50] + '...' if len(step_name) > 50 else step_name
            display_reason = reason[:40] + '...' if len(reason) > 40 else reason
            
            step_data.append([
                display_name,
                f"{drop_rate:.1f}%",
                f"{exited:,}",
                display_reason
            ])
        
        step_table = Table(step_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
        step_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
        ]))
        story.append(step_table)
    
    story.append(Spacer(1, 0.2*inch))
    
    # Failure Reasons Summary
    story.append(Paragraph("Why Users Are Leaving", heading2_style))
    
    failure_reasons = analysis['failure_reasons']
    if failure_reasons:
        reasons_data = [
            ['Failure Reason', 'Count', 'Percentage']
        ]
        
        # Convert to list of tuples if it's a Counter
        if isinstance(failure_reasons, Counter):
            failure_items = failure_reasons.most_common(5)
        else:
            # If it's already a dict, convert to sorted list
            failure_items = sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        
        total_failures = sum(failure_reasons.values())
        for reason, count in failure_items:
            pct = (count / total_failures * 100) if total_failures > 0 else 0
            reasons_data.append([
                reason,
                f"{count:,}",
                f"{pct:.1f}%"
            ])
        
        reasons_table = Table(reasons_data, colWidths=[3.5*inch, 1*inch, 1*inch])
        reasons_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f4ff')]),
        ]))
        story.append(reasons_table)
    
    story.append(PageBreak())
    
    # Section 2: Why It's Not Working
    story.append(Paragraph("2. Why It's Not Working: Behavioral Analysis", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "Understanding the 'why' behind user drop-offs requires examining the psychological "
        "and behavioral factors at play. Our simulation models cognitive energy, perceived risk, "
        "effort, and value—the key drivers of user decision-making.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    # Detailed Step Analysis
    story.append(Paragraph("Behavioral Metrics by Step", heading2_style))
    
    # Get top 5 problem steps for detailed analysis
    top_problems = analysis['problem_steps'][:5]
    
    for step_name, stats in top_problems:
        story.append(Paragraph(f"Step: {step_name[:60]}", heading2_style))
        
        metrics_data = [
            ['Metric', 'Average Value', 'Interpretation'],
            [
                'Drop Rate',
                f"{stats['drop_rate']:.1f}%",
                'High' if stats['drop_rate'] > 50 else 'Moderate' if stats['drop_rate'] > 25 else 'Low'
            ],
            [
                'Cognitive Energy',
                f"{stats['avg_cognitive_energy']:.2f}",
                'Depleted' if stats['avg_cognitive_energy'] < 0.2 else 'Low' if stats['avg_cognitive_energy'] < 0.5 else 'Adequate'
            ],
            [
                'Perceived Risk',
                f"{stats['avg_perceived_risk']:.2f}",
                'Very High' if stats['avg_perceived_risk'] > 0.8 else 'High' if stats['avg_perceived_risk'] > 0.5 else 'Moderate'
            ],
            [
                'Perceived Effort',
                f"{stats['avg_perceived_effort']:.2f}",
                'Very High' if stats['avg_perceived_effort'] > 1.0 else 'High' if stats['avg_perceived_effort'] > 0.7 else 'Moderate'
            ],
            [
                'Perceived Value',
                f"{stats['avg_perceived_value']:.2f}",
                'Low' if stats['avg_perceived_value'] < 0.3 else 'Moderate' if stats['avg_perceived_value'] < 0.5 else 'High'
            ],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Failure reason explanation
        if stats['dominant_failure_reason'] and stats['dominant_failure_reason'] != 'None':
            story.append(Paragraph(
                f"<b>Primary Failure Reason:</b> {stats['dominant_failure_reason']}",
                body_style
            ))
            story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # Section 3: What We've Been Solving
    story.append(Paragraph("3. What We've Been Solving: The Simulation Approach", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "Traditional analytics tell you <i>where</i> users drop off, but not <i>why</i>. "
        "Our behavioral simulation approach models the psychological factors that drive user decisions, "
        "enabling us to predict and understand drop-offs before they happen in production.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    story.append(Paragraph("The Behavioral Simulation Framework", heading2_style))
    
    approach_points = [
        "<b>1. Cognitive Energy Modeling:</b> Tracks users' mental resources as they progress through the journey. "
        "When cognitive energy depletes, users become more likely to abandon, even if they're interested.",
        
        "<b>2. Perceived Risk Assessment:</b> Models how risky each step feels to users. High perceived risk "
        "without adequate reassurance leads to abandonment, especially for financial products.",
        
        "<b>3. Effort-Value Balance:</b> Users continuously evaluate whether the effort required is worth the "
        "value they expect to receive. When effort exceeds perceived value, abandonment becomes likely.",
        
        "<b>4. State Variants:</b> Simulates users in different mental states (fresh, tired, distrustful, etc.) "
        "to understand how context affects behavior. This reveals which steps are sensitive to user state.",
        
        "<b>5. Failure Mode Identification:</b> Categorizes why users drop off (System 2 fatigue, value-risk mismatch, "
        "trust issues, etc.) to provide actionable insights rather than just metrics.",
        
        "<b>6. Predictive Analysis:</b> By modeling behavioral dynamics, we can predict drop-offs before they happen "
        "and test interventions in simulation rather than through expensive A/B tests.",
    ]
    
    for point in approach_points:
        story.append(Paragraph(point, body_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Insights from This Analysis", heading2_style))
    
    insights = []
    
    # Generate insights based on analysis
    if analysis['completion_rate'] < 10:
        insights.append(
            "The extremely low completion rate indicates fundamental structural issues in the user journey, "
            "not just isolated problems. This suggests the need for a comprehensive redesign rather than "
            "incremental improvements."
        )
    
    failure_reasons = analysis['failure_reasons']
    if isinstance(failure_reasons, Counter):
        failure_reasons_dict = dict(failure_reasons)
    else:
        failure_reasons_dict = failure_reasons
    
    if failure_reasons_dict.get('System 2 fatigue', 0) > 0:
        fatigue_count = failure_reasons_dict['System 2 fatigue']
        total_failures = sum(failure_reasons_dict.values())
        fatigue_pct = (fatigue_count / total_failures * 100) if total_failures > 0 else 0
        insights.append(
            f"System 2 fatigue accounts for {fatigue_pct:.1f}% of failures, indicating that the journey "
            "is too cognitively demanding. Users are mentally exhausted before they can complete the flow."
        )
    
    # Check for high effort steps
    high_effort_steps = [
        (name, stats) for name, stats in analysis['problem_steps']
        if stats['avg_perceived_effort'] > 0.8
    ]
    if high_effort_steps:
        insights.append(
            f"{len(high_effort_steps)} critical steps have very high perceived effort (>0.8), suggesting "
            "users find the process too difficult or time-consuming."
        )
    
    # Check for low value steps
    low_value_steps = [
        (name, stats) for name, stats in analysis['problem_steps']
        if stats['avg_perceived_value'] < 0.3
    ]
    if low_value_steps:
        insights.append(
            f"{len(low_value_steps)} critical steps have low perceived value (<0.3), meaning users don't "
            "see enough benefit to justify continuing."
        )
    
    if not insights:
        insights.append(
            "The simulation reveals multiple interconnected behavioral barriers. Addressing these requires "
            "a holistic approach that considers cognitive load, value communication, and risk management together."
        )
    
    for insight in insights:
        story.append(Paragraph(f"• {insight}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # Section 4: Recommendations
    story.append(Paragraph("4. Recommendations and Next Steps", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "Based on the behavioral analysis, here are prioritized recommendations to improve the user journey:",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    # Generate recommendations based on top problems
    recommendations = []
    
    for i, (step_name, stats) in enumerate(analysis['problem_steps'][:5], 1):
        rec_text = f"<b>Priority {i}: Address {step_name[:50]}</b><br/>"
        
        if stats['avg_perceived_effort'] > 0.8:
            rec_text += "• Reduce effort: Simplify the step, reduce required inputs, or use progressive disclosure.<br/>"
        
        if stats['avg_perceived_value'] < 0.3:
            rec_text += "• Increase value visibility: Show concrete benefits, use examples, or demonstrate progress toward value.<br/>"
        
        if stats['avg_perceived_risk'] > 0.7:
            rec_text += "• Reduce perceived risk: Add reassurance elements, social proof, or security indicators.<br/>"
        
        if stats['avg_cognitive_energy'] < 0.2:
            rec_text += "• Reduce cognitive load: Break complex decisions into smaller steps, provide defaults, or use visual aids.<br/>"
        
        if stats['dominant_failure_reason'] == 'System 2 fatigue':
            rec_text += "• Combat fatigue: Shorten the journey, provide breaks, or save progress for later.<br/>"
        
        recommendations.append(rec_text)
    
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 0.15*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Add aggregated insights if available
    if analysis.get('aggregated_results'):
        story.append(Paragraph("Additional Insights from Aggregated Analysis", heading2_style))
        story.append(Spacer(1, 0.15*inch))
        
        aggregated = analysis['aggregated_results']
        
        # Step summary if available
        if 'step_summary' in aggregated:
            story.append(Paragraph("Step-Level Failure Summary", heading2_style))
            step_summary = aggregated['step_summary']
            
            summary_data = [['Step', 'Failure Rate', 'Personas Affected', 'Dominant Reason']]
            for step_name, step_data in list(step_summary.items())[:8]:
                summary_data.append([
                    step_name[:40] + '...' if len(step_name) > 40 else step_name,
                    f"{step_data.get('failure_rate', 0):.1f}%",
                    f"{step_data.get('persona_count', 0):,}",
                    (step_data.get('dominant_reason', 'N/A') or 'N/A')[:30]
                ])
            
            if len(summary_data) > 1:
                agg_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.2*inch, 1.3*inch])
                agg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(agg_table)
                story.append(Spacer(1, 0.2*inch))
        
        # Interpretations if available
        if 'interpretations' in aggregated:
            interpretations = aggregated['interpretations']
            
            if interpretations.get('structural_flaws'):
                story.append(Paragraph("🔴 Structural Product Flaws", heading2_style))
                for flaw in interpretations['structural_flaws'][:3]:
                    story.append(Paragraph(f"• {flaw.get('interpretation', 'N/A')}", body_style))
                story.append(Spacer(1, 0.15*inch))
            
            if interpretations.get('intent_sensitive_steps'):
                story.append(Paragraph("🟡 Intent-Sensitive Steps", heading2_style))
                for step in interpretations['intent_sensitive_steps'][:3]:
                    story.append(Paragraph(f"• {step.get('interpretation', 'N/A')}", body_style))
                story.append(Spacer(1, 0.15*inch))
            
            if interpretations.get('fatigue_sensitive_steps'):
                story.append(Paragraph("🟠 Fatigue-Sensitive Steps", heading2_style))
                for step in interpretations['fatigue_sensitive_steps'][:3]:
                    story.append(Paragraph(f"• {step.get('interpretation', 'N/A')}", body_style))
                story.append(Spacer(1, 0.15*inch))
    
    # Add aggregated report text if available (as additional context)
    if analysis.get('aggregated_report_text'):
        story.append(PageBreak())
        story.append(Paragraph("5. Detailed Analysis Summary", heading1_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Split the report text into paragraphs and add
        report_text = analysis['aggregated_report_text']
        # Limit to first 2000 characters to avoid overwhelming the PDF
        if len(report_text) > 2000:
            report_text = report_text[:2000] + "...\n\n[Report truncated for brevity. Full analysis available in JSON data.]"
        
        # Split by lines and add as paragraphs
        for line in report_text.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))
                story.append(Spacer(1, 0.05*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("General Principles", heading2_style))
    
    principles = [
        "<b>1. Value First:</b> Always establish value proposition before asking for commitment or personal information.",
        "<b>2. Reduce Friction:</b> Minimize cognitive effort and perceived risk at every step.",
        "<b>3. Progressive Disclosure:</b> Don't overwhelm users—reveal information and requirements gradually.",
        "<b>4. Reassurance Throughout:</b> Build trust continuously, not just at the beginning.",
        "<b>5. Respect Cognitive Limits:</b> Keep the journey short enough that users don't exhaust their mental resources.",
    ]
    
    for principle in principles:
        story.append(Paragraph(principle, body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Footer with timestamp
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    print(f"✓ PDF report generated: {output_path}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate PDF report from simulation results')
    parser.add_argument(
        '--input',
        type=str,
        default='credigo_ss_targeted_explicit_results.json',
        help='Input JSON file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='credigo_simulation_report.pdf',
        help='Output PDF file path'
    )
    
    args = parser.parse_args()
    
    # Load and analyze
    json_data = load_json_data(args.input)
    analysis = analyze_trajectories(json_data)
    
    # Generate PDF
    create_pdf_report(analysis, args.output, json_data)
    
    print(f"\n✅ Report generation complete!")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")


if __name__ == '__main__':
    main()

