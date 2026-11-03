import re

GREEK_LETTERS = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\Gamma': 'Γ',
    r'\delta': 'δ', r'\Delta': 'Δ', r'\epsilon': 'ε', r'\varepsilon': 'ε',
    r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ', r'\Theta': 'Θ',
    r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\Lambda': 'Λ',
    r'\mu': 'μ', r'\nu': 'ν', r'\xi': 'ξ', r'\Xi': 'Ξ',
    r'\pi': 'π', r'\Pi': 'Π', r'\rho': 'ρ', r'\sigma': 'σ',
    r'\Sigma': 'Σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
    r'\Phi': 'Φ', r'\chi': 'χ', r'\psi': 'ψ', r'\Psi': 'Ψ',
    r'\omega': 'ω', r'\Omega': 'Ω'
}

MATH_OPERATORS = {
    r'\times': '×',
    r'\div': '÷',
    r'\cdot': '·',
    r'\pm': '±',
    r'\mp': '∓',
    r'\approx': '≈',
    r'\neq': '≠',
    r'\le': '≤',
    r'\leq': '≤',
    r'\ge': '≥',
    r'\geq': '≥',
    r'\infty': '∞',
    r'\int': '∫',
    r'\iint': '∬',
    r'\sum': '∑',
    r'\prod': '∏',
    r'\partial': '∂',
    r'\nabla': '∇',
    r'\sqrt': '√',
    r'\rightarrow': '→',
    r'\to': '→',
    r'\leftarrow': '←',
    r'\Rightarrow': '⇒',
    r'\Leftarrow': '⇐',
    r'\leftrightarrow': '↔',
    r'\Leftrightarrow': '⇔',
    r'\forall': '∀',
    r'\exists': '∃',
    r'\in': '∈',
    r'\notin': '∉',
    r'\subset': '⊂',
    r'\subseteq': '⊆',
    r'\cup': '∪',
    r'\cap': '∩',
    r'\degree': '°',
    r'\circ': '°'
}

SUPERSCRIPTS = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'n': 'ⁿ', 'i': 'ⁱ', 'x': 'ˣ', 'y': 'ʸ', 't': 'ᵗ',
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'm': 'ᵐ'
}

SUBSCRIPTS = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'o': 'ₒ', 'x': 'ₓ', 'i': 'ᵢ',
    'j': 'ⱼ', 'k': 'ₖ', 't': 'ₜ', 'n': 'ₙ', 'm': 'ₘ'
}

def clean_latex_fractions(text: str) -> str:
    """Recursively convert LaTeX fractions \\frac{numerator}{denominator} -> (numerator / denominator)."""
    pattern = r'\\frac\{([^{}]+)\}\{([^{}]+)\}'
    for _ in range(5):
        if not re.search(pattern, text):
            break
        text = re.sub(pattern, r'(\1 / \2)', text)
    return text

def clean_latex_roots(text: str) -> str:
    """Convert \\sqrt[n]{x} -> ⁿ√(x) and \\sqrt{x} -> √(x)."""
    def root_n_repl(m):
        n_str = m.group(1)
        inner = m.group(2)
        n_sup = "".join(SUPERSCRIPTS.get(c, c) for c in n_str)
        return f"{n_sup}√({inner})"

    text = re.sub(r'\\sqrt\[([^\[\]]+)\]\{([^{}]+)\}', root_n_repl, text)
    text = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', text)
    return text

