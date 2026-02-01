#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Generate PDF using ReportLab (already installed).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
import re

def clean_markdown(text):
    """Simple markdown to plain text converter."""
    # Remove markdown headers
    text = re.sub(r'^#+\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text.strip()

def parse_markdown_file(filename):
    """Parse markdown file into sections."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sections = []
    current_section = {'title': '', 'content': []}
    
    for line in content.split('\n'):
        # Check for headers
        if line.startswith('#'):
            if current_section['title']:
                sections.append(current_section)
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            current_section = {'title': title, 'level': level, 'content': []}
        elif line.strip() == '---':
            if current_section['title']:
                sections.append(current_section)
            current_section = {'title': '', 'content': []}
        elif line.strip():
            current_section['content'].append(line)
        else:
            current_section['content'].append('')
    
    if current_section['title']:
        sections.append(current_section)
    
    return sections

def create_pdf():
    """Create PDF document."""
    print("📄 Reading markdown file...")
    sections = parse_markdown_file('blink_money_technical_brief_enhanced.md')
    
    print("📄 Creating PDF...")
    doc = SimpleDocTemplate(
        'blink_money_technical_brief.pdf',
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=18
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    # Build story
    story = []
    
    for section in sections:
        if not section['title']:
            continue
        
        level = section.get('level', 1)
        title = section['title']
        content = '\n'.join(section['content'])
        
        # Add title
        if level == 1:
            story.append(Paragraph(title, title_style))
        elif level == 2:
            story.append(Paragraph(title, h1_style))
        elif level == 3:
            story.append(Paragraph(title, h2_style))
        
        story.append(Spacer(1, 0.3*cm))
        
        # Add content
        if content.strip():
            # Split into paragraphs
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Clean markdown
                    para = clean_markdown(para)
                    # Handle bullet points
                    if para.startswith('- ') or para.startswith('* '):
                        para = '• ' + para[2:]
                    story.append(Paragraph(para, body_style))
                    story.append(Spacer(1, 0.2*cm))
        
        story.append(Spacer(1, 0.5*cm))
    
    # Build PDF
    doc.build(story)
    print("✅ PDF generated: blink_money_technical_brief.pdf")
    print(f"   File size: {os.path.getsize('blink_money_technical_brief.pdf') / 1024:.1f} KB")

if __name__ == '__main__':
    import os
    try:
        create_pdf()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
