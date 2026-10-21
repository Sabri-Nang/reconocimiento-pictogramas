"""Regresiones de contraste, validación amable y construcción de la guía."""
import pytest
from reconocimiento_pictogramas.sensory_theme import DESIGN_TOKENS, TOKENS, contrast_ratio, create_theme
from reconocimiento_pictogramas.design_system import build_showcase, show_result


@pytest.mark.parametrize("role", ["primary", "secondary", "accent"])
def test_button_roles_have_accessible_text_contrast(role):
    colors = DESIGN_TOKENS["button_roles"][role]
    assert contrast_ratio(TOKENS[colors["foreground"]], TOKENS[colors["background"]]) >= 4.5


def test_primary_and_accent_theme_preserve_their_roles():
    primary = create_theme(primary_action="primary")
    assert primary.button_primary_background_fill == TOKENS["primary"]
    assert primary.button_primary_text_color == TOKENS["surface"]
    assert primary.button_primary_background_fill_hover == primary.button_primary_background_fill
    # La llamada a la acción de la app existente conserva mostaza y carbón.
    accent = create_theme()
    assert accent.button_primary_background_fill == TOKENS["accent"]
    assert accent.button_primary_text_color == TOKENS["text"]


@pytest.mark.parametrize("text,activity,expected", [("", "Jugar", "Falta tu texto"), ("   ", "Leer", "Falta tu texto"), ("agua", None, "Falta elegir una actividad")])
def test_required_fields_have_actionable_errors(text, activity, expected):
    output = show_result(text, activity, [])
    assert expected in output and 'role="status"' in output


def test_result_escapes_input_and_handles_optional_supports():
    result = show_result("<script>", "Leer", [])
    assert "<script>" not in result and "&lt;script&gt;" in result
    assert "sin apoyos adicionales" in result
    assert "Éxito" in result


def test_showcase_contains_requested_components_and_disabled_example():
    config = build_showcase().config
    types = {item["type"] for item in config["components"]}
    assert {"textbox", "radio", "checkboxgroup", "button", "html"} <= types
    assert any(item["type"] == "button" and item["props"].get("interactive") is False for item in config["components"])
