# PDF Generation Instructions

## Option 1: Install Pandoc (Recommended for Best Quality)

### Install Pandoc on macOS:
```bash
# Using Homebrew (if you have it)
brew install pandoc
brew install basictex  # or mactex for full LaTeX support

# Then generate PDF:
pandoc blink_money_technical_brief_enhanced.md -o blink_money_technical_brief.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=2cm \
  -V fontfamily=georgia \
  -V fontsize=11pt
```

### Alternative: Install via MacPorts or download from:
https://pandoc.org/installing.html

---

## Option 2: Use Python with WeasyPrint

```bash
# Install dependencies
pip3 install weasyprint markdown

# Run the script
python3 generate_pdf_brief.py
```

---

## Option 3: Use Online Converters

1. **Dillinger.io** (https://dillinger.io/)
   - Open the markdown file
   - Click "Export as" → "PDF"

2. **Markdown to PDF** (https://www.markdowntopdf.com/)
   - Upload `blink_money_technical_brief_enhanced.md`
   - Download PDF

3. **VS Code Extension**
   - Install "Markdown PDF" extension
   - Open the .md file
   - Right-click → "Markdown PDF: Export (pdf)"

---

## Option 4: Use Google Docs / Word

1. Copy the markdown content
2. Paste into Google Docs or Word
3. Format as needed
4. Export as PDF

---

## Quick Install (Homebrew)

If you have Homebrew installed, run:
```bash
brew install pandoc basictex
```

Then use the pandoc command shown in Option 1.
