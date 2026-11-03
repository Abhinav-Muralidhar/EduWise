import io
import os
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from app.utils.colors import hex_to_rgbcolor, hex_to_rgb, is_dark_color, blend_hex
from app.utils.math_formatter import format_math_for_pptx
from app.services.image_search import get_image_urls_for_topic_google, download_image_to_tempfile
from flask import current_app

def _get_palette(theme_data, customization):
    """
    Compute a cohesive, high-contrast Canva-style color palette
    from user theme preferences and background luminance.
    """
    bg_hex = theme_data.get('bg-color', '#FFFFFF')
    title_hex = theme_data.get('font-color-title', '#1C1A17')
    body_hex = theme_data.get('font-color-body', '#4B5563')
    accent_hex = theme_data.get('accent-color', '#E8590C')
    theme_base = customization.get('theme_base', 'ai_choice')

    is_dark = is_dark_color(bg_hex) or theme_base == 'dark'

    if is_dark:
        bg_hex = bg_hex if is_dark_color(bg_hex) else '#18181B'
        card_bg_hex = blend_hex(bg_hex, '#FFFFFF', 0.08)
        card_border_hex = blend_hex(bg_hex, '#FFFFFF', 0.16)
        title_hex = '#FFFFFF' if is_dark_color(title_hex) else title_hex
        body_hex = '#D4D4D8' if is_dark_color(body_hex) else body_hex
        subtle_line_hex = blend_hex(bg_hex, '#FFFFFF', 0.20)
        badge_bg_hex = blend_hex(accent_hex, bg_hex, 0.70)
        badge_text_hex = '#FFFFFF'
        pill_bg_hex = blend_hex(accent_hex, bg_hex, 0.80)
        hero_fill_hex = blend_hex(accent_hex, bg_hex, 0.88)
        alt_card_hex = blend_hex(bg_hex, '#FFFFFF', 0.12)
    else:
        bg_hex = bg_hex if not is_dark_color(bg_hex) else '#F8F9FA'
        card_bg_hex = '#FFFFFF'
        card_border_hex = blend_hex(bg_hex, '#000000', 0.10)
        title_hex = '#111827' if not is_dark_color(title_hex) else title_hex
        body_hex = '#4B5563' if not is_dark_color(body_hex) else body_hex
        subtle_line_hex = blend_hex(bg_hex, '#000000', 0.12)
        badge_bg_hex = accent_hex
        badge_text_hex = '#FFFFFF'
        pill_bg_hex = blend_hex(accent_hex, '#FFFFFF', 0.88)
        hero_fill_hex = blend_hex(accent_hex, '#FFFFFF', 0.94)
        alt_card_hex = blend_hex(accent_hex, '#FFFFFF', 0.96)

    return {
        'is_dark': is_dark,
        'bg_rgb': hex_to_rgbcolor(bg_hex),
        'title_rgb': hex_to_rgbcolor(title_hex),
        'body_rgb': hex_to_rgbcolor(body_hex),
        'accent_rgb': hex_to_rgbcolor(accent_hex),
        'card_bg_rgb': hex_to_rgbcolor(card_bg_hex),
        'card_border_rgb': hex_to_rgbcolor(card_border_hex),
        'subtle_line_rgb': hex_to_rgbcolor(subtle_line_hex),
        'badge_bg_rgb': hex_to_rgbcolor(badge_bg_hex),
        'badge_text_rgb': hex_to_rgbcolor(badge_text_hex),
        'pill_bg_rgb': hex_to_rgbcolor(pill_bg_hex),
        'hero_fill_rgb': hex_to_rgbcolor(hero_fill_hex),
        'alt_card_rgb': hex_to_rgbcolor(alt_card_hex),
        'accent_hex': accent_hex,
        'title_font': theme_data.get('font-title', 'Roboto'),
        'body_font': theme_data.get('font-body', 'Roboto')
    }

def _parse_point_parts(point_str):
    """
    Split a bullet point into headline and body if structured like 'Title: Description'
    or 'Title - Description'. Formats mathematical notations cleanly.
    """
    cleaned = format_math_for_pptx(re.sub(r'^\d+[\.\)]\s*', '', str(point_str).strip()))
    for sep in [': ', ' - ', ' – ']:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            headline, body = parts[0].strip(), parts[1].strip()
            if 1 <= len(headline.split()) <= 7 and len(body) > 3:
                return headline, body
    return "", cleaned

