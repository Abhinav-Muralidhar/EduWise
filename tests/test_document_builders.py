import io
from pptx import Presentation
from app.services.pptx_builder import create_pptx_file
from app.services.pdf_builder import create_pdf_reportlab

def test_pptx_canva_builder_all_layouts(app):
    with app.app_context():
        slides_data = [
            {
                'slide_type': 'intro',
                'title': 'Quantum Computing Principles',
                'points': ['Superposition', 'Entanglement', 'Interference']
            },
            {
                'slide_type': 'content',
                'title': 'Core Quantum Phenomena',
                'points': [
                    'Superposition: Qubits exist as linear combinations of basis states |0> and |1>',
                    'Entanglement: Correlation between multi-qubit states without classical analogue',
                    'Interference: Constructive and destructive phase manipulation'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'content',
                'title': 'Quantum Hardware Approaches',
                'points': [
                    'Superconducting Transmons: Josephson junction circuit loops',
                    'Trapped Ions: Laser-manipulated atomic electronic transitions',
                    'Topological Qubits: Non-Abelian anyon braids with hardware-level fault tolerance',
                    'Photonic Qubits: Linear optical networks operating at room temperature'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'content',
                'title': 'Single Point Highlight',
                'points': [
                    'Decoherence Time: The critical window before environmental noise degrades quantum states.'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'content',
                'title': 'Six Sub-topics Overview',
                'points': [
                    'Point 1: Qubit registers',
                    'Point 2: Unitary gates',
                    'Point 3: Measurement collapse',
                    'Point 4: Quantum error correction',
                    'Point 5: Surface codes',
                    'Point 6: Threshold theorem'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'thanks',
                'title': 'Summary & Further Reading',
                'points': ['Review Shor and Grover algorithms', 'Practice circuit decomposition']
            }
        ]

        theme_data = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#1C1A17',
            'font-color-body': '#4B5563',
            'bg-color': '#F6F4EE',
            'accent-color': '#E8590C'
        }
        customization = {'theme_base': 'light', 'image_strategy': 'none'}

        pptx_buf = create_pptx_file(slides_data, theme_data, customization)
        assert pptx_buf is not None
        data = pptx_buf.getvalue()
        assert len(data) > 1000

        # Validate that the generated file is a valid 16:9 presentation
        prs = Presentation(io.BytesIO(data))
        assert len(prs.slides) == 6
        assert round(prs.slide_width.inches, 2) == 13.33
        assert round(prs.slide_height.inches, 2) == 7.5

def test_pptx_dark_mode(app):
    with app.app_context():
        slides_data = [
            {'slide_type': 'intro', 'title': 'Dark Theme Deck', 'points': []},
            {'slide_type': 'content', 'title': 'Two Pillars', 'points': ['Alpha: First concept', 'Beta: Second concept'], 'image_query': 'none'}
        ]
        theme_dark = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#FFFFFF',
            'font-color-body': '#D1D5DB',
            'bg-color': '#18181B',
            'accent-color': '#6366F1'
        }
        pptx_buf = create_pptx_file(slides_data, theme_dark, {'theme_base': 'dark', 'image_strategy': 'none'})
        assert len(pptx_buf.getvalue()) > 1000

def test_pdf_canva_builder_all_elements(app):
    with app.app_context():
        content = """
## Introduction to Cellular Respiration
Cellular respiration is the biochemical pathway through which cells release energy from glucose.

> Core Concept: Glycolysis occurs in the cytoplasm and is an anaerobic process producing 2 net ATP.

### Metabolic Pathways
* **Glycolysis**: Cytoplasmic breakdown of 6-carbon glucose into two 3-carbon pyruvate molecules.
* **Citric Acid Cycle**: Matrix reactions oxidizing acetyl-CoA into carbon dioxide.
* **Electron Transport Chain**: Inner mitochondrial membrane cristae proton pumping.

| Stage | ATP Yield | Cellular Location |
| Glycolysis | 2 ATP | Cytoplasm |
| Krebs Cycle | 2 ATP | Mitochondrial Matrix |
| Oxidative Phosphorylation | 28-32 ATP | Inner Membrane |

```python
# Net energy equation
glucose + 6O2 -> 6CO2 + 6H2O + 32ATP
```
"""
        theme = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#1C1A17',
            'font-color-body': '#374151',
            'bg-color': '#FFFFFF',
            'accent-color': '#E8590C'
        }

        # Test with Hero Header (intro_slide = false)
        pdf_buf1 = create_pdf_reportlab('Cellular Respiration 101', content, theme, {'intro_slide': 'false', 'theme_base': 'light'})
        assert pdf_buf1 is not None
        assert len(pdf_buf1.getvalue()) > 5000

        # Test with Cover Page (intro_slide = true) in Dark Mode
        theme_dark = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#FFFFFF',
            'font-color-body': '#D1D5DB',
            'bg-color': '#18181B',
            'accent-color': '#6366F1'
        }
        pdf_buf2 = create_pdf_reportlab('Cellular Respiration 101', content, theme_dark, {'intro_slide': 'true', 'theme_base': 'dark'})
        assert pdf_buf2 is not None
        assert len(pdf_buf2.getvalue()) > 5000