def replace_greek_and_symbols(text: str) -> str:
    """Replace LaTeX Greek commands and common mathematical operators."""
    # Greek letters
    for cmd, sym in sorted(GREEK_LETTERS.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(re.escape(cmd) + r'(?![a-zA-Z])', sym, text)

    # Math operators
    for cmd, sym in sorted(MATH_OPERATORS.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(re.escape(cmd) + r'(?![a-zA-Z])', sym, text)

    # Plain text arrows & operators
    text = re.sub(r'<->|<=>', '↔', text)
    text = re.sub(r'-->|->', '→', text)
    text = re.sub(r'<--|<-', '←', text)
    text = re.sub(r'!=', '≠', text)
    text = re.sub(r'<=', '≤', text)
    text = re.sub(r'>=', '≥', text)
    text = re.sub(r'\+/-', '±', text)

    return text

def format_math_for_pptx(text: str) -> str:
    """
    Format mathematical equations and scientific notations into clean,
    Unicode-compliant strings ideal for PowerPoint text shapes.
    """
    if not text:
        return ""

    text = clean_latex_fractions(text)
    text = clean_latex_roots(text)
    text = replace_greek_and_symbols(text)

    # Superscripts: ^{12} or ^2 -> ¹² or ²
    def sup_repl(m):
        inner = m.group(1) or m.group(2)
        return "".join(SUPERSCRIPTS.get(c, c) for c in inner)

    text = re.sub(r'\^\{([a-zA-Z0-9+\-=()]+)\}|\^([0-9nixytabcdm])', sup_repl, text)

    # Subscripts: _{12} or _2 -> ₁₂ or ₂
    def sub_repl(m):
        inner = m.group(1) or m.group(2)
        return "".join(SUBSCRIPTS.get(c, c) for c in inner)

    text = re.sub(r'_\{([a-zA-Z0-9+\-=()]+)\}|_([0-9aeoxijkntm])', sub_repl, text)

    # Clean display math and inline math delimiters: $$...$$ or $...$
    text = re.sub(r'\$\$([^\$]+)\$\$', r'\1', text)
    text = re.sub(r'\$([^\$]+)\$', r'\1', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\1', text)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text)

    # Clean leftover backslashes in simple words (e.g. \text{hello} -> hello)
    text = re.sub(r'\\text\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\mathbf\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\mathit\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\mathrm\{([^{}]+)\}', r'\1', text)

    return text.strip()

def format_math_for_reportlab(text: str) -> str:
    """
    Format mathematical equations and scientific notations for ReportLab XML flowables,
    leveraging <sup> and <sub> tags, Greek characters, and clean math operators.
    """
    if not text:
        return ""

    text = clean_latex_fractions(text)
    text = clean_latex_roots(text)
    text = replace_greek_and_symbols(text)

    # Superscripts -> <sup>...</sup>
    def sup_xml_repl(m):
        inner = m.group(1) or m.group(2)
        return f"<sup>{inner}</sup>"

    text = re.sub(r'\^\{([a-zA-Z0-9+\-=()]+)\}|\^([0-9nixytabcdm])', sup_xml_repl, text)

    # Subscripts -> <sub>...</sub>
    def sub_xml_repl(m):
        inner = m.group(1) or m.group(2)
        return f"<sub>{inner}</sub>"

    text = re.sub(r'_\{([a-zA-Z0-9+\-=()]+)\}|_([0-9aeoxijkntm])', sub_xml_repl, text)

    # Clean display math and inline math delimiters: $$...$$ or $...$
    text = re.sub(r'\$\$([^\$]+)\$\$', r'\1', text)
    text = re.sub(r'\$([^\$]+)\$', r'\1', text)
    text = re.sub(r'\\\[(.*?)\\\]', r'\1', text)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text)

    # Clean leftover backslashes in simple words (e.g. \text{hello} -> hello)
    text = re.sub(r'\\text\{([^{}]+)\}', r'\1', text)
    text = re.sub(r'\\mathbf\{([^{}]+)\}', r'<b>\1</b>', text)
    text = re.sub(r'\\mathit\{([^{}]+)\}', r'<i>\1</i>', text)
    text = re.sub(r'\\mathrm\{([^{}]+)\}', r'\1', text)

    return text.strip()

def is_mathematical_line(text: str) -> bool:
    """Identify if a line is an isolated mathematical formula or formal scientific relationship."""
    stripped = text.strip()
    if stripped.startswith('$$') and stripped.endswith('$$'):
        return True
    if stripped.startswith(r'\[') and stripped.endswith(r'\]'):
        return True
    # Math indicator patterns
    math_signals = [r'\frac', r'\sqrt', r'\sum', r'\int', r'\alpha', r'\beta', r'\Delta', r'\partial', r'\nabla']
    if any(s in stripped for s in math_signals) and ('=' in stripped or '→' in stripped or '->' in stripped):
        return True
    return False