def _safe_font_name(font_name):
    supported = current_app.config.get('SUPPORTED_FONTS', {}) if current_app else {}
    return font_name if font_name in supported else 'Arial'

def _draw_card_shape(slide, left, top, width, height, bg_rgb, border_rgb, border_pt=1):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_rgb
    if border_rgb and border_pt > 0:
        shape.line.color.rgb = border_rgb
        shape.line.width = Pt(border_pt)
    else:
        shape.line.fill.background()
    return shape

def _render_intro_slide(slide, title, points, palette, prs_width, prs_height):
    # Left vertical decorative book-spine bar
    accent_spine = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.8), Inches(0.9), Inches(0.14), Inches(5.7)
    )
    accent_spine.fill.solid()
    accent_spine.fill.fore_color.rgb = palette['accent_rgb']
    accent_spine.line.fill.background()

    # Category Pill Badge
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.2), Inches(1.15), Inches(3.2), Inches(0.42)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = palette['pill_bg_rgb']
    pill.line.fill.background()
    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = "ACADEMIC STUDY DECK"
    p_pill.font.name = _safe_font_name(palette['title_font'])
    p_pill.font.size = Pt(10)
    p_pill.font.bold = True
    p_pill.font.color.rgb = palette['accent_rgb']
    p_pill.alignment = PP_ALIGN.CENTER

    # Grand Presentation Title with Math formatting
    title_box = slide.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(2.2))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = Inches(0)
    tf_title.margin_top = Inches(0)
    p_title = tf_title.paragraphs[0]
    p_title.text = format_math_for_pptx(title)
    p_title.font.name = _safe_font_name(palette['title_font'])
    p_title.font.size = Pt(38)
    p_title.font.bold = True
    p_title.font.color.rgb = palette['title_rgb']

    # Accent decorative rule below title
    rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.2), Inches(4.1), Inches(2.2), Inches(0.04)
    )
    rule.fill.solid()
    rule.fill.fore_color.rgb = palette['accent_rgb']
    rule.line.fill.background()

    # Subtitle or key takeaway preview cards
    if points and len(points) > 0:
        sub_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.35), Inches(11.0), Inches(1.8))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = Inches(0)
        for idx, pt in enumerate(points[:3]):
            p = tf_sub.paragraphs[0] if idx == 0 else tf_sub.add_paragraph()
            p.text = f"•  {format_math_for_pptx(pt)}"
            p.font.name = _safe_font_name(palette['body_font'])
            p.font.size = Pt(15)
            p.font.color.rgb = palette['body_rgb']
            p.space_before = Pt(4)
    else:
        sub_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.35), Inches(10.0), Inches(1.2))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = Inches(0)
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = "Comprehensive course curriculum synthesized and grounded in your study materials."
        p_sub.font.name = _safe_font_name(palette['body_font'])
        p_sub.font.size = Pt(16)
        p_sub.font.color.rgb = palette['body_rgb']

    # Bottom footer branding
    footer_box = slide.shapes.add_textbox(Inches(1.2), Inches(6.5), Inches(11.0), Inches(0.5))
    tf_foot = footer_box.text_frame
    tf_foot.margin_left = Inches(0)
    p_foot = tf_foot.paragraphs[0]
    p_foot.text = "EduWise AI Studio  ·  Grounded Active Retention"
    p_foot.font.name = _safe_font_name(palette['body_font'])
    p_foot.font.size = Pt(10)
    p_foot.font.color.rgb = palette['body_rgb']