def test_document_builders_with_math_and_archetypes(app):
    with app.app_context():
        # PPTX with math and layout archetypes
        slides_data = [
            {'slide_type': 'intro', 'title': 'Physics & Thermodynamics', 'points': []},
            {
                'slide_type': 'content',
                'title': 'Fundamental Thermodynamic Relation',
                'layout_style': 'formula_callout',
                'points': [
                    r'$$ \Delta G = \Delta H - T \Delta S $$',
                    'Enthalpy (ΔH): Total heat content of the closed system',
                    'Entropy (ΔS): Degree of thermal disorder and microscopic microstates',
                    r'Spontaneity: Reaction is spontaneous if \Delta G < 0'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'content',
                'title': 'Chemical Reaction Stages',
                'layout_style': 'timeline_process',
                'points': [
                    'Reactants: Initial chemical bonds and energy states (H_2 + O_2)',
                    'Transition State: Peak activation energy barrier E_a',
                    'Products: Final thermodynamically stable state (H_2O)'
                ],
                'image_query': 'none'
            },
            {
                'slide_type': 'content',
                'title': 'Classical vs Quantum Mechanics',
                'layout_style': 'comparison_split',
                'points': [
                    'Classical Physics: Continuous energy values and deterministic trajectory',
                    'Quantum Mechanics: Discrete quantized energy levels and probability wavefunctions'
                ],
                'image_query': 'none'
            }
        ]

        theme = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#0F172A',
            'font-color-body': '#334155',
            'bg-color': '#F8FAFC',
            'accent-color': '#2563EB'
        }

        pptx_buf = create_pptx_file(slides_data, theme, {'theme_base': 'light', 'image_strategy': 'none'})
        assert pptx_buf is not None
        prs = Presentation(io.BytesIO(pptx_buf.getvalue()))
        assert len(prs.slides) == 4

        # PDF with standalone formula cards and inline math notations
        pdf_math_content = r"""
## Thermodynamic Formulations

Here is the foundational criterion for chemical spontaneity at constant temperature and pressure:

$$ \Delta G = \Delta H - T \Delta S $$

* **Gibbs Energy**: \Delta G must be negative (\Delta G \le 0) for spontaneity.
* **Enthalpy**: \Delta H represents internal heat changes.
* **Water Formation**: 2H_2 + O_2 \rightarrow 2H_2O with reaction quotient Q \le K_{eq}.

| State Variable | Symbol | Unit of Measure |
| Gibbs Free Energy | \Delta G | kJ/mol |
| Temperature | T | K |
| Entropy Change | \Delta S | J/(mol\cdot K) |
"""
        pdf_buf = create_pdf_reportlab('Advanced Thermodynamics', pdf_math_content, theme, {'intro_slide': 'false', 'theme_base': 'light'})
        assert pdf_buf is not None
        assert len(pdf_buf.getvalue()) > 3000

