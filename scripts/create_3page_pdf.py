#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Create a beautiful 3-page PDF with visual elements.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics import renderPDF
import os

def draw_context_graph(canvas_obj, x, y, width, height):
    """Draw the context graph visualization."""
    # Draw boxes for each step
    step_height = height / 5
    step_width = width * 0.4
    
    steps = [
        ("Step 0: Smart Credit\nExploration", 0.1, 0.3, 4, 0.0),
        ("Step 1: Eligibility Check\n(Phone Number)", 0.3, 0.0, 3, 0.2),
        ("Step 2: PAN & DOB\nInput", 0.7, 0.0, 2, 0.4),
        ("Step 3: OTP\nVerification", 0.6, 0.0, 1, 0.3),
        ("Step 4: Eligibility\nConfirmation", 0.0, 0.8, 0, 0.1),
    ]
    
    for i, (label, risk, value, delay, irrev) in enumerate(steps):
        step_y = y + height - (i + 1) * step_height
        
        # Draw step box
        canvas_obj.setStrokeColor(HexColor('#2c3e50'))
        canvas_obj.setFillColor(HexColor('#ecf0f1'))
        canvas_obj.rect(x, step_y, step_width, step_height - 5, fill=1, stroke=1)
        
        # Add label
        canvas_obj.setFillColor(black)
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(x + 5, step_y + step_height - 20, label)
        
        # Add metrics
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(x + 5, step_y + step_height - 35, f"Risk: {risk:.1f} | Value: {value:.1f}")
        canvas_obj.drawString(x + 5, step_y + step_height - 48, f"Delay: {delay} steps | Irrev: {irrev:.1f}")
        
        # Mark belief break points
        if i < 3:
            canvas_obj.setFillColor(HexColor('#e74c3c'))
            canvas_obj.circle(x + step_width - 15, step_y + step_height/2, 5, fill=1)
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.drawString(x + step_width - 12, step_y + step_height/2 - 3, "!")
        
        # Draw arrow to next step
        if i < 4:
            canvas_obj.setStrokeColor(HexColor('#7f8c8d'))
            canvas_obj.line(x + step_width/2, step_y, x + step_width/2, step_y - 5)
            canvas_obj.line(x + step_width/2 - 3, step_y - 3, x + step_width/2, step_y - 5)
            canvas_obj.line(x + step_width/2 + 3, step_y - 3, x + step_width/2, step_y - 5)
    
    # Add key insight box
    insight_y = y + 10
    canvas_obj.setFillColor(HexColor('#3498db'))
    canvas_obj.setStrokeColor(HexColor('#2980b9'))
    canvas_obj.rect(x + step_width + 10, insight_y, width - step_width - 10, 60, fill=1, stroke=1)
    canvas_obj.setFillColor(white)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(x + step_width + 15, insight_y + 40, "KEY INSIGHT:")
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawString(x + step_width + 15, insight_y + 25, "Trust demanded at Steps 1-3")
    canvas_obj.drawString(x + step_width + 15, insight_y + 15, "Value delayed until Step 4")
    canvas_obj.drawString(x + step_width + 15, insight_y + 5, "This misalignment causes abandonment")