def _render_header_bar(slide, title, palette, slide_num, total_slides, kicker_text="CONCEPT BREAKDOWN"):
    """Render consistent modern header bar across content slides."""
    kicker = slide.shapes.add_textbox(Inches(1.0), Inches(0.42), Inches(6.0), Inches(0.3))
    tf_k = kicker.text_frame
    tf_k.margin_left = Inches(0)
    tf_k.margin_top = Inches(0)
    p_k = tf_k.paragraphs[0]
    p_k.text = kicker_text
    p_k.font.name = _safe_font_name(palette['title_font'])
    p_k.font.size = Pt(9.5)
    p_k.font.bold = True
    p_k.font.color.rgb = palette['accent_rgb']

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.72), Inches(9.8), Inches(0.7))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = Inches(0)
    tf_title.margin_top = Inches(0)
    p_t = tf_title.paragraphs[0]
    p_t.text = format_math_for_pptx(title)
    p_t.font.name = _safe_font_name(palette['title_font'])
    p_t.font.size = Pt(24)
    p_t.font.bold = True
    p_t.font.color.rgb = palette['title_rgb']

    # Slide Index Badge (Top Right)
    index_badge = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(11.5), Inches(0.65), Inches(0.9), Inches(0.35)
    )
    index_badge.fill.solid()
    index_badge.fill.fore_color.rgb = palette['card_bg_rgb']
    index_badge.line.color.rgb = palette['card_border_rgb']
    index_badge.line.width = Pt(1)
    tf_idx = index_badge.text_frame
    tf_idx.word_wrap = False
    p_idx = tf_idx.paragraphs[0]
    p_idx.text = f"{slide_num:02d} / {total_slides:02d}"
    p_idx.font.name = _safe_font_name(palette['body_font'])
    p_idx.font.size = Pt(9.5)
    p_idx.font.bold = True
    p_idx.font.color.rgb = palette['body_rgb']
    p_idx.alignment = PP_ALIGN.CENTER

    # Subtle Hairline divider
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.0), Inches(1.48), Inches(11.4), Inches(0.015)
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = palette['subtle_line_rgb']
    divider.line.fill.background()

# ----------------- DIVERSE CONTENT SLIDE ARCHETYPES -----------------

def _render_bento_hero_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 1: 1 Prominent Hero Card on Left + 2 Stacked Cards on Right."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "FOUNDATIONAL PRINCIPLE")
    top_y = Inches(1.75)
    avail_h = Inches(5.1)

    pts = points if points else ["Key topic analysis and structured overview."]
    hero_pt = pts[0]
    side_pts = pts[1:3] if len(pts) > 1 else ["Supporting analytical context."]

    # Left Hero Card (Width: 5.2 in)
    hero_w = Inches(5.2)
    _draw_card_shape(slide, Inches(1.0), top_y, hero_w, avail_h, palette['hero_fill_rgb'], palette['accent_rgb'], 1.5)

    hero_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.35), top_y + Inches(0.35), Inches(1.7), Inches(0.36))
    hero_badge.fill.solid()
    hero_badge.fill.fore_color.rgb = palette['badge_bg_rgb']
    hero_badge.line.fill.background()
    tf_hb = hero_badge.text_frame
    p_hb = tf_hb.paragraphs[0]
    p_hb.text = "01 · CORE FOCUS"
    p_hb.font.size = Pt(10)
    p_hb.font.bold = True
    p_hb.font.color.rgb = palette['badge_text_rgb']
    p_hb.alignment = PP_ALIGN.CENTER

    headline, body = _parse_point_parts(hero_pt)
    tb_h = slide.shapes.add_textbox(Inches(1.35), top_y + Inches(0.95), hero_w - Inches(0.7), avail_h - Inches(1.2))
    tf_h = tb_h.text_frame
    tf_h.word_wrap = True
    if headline:
        p_head = tf_h.paragraphs[0]
        p_head.text = headline
        p_head.font.name = _safe_font_name(palette['title_font'])
        p_head.font.size = Pt(21)
        p_head.font.bold = True
        p_head.font.color.rgb = palette['title_rgb']

        p_b = tf_h.add_paragraph()
        p_b.text = body
        p_b.font.name = _safe_font_name(palette['body_font'])
        p_b.font.size = Pt(14.5)
        p_b.font.color.rgb = palette['body_rgb']
        p_b.space_before = Pt(10)
    else:
        p_b = tf_h.paragraphs[0]
        p_b.text = body
        p_b.font.name = _safe_font_name(palette['body_font'])
        p_b.font.size = Pt(16)
        p_b.font.color.rgb = palette['body_rgb']

    # Right Stacked Cards (Width: 5.8 in, 2 cards)
    right_x = Inches(6.6)
    right_w = Inches(5.8)
    card_h = (avail_h - Inches(0.3)) / 2

    for i, pt in enumerate(side_pts[:2]):
        cy = top_y + (card_h + Inches(0.3)) * i
        _draw_card_shape(slide, right_x, cy, right_w, card_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x + Inches(0.3), cy + Inches(0.25), Inches(0.65), Inches(0.32))
        b.fill.solid()
        b.fill.fore_color.rgb = palette['card_bg_rgb']
        b.line.color.rgb = palette['card_border_rgb']
        b.line.width = Pt(1)
        tf_b = b.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"{i+2:02d}"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['accent_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        hl, bd = _parse_point_parts(pt)
        tb = slide.shapes.add_textbox(right_x + Inches(1.1), cy + Inches(0.2), right_w - Inches(1.3), card_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        if hl:
            ph = tf.paragraphs[0]
            ph.text = hl
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(15.5)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = bd
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12.5)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(4)
        else:
            pb = tf.paragraphs[0]
            pb.text = bd
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(13)
            pb.font.color.rgb = palette['body_rgb']

def _render_stepper_process_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 2: Horizontal Sequential Process Pipeline with Chevrons (Step 1 -> Step 2 -> Step 3)."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "PROCESS & WORKFLOW PIPELINE")
    top_y = Inches(1.75)
    avail_h = Inches(5.1)

    pts = points if points else ["Step 1", "Step 2", "Step 3"]
    step_count = min(max(len(pts), 2), 4)
    step_pts = pts[:step_count]

    arrow_w = Inches(0.35)
    total_arrow_w = arrow_w * (step_count - 1)
    card_w = (Inches(11.4) - total_arrow_w - Inches(0.3 * (step_count - 1))) / step_count
    gap = Inches(0.3)

    for i, pt in enumerate(step_pts):
        cx = Inches(1.0) + i * (card_w + arrow_w + gap)
        _draw_card_shape(slide, cx, top_y, card_w, avail_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        # Step Pill Badge
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.25), top_y + Inches(0.3), Inches(1.0), Inches(0.34))
        badge.fill.solid()
        badge.fill.fore_color.rgb = palette['badge_bg_rgb']
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"STEP {i+1:02d}"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        headline, body = _parse_point_parts(pt)
        tb = slide.shapes.add_textbox(cx + Inches(0.25), top_y + Inches(0.85), card_w - Inches(0.5), avail_h - Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        if headline:
            ph = tf.paragraphs[0]
            ph.text = headline
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(16)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12.5)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(6)
        else:
            pb = tf.paragraphs[0]
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(13)
            pb.font.color.rgb = palette['body_rgb']

        # Connecting Arrow between cards
        if i < step_count - 1:
            arrow_x = cx + card_w + Inches(0.08)
            arrow_box = slide.shapes.add_textbox(arrow_x, top_y + Inches(2.2), arrow_w + Inches(0.14), Inches(0.6))
            tf_a = arrow_box.text_frame
            p_a = tf_a.paragraphs[0]
            p_a.text = "→"
            p_a.font.size = Pt(24)
            p_a.font.bold = True
            p_a.font.color.rgb = palette['accent_rgb']
            p_a.alignment = PP_ALIGN.CENTER

