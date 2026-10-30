import re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Canvas to handle two-pass page numbering: Page X of Y and clean running footer.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Bottom rule
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)
        
        # Footer text
        self.drawString(40, 28, "Watch Less. Understand More.")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 28, page_str)
        self.restoreState()


def clean_markdown_inline(text):
    """
    Converts basic markdown inline styles into ReportLab HTML tags.
    """
    
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#2563EB">\1</font>', text)
    return text


def build_notes_pdf(title, notes_text, topics_text=None, video_url=None):
    """
    Generates a professional, cleanly styled PDF containing notes and key topics.
    Returns BytesIO object.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#1E293B")
    accent_color = colors.HexColor("#2563EB")
    sub_color = colors.HexColor("#475569")
    card_bg = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=accent_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    numbered_style = ParagraphStyle(
        'NumberedItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=18,
        firstLineIndent=-12,
        spaceAfter=4
    )

    story = []

    clean_title = (title or "YouTube Video Notes").strip()
    story.append(Paragraph(clean_title, title_style))
    
    meta_parts = []
    if video_url:
        meta_parts.append(f"Source: {video_url}")
    meta_parts.append("Generated with Synthesis & RAG")
    story.append(Paragraph(" • ".join(meta_parts), meta_style))

    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=14))

    def process_markdown_block(raw_text):
        if not raw_text:
            return
        lines = raw_text.splitlines()
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue

            if line.startswith("### "):
                clean_text = clean_markdown_inline(line[4:].strip())
                story.append(Paragraph(clean_text, h2_style))
            elif line.startswith("## "):
                clean_text = clean_markdown_inline(line[3:].strip())
                story.append(Paragraph(clean_text, h1_style))
            elif line.startswith("# "):
                clean_text = clean_markdown_inline(line[2:].strip())
                story.append(Paragraph(clean_text, h1_style))
            elif line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
                bullet_content = line[2:].strip()
                bullet_content = clean_markdown_inline(bullet_content)
                story.append(Paragraph(f"&bull;&nbsp; {bullet_content}", bullet_style))
            elif re.match(r'^\d+[\.\)]\s+', line):
                match = re.match(r'^(\d+[\.\)])\s+(.*)', line)
                num_prefix = match.group(1)
                num_content = clean_markdown_inline(match.group(2))
                story.append(Paragraph(f"<b>{num_prefix}</b> {num_content}", numbered_style))
            else:
                clean_text = clean_markdown_inline(line)
                story.append(Paragraph(clean_text, body_style))

    if topics_text and topics_text.strip():
        story.append(Paragraph("Key Highlights & Topics", h1_style))
        process_markdown_block(topics_text)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=12))

    if notes_text and notes_text.strip():
        story.append(Paragraph("Structured Comprehensive Notes", h1_style))
        process_markdown_block(notes_text)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
