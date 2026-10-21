"""Verifica el contraste del texto configurado y los estados del ejemplo."""
import runpy
from pathlib import Path
import pytest
from reconocimiento_pictogramas.sensory_theme import TOKENS, TEXT_PAIRS, contrast_ratio, create_theme, state_message


@pytest.mark.parametrize("name", TEXT_PAIRS)
def test_text_pairs_meet_wcag_aa(name):
    assert contrast_ratio(*TEXT_PAIRS[name]) >= 4.5, name


def test_original_error_is_not_used_as_a_text_background():
    assert contrast_ratio(TOKENS["text"], TOKENS["error"]) < 4.5
    assert contrast_ratio(TOKENS["surface"], TOKENS["error"]) < 4.5
    assert (TOKENS["text"], TOKENS["error"]) not in TEXT_PAIRS.values()


def test_theme_retains_warm_background_and_requested_palette():
    theme = create_theme()
    assert theme.body_background_fill == "#F7F5EE"
    assert theme.body_background_fill_dark == "#F7F5EE"
    assert theme.button_primary_background_fill == "#E9B44C"
    assert theme.button_primary_text_color == "#2B2D42"


def test_example_builds_and_escapes_output():
    script = Path(__file__).resolve().parents[1] / "scripts/demo_tema_tea.py"
    module = runpy.run_path(str(script))
    assert module["build_demo"]().config["title"].startswith("Pictovoz")
    assert "Falta el texto" in module["mostrar_resultado"]("", "Agua")
    output = module["mostrar_resultado"]("<script>", "Agua")
    assert "<script>" not in output and "&lt;script&gt;" in output
    assert 'role="status"' in state_message("Listo", "success")