def test_pdf_patterns_and_editorial_archetypes(app):
    from app.utils.pdf_patterns import determine_pattern_style

    # 1. Pattern selector tests
    assert determine_pattern_style('Machine Learning Algorithms', '#2563EB') == 'circuit_nodes'
    assert determine_pattern_style('Cellular Biology & Genetics', '#10B981') == 'isometric_grid'
    assert determine_pattern_style('Macro Economics and Trade Policy', '#7C3AED') == 'diagonal_pinstripes'
    assert determine_pattern_style('General Overview', '#E8590C') == 'dot_matrix'

    with app.app_context():
        # 2. Multi-archetype callout rendering
        editorial_content = """
## Advanced Orbital Mechanics & Celestial Navigation

Here is the central governing body equation:

$$ F = G \\frac{m_1 m_2}{r^2} $$

> Exam Tip: Do not confuse orbital velocity with escape velocity; escape velocity is \\sqrt{2} times orbital velocity.

> Real-World Application: The Apollo lunar transfer orbit utilized this exact patched-conic approximation for fuel efficiency.

> Key Concept: Specific orbital energy is conserved along any Keplerian conic section.

* Orbital Period: T^2 \\propto a^3 (Kepler's Third Law)
* Universal Constant: G \\approx 6.674 \\times 10^{-11} m^3 kg^{-1} s^{-2}
"""
        theme = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#0F172A',
            'font-color-body': '#334155',
            'bg-color': '#FFFFFF',
            'accent-color': '#2563EB'
        }

        # Test full generation with cover page
        buf_cover = create_pdf_reportlab('Orbital Mechanics', editorial_content, theme, {'intro_slide': 'true', 'theme_base': 'light'})
        assert buf_cover is not None
        assert len(buf_cover.getvalue()) > 4000

        # Test dark mode generation with direct header
        dark_theme = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#FFFFFF',
            'font-color-body': '#D1D5DB',
            'bg-color': '#111827',
            'accent-color': '#38BDF8'
        }
        buf_dark = create_pdf_reportlab('Orbital Mechanics', editorial_content, dark_theme, {'intro_slide': 'false', 'theme_base': 'dark'})
        assert buf_dark is not None
        assert len(buf_dark.getvalue()) > 4000

def test_contrast_engine_prevents_low_visibility_and_white_on_white(app):
    from app.utils.colors import (
        get_contrast_ratio, ensure_contrast, ensure_accessible_accent, pick_best_text_color
    )

    # 1. Pure white on pure white must fail and be adjusted
    assert round(get_contrast_ratio('#FFFFFF', '#FFFFFF'), 2) == 1.0
    safe_on_white = ensure_contrast('#FFFFFF', '#FFFFFF', min_ratio=4.5)
    assert safe_on_white != '#FFFFFF'
    assert get_contrast_ratio(safe_on_white, '#FFFFFF') >= 4.5

    # 2. Pure black on dark background must fail and be adjusted
    assert get_contrast_ratio('#000000', '#18181B') < 2.0
    safe_on_dark = ensure_contrast('#000000', '#18181B', min_ratio=4.5)
    assert safe_on_dark != '#000000'
    assert get_contrast_ratio(safe_on_dark, '#18181B') >= 4.5

    # 3. Low visibility accents (like yellow on white) must be darkened
    yellow_on_white = ensure_accessible_accent('#FBBF24', '#FFFFFF', min_ratio=4.5)
    assert yellow_on_white != '#FBBF24'
    assert get_contrast_ratio(yellow_on_white, '#FFFFFF') >= 4.5

    # 4. Table header text picker
    assert pick_best_text_color('#FBBF24') == '#0F172A'  # on yellow, pick dark text
    assert pick_best_text_color('#1E293B') == '#FFFFFF'  # on navy, pick light text

    # 5. Pathological theme generation test in both PDF and PPTX
    with app.app_context():
        bad_theme = {
            'font-title': 'Roboto',
            'font-body': 'Roboto',
            'font-color-title': '#FFFFFF',  # White text on white page!
            'font-color-body': '#FFFFFF',   # White text on white page!
            'bg-color': '#FFFFFF',
            'accent-color': '#FBBF24'       # Light yellow accent!
        }
        test_markdown = """
## Pathological Visibility Stress Test
This text must be readable and never render as invisible white-on-white.

| Header A | Header B |
| Value 1 | Value 2 |

> Key Concept: Contrast must satisfy WCAG AA minimum 4.5:1.
"""
        # Test PDF generator with pathological white-on-white theme
        pdf_buf = create_pdf_reportlab('Visibility Test', test_markdown, bad_theme, {'intro_slide': 'false', 'theme_base': 'light'})
        assert pdf_buf is not None
        assert len(pdf_buf.getvalue()) > 3000

        # Test PPTX generator with pathological white-on-white theme
        slides_data = [
            {'slide_type': 'intro', 'title': 'Contrast Stress Test', 'points': []},
            {'slide_type': 'content', 'title': 'Accessible Visibility', 'points': ['Point 1: High contrast', 'Point 2: Crisp visibility'], 'image_query': 'none'}
        ]
        pptx_buf = create_pptx_file(slides_data, bad_theme, {'theme_base': 'light', 'image_strategy': 'none'})
        assert pptx_buf is not None
        assert len(pptx_buf.getvalue()) > 1000




