#!/usr/bin/env python3
import sys
from pathlib import Path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"""
Generate a beautiful PDF from the technical brief markdown.
"""

from markdown import markdown
from weasyprint import HTML, CSS
import os

def generate_pdf():
    # Read the markdown file
    with open('blink_money_technical_brief_enhanced.md', 'r') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown(markdown_content, extensions=['extra', 'codehilite'])
    
    # Add custom CSS for beautiful formatting
    css = """
    @page {
        size: A4;
        margin: 2cm;
    }
    
    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        font-size: 24pt;
        font-weight: bold;
        color: #1a1a1a;
        margin-top: 0;
        margin-bottom: 0.5em;
        border-bottom: 3px solid #2c3e50;
        padding-bottom: 0.3em;
    }
    
    h2 {
        font-size: 18pt;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.2em;
    }
    
    h3 {
        font-size: 14pt;
        font-weight: bold;
        color: #34495e;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    
    p {
        margin: 0.8em 0;
        text-align: justify;
    }
    
    ul, ol {
        margin: 0.8em 0;
        padding-left: 2em;
    }
    
    li {
        margin: 0.4em 0;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    
    pre {
        background-color: #f8f8f8;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1em;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
        line-height: 1.4;
    }
    
    strong {
        color: #2c3e50;
        font-weight: bold;
    }
    
    em {
        font-style: italic;
        color: #555;
    }
    
    hr {
        border: none;
        border-top: 2px solid #e0e0e0;
        margin: 2em 0;
    }
    
    blockquote {
        border-left: 4px solid #3498db;
        margin: 1em 0;
        padding-left: 1em;
        color: #555;
        font-style: italic;
    }
    """
    
    # Wrap HTML content
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF
    HTML(string=full_html).write_pdf('blink_money_technical_brief.pdf')
    print("✅ PDF generated: blink_money_technical_brief.pdf")

if __name__ == '__main__':
    try:
        generate_pdf()
    except ImportError:
        print("⚠️  WeasyPrint not installed. Install with: pip install weasyprint markdown")
        print("   Or use pandoc: pandoc blink_money_technical_brief_enhanced.md -o blink_money_technical_brief.pdf")
    except Exception as e:
        print(f"❌ Error: {e}")