def _render_comparison_split_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 3: Two-Column Analytical Split (Option A vs Option B or Concept 1 vs Concept 2)."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "COMPARATIVE ANALYSIS")
    top_y = Inches(1.75)
    avail_h = Inches(5.1)

    pts = points if points else ["Dimension 1 Overview", "Dimension 2 Overview"]
    card_w = Inches(5.5)
    gap = Inches(0.4)

    for i in range(2):
        cx = Inches(1.0) + (card_w + gap) * i
        pt = pts[i] if i < len(pts) else pts[0]

        card_bg = palette['card_bg_rgb'] if i == 0 else palette['alt_card_rgb']
        _draw_card_shape(slide, cx, top_y, card_w, avail_h, card_bg, palette['card_border_rgb'], 1)

        # Top Accent Header Bar on each card
        top_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, top_y, card_w, Inches(0.06))
        top_accent.fill.solid()
        top_accent.fill.fore_color.rgb = palette['accent_rgb'] if i == 0 else palette['badge_bg_rgb']
        top_accent.line.fill.background()

        badge_text = "DIMENSION A" if i == 0 else "DIMENSION B"
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.35), top_y + Inches(0.3), Inches(1.6), Inches(0.35))
        badge.fill.solid()
        badge.fill.fore_color.rgb = palette['badge_bg_rgb'] if i == 0 else palette['pill_bg_rgb']
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = badge_text
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb'] if i == 0 else palette['accent_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        headline, body = _parse_point_parts(pt)
        tb = slide.shapes.add_textbox(cx + Inches(0.35), top_y + Inches(0.85), card_w - Inches(0.7), avail_h - Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        if headline:
            ph = tf.paragraphs[0]
            ph.text = headline
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(19)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(14)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(8)
        else:
            pb = tf.paragraphs[0]
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(15)
            pb.font.color.rgb = palette['body_rgb']

def _render_formula_callout_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 4: Large Central Formula / Governing Law Hero Banner + Breakdown Cards Below."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "MATHEMATICAL & THEORETICAL FORMULATION")
    top_y = Inches(1.75)

    pts = points if points else ["Core formula formulation"]
    formula_pt = pts[0]
    breakdown_pts = pts[1:] if len(pts) > 1 else ["Component variable and operational boundary conditions."]

    # Top Central Formula Hero Banner
    banner_w = Inches(11.4)
    banner_h = Inches(1.85)
    _draw_card_shape(slide, Inches(1.0), top_y, banner_w, banner_h, palette['hero_fill_rgb'], palette['accent_rgb'], 1.5)

    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.3), top_y + Inches(0.2), Inches(3.2), Inches(0.32))
    pill.fill.solid()
    pill.fill.fore_color.rgb = palette['pill_bg_rgb']
    pill.line.fill.background()
    tf_p = pill.text_frame
    p_p = tf_p.paragraphs[0]
    p_p.text = "CORE EQUATION & GOVERNING LAW"
    p_p.font.size = Pt(9.5)
    p_p.font.bold = True
    p_p.font.color.rgb = palette['accent_rgb']
    p_p.alignment = PP_ALIGN.CENTER

    headline, body = _parse_point_parts(formula_pt)
    equation_text = headline if headline else body
    tb_eq = slide.shapes.add_textbox(Inches(1.3), top_y + Inches(0.65), banner_w - Inches(0.6), Inches(0.95))
    tf_eq = tb_eq.text_frame
    tf_eq.word_wrap = True
    p_eq = tf_eq.paragraphs[0]
    p_eq.text = format_math_for_pptx(equation_text)
    p_eq.font.name = _safe_font_name(palette['title_font'])
    p_eq.font.size = Pt(26)
    p_eq.font.bold = True
    p_eq.font.color.rgb = palette['title_rgb']
    p_eq.alignment = PP_ALIGN.CENTER

    # Bottom Breakdown Cards (2 or 3 cards)
    bot_y = top_y + banner_h + Inches(0.3)
    bot_h = Inches(5.1) - banner_h - Inches(0.3)
    b_count = min(len(breakdown_pts), 3)
    c_w = (banner_w - Inches(0.35 * (b_count - 1))) / b_count

    for i in range(b_count):
        cx = Inches(1.0) + (c_w + Inches(0.35)) * i
        _draw_card_shape(slide, cx, bot_y, c_w, bot_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.25), bot_y + Inches(0.25), Inches(0.65), Inches(0.3))
        b.fill.solid()
        b.fill.fore_color.rgb = palette['badge_bg_rgb']
        b.line.fill.background()
        tf_b = b.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"{i+1:02d}"
        p_b.font.size = Pt(9.5)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        hl, bd = _parse_point_parts(breakdown_pts[i])
        tb = slide.shapes.add_textbox(cx + Inches(1.0), bot_y + Inches(0.18), c_w - Inches(1.15), bot_h - Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True
        if hl:
            ph = tf.paragraphs[0]
            ph.text = hl
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(14)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = bd
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12)
            pb.font.color.rgb = palette['body_rgb']
        else:
            pb = tf.paragraphs[0]
            pb.text = bd
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12.5)
            pb.font.color.rgb = palette['body_rgb']

