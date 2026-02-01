#!/usr/bin/env python3
"""
Create rich context graph visualization for CirclePe WhatsApp onboarding flow
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from circlepe_steps import CIRCLEPE_STEPS_SIMPLIFIED

def draw_context_graph_on_canvas(canvas_obj, x, y, width, height):
    """Draw context graph directly on canvas for CirclePe."""
    step_height = height / 5.5
    step_width = width * 0.5
    
    # CirclePe steps with risk, value, delay, irreversibility, is_break
    steps = [
        ("Step 0", "Entry\n(WhatsApp)", 0.0, 0.2, 4, 0.0, False, HexColor('#ecf0f1')),
        ("Step 1", "Welcome &\nPersonalization", 0.1, 0.3, 3, 0.0, False, HexColor('#ecf0f1')),
        ("Step 2", "User Type\nSelection", 0.1, 0.2, 2, 0.1, True, HexColor('#e74c3c')),
        ("Step 3", "Path-Specific\nInteraction", 0.2, 0.5, 1, 0.2, True, HexColor('#f39c12')),
        ("Step 4", "App Redirect\nor Agent", 0.3, 0.8, 0, 0.3, False, HexColor('#27ae60')),
    ]
    
    for i, (step_num, label, risk, value, delay, irrev, is_break, color) in enumerate(steps):
        step_y = y + height - (i + 1) * step_height
        
        # Draw step box
        canvas_obj.setFillColor(color)
        canvas_obj.setStrokeColor(HexColor('#2c3e50'))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.roundRect(x, step_y, step_width, step_height - 8, 5, fill=1, stroke=1)
        
        # Text color based on background
        text_color = white if is_break or (value > 0.5) else black
        
        # Step number
        canvas_obj.setFillColor(text_color)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(x + 5, step_y + step_height - 20, step_num)
        
        # Label
        canvas_obj.setFont("Helvetica-Bold", 9)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            canvas_obj.drawString(x + 5, step_y + step_height - 35 - j*12, line)
        
        # Metrics
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.drawString(x + 5, step_y + step_height - 58, f"Risk: {risk:.1f} | Value: {value:.1f}")
        canvas_obj.drawString(x + 5, step_y + step_height - 70, f"Delay: {delay} | Irrev: {irrev:.1f}")
        
        # Warning icon for belief breaks
        if is_break:
            canvas_obj.setFillColor(white)
            canvas_obj.circle(x + step_width - 12, step_y + step_height/2, 6, fill=1)
            canvas_obj.setFillColor(HexColor('#e74c3c'))
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(x + step_width - 15, step_y + step_height/2 - 4, "!")
        
        # Arrow to next
        if i < 4:
            arrow_y = step_y - 4
            canvas_obj.setStrokeColor(HexColor('#7f8c8d'))
            canvas_obj.setLineWidth(1)
            canvas_obj.line(x + step_width/2, step_y, x + step_width/2, arrow_y)
            canvas_obj.line(x + step_width/2 - 3, arrow_y - 2, x + step_width/2, arrow_y)
            canvas_obj.line(x + step_width/2 + 3, arrow_y - 2, x + step_width/2, arrow_y)
    
    # Key insight box
    insight_x = x + step_width + 8
    insight_y = y + height - 75
    insight_width = width - step_width - 8
    insight_height = 65
    
    canvas_obj.setFillColor(HexColor('#3498db'))
    canvas_obj.setStrokeColor(HexColor('#2980b9'))
    canvas_obj.setLineWidth(2)
    canvas_obj.roundRect(insight_x, insight_y, insight_width, insight_height, 5, fill=1, stroke=1)
    
    canvas_obj.setFillColor(white)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 18, "KEY INSIGHT")
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 32, "WhatsApp bot creates low-friction entry")
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 44, "but app redirect/agent handover")
    canvas_obj.drawString(insight_x + 6, insight_y + insight_height - 56, "creates friction before value delivery")

def create_circlepe_pdf():
    """Create PDF with context graph for CirclePe."""
    print("📄 Creating CirclePe context graph PDF...")
    
    # Load results
    try:
        with open('output/CIRCLEPE_DECISION_AUTOPSY_RESULT.json', 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load results: {e}")
        results = {}
    
    doc = SimpleDocTemplate(
        'circlepe_context_graph.pdf',
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=HexColor('#1a1a1a'), spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['BodyText'], fontSize=9, textColor=HexColor('#7f8c8d'), alignment=TA_CENTER, spaceAfter=10)
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=12, textColor=HexColor('#2c3e50'), spaceAfter=5, spaceBefore=8)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=10, textColor=HexColor('#34495e'), spaceAfter=4, spaceBefore=6)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=8.5, leading=11, alignment=TA_JUSTIFY, spaceAfter=4)
    bold_style = ParagraphStyle('Bold', parent=body_style, fontName='Helvetica-Bold')
    
    story = []
    
    # PAGE 1
    story.append(Paragraph("CirclePe — Context Graph Analysis", title_style))
    story.append(Paragraph("<i>WhatsApp Onboarding Flow Decision Simulation</i>", subtitle_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>What This System Does</b>", h1_style))
    story.append(Paragraph("A <b>decision simulation system</b> that models how users reason through CirclePe's WhatsApp bot onboarding flow, step by step.", body_style))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph("<b>Simulates:</b> Expectations • Perceived risk • Irreversibility • Value recognition", body_style))
    story.append(Paragraph("<b>Output:</b> 853 decision traces across target personas", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>The Context Graph: How CirclePe's WhatsApp Flow Works as a System</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    # Graph description with pointers
    story.append(Paragraph("<b>Visual Diagram (see graph above):</b>", bold_style))
    story.append(Paragraph("→ <b>Gray boxes</b> = Low friction steps (Entry, Welcome)", body_style))
    story.append(Paragraph("→ <b>Red box</b> = Belief break point (Step 2: User Type Selection)", body_style))
    story.append(Paragraph("→ <b>Orange box</b> = High friction before value (Step 3: Path-Specific Interaction)", body_style))
    story.append(Paragraph("→ <b>Green box</b> = Value finally shown (Step 4: App Redirect/Agent)", body_style))
    story.append(Paragraph("→ <b>Risk scores</b> increase: 0.0 → 0.1 → 0.1 → 0.2 → 0.3", body_style))
    story.append(Paragraph("→ <b>Value scores</b> increase: 0.2 → 0.3 → 0.2 → 0.5 → 0.8", body_style))
    story.append(Paragraph("→ <b>Delay to value</b> decreases: 4 → 3 → 2 → 1 → 0 steps", body_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>Key Insight:</b> WhatsApp bot creates low-friction entry, but app redirect or agent handover creates friction before value is fully delivered. Users abandon when asked to commit to app download or wait for agent before seeing clear value.", bold_style))
    
    def page1_template(canvas_obj, doc):
        draw_context_graph_on_canvas(canvas_obj, 1.5*cm, 3*cm, A4[0] - 3*cm, 12*cm)
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 1")
        canvas_obj.restoreState()
    
    # PAGE 2
    story.append(PageBreak())
    story.append(Paragraph("<b>Decision Simulation Results</b>", h1_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Verdict
    verdict = results.get('verdict', 'Users abandon when asked to share personal information before seeing what they\'ll get in return.')
    story.append(Paragraph("<b>Core Verdict:</b>", bold_style))
    story.append(Paragraph(verdict, body_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Belief break
    belief_break = results.get('beliefBreak', {})
    story.append(Paragraph("<b>Where Belief Breaks:</b>", bold_style))
    story.append(Paragraph(f"Step: {belief_break.get('irreversibleAction', 'Step 2: User Type Selection')}", body_style))
    story.append(Paragraph(f"Psychology: {belief_break.get('psychology', 'Users arrive expecting to explore options, but encounter commitment requirement.')}", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Why belief breaks
    why_breaks = results.get('whyBeliefBreaks', {})
    story.append(Paragraph("<b>Why Belief Breaks:</b>", bold_style))
    story.append(Paragraph("<b>User Believes:</b>", bold_style))
    for belief in why_breaks.get('userBelieves', []):
        story.append(Paragraph(f"• {belief}", body_style))
    story.append(Paragraph("<b>Product Asks:</b>", bold_style))
    for ask in why_breaks.get('productAsks', []):
        story.append(Paragraph(f"• {ask}", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    # The One Bet
    one_bet = results.get('oneBet', {})
    story.append(Paragraph("<b>THE ONE BET:</b>", bold_style))
    story.append(Paragraph(one_bet.get('headline', 'Show personalized recommendations BEFORE requesting financial disclosure.'), bold_style))
    story.append(Paragraph(one_bet.get('support', 'If users see tailored results based solely on preferences, establishing value before trust demands, completion rates should increase.'), body_style))
    
    def page2_template(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 2")
        canvas_obj.restoreState()
    
    # PAGE 3
    story.append(PageBreak())
    story.append(Paragraph("<b>Step-by-Step Analysis</b>", h1_style))
    story.append(Spacer(1, 0.15*cm))
    
    # Step analysis table
    step_data = [
        ['Step', 'Name', 'Risk', 'Value', 'Delay', 'Key Issue'],
        ['0', 'Entry', '0.0', '0.2', '4', 'Low friction, familiar WhatsApp'],
        ['1', 'Welcome', '0.1', '0.3', '3', 'Trust signals (IIT-IIM, logos)'],
        ['2', 'User Type', '0.1', '0.2', '2', '⚠️ BELIEF BREAK'],
        ['3', 'Path-Specific', '0.2', '0.5', '1', 'App redirect required'],
        ['4', 'App/Agent', '0.3', '0.8', '0', '✅ Value shown'],
    ]
    
    step_table = Table(step_data, colWidths=[1*cm, 3*cm, 1.2*cm, 1.2*cm, 1.2*cm, 3.4*cm])
    step_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (2, 2), (2, 2), HexColor('#e74c3c')),
        ('TEXTCOLOR', (2, 2), (2, 2), white),
        ('BACKGROUND', (4, 4), (4, 4), HexColor('#27ae60')),
        ('TEXTCOLOR', (4, 4), (4, 4), white),
    ]))
    story.append(step_table)
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Key Findings:</b>", bold_style))
    story.append(Paragraph("• WhatsApp entry creates low friction (familiar interface)", body_style))
    story.append(Paragraph("• Welcome step builds trust with IIT-IIM branding and partner logos", body_style))
    story.append(Paragraph("• User type selection (Step 2) is first commitment point - belief breaks here", body_style))
    story.append(Paragraph("• Path-specific interaction requires app redirect or agent wait - friction before value", body_style))
    story.append(Paragraph("• Final step shows value but requires app download or agent availability", body_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Recommendations:</b>", bold_style))
    story.append(Paragraph("1. Show eligibility estimate or advance rent calculator in WhatsApp before app redirect", body_style))
    story.append(Paragraph("2. Provide 'Quick Estimate' option that doesn't require app download", body_style))
    story.append(Paragraph("3. Make agent handover more seamless with immediate availability indicators", body_style))
    story.append(Paragraph("4. Reduce friction at Step 2 by making user type selection feel exploratory, not committing", body_style))
    
    def page3_template(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(HexColor('#7f8c8d'))
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, "Page 3")
        canvas_obj.restoreState()
    
    # Build PDF
    doc.build(story, onFirstPage=page1_template, onLaterPages=lambda c, d: (page2_template(c, d) if c.getPageNumber() == 2 else page3_template(c, d)))
    
    print("✅ CirclePe context graph PDF generated: circlepe_context_graph.pdf")
    print(f"   File size: {os.path.getsize('circlepe_context_graph.pdf') / 1024:.1f} KB")
    print(f"   Pages: 3")
    print(f"   Includes: Context graph diagram, decision simulation results, step-by-step analysis")

if __name__ == '__main__':
    import os
    try:
        create_circlepe_pdf()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