def create_3page_pdf():
    """Create 3-page PDF."""
    os.makedirs("output", exist_ok=True)
    print("📄 Creating 3-page PDF...")
    
    doc = SimpleDocTemplate(
        'output/blink_money_3page_brief.pdf',
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=8
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    # Build story
    story = []
    
    # PAGE 1: Overview and Context Graph
    story.append(Paragraph("Blink Money — Technical Intelligence Brief", title_style))
    story.append(Paragraph("<i>How user decision-making unfolds inside the product</i>", body_style))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>What This System Does</b>", h1_style))
    story.append(Paragraph("This is a <b>decision simulation system</b> that models how users reason through your product, step by step.", body_style))
    story.append(Paragraph("<b>Instead of tracking clicks, we simulate:</b>", bold_style))
    story.append(Paragraph("• What users expect to see", body_style))
    story.append(Paragraph("• How risky each action feels", body_style))
    story.append(Paragraph("• Which actions feel irreversible", body_style))
    story.append(Paragraph("• When value becomes visible", body_style))
    story.append(Paragraph("<b>Output:</b> 13 decision traces across 5 personas, revealing where belief breaks and why.", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>The Context Graph: How Your Product Works as a System</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Add context graph description
    graph_text = """
    <b>STEP 0:</b> Smart Credit Exploration (Risk: 0.1, Value: 0.3, Delay: 4 steps)<br/>
    <b>STEP 1:</b> Eligibility Check - Phone Number (Risk: 0.3, Value: 0.0, Delay: 3 steps) ⚠️ BELIEF BREAK<br/>
    <b>STEP 2:</b> PAN & DOB Input (Risk: 0.7, Value: 0.0, Delay: 2 steps) ⚠️ BELIEF BREAK<br/>
    <b>STEP 3:</b> OTP Verification (Risk: 0.6, Value: 0.0, Delay: 1 step) ⚠️ BELIEF BREAK<br/>
    <b>STEP 4:</b> Eligibility Confirmation (Risk: 0.0, Value: 0.8, Delay: 0) ✅ VALUE SHOWN<br/>
    <br/>
    <b>KEY INSIGHT:</b> Trust is demanded at Steps 1-3 (phone, PAN, OTP) but no value is shown. 
    Value is delayed until Step 4. This misalignment causes abandonment.
    """
    story.append(Paragraph(graph_text, body_style))
    story.append(PageBreak())
    
    # PAGE 2: Persona Patterns and Non-Obvious Patterns
    story.append(Paragraph("<b>Persona Decision Patterns</b>", h1_style))
    story.append(Paragraph("<i>Five User Mindsets Through the Same Flow</i>", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Persona table
    persona_data = [
        ['Persona', 'Drop Rate', 'Drop Step', 'Primary Concern'],
        ['Salaried Professionals', '38%', 'Step 1', 'Delay in seeing credit limit'],
        ['Self-Employed', '35%', 'Step 2', 'PAN/DOB anxiety, credit score impact'],
        ['Credit-Aware', '40%', 'Step 3', 'Comparison to alternatives'],
        ['Speed-Seekers', '42%', 'Step 0', '5-step process feels slow'],
        ['Cost-Conscious', '45%', 'Step 4', 'Unclear interest rates/terms'],
    ]
    
    persona_table = Table(persona_data, colWidths=[4*cm, 2*cm, 2.5*cm, 5*cm])
    persona_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(persona_table)
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Shared Pattern:</b> All five abandon when asked to share personal information before seeing value.", bold_style))
    story.append(Paragraph("<b>Different Reasons, Same Structural Flaw:</b>", bold_style))
    story.append(Paragraph("• Salaried: 'I don't see my limit yet' (value delay)", body_style))
    story.append(Paragraph("• Self-employed: 'I'm anxious about data sharing' (risk perception)", body_style))
    story.append(Paragraph("• Credit-aware: 'I'm comparing to alternatives' (comparison need)", body_style))
    story.append(Paragraph("<b>The Insight:</b> Same step fails for different psychological reasons, but all point to the same structural issue: <b>value comes too late</b>.", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Non-Obvious Patterns</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Pattern 1: Progress Indicators Increase Anxiety</b>", h2_style))
    story.append(Paragraph("<b>What Teams Assume:</b> 'Step 2 of 5' indicator reduces friction by showing progress.", body_style))
    story.append(Paragraph("<b>What Actually Happens:</b> User sees '40% complete' → expects smooth progress → Step 2 introduces new friction → expectation mismatch triggers abandonment.", body_style))
    story.append(Paragraph("<b>The Insight:</b> Progress indicators work when they match expectations. They fail when they don't.", bold_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Pattern 2: Trust Signals Ineffective Before Value</b>", h2_style))
    story.append(Paragraph("<b>What Teams Assume:</b> Partner logos (HDFC, Axis, SBI) build trust and reduce abandonment.", body_style))
    story.append(Paragraph("<b>What Actually Happens:</b> Trust signals visible at Steps 1-3, but abandonment still occurs. Trust signals become effective at Step 4 (when value is shown).", body_style))
    story.append(Paragraph("<b>The Insight:</b> Trust signals work when trust already exists. They don't create it. Showing value first creates trust; trust signals reinforce it.", bold_style))
    story.append(PageBreak())
    
    # PAGE 3: Core Insight and What This Enables
    story.append(Paragraph("<b>The Core Structural Insight</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>The Flaw:</b> Sequencing and trust, not UX or copy.", bold_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>The Problem:</b>", bold_style))
    story.append(Paragraph("• <b>Irreversible actions</b> (phone, PAN, OTP) appear at Steps 1-3", body_style))
    story.append(Paragraph("• <b>Reversible value</b> (credit limit) appears at Step 4", body_style))
    story.append(Paragraph("• Users are asked to trust before they see what they'll get", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Why This Matters:</b>", bold_style))
    story.append(Paragraph("• Irreversible actions feel like commitments", body_style))
    story.append(Paragraph("• Reversible value feels like exploration", body_style))
    story.append(Paragraph("• When commitment comes before exploration, users leave", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>The Fix:</b> Show credit limit estimate after phone + PAN (Step 2-3), before OTP. This establishes value before asking for more trust.", bold_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("<b>What This Enables</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>See blind spots before metrics move</b>", h2_style))
    story.append(Paragraph("Traditional analytics show problems after they happen. This system shows where problems will occur before users encounter them.", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Align teams around shared diagnosis</b>", h2_style))
    story.append(Paragraph("Product, growth, and engineering see the same structural issue. No debate about whether problem is UX or copy or targeting.", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Make smaller, safer bets</b>", h2_style))
    story.append(Paragraph("Every recommendation includes risk assessment and learning goals. Reversible changes with clear rollback plans.", body_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("<b>Closing Perspective</b>", h1_style))
    story.append(Paragraph("This is about seeing how users decide, not forcing them to convert. When you understand the decision-making process, you can design products that align with how users actually think, not how you hope they think.", body_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<i>Analysis based on 13 decision traces across 5 personas, 5 product steps, and 3-level inference depth. All insights derived from structured decision simulations.</i>", ParagraphStyle('Footer', parent=body_style, fontSize=7, textColor=HexColor('#7f8c8d'))))
    
    # Build PDF
    doc.build(story)
    print("✅ 3-page PDF generated: output/blink_money_3page_brief.pdf")
    print(f"   File size: {os.path.getsize('output/blink_money_3page_brief.pdf') / 1024:.1f} KB")

if __name__ == '__main__':
    try:
        create_3page_pdf()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