def _render_three_cards_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 5: Balanced 3-Column Bento Grid."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "CONCEPT ANALYSIS")
    top_y = Inches(1.75)
    avail_h = Inches(5.1)

    pts = points if points else ["Key point 1", "Key point 2", "Key point 3"]
    card_w = Inches(3.55)
    gap = Inches(0.38)

    for i, pt in enumerate(pts[:3]):
        cx = Inches(1.0) + (card_w + gap) * i
        _draw_card_shape(slide, cx, top_y, card_w, avail_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.3), top_y + Inches(0.35), Inches(0.7), Inches(0.35))
        badge.fill.solid()
        badge.fill.fore_color.rgb = palette['badge_bg_rgb']
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"{i+1:02d}"
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        headline, body = _parse_point_parts(pt)
        tb = slide.shapes.add_textbox(cx + Inches(0.3), top_y + Inches(0.9), card_w - Inches(0.6), avail_h - Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        if headline:
            ph = tf.paragraphs[0]
            ph.text = headline
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(17)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(13)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(6)
        else:
            pb = tf.paragraphs[0]
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(14)
            pb.font.color.rgb = palette['body_rgb']

def _render_two_by_two_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 6: 2x2 Matrix Grid (4 Quadrants)."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "QUADRANT MATRIX")
    top_y = Inches(1.75)

    card_w = Inches(5.5)
    card_h = Inches(2.4)
    gap_x = Inches(0.4)
    gap_y = Inches(0.3)
    pts = points if points else ["Q1", "Q2", "Q3", "Q4"]

    for i, pt in enumerate(pts[:4]):
        row = i // 2
        col = i % 2
        cx = Inches(1.0) + (card_w + gap_x) * col
        cy = top_y + (card_h + gap_y) * row

        _draw_card_shape(slide, cx, cy, card_w, card_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.25), cy + Inches(0.25), Inches(0.65), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = palette['badge_bg_rgb']
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"{i+1:02d}"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        headline, body = _parse_point_parts(pt)
        tb = slide.shapes.add_textbox(cx + Inches(1.05), cy + Inches(0.2), card_w - Inches(1.2), card_h - Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True
        if headline:
            ph = tf.paragraphs[0]
            ph.text = headline
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(15)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(3)
        else:
            pb = tf.paragraphs[0]
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(13)
            pb.font.color.rgb = palette['body_rgb']

def _render_split_image_slide(slide, title, points, image_path, palette, slide_num, total_slides):
    """Layout 7: Split Layout with Framed Image."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "VISUAL SYNTHESIS")
    left_w = Inches(6.1)
    right_w = Inches(4.9)
    top_y = Inches(1.75)
    avail_h = Inches(5.1)

    # Image Frame Card
    _draw_card_shape(slide, Inches(7.45), top_y, right_w, avail_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)
    try:
        slide.shapes.add_picture(
            image_path,
            Inches(7.6), top_y + Inches(0.15),
            width=right_w - Inches(0.3),
            height=avail_h - Inches(0.3)
        )
    except Exception:
        pass

    pts = points if points else ["Key discussion details on this concept."]
    card_count = min(len(pts), 3)
    card_h = (avail_h - Inches(0.25 * (card_count - 1))) / card_count

    for i in range(card_count):
        cy = top_y + (card_h + Inches(0.25)) * i
        _draw_card_shape(slide, Inches(1.0), cy, left_w, card_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.25), cy + Inches(0.25), Inches(0.65), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = palette['badge_bg_rgb']
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"{i+1:02d}"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = palette['badge_text_rgb']
        p_b.alignment = PP_ALIGN.CENTER

        headline, body = _parse_point_parts(pts[i])
        tb = slide.shapes.add_textbox(Inches(2.05), cy + Inches(0.18), left_w - Inches(1.2), card_h - Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True
        if headline:
            ph = tf.paragraphs[0]
            ph.text = headline
            ph.font.name = _safe_font_name(palette['title_font'])
            ph.font.size = Pt(15)
            ph.font.bold = True
            ph.font.color.rgb = palette['title_rgb']

            pb = tf.add_paragraph()
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(12)
            pb.font.color.rgb = palette['body_rgb']
            pb.space_before = Pt(3)
        else:
            pb = tf.paragraphs[0]
            pb.text = body
            pb.font.name = _safe_font_name(palette['body_font'])
            pb.font.size = Pt(13)
            pb.font.color.rgb = palette['body_rgb']

def _render_chips_slide(slide, title, points, palette, slide_num, total_slides):
    """Layout 8: 5+ Points Across 2 Columns of Sleek Horizontal Chips."""
    _render_header_bar(slide, title, palette, slide_num, total_slides, "DETAILED BREAKDOWN")
    top_y = Inches(1.75)
    avail_h = Inches(5.1)
    pts = points if points else ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"]
    col_w = Inches(5.5)
    gap_x = Inches(0.4)

    half = (len(pts) + 1) // 2
    pts_left = pts[:half]
    pts_right = pts[half:6]

    for col_idx, col_pts in enumerate([pts_left, pts_right]):
        cx = Inches(1.0) + (col_w + gap_x) * col_idx
        chip_h = (avail_h - Inches(0.18 * (len(col_pts) - 1))) / max(len(col_pts), 1)

        for row_idx, pt in enumerate(col_pts):
            cy = top_y + (chip_h + Inches(0.18)) * row_idx
            _draw_card_shape(slide, cx, cy, col_w, chip_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

            num = col_idx * len(pts_left) + row_idx + 1
            badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.2), cy + Inches(0.18), Inches(0.6), Inches(0.28))
            badge.fill.solid()
            badge.fill.fore_color.rgb = palette['badge_bg_rgb']
            badge.line.fill.background()
            tf_b = badge.text_frame
            p_b = tf_b.paragraphs[0]
            p_b.text = f"{num:02d}"
            p_b.font.size = Pt(9.5)
            p_b.font.bold = True
            p_b.font.color.rgb = palette['badge_text_rgb']
            p_b.alignment = PP_ALIGN.CENTER

            headline, body = _parse_point_parts(pt)
            tb = slide.shapes.add_textbox(cx + Inches(0.95), cy + Inches(0.12), col_w - Inches(1.1), chip_h - Inches(0.24))
            tf = tb.text_frame
            tf.word_wrap = True
            if headline:
                ph = tf.paragraphs[0]
                ph.text = headline
                ph.font.name = _safe_font_name(palette['title_font'])
                ph.font.size = Pt(13.5)
                ph.font.bold = True
                ph.font.color.rgb = palette['title_rgb']

                pb = tf.add_paragraph()
                pb.text = body
                pb.font.name = _safe_font_name(palette['body_font'])
                pb.font.size = Pt(11)
                pb.font.color.rgb = palette['body_rgb']
            else:
                pb = tf.paragraphs[0]
                pb.text = body
                pb.font.name = _safe_font_name(palette['body_font'])
                pb.font.size = Pt(12)
                pb.font.color.rgb = palette['body_rgb']

def _render_thanks_slide(slide, title, points, palette, prs_width, prs_height):
    card_w = Inches(10.5)
    card_h = Inches(5.2)
    left_x = Inches(1.416)
    top_y = Inches(1.15)

    _draw_card_shape(slide, left_x, top_y, card_w, card_h, palette['card_bg_rgb'], palette['card_border_rgb'], 1)

    top_strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, top_y, card_w, Inches(0.08))
    top_strip.fill.solid()
    top_strip.fill.fore_color.rgb = palette['accent_rgb']
    top_strip.line.fill.background()

    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_x + Inches(3.75), top_y + Inches(0.6), Inches(3.0), Inches(0.38))
    pill.fill.solid()
    pill.fill.fore_color.rgb = palette['pill_bg_rgb']
    pill.line.fill.background()
    tf_pill = pill.text_frame
    p_pill = tf_pill.paragraphs[0]
    p_pill.text = "PRESENTATION COMPLETE"
    p_pill.font.name = _safe_font_name(palette['title_font'])
    p_pill.font.size = Pt(10)
    p_pill.font.bold = True
    p_pill.font.color.rgb = palette['accent_rgb']
    p_pill.alignment = PP_ALIGN.CENTER

    tb = slide.shapes.add_textbox(left_x + Inches(0.8), top_y + Inches(1.2), card_w - Inches(1.6), Inches(1.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = format_math_for_pptx(title if title else "Summary & Key Takeaways")
    p.font.name = _safe_font_name(palette['title_font'])
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = palette['title_rgb']
    p.alignment = PP_ALIGN.CENTER

    sub_tb = slide.shapes.add_textbox(left_x + Inches(1.0), top_y + Inches(2.5), card_w - Inches(2.0), Inches(1.4))
    tf_sub = sub_tb.text_frame
    tf_sub.word_wrap = True
    p_s = tf_sub.paragraphs[0]
    p_s.text = "Review these core concepts using active recall flashcards and self-grading quizzes on EduWise."
    p_s.font.name = _safe_font_name(palette['body_font'])
    p_s.font.size = Pt(16)
    p_s.font.color.rgb = palette['body_rgb']
    p_s.alignment = PP_ALIGN.CENTER

    if points:
        for pt in points[:3]:
            p_pt = tf_sub.add_paragraph()
            p_pt.text = f"✓  {format_math_for_pptx(pt)}"
            p_pt.font.name = _safe_font_name(palette['body_font'])
            p_pt.font.size = Pt(13)
            p_pt.font.color.rgb = palette['body_rgb']
            p_pt.alignment = PP_ALIGN.CENTER
            p_pt.space_before = Pt(4)

    foot_tb = slide.shapes.add_textbox(left_x + Inches(1.0), top_y + Inches(4.5), card_w - Inches(2.0), Inches(0.4))
    tf_foot = foot_tb.text_frame
    p_f = tf_foot.paragraphs[0]
    p_f.text = "EduWise AI Studio  ·  Deep Learning for Serious Minds"
    p_f.font.name = _safe_font_name(palette['body_font'])
    p_f.font.size = Pt(10.5)
    p_f.font.color.rgb = palette['body_rgb']
    p_f.alignment = PP_ALIGN.CENTER

def _dispatch_content_layout(slide, title, points, image_path, palette, slide_num, total_slides, explicit_style=None):
    """
    Intelligently select diverse, alternating visual archetypes
    so that every slide in the presentation has a unique, engaging structure.
    """
    if image_path:
        _render_split_image_slide(slide, title, points, image_path, palette, slide_num, total_slides)
        return

    pts = points if points else []
    n_pts = len(pts)

    # Check for math or formula signals in points or title
    has_math = any(s in " ".join(pts) for s in ['=', '∑', '∫', 'Δ', 'α', 'β', 'λ', 'μ', '^', '²', '³', '→', '√', 'frac'])
    # Check for process signals
    has_process = any(s in " ".join(pts).lower() for s in ['step', 'phase', 'stage', 'process', 'cycle', 'first', 'second', 'third', 'pipeline', 'workflow'])
    # Check for comparison signals
    has_comparison = any(s in " ".join(pts).lower() for s in ['vs', 'versus', 'difference', 'compared to', 'contrast', 'pros and cons', 'advantage'])

    style = explicit_style or ""

    if style == 'timeline_process' or has_process:
        _render_stepper_process_slide(slide, title, points, palette, slide_num, total_slides)
    elif style == 'formula_callout' or has_math:
        _render_formula_callout_slide(slide, title, points, palette, slide_num, total_slides)
    elif style == 'comparison_split' or has_comparison or n_pts == 2:
        _render_comparison_split_slide(slide, title, points, palette, slide_num, total_slides)
    elif style == 'two_by_two' or n_pts == 4:
        _render_two_by_two_slide(slide, title, points, palette, slide_num, total_slides)
    elif n_pts >= 5:
        _render_chips_slide(slide, title, points, palette, slide_num, total_slides)
    else:
        # Dynamically rotate between Bento Hero, 3-Card Grid, and Process Flow across consecutive slides
        cycle_idx = slide_num % 3
        if cycle_idx == 1:
            _render_bento_hero_slide(slide, title, points, palette, slide_num, total_slides)
        elif cycle_idx == 2:
            _render_three_cards_slide(slide, title, points, palette, slide_num, total_slides)
        else:
            _render_stepper_process_slide(slide, title, points, palette, slide_num, total_slides)

def create_pptx_file(slides_data, theme_data, customization):
    """
    Generate modern, Canva-level widescreen (16:9) presentations
    with dynamic, alternating layouts, math formatting, and rich visual hierarchy.
    """
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]
    palette = _get_palette(theme_data, customization)
    temp_files_to_delete = []

    total_content_slides = sum(1 for s in slides_data if s.get('slide_type', 'content') == 'content')
    current_content_slide = 0

    try:
        for slide_info in slides_data:
            slide_type = slide_info.get('slide_type', 'content')
            title = slide_info.get('title', 'Untitled Slide')
            points = slide_info.get('points', [])
            image_query = slide_info.get('image_query', 'none')
            explicit_style = slide_info.get('layout_style', None)

            slide = prs.slides.add_slide(blank_layout)

            # Solid background fill
            fill = slide.background.fill
            fill.solid()
            fill.fore_color.rgb = palette['bg_rgb']

            if slide_type == 'intro':
                _render_intro_slide(slide, title, points, palette, prs.slide_width, prs.slide_height)

            elif slide_type == 'thanks':
                _render_thanks_slide(slide, title, points, palette, prs.slide_width, prs.slide_height)

            else:
                current_content_slide += 1
                image_path = None
                if image_query != 'none' and customization.get('image_strategy') != 'none':
                    image_urls = get_image_urls_for_topic_google(image_query)
                    if image_urls:
                        for url in image_urls:
                            image_path = download_image_to_tempfile(url)
                            if image_path:
                                temp_files_to_delete.append(image_path)
                                break

                _dispatch_content_layout(
                    slide, title, points, image_path, palette,
                    current_content_slide, max(total_content_slides, 1),
                    explicit_style=explicit_style
                )

        pptx_file = io.BytesIO()
        prs.save(pptx_file)
        pptx_file.seek(0)
        return pptx_file

    finally:
        for path in temp_files_to_delete:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                current_app.logger.warning("Error removing temp file %s: %s", path, e)
