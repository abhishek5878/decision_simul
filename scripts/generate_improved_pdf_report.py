#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Generate comprehensive PDF report from improved simulation results.
"""

import json
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def load_results(filepath: str) -> Dict:
    """Load improved simulation results JSON."""
    print(f"Loading results from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded results successfully")
    return data


def create_improved_pdf_report(data: Dict, output_path: str):
    """Create comprehensive PDF report from improved simulation results."""
    print(f"Generating PDF report: {output_path}...")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
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
    story.append(Paragraph("Credigo.club Simulation Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Improved Behavioral Engine Results", styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading1_style))
    
    overall_completion = data.get('overall_completion_rate', 0) * 100
    total_personas = data.get('total_personas', 0)
    total_trajectories = data.get('total_trajectories', 0)
    completed = int(total_trajectories * data.get('overall_completion_rate', 0))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Personas Simulated', f"{total_personas:,}"],
        ['Total Trajectories', f"{total_trajectories:,}"],
        ['Completed Trajectories', f"{completed:,}"],
        ['Overall Completion Rate', f"{overall_completion:.1f}%"],
        ['Simulation Type', data.get('simulation_type', 'Improved Behavioral Engine')],
        ['Product', data.get('product', 'Credigo.club')],
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
    
    # Section 1: Funnel Analysis
    story.append(Paragraph("1. Funnel Analysis: Step-by-Step Drop-Off", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "This section shows where users are dropping off at each step of the Credigo.club journey. "
        "Understanding these drop-off points helps identify which steps need the most attention.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    funnel_data = data.get('funnel_analysis', {})
    if funnel_data:
        funnel_table_data = [
            ['Step', 'Users Entering', 'Users Exiting', 'Drop Rate', 'Cumulative Loss']
        ]
        
        cumulative_entered = total_trajectories
        cumulative_exited = 0
        
        for step_name, step_data in funnel_data.items():
            entered = step_data.get('entered', 0)
            exited = step_data.get('exited', 0)
            drop_rate = step_data.get('drop_rate', 0)
            cumulative_exited += exited
            cumulative_loss = (cumulative_exited / total_trajectories * 100) if total_trajectories > 0 else 0
            
            funnel_table_data.append([
                step_name,
                f"{entered:,}",
                f"{exited:,}",
                f"{drop_rate:.1f}%",
                f"{cumulative_loss:.1f}%"
            ])
        
        # Add completed row
        funnel_table_data.append([
            'Completed',
            f"{total_trajectories:,}",
            f"{completed:,}",
            'N/A',
            'N/A'
        ])
        
        funnel_table = Table(funnel_table_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1*inch, 1.2*inch])
        funnel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
        ]))
        story.append(funnel_table)
    
    story.append(PageBreak())
    
    # Section 2: Failure Reasons
    story.append(Paragraph("2. Why Users Are Leaving: Failure Reasons", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "Understanding the behavioral reasons behind drop-offs helps identify what's driving users away. "
        "The improved model tracks multiple failure modes, not just cognitive fatigue.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    failure_reasons = data.get('failure_reasons', {})
    if failure_reasons:
        reasons_data = [
            ['Failure Reason', 'Count', 'Percentage']
        ]
        
        total_failures = sum(failure_reasons.values())
        for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
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
    else:
        story.append(Paragraph("No failure data available.", body_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Exit Step Distribution
    story.append(Paragraph("Exit Step Distribution", heading2_style))
    
    exit_steps = data.get('exit_steps', {})
    if exit_steps:
        exit_data = [
            ['Exit Step', 'Count', 'Percentage']
        ]
        
        total_exits = sum(exit_steps.values())
        for step, count in sorted(exit_steps.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (count / total_exits * 100) if total_exits > 0 else 0
            exit_data.append([
                step[:40] + '...' if len(step) > 40 else step,
                f"{count:,}",
                f"{pct:.1f}%"
            ])
        
        exit_table = Table(exit_data, colWidths=[3.5*inch, 1*inch, 1*inch])
        exit_table.setStyle(TableStyle([
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
        story.append(exit_table)
    
    story.append(PageBreak())
    
    # Section 3: Behavioral Insights
    story.append(Paragraph("3. Behavioral Insights: What's Working", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Energy Recovery
    energy_recovery = data.get('energy_recovery', {})
    if energy_recovery:
        story.append(Paragraph("Energy Recovery Mechanisms", heading2_style))
        
        recovery_events = energy_recovery.get('total_events', 0)
        recovery_rate = energy_recovery.get('recovery_rate', 0)
        
        story.append(Paragraph(
            f"The improved model includes energy recovery mechanisms where users can regain cognitive "
            f"energy when they see value, make progress, or receive reassurance. "
            f"<b>{recovery_events:,} recovery events</b> were detected ({recovery_rate:.1f}% of steps), "
            f"demonstrating that users can recover from low energy states.",
            body_style
        ))
        story.append(Spacer(1, 0.15*inch))
    
    # Persona Variance
    persona_variance = data.get('persona_variance', {})
    if persona_variance:
        story.append(Paragraph("Persona Behavioral Diversity", heading2_style))
        
        mean = persona_variance.get('mean', 0) * 100
        median = persona_variance.get('median', 0) * 100
        std_dev = persona_variance.get('std_dev', 0) * 100
        min_rate = persona_variance.get('min', 0) * 100
        max_rate = persona_variance.get('max', 0) * 100
        
        variance_data = [
            ['Metric', 'Value'],
            ['Mean Completion Rate', f"{mean:.1f}%"],
            ['Median Completion Rate', f"{median:.1f}%"],
            ['Standard Deviation', f"{std_dev:.1f}%"],
            ['Minimum', f"{min_rate:.1f}%"],
            ['Maximum', f"{max_rate:.1f}%"],
        ]
        
        variance_table = Table(variance_data, colWidths=[3*inch, 2*inch])
        variance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(variance_table)
        
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph(
            f"The completion rate ranges from {min_rate:.1f}% to {max_rate:.1f}%, with a standard deviation "
            f"of {std_dev:.1f}%, showing good behavioral diversity across different persona archetypes.",
            body_style
        ))
    
    story.append(PageBreak())
    
    # Section 4: Key Improvements
    story.append(Paragraph("4. Model Improvements: What Changed", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    improvements = [
        "<b>1. Probabilistic Decisions:</b> Instead of binary drop/continue decisions, the model now uses "
        "probabilistic continuation. This prevents total collapse and creates realistic variance.",
        
        "<b>2. Energy Recovery:</b> Cognitive energy can now recover when users see value, make progress, "
        "or receive reassurance. This creates realistic 'second wind' moments.",
        
        "<b>3. Value Override:</b> High perceived value can override fatigue, allowing users to push through "
        "even when cognitive energy is low. This models real-world persistence.",
        
        "<b>4. Commitment Effect:</b> Users who've made progress are more likely to continue, modeling the "
        "sunk cost effect. Later steps show higher continuation rates.",
        
        "<b>5. Heterogeneous Behavior:</b> Different persona archetypes behave differently based on their "
        "traits (digital literacy, aspiration, risk tolerance, etc.).",
        
        "<b>6. Minimum Persistence:</b> Even in worst-case scenarios, some users (10%) continue, preventing "
        "unrealistic total collapse.",
    ]
    
    for improvement in improvements:
        story.append(Paragraph(improvement, body_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # Section 5: Recommendations
    story.append(Paragraph("5. Recommendations and Next Steps", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(
        "Based on the simulation results, here are prioritized recommendations to improve the Credigo.club user journey:",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    # Generate recommendations based on funnel data
    recommendations = []
    
    if funnel_data:
        # Sort by drop rate
        sorted_steps = sorted(
            funnel_data.items(),
            key=lambda x: x[1].get('drop_rate', 0),
            reverse=True
        )[:5]
        
        for i, (step_name, step_data) in enumerate(sorted_steps, 1):
            drop_rate = step_data.get('drop_rate', 0)
            entered = step_data.get('entered', 0)
            
            if drop_rate > 30:  # High drop rate
                rec_text = f"<b>Priority {i}: Address {step_name}</b><br/>"
                rec_text += f"• <b>Problem:</b> {drop_rate:.1f}% drop rate ({step_data.get('exited', 0):,} users)<br/>"
                
                if 'Landing' in step_name:
                    rec_text += "• <b>Solution:</b> Improve value proposition clarity, add social proof, reduce perceived risk<br/>"
                elif 'Quiz' in step_name:
                    rec_text += "• <b>Solution:</b> Reduce cognitive load, show progress, add value signals<br/>"
                else:
                    rec_text += "• <b>Solution:</b> Reduce effort, increase value visibility, add reassurance<br/>"
                
                recommendations.append(rec_text)
    
    if not recommendations:
        recommendations.append(
            "<b>General Recommendations:</b><br/>"
            "• Focus on early steps where most drop-offs occur<br/>"
            "• Increase value visibility throughout the journey<br/>"
            "• Reduce cognitive load and effort requirements<br/>"
            "• Add progress indicators and reassurance elements"
        )
    
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 0.15*inch))
    
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
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    timestamp = data.get('timestamp', datetime.now().isoformat())
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        formatted_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    story.append(Paragraph(
        f"<i>Report generated on {formatted_time}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    print(f"✓ PDF report generated: {output_path}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate PDF report from improved simulation results')
    parser.add_argument(
        '--input',
        type=str,
        default='credigo_improved_results.json',
        help='Input JSON file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='credigo_improved_simulation_report.pdf',
        help='Output PDF file path'
    )
    
    args = parser.parse_args()
    
    # Load and generate PDF
    data = load_results(args.input)
    create_improved_pdf_report(data, args.output)
    
    print(f"\n✅ Report generation complete!")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")


if __name__ == '__main__':
    main()

