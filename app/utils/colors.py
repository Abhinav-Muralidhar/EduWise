from pptx.dml.color import RGBColor
from reportlab.lib.colors import HexColor

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string (with or without #) to an (R, G, B) tuple of ints 0-255."""
    if not hex_str:
        return (0, 0, 0)
    cleaned = hex_str.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    if len(cleaned) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(cleaned[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)

def hex_to_rgbcolor(hex_str: str) -> RGBColor:
    """Convert hex string to python-pptx RGBColor object."""
    r, g, b = hex_to_rgb(hex_str)
    return RGBColor(r, g, b)

def hex_to_reportlab_color(hex_str: str) -> HexColor:
    """Convert hex string to ReportLab HexColor object."""
    if not hex_str:
        return HexColor('#000000')
    cleaned = hex_str.lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    if len(cleaned) != 6:
        return HexColor('#000000')
    return HexColor(f"#{cleaned}")

def srgb_to_linear(c_val: int) -> float:
    """Convert 8-bit sRGB channel (0-255) to linear light value (0.0 - 1.0)."""
    c_norm = max(0, min(255, c_val)) / 255.0
    return c_norm / 12.92 if c_norm <= 0.03928 else ((c_norm + 0.055) / 1.055) ** 2.4

def get_relative_luminance(hex_str: str) -> float:
    """Calculate WCAG 2.1 relative luminance (0.0 to 1.0)."""
    r, g, b = hex_to_rgb(hex_str)
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def get_contrast_ratio(hex1: str, hex2: str) -> float:
    """
    Calculate WCAG contrast ratio between two hex colors (1.0 to 21.0).
    A ratio >= 4.5 is required for standard text; >= 3.0 for large text/icons.
    """
    l1 = get_relative_luminance(hex1)
    l2 = get_relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def is_dark_color(hex_str: str) -> bool:
    """Determine whether a color is perceptually dark using relative luminance."""
    return get_relative_luminance(hex_str) < 0.35

def blend_hex(hex1: str, hex2: str, ratio: float = 0.5) -> str:
    """Linearly blend two hex colors with a ratio (0.0 = all hex1, 1.0 = all hex2)."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    ratio = max(0.0, min(1.0, ratio))
    r = int(r1 * (1.0 - ratio) + r2 * ratio)
    g = int(g1 * (1.0 - ratio) + g2 * ratio)
    b = int(b1 * (1.0 - ratio) + b2 * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"

def pick_best_text_color(bg_hex: str, dark_option: str = '#0F172A', light_option: str = '#FFFFFF') -> str:
    """Choose whichever text color has the higher WCAG contrast ratio against the given background."""
    dark_ratio = get_contrast_ratio(dark_option, bg_hex)
    light_ratio = get_contrast_ratio(light_option, bg_hex)
    return dark_option if dark_ratio >= light_ratio else light_option

def ensure_contrast(fg_hex: str, bg_hex: str, min_ratio: float = 4.5, dark_fallback: str = '#0F172A', light_fallback: str = '#FFFFFF') -> str:
    """
    Ensure the foreground color has at least min_ratio contrast against bg_hex.
    If it fails, automatically substitutes the optimal high-contrast fallback.
    Prevents white-on-white, black-on-black, or low-visibility text.
    """
    if get_contrast_ratio(fg_hex, bg_hex) >= min_ratio:
        return fg_hex
    return pick_best_text_color(bg_hex, dark_option=dark_fallback, light_option=light_fallback)

def ensure_accessible_accent(accent_hex: str, bg_hex: str, min_ratio: float = 4.5) -> str:
    """
    Adjust an accent color so it can be legibly used as text/typography on bg_hex,
    preserving the hue while deepening or brightening the shade to satisfy min_ratio contrast.
    """
    if get_contrast_ratio(accent_hex, bg_hex) >= min_ratio:
        return accent_hex

    is_bg_light = get_relative_luminance(bg_hex) > 0.35
    r, g, b = hex_to_rgb(accent_hex)

    # Progressively shift shade until contrast threshold is reached
    for step in range(1, 20):
        if is_bg_light:
            factor = max(0.0, 1.0 - (step * 0.05))
            nr, ng, nb = int(r * factor), int(g * factor), int(b * factor)
        else:
            factor = step * 0.06
            nr = int(r + (255 - r) * factor)
            ng = int(g + (255 - g) * factor)
            nb = int(b + (255 - b) * factor)

        candidate = f"#{nr:02x}{ng:02x}{nb:02x}"
        if get_contrast_ratio(candidate, bg_hex) >= min_ratio:
            return candidate

    return '#0F172A' if is_bg_light else '#FFFFFF'
