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

def is_dark_color(hex_str: str) -> bool:
    """Determine whether a color is perceptually dark using relative luminance."""
    r, g, b = hex_to_rgb(hex_str)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < 135

def blend_hex(hex1: str, hex2: str, ratio: float = 0.5) -> str:
    """Linearly blend two hex colors with a ratio (0.0 = all hex1, 1.0 = all hex2)."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    ratio = max(0.0, min(1.0, ratio))
    r = int(r1 * (1.0 - ratio) + r2 * ratio)
    g = int(g1 * (1.0 - ratio) + g2 * ratio)
    b = int(b1 * (1.0 - ratio) + b2 * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"

