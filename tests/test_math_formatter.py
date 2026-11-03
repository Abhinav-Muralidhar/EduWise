from app.utils.math_formatter import format_math_for_pptx, format_math_for_reportlab

def test_equation_formatting():
    raw = r"Energy is $E=mc^2$, and $\Delta G = \Delta H - T\Delta S$."
    pptx_formatted = format_math_for_pptx(raw)
    rl_formatted = format_math_for_reportlab(raw)

    assert "E=mc²" in pptx_formatted
    assert "ΔG" in pptx_formatted or "Δ G" in pptx_formatted
    assert "$" not in pptx_formatted

    assert "E=mc<sup>2</sup>" in rl_formatted
    assert "ΔG" in rl_formatted or "Δ G" in rl_formatted
    assert "$" not in rl_formatted

def test_chemical_formulas():
    raw = "Water is H_2O, carbon dioxide is CO_2, glucose is C_6H_{12}O_6."
    pptx_formatted = format_math_for_pptx(raw)
    rl_formatted = format_math_for_reportlab(raw)

    assert "H₂O" in pptx_formatted
    assert "CO₂" in pptx_formatted
    assert "C₆H₁₂O₆" in pptx_formatted

    assert "H<sub>2</sub>O" in rl_formatted
    assert "CO<sub>2</sub>" in rl_formatted
    assert "C<sub>6</sub>H<sub>12</sub>O<sub>6</sub>" in rl_formatted

def test_fractions_and_operators():
    raw = r"\frac{a+b}{c} \le \sqrt{x} \approx \pi \cdot r^2"
    pptx_formatted = format_math_for_pptx(raw)
    rl_formatted = format_math_for_reportlab(raw)

    assert "(a+b / c)" in pptx_formatted
    assert "≤" in pptx_formatted
    assert "√(x)" in pptx_formatted
    assert "≈" in pptx_formatted
    assert "π" in pptx_formatted
    assert "·" in pptx_formatted
    assert "r²" in pptx_formatted

