import io
import re
import os
from xml.sax import saxutils
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
)
from app.utils.colors import (
    hex_to_reportlab_color, is_dark_color, blend_hex,
    ensure_contrast, ensure_accessible_accent, pick_best_text_color
)
from app.utils.math_formatter import format_math_for_reportlab, is_mathematical_line
from app.utils.pdf_patterns import create_pattern_canvas_maker, draw_page_background
from app.services.image_search import get_image_urls_for_topic_google, download_image_to_tempfile
from flask import current_app

def parse_inline_markdown(text):
    """Convert common inline markdown tags and math notations to ReportLab XML formatting."""
    placeholders = {}

    def code_replacer(match):
        key = f"__CODE_PLACEHOLDER_{len(placeholders)}__"
        placeholders[key] = f'<font name="Courier" color="#C7254E" backColor="#F9F2F4">{saxutils.escape(match.group(1))}</font>'
        return key

    text = re.sub(r'`(.*?)`', code_replacer, text)
    text = format_math_for_reportlab(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

    for key, value in sorted(placeholders.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(key, value)
    return text

def create_pdf_reportlab(topic, content, theme_data, customization):
    """
    Generate publication-ready, Canva/editorial-grade PDF study notes
    with modern section banners, key concept callouts, and clean data tables.
    """
    buffer = io.BytesIO()
    supported_fonts = current_app.config.get('SUPPORTED_FONTS', {}) if current_app else {}
    font_list = list(supported_fonts.keys())
    temp_files_to_delete = []

    # Typography selection
    title_font_name = theme_data.get('font-title', 'Roboto')
    if title_font_name not in font_list:
        title_font_name = 'Roboto' if 'Roboto' in font_list else 'Helvetica'

    body_font_name = theme_data.get('font-body', 'Roboto')
    if body_font_name not in font_list:
        body_font_name = 'Roboto' if 'Roboto' in font_list else 'Helvetica'

    # Color definitions
    bg_hex = theme_data.get('bg-color', '#FFFFFF')
    title_hex = theme_data.get('font-color-title', '#1C1A17')
    body_hex = theme_data.get('font-color-body', '#374151')
    accent_hex = theme_data.get('accent-color', '#E8590C')
    theme_base = customization.get('theme_base', 'ai_choice')

    is_dark = is_dark_color(bg_hex) or theme_base == 'dark'

    if is_dark:
        bg_hex = bg_hex if is_dark_color(bg_hex) else '#18181B'
        card_bg_hex = '#1E242B'
        card_border_hex = '#374151'
        callout_bg_hex = blend_hex(accent_hex, '#18181B', 0.82)
        table_hdr_hex = accent_hex
        table_even_hex = '#1E242B'
        table_odd_hex = '#262D37'
        code_bg_hex = '#111827'
        code_text_hex = '#F9FAFB'
        divider_hex = '#374151'
    else:
        bg_hex = bg_hex if not is_dark_color(bg_hex) else '#FFFFFF'
        card_bg_hex = '#FAF9F6'
        card_border_hex = '#E5E7EB'
        callout_bg_hex = blend_hex(accent_hex, '#FFFFFF', 0.93)
        table_hdr_hex = accent_hex
        table_even_hex = '#FFFFFF'
        table_odd_hex = '#F8FAFC'
        code_bg_hex = '#1E242B'
        code_text_hex = '#F3F4F6'
        divider_hex = '#E5E7EB'

    # STRICT CONTRAST ENFORCEMENT TO GUARANTEE ZERO WHITE-ON-WHITE OR LOW-VISIBILITY TEXT
    title_hex = ensure_contrast(title_hex, bg_hex, min_ratio=4.5, dark_fallback='#0F172A', light_fallback='#FFFFFF')
    body_hex = ensure_contrast(body_hex, bg_hex, min_ratio=4.5, dark_fallback='#334155', light_fallback='#E2E8F0')

    # Accent color adjusted for legible typography on card backgrounds
    accent_text_hex = ensure_accessible_accent(accent_hex, card_bg_hex, min_ratio=4.5)

    # Table header text: dynamically pick whichever has highest contrast against table_hdr_hex
    table_hdr_text_hex = pick_best_text_color(table_hdr_hex, dark_option='#0F172A', light_option='#FFFFFF')

    title_font_color = hex_to_reportlab_color(title_hex)
    body_font_color = hex_to_reportlab_color(body_hex)
    accent_color = hex_to_reportlab_color(accent_hex)
    accent_text_color = hex_to_reportlab_color(accent_text_hex)
    card_bg_color = hex_to_reportlab_color(card_bg_hex)
    card_border_color = hex_to_reportlab_color(card_border_hex)
    callout_bg_color = hex_to_reportlab_color(callout_bg_hex)
    table_hdr_color = hex_to_reportlab_color(table_hdr_hex)
    table_hdr_text_color = hex_to_reportlab_color(table_hdr_text_hex)
    table_even_color = hex_to_reportlab_color(table_even_hex)
    table_odd_color = hex_to_reportlab_color(table_odd_hex)
    divider_color = hex_to_reportlab_color(divider_hex)

    # Document Geometry
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
        topMargin=0.85 * inch, bottomMargin=0.65 * inch
    )
    content_width = doc.width

    styles = getSampleStyleSheet()

    # Paragraph Styles
    normal_style = ParagraphStyle(
        name='NormalStyle',
        fontName=body_font_name,
        fontSize=10,
        leading=15,
        textColor=body_font_color,
        spaceAfter=7,
        alignment=TA_LEFT
    )

    hero_kicker_style = ParagraphStyle(
        name='HeroKicker',
        fontName=f"{title_font_name}-Bold",
        fontSize=8.5,
        leading=11,
        textColor=accent_text_color,
        spaceAfter=3,
        alignment=TA_LEFT
    )

    hero_title_style = ParagraphStyle(
        name='HeroTitle',
        fontName=f"{title_font_name}-Bold",
        fontSize=20,
        leading=25,
        textColor=title_font_color,
        spaceAfter=4,
        alignment=TA_LEFT
    )

    hero_sub_style = ParagraphStyle(
        name='HeroSubtitle',
        fontName=body_font_name,
        fontSize=9.5,
        leading=13,
        textColor=body_font_color,
        alignment=TA_LEFT
    )

    h2_kicker_style = ParagraphStyle(
        name='H2Kicker',
        fontName=f"{title_font_name}-Bold",
        fontSize=8,
        leading=10,
        textColor=accent_text_color,
        spaceAfter=2,
        alignment=TA_LEFT
    )

    h2_banner_style = ParagraphStyle(
        name='H2Banner',
        fontName=f"{title_font_name}-Bold",
        fontSize=14,
        leading=18,
        textColor=title_font_color,
        alignment=TA_LEFT
    )

    h3_style = ParagraphStyle(
        name='H3Style',
        fontName=f"{title_font_name}-Bold",
        fontSize=11.5,
        leading=15,
        textColor=title_font_color,
        spaceBefore=11,
        spaceAfter=5,
        alignment=TA_LEFT
    )

    bullet_style = ParagraphStyle(
        name='BulletStyle',
        parent=normal_style,
        leftIndent=0.25 * inch,
        firstLineIndent=-0.14 * inch,
        spaceAfter=4.5
    )

    callout_tag_style = ParagraphStyle(
        name='CalloutTag',
        fontName=f"{title_font_name}-Bold",
        fontSize=8.5,
        leading=11,
        textColor=accent_text_color,
        spaceAfter=3,
        alignment=TA_LEFT
    )

    callout_body_style = ParagraphStyle(
        name='CalloutBody',
        fontName=body_font_name,
        fontSize=9.5,
        leading=14,
        textColor=body_font_color,
        alignment=TA_LEFT
    )

    formula_tag_style = ParagraphStyle(
        name='FormulaTag',
        fontName=f"{title_font_name}-Bold",
        fontSize=8.5,
        leading=11,
        textColor=accent_text_color,
        spaceAfter=3,
        alignment=TA_CENTER
    )

    formula_body_style = ParagraphStyle(
        name='FormulaBody',
        fontName=f"{title_font_name}-Bold",
        fontSize=12,
        leading=16,
        textColor=title_font_color,
        alignment=TA_CENTER
    )

    code_style = ParagraphStyle(
        name='CodeStyle',
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=hex_to_reportlab_color(code_text_hex),
        alignment=TA_LEFT
    )

    table_header_style = ParagraphStyle(
        name='TableHdr',
        fontName=f"{title_font_name}-Bold",
        fontSize=9.5,
        leading=12,
        textColor=table_hdr_text_color,
        alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        name='TableCell',
        fontName=body_font_name,
        fontSize=9,
        leading=12.5,
        textColor=body_font_color,
        alignment=TA_LEFT
    )

    story = []

    # Cover Page or Hero Header Card
    if customization.get('intro_slide') == 'true':
        story.append(Spacer(1, 1.1 * inch))

        cover_pill_style = ParagraphStyle(
            name='CoverPill',
            fontName=f"{title_font_name}-Bold",
            fontSize=9.5,
            leading=12,
            textColor=accent_text_color,
            spaceAfter=12
        )
        pill_table = Table([[Paragraph("•  GROUNDED STUDY GUIDE &amp; REFERENCE MANUAL", cover_pill_style)]])
        pill_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
            ('BOX', (0, 0), (-1, -1), 0.75, accent_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(pill_table)
        story.append(Spacer(1, 0.15 * inch))

        cover_title_style = ParagraphStyle(
            name='CoverTitle',
            fontName=f"{title_font_name}-Bold",
            fontSize=28,
            leading=34,
            textColor=title_font_color,
            spaceAfter=14
        )
        story.append(Paragraph(saxutils.escape(topic), cover_title_style))

        # Dual Accent Rule
        rule_table = Table([["", ""]], colWidths=[2.0 * inch, 0.8 * inch], rowHeights=[4])
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), accent_color),
            ('BACKGROUND', (1, 0), (1, 0), divider_color),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(rule_table)
        story.append(Spacer(1, 0.22 * inch))

        cover_sub_style = ParagraphStyle(
            name='CoverSub',
            fontName=body_font_name,
            fontSize=11,
            leading=16,
            textColor=body_font_color,
            spaceAfter=20
        )
        story.append(Paragraph("Structured educational synthesis grounded in syllabus reference materials for deep conceptual retention and active recall.", cover_sub_style))

        # 4-Quadrant Executive Scorecard Table
        scorecard_data = [
            [
                Paragraph(f'<font size="7" color="{accent_text_hex}"><b>STUDY DIFFICULTY</b></font><br/><b>Core to Advanced Mastery</b>', normal_style),
                Paragraph(f'<font size="7" color="{accent_text_hex}"><b>ESTIMATED TIME</b></font><br/><b>~20–25 Mins Active Recall</b>', normal_style)
            ],
            [
                Paragraph(f'<font size="7" color="{accent_text_hex}"><b>GROUNDING SOURCES</b></font><br/><b>Course Syllabus &amp; Documents</b>', normal_style),
                Paragraph(f'<font size="7" color="{accent_text_hex}"><b>PEDAGOGICAL FORMAT</b></font><br/><b>Dual-Coding &amp; Spaced Retrieval</b>', normal_style)
            ]
        ]
        scorecard_table = Table(scorecard_data, colWidths=[content_width * 0.5, content_width * 0.5])
        scorecard_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
            ('BOX', (0, 0), (-1, -1), 0.75, card_border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, divider_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(scorecard_table)
        story.append(Spacer(1, 0.2 * inch))

        # Key Learning Outcomes / Synthesis Goals Card
        outcomes_cells = [
            Paragraph("LEARNING OBJECTIVES &amp; SYNTHESIS GOALS", hero_kicker_style),
            Paragraph("• <b>Conceptual Clarity:</b> Deconstruct foundational principles, domain boundaries, and core laws.<br/>"
                      "• <b>Formulation Rigor:</b> Master analytical equations, variable dependencies, and boundary conditions.<br/>"
                      "• <b>Active Recall:</b> Solidify long-term retention through dual-coding and retrieval practice.", normal_style)
        ]
        outcomes_table = Table([[outcomes_cells]], colWidths=[content_width])
        outcomes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
            ('BOX', (0, 0), (-1, -1), 0.5, card_border_color),
            ('LINELEFT', (0, 0), (0, 0), 3.5, accent_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(outcomes_table)

        story.append(Spacer(1, 1.2 * inch))
        story.append(PageBreak())

    else:
        # Top-of-Page Hero Header Card on Page 1
        hero_cell = [
            Paragraph("REVISION &amp; STUDY NOTES  ·  ACTIVE RECALL", hero_kicker_style),
            Paragraph(saxutils.escape(topic), hero_title_style),
            Paragraph("Synthesized for active recall, dual-coding retention, and grounded conceptual mastery.", hero_sub_style),
            Paragraph(f'<font size="7.5" color="{accent_text_hex}"><b>[ ⏱ ~15 Mins Read ]</b></font>  &nbsp;·&nbsp;  '
                      f'<font size="7.5" color="{accent_text_hex}"><b>[ 📚 Grounded Reference ]</b></font>  &nbsp;·&nbsp;  '
                      f'<font size="7.5" color="{accent_text_hex}"><b>[ 🎯 Active Recall ]</b></font>', normal_style)
        ]
        hero_table = Table([[hero_cell]], colWidths=[content_width])
        hero_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
            ('LINELEFT', (0, 0), (0, 0), 4, accent_color),
            ('BOX', (0, 0), (-1, -1), 0.5, card_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))
        story.append(hero_table)
        story.append(Spacer(1, 0.22 * inch))

    # Content Parsing Loop
    is_parsing_table = False
    table_data = []

    is_parsing_code = False
    code_buffer = []

    is_parsing_callout = False
    callout_buffer = []

    section_counter = 0
    lines = content.split('\n')

    def flush_table():
        nonlocal is_parsing_table, table_data
        if not table_data:
            is_parsing_table = False
            return

        col_count = len(table_data[0])
        col_w = content_width / max(col_count, 1)
        t = Table(table_data, colWidths=[col_w] * col_count)

        t_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), table_hdr_color),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [table_even_color, table_odd_color]),
            ('BOX', (0, 0), (-1, -1), 1, card_border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, divider_color),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        t.setStyle(TableStyle(t_styles))
        story.append(t)
        story.append(Spacer(1, 0.16 * inch))
        table_data = []
        is_parsing_table = False

    def flush_code():
        nonlocal is_parsing_code, code_buffer
        if not code_buffer:
            is_parsing_code = False
            return
        full_code = "<br/>".join(saxutils.escape(c) for c in code_buffer)
        code_p = Paragraph(full_code, code_style)
        c_table = Table([[code_p]], colWidths=[content_width])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), hex_to_reportlab_color(code_bg_hex)),
            ('BOX', (0, 0), (-1, -1), 1, card_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(c_table)
        story.append(Spacer(1, 0.14 * inch))
        code_buffer = []
        is_parsing_code = False

    def flush_callout():
        nonlocal is_parsing_callout, callout_buffer
        if not callout_buffer:
            is_parsing_callout = False
            return

        combined_text = " ".join(callout_buffer).strip()
        body_text = combined_text

        # Determine callout archetype and tag
        callout_type = 'concept'
        tag = "KEY CONCEPT &amp; TAKEAWAY"

        lower_c = combined_text.lower()
        if any(lower_c.startswith(p) for p in ["exam tip:", "misconception:", "warning:", "caution:", "common error:", "avoid:", "trap:"]):
            callout_type = 'warning'
            for prefix in ["Exam Tip:", "Misconception:", "Warning:", "Caution:", "Common Error:", "Avoid:", "Trap:"]:
                if combined_text.lower().startswith(prefix.lower()):
                    tag = prefix.rstrip(":").upper()
                    body_text = combined_text[len(prefix):].strip()
                    break
        elif any(lower_c.startswith(p) for p in ["real-world:", "application:", "case study:", "industry:", "example:", "in practice:"]):
            callout_type = 'application'
            for prefix in ["Real-World:", "Application:", "Case Study:", "Industry:", "Example:", "In Practice:"]:
                if combined_text.lower().startswith(prefix.lower()):
                    tag = prefix.rstrip(":").upper()
                    body_text = combined_text[len(prefix):].strip()
                    break
        else:
            for prefix in ["Key Concept:", "Important:", "Core Concept:", "Definition:", "Formula:", "Note:"]:
                if combined_text.lower().startswith(prefix.lower()):
                    tag = prefix.rstrip(":").upper()
                    body_text = combined_text[len(prefix):].strip()
                    break

        if callout_type == 'warning':
            border_c = hex_to_reportlab_color('#EF4444' if not is_dark else '#F87171')
            bg_c = hex_to_reportlab_color('#FFF1F2' if not is_dark else '#2D1517')
            icon_tag = f"⚠️  {tag}"
            tag_c = border_c
        elif callout_type == 'application':
            border_c = hex_to_reportlab_color('#10B981' if not is_dark else '#34D399')
            bg_c = hex_to_reportlab_color('#F0FDF4' if not is_dark else '#0E291E')
            icon_tag = f"🌍  {tag}"
            tag_c = border_c
        else:
            border_c = accent_color
            bg_c = callout_bg_color
            icon_tag = f"💡  {tag}"
            tag_c = accent_color

        c_tag_style = ParagraphStyle(
            name=f'CalloutTag_{callout_type}_{len(story)}',
            fontName=f"{title_font_name}-Bold",
            fontSize=8.5,
            leading=11,
            textColor=tag_c,
            spaceAfter=3,
            alignment=TA_LEFT
        )

        cell_flowables = [
            Paragraph(icon_tag, c_tag_style),
            Paragraph(parse_inline_markdown(body_text), callout_body_style)
        ]
        callout_table = Table([[cell_flowables]], colWidths=[content_width])
        callout_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_c),
            ('LINELEFT', (0, 0), (0, 0), 3.5, border_c),
            ('BOX', (0, 0), (-1, -1), 0.5, card_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(callout_table)
        story.append(Spacer(1, 0.14 * inch))
        callout_buffer = []
        is_parsing_callout = False

    for line in lines:
        stripped_line = line.strip()
        stripped_line = re.sub(r'\s#+$', '', stripped_line)
        robust_line = stripped_line.strip('` ')

        # Code block handling
        if stripped_line.startswith('```'):
            if is_parsing_code:
                flush_code()
            else:
                if is_parsing_table:
                    flush_table()
                if is_parsing_callout:
                    flush_callout()
                is_parsing_code = True
            continue

        if is_parsing_code:
            code_buffer.append(line)
            continue

        # Callout handling (lines starting with >)
        if stripped_line.startswith('>'):
            if is_parsing_table:
                flush_table()
            is_parsing_callout = True
            callout_text = stripped_line.lstrip('>').strip()
            if callout_text:
                callout_buffer.append(callout_text)
            continue
        elif is_parsing_callout:
            flush_callout()

        # Table handling
        if is_parsing_table and not robust_line.startswith('|'):
            flush_table()

        if not stripped_line:
            continue

        # Image Tag Handling
        image_match = re.match(r'^\[IMAGE:\s*(.+?)\s*\]$', stripped_line, flags=re.IGNORECASE)
        if image_match:
            image_query = image_match.group(1).strip()
            image_path = None
            try:
                image_urls = get_image_urls_for_topic_google(image_query)
                if image_urls:
                    for url in image_urls:
                        image_path = download_image_to_tempfile(url)
                        if image_path:
                            temp_files_to_delete.append(image_path)
                            break
            except Exception:
                image_path = None

            if image_path:
                try:
                    story.append(Spacer(1, 0.08 * inch))
                    story.append(Image(image_path, width=content_width * 0.95, height=3.2 * inch, kind='proportional'))
                    story.append(Spacer(1, 0.14 * inch))
                except Exception:
                    pass
            continue

        # Standalone Mathematical Formula Card
        if is_mathematical_line(stripped_line):
            if is_parsing_table:
                flush_table()
            if is_parsing_callout:
                flush_callout()

            clean_formula = format_math_for_reportlab(stripped_line)
            formula_cells = [
                Paragraph("📐  KEY FORMULATION", formula_tag_style),
                Paragraph(clean_formula, formula_body_style)
            ]
            f_table = Table([[formula_cells]], colWidths=[content_width])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
                ('BOX', (0, 0), (-1, -1), 0.75, accent_color),
                ('LINELEFT', (0, 0), (0, 0), 3.5, accent_color),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(Spacer(1, 0.08 * inch))
            story.append(f_table)
            story.append(Spacer(1, 0.12 * inch))
            continue

        # Markdown Table Row Parsing
        if robust_line.startswith('|'):
            if re.fullmatch(r'\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?', robust_line):
                continue
            if not is_parsing_table:
                is_parsing_table = True
                table_data = []

            normalized = robust_line
            if normalized.startswith('|'):
                normalized = normalized[1:]
            if normalized.endswith('|'):
                normalized = normalized[:-1]

            cells = [c.strip() for c in normalized.split('|')]
            if cells:
                is_hdr_row = len(table_data) == 0
                cell_style = table_header_style if is_hdr_row else table_cell_style
                table_data.append([Paragraph(parse_inline_markdown(c), cell_style) for c in cells])
            continue

        # Section Heading (`## ` or `# `) -> Modern Canva Section Banner
        if stripped_line.startswith('# ') or stripped_line.startswith('## '):
            heading_text = stripped_line[2:] if stripped_line.startswith('# ') else stripped_line[3:]
            section_counter += 1

            banner_cells = [
                Paragraph(f"SECTION {section_counter:02d}", h2_kicker_style),
                Paragraph(parse_inline_markdown(heading_text), h2_banner_style)
            ]
            sec_table = Table([[banner_cells]], colWidths=[content_width])
            sec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
                ('LINELEFT', (0, 0), (0, 0), 3.5, accent_color),
                ('LINEBOTTOM', (0, 0), (-1, -1), 0.5, divider_color),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(Spacer(1, 0.16 * inch))
            story.append(sec_table)
            story.append(Spacer(1, 0.1 * inch))

        # Sub-heading (`### `)
        elif stripped_line.startswith('### '):
            sub_text = stripped_line[4:]
            story.append(Paragraph(f"▪  {parse_inline_markdown(sub_text)}", h3_style))

        # Sub-sub-heading (`#### `)
        elif stripped_line.startswith('#### '):
            sub_text = stripped_line[5:]
            story.append(Paragraph(parse_inline_markdown(sub_text), h3_style))

        # Bullet List Items (`* ` or `- `)
        elif stripped_line.startswith('* ') or stripped_line.startswith('- '):
            bullet_text = stripped_line[2:].strip()
            # If bullet has bold prefix (e.g. `**Title**: desc`), highlight neatly
            story.append(Paragraph(parse_inline_markdown(bullet_text), bullet_style, bulletText='•'))

        # Standard Paragraph
        else:
            clean_line = re.sub(r'^#+\s*', '', line)
            story.append(Paragraph(parse_inline_markdown(clean_line), normal_style))

    # Clean up lingering open blocks
    if is_parsing_code:
        flush_code()
    if is_parsing_callout:
        flush_callout()
    if is_parsing_table:
        flush_table()

    # Active Recall Review & Retention Checklist Card
    story.append(Spacer(1, 0.18 * inch))
    checklist_cells = [
        Paragraph("🎓  STUDY MASTERY &amp; ACTIVE RECALL CHECKLIST", formula_tag_style),
        Paragraph("<b>[✓] Core Definitions:</b> Reviewed foundational principles, terminologies, and domain boundaries.", normal_style),
        Paragraph("<b>[✓] Key Formulations:</b> Verified analytical relationships, state variables, and units.", normal_style),
        Paragraph("<b>[✓] Active Retrieval:</b> Ready for self-testing with generated flashcards and practice quizzes.", normal_style)
    ]
    summary_card = Table([[checklist_cells]], colWidths=[content_width])
    summary_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), card_bg_color),
        ('BOX', (0, 0), (-1, -1), 0.75, card_border_color),
        ('LINELEFT', (0, 0), (0, 0), 3.5, accent_color),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_card)

    # Build the PDF with Custom Numbered Vector Pattern Canvas
    has_cover = (customization.get('intro_slide') == 'true')
    canvas_maker = create_pattern_canvas_maker(
        topic=topic,
        title_font_name=title_font_name,
        body_font_name=body_font_name,
        bg_hex=bg_hex,
        title_hex=title_hex,
        body_hex=body_hex,
        accent_hex=accent_hex,
        is_dark=is_dark,
        has_intro_cover=has_cover,
        accent_text_hex=accent_text_hex
    )

    def first_page_cb(canv, document):
        draw_page_background(canv, document, topic, accent_hex, bg_hex, is_dark, has_cover, accent_text_hex, is_first_page=True)

    def later_pages_cb(canv, document):
        draw_page_background(canv, document, topic, accent_hex, bg_hex, is_dark, has_cover, accent_text_hex, is_first_page=False)

    doc.build(story, onFirstPage=first_page_cb, onLaterPages=later_pages_cb, canvasmaker=canvas_maker)
    buffer.seek(0)

    for path in temp_files_to_delete:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    return buffer
