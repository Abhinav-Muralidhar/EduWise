from pptx.dml.color import RGBColor
from reportlab.lib.colors import HexColor

def hex_to_rgbcolor(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return RGBColor(0, 0, 0)
    return RGBColor(*(int(hex_str[i:i+2], 16) for i in (0, 2, 4)))

def hex_to_reportlab_color(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return HexColor('#000000')
    return HexColor(f"#{hex_str}")
