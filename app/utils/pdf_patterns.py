import math
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from app.utils.colors import hex_to_reportlab_color, blend_hex, is_dark_color

def determine_pattern_style(topic: str, accent_hex: str) -> str:
    """
    Intelligently select a geometric pattern style based on topic domain
    and color palette to match high-end editorial and textbook design standards.
    """
    topic_lower = (topic or "").lower()

    stem_keywords = [
        'computer', 'algorithm', 'code', 'data', 'software', 'network',
        'quantum', 'circuit', 'crypto', 'system', 'binary', 'logic',
        'machine learning', 'ai', 'neural', 'cloud', 'database'
    ]
    science_keywords = [
        'cell', 'biology', 'chemistry', 'molecule', 'physics', 'energy',
        'thermodynamic', 'organic', 'genetics', 'anatomy', 'organism',
        'reaction', 'ecology', 'atom', 'particle', 'astronomy'
    ]
    humanities_keywords = [
        'history', 'literature', 'philosophy', 'law', 'business', 'economy',
        'market', 'management', 'art', 'culture', 'finance', 'policy',
        'psychology', 'sociology', 'ethics', 'politics'
    ]

    for kw in stem_keywords:
        if kw in topic_lower:
            return 'circuit_nodes'

    for kw in science_keywords:
        if kw in topic_lower:
            return 'isometric_grid'

    for kw in humanities_keywords:
        if kw in topic_lower:
            return 'diagonal_pinstripes'

    accent_upper = (accent_hex or "").upper()
    if any(accent_upper.startswith(c) for c in ['#25', '#1D', '#02', '#0E', '#3B']):
        return 'circuit_nodes'
    elif any(accent_upper.startswith(c) for c in ['#05', '#10', '#16', '#0D']):
        return 'isometric_grid'
    elif any(accent_upper.startswith(c) for c in ['#7C', '#93', '#C0', '#DB', '#E1']):
        return 'diagonal_pinstripes'

    return 'dot_matrix'

def draw_dot_matrix(canvas_obj, x, y, width, height, dot_color, spacing=13, radius=1.0, accent_color=None):
    """Draw a clean, architectural dot-matrix grid."""
    canvas_obj.saveState()
    canvas_obj.setFillColor(dot_color)

    clip_path = canvas_obj.beginPath()
    clip_path.rect(x, y, width, height)
    canvas_obj.clipPath(clip_path, stroke=0)

    cols = int(width // spacing) + 1
    rows = int(height // spacing) + 1

    for c_idx in range(cols):
        for r_idx in range(rows):
            px = x + c_idx * spacing
            py = y + r_idx * spacing

            if accent_color and (c_idx % 4 == 0 and r_idx % 4 == 0):
                canvas_obj.setFillColor(accent_color)
                canvas_obj.circle(px, py, radius * 1.5, fill=1, stroke=0)
                canvas_obj.setFillColor(dot_color)
            else:
                canvas_obj.circle(px, py, radius, fill=1, stroke=0)

    canvas_obj.restoreState()

def draw_isometric_grid(canvas_obj, x, y, width, height, stroke_color, spacing=16):
    """Draw a modern isometric triangular / diamond micro-grid."""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(stroke_color)
    canvas_obj.setLineWidth(0.45)

    clip_path = canvas_obj.beginPath()
    clip_path.rect(x, y, width, height)
    canvas_obj.clipPath(clip_path, stroke=0)

    diag_span = width + height * 2
    steps = int(diag_span // spacing) + 2

    for i in range(-steps, steps):
        x_start = x + i * spacing
        canvas_obj.line(x_start, y, x_start + height * 1.732, y + height)

    for i in range(-steps, steps):
        x_start = x + i * spacing
        canvas_obj.line(x_start, y + height, x_start + height * 1.732, y)

    canvas_obj.restoreState()

def draw_diagonal_pinstripes(canvas_obj, x, y, width, height, stroke_color, spacing=14):
    """Draw sleek 45-degree angled pinstripe hatching."""
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(stroke_color)
    canvas_obj.setLineWidth(0.5)

    clip_path = canvas_obj.beginPath()
    clip_path.rect(x, y, width, height)
    canvas_obj.clipPath(clip_path, stroke=0)

    total_span = width + height
    steps = int(total_span // spacing) + 2

    for i in range(-int(height // spacing), int(width // spacing) + 2):
        x0 = x + i * spacing
        canvas_obj.line(x0, y, x0 + height, y + height)

    canvas_obj.restoreState()

def draw_circuit_nodes(canvas_obj, x, y, width, height, stroke_color, dot_color, spacing=18):
    """Draw a tech / STEM inspired node matrix with subtle orthogonal traces."""
    canvas_obj.saveState()

    clip_path = canvas_obj.beginPath()
    clip_path.rect(x, y, width, height)
    canvas_obj.clipPath(clip_path, stroke=0)

    cols = int(width // spacing) + 1
    rows = int(height // spacing) + 1

    canvas_obj.setStrokeColor(stroke_color)
    canvas_obj.setLineWidth(0.4)

    for c_idx in range(0, cols, 2):
        for r_idx in range(0, rows, 2):
            px = x + c_idx * spacing
            py = y + r_idx * spacing
            if (c_idx + r_idx) % 3 == 0 and c_idx + 1 < cols:
                canvas_obj.line(px, py, px + spacing, py)
            if (c_idx * r_idx) % 4 == 0 and r_idx + 1 < rows:
                canvas_obj.line(px, py, px, py + spacing)

    canvas_obj.setFillColor(dot_color)
    for c_idx in range(cols):
        for r_idx in range(rows):
            px = x + c_idx * spacing
            py = y + r_idx * spacing
            r = 1.3 if (c_idx % 2 == 0 and r_idx % 2 == 0) else 0.75
            canvas_obj.circle(px, py, r, fill=1, stroke=0)

    canvas_obj.restoreState()

def render_pattern_block(canvas_obj, pattern_style, x, y, width, height, stroke_color, dot_color, accent_color=None):
    """Dispatch drawing to the appropriate pattern primitive."""
    if pattern_style == 'circuit_nodes':
        draw_circuit_nodes(canvas_obj, x, y, width, height, stroke_color, dot_color, spacing=18)
    elif pattern_style == 'isometric_grid':
        draw_isometric_grid(canvas_obj, x, y, width, height, stroke_color, spacing=16)
    elif pattern_style == 'diagonal_pinstripes':
        draw_diagonal_pinstripes(canvas_obj, x, y, width, height, stroke_color, spacing=14)
    else:
        draw_dot_matrix(canvas_obj, x, y, width, height, dot_color, spacing=13, radius=1.0, accent_color=accent_color)

def _safe_font(font_name, is_bold=False):
    """Return a safe font name registered in ReportLab or core font fallback."""
    target = f"{font_name}-Bold" if is_bold else font_name
    core = ['Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Times-Roman', 'Times-Bold', 'Courier', 'Courier-Bold']
    if target in pdfmetrics.getRegisteredFontNames() or target in core:
        return target
    return 'Helvetica-Bold' if is_bold else 'Helvetica'

def draw_page_background(canvas_obj, doc, topic, accent_hex, bg_hex, is_dark, has_intro_cover, accent_text_hex=None, is_first_page=True):
    """
    Render edge-to-edge background fills and decorative vector pattern canopies.
    CRITICAL ARCHITECTURE RULE:
    This MUST execute in onFirstPage and onLaterPages callbacks BEFORE story flowables are drawn.
    This guarantees that background colors and watermark patterns reside at z-index 0 (behind text),
    completely eliminating any blank, black-on-black, or white-on-white text coverage bugs.
    """
    page_w, page_h = doc.pagesize
    accent_color = hex_to_reportlab_color(accent_hex)
    bg_color = hex_to_reportlab_color(bg_hex)
    pattern_style = determine_pattern_style(topic, accent_hex)

    pattern_stroke_hex = blend_hex(accent_hex, bg_hex, 0.75 if is_dark else 0.86)
    pattern_dot_hex = blend_hex(accent_hex, bg_hex, 0.65 if is_dark else 0.78)
    pattern_stroke_color = hex_to_reportlab_color(pattern_stroke_hex)
    pattern_dot_color = hex_to_reportlab_color(pattern_dot_hex)

    # 1. Edge-to-edge background fill if dark or custom color
    if is_dark or bg_hex.upper() != '#FFFFFF':
        canvas_obj.saveState()
        canvas_obj.setFillColor(bg_color)
        canvas_obj.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        canvas_obj.restoreState()

    # 2. First Page: Prominent Accent Bar & Geometric Pattern Canopy
    if is_first_page:
        canvas_obj.saveState()
        canvas_obj.setFillColor(accent_color)
        canvas_obj.rect(0, page_h - 6, page_w, 6, fill=1, stroke=0)

        # Prominent Top-Right Pattern Canopy
        canopy_w, canopy_h = 240, 130
        canopy_x = page_w - canopy_w
        canopy_y = page_h - canopy_h
        render_pattern_block(
            canvas_obj, pattern_style,
            canopy_x, canopy_y, canopy_w, canopy_h,
            pattern_stroke_color, pattern_dot_color, accent_color
        )

        # Accent canopy boundary rule
        canvas_obj.setStrokeColor(accent_color)
        canvas_obj.setLineWidth(1.0)
        canvas_obj.line(canopy_x, canopy_y, page_w, canopy_y)
        canvas_obj.restoreState()

        # Dedicated cover gets bottom accent motif
        if has_intro_cover:
            canvas_obj.saveState()
            canvas_obj.setFillColor(accent_color)
            canvas_obj.rect(0, 0, page_w, 6, fill=1, stroke=0)
            render_pattern_block(
                canvas_obj, pattern_style,
                0, 6, 200, 80,
                pattern_stroke_color, pattern_dot_color, accent_color
            )
            canvas_obj.restoreState()

def create_pattern_canvas_maker(topic, title_font_name, body_font_name, bg_hex, title_hex, body_hex, accent_hex, is_dark, has_intro_cover, accent_text_hex=None):
    """
    Factory creating a publication-grade NumberedCanvas class that records all pages,
    and draws running headers and footers with 'Page X of Y' strictly in the safe page margins.
    Never paints full-page background rectangles over story content.
    """
    if not accent_text_hex:
        accent_text_hex = blend_hex(accent_hex, '#000000', 0.3) if not is_dark else blend_hex(accent_hex, '#FFFFFF', 0.3)

    class NumberedCanvasWithPatterns(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            accent_color = hex_to_reportlab_color(accent_hex)
            accent_label_color = hex_to_reportlab_color(accent_text_hex)
            title_font_color = hex_to_reportlab_color(title_hex)
            divider_color = hex_to_reportlab_color('#374151' if is_dark else '#E5E7EB')
            muted_text_color = hex_to_reportlab_color('#9CA3AF' if is_dark else '#4B5563')

            font_title_bold = _safe_font(title_font_name, is_bold=True)
            font_body_reg = _safe_font(body_font_name, is_bold=False)

            for idx, state in enumerate(self._saved_page_states):
                self.__dict__.update(state)
                page_num = idx + 1
                page_w, page_h = self._pagesize

                # Running Footers and Headers strictly within safe margin bounds (y <= 0.55" or y >= page_h - 0.55")

                # Single-page document (page 1 is also the final page)
                if num_pages == 1:
                    if not has_intro_cover:
                        self.saveState()
                        self.setStrokeColor(divider_color)
                        self.setLineWidth(0.5)
                        self.line(0.55 * inch, 0.5 * inch, page_w - 0.55 * inch, 0.5 * inch)

                        self.setFont(font_body_reg, 8)
                        self.setFillColor(muted_text_color)
                        self.drawString(0.55 * inch, 0.35 * inch, "EduWise  ·  Grounded Active Learning Studio")
                        self.drawRightString(page_w - 0.55 * inch, 0.35 * inch, "Page 1 of 1  ·  Complete")

                        self.setFont(font_title_bold, 7)
                        self.setFillColor(accent_label_color)
                        self.drawRightString(page_w - 0.55 * inch, 0.55 * inch, "🎓 ACTIVE RECALL & RETENTION VERIFIED")
                        self.restoreState()

                # Multi-page document: Page 1
                elif page_num == 1:
                    if not has_intro_cover:
                        self.saveState()
                        self.setStrokeColor(divider_color)
                        self.setLineWidth(0.5)
                        self.line(0.55 * inch, 0.5 * inch, page_w - 0.55 * inch, 0.5 * inch)

                        self.setFont(font_body_reg, 8)
                        self.setFillColor(muted_text_color)
                        self.drawString(0.55 * inch, 0.35 * inch, "EduWise  ·  Grounded Active Learning Studio")
                        self.drawRightString(page_w - 0.55 * inch, 0.35 * inch, f"Page 1 of {num_pages}")
                        self.restoreState()

                # Multi-page document: Final Page
                elif page_num == num_pages:
                    self.saveState()
                    # Running footer rule
                    self.setStrokeColor(divider_color)
                    self.setLineWidth(0.5)
                    self.line(0.55 * inch, 0.5 * inch, page_w - 0.55 * inch, 0.5 * inch)

                    self.setFont(font_body_reg, 8)
                    self.setFillColor(muted_text_color)
                    self.drawString(0.55 * inch, 0.35 * inch, "EduWise  ·  Grounded Active Learning Studio")
                    self.drawRightString(page_w - 0.55 * inch, 0.35 * inch, f"Page {page_num} of {num_pages}  ·  Complete")

                    # Completion seal
                    self.setFont(font_title_bold, 7)
                    self.setFillColor(accent_label_color)
                    self.drawRightString(page_w - 0.55 * inch, 0.55 * inch, "🎓 ACTIVE RECALL & RETENTION VERIFIED")
                    self.restoreState()

                # Multi-page document: Interior Pages (1 < page_num < num_pages)
                else:
                    self.saveState()
                    # Running Header in top margin
                    self.setStrokeColor(accent_color)
                    self.setLineWidth(0.75)
                    self.line(0.55 * inch, page_h - 0.55 * inch, page_w - 0.55 * inch, page_h - 0.55 * inch)

                    header_title = topic[:55] + ("..." if len(topic) > 55 else "")
                    self.setFont(font_title_bold, 8.5)
                    self.setFillColor(title_font_color)
                    self.drawString(0.55 * inch, page_h - 0.45 * inch, header_title)

                    self.setFont(font_body_reg, 8)
                    self.setFillColor(muted_text_color)
                    self.drawRightString(page_w - 0.55 * inch, page_h - 0.45 * inch, "Comprehensive Study Notes  ▪ ▪ ▪")

                    # Running Footer in bottom margin
                    self.setStrokeColor(divider_color)
                    self.setLineWidth(0.5)
                    self.line(0.55 * inch, 0.5 * inch, page_w - 0.55 * inch, 0.5 * inch)

                    self.drawString(0.55 * inch, 0.35 * inch, "EduWise  ·  Grounded Active Learning Studio")
                    self.drawRightString(page_w - 0.55 * inch, 0.35 * inch, f"Page {page_num} of {num_pages}")
                    self.restoreState()

                super().showPage()
            super().save()

    return NumberedCanvasWithPatterns
