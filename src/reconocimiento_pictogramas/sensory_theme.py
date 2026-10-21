"""Tokens de Pictovoz: tonos desaturados, contraste medido y estados predecibles.

El fondo cálido y el uso acotado del acento buscan reducir deslumbramiento y
fatiga sensorial. Son decisiones de diseño, no un efecto clínico demostrado:
las preferencias sensoriales varían y deben validarse con cada usuario.
"""
from html import escape
import gradio as gr

DESIGN_TOKENS = {
    "colors": {
    "primary": "#3E6B89",
    "secondary": "#A3C9A8",
    "background": "#F7F5EE",
    "surface": "#FFFFFF",
    "text": "#2B2D42",
    "accent": "#E9B44C",
    "error": "#C86D61",
    "success": "#6FA287",
    },
    "typography": {
        "family": "Verdana, Arial, sans-serif", "body": "1.125rem",
        "h1": "2.25rem", "h2": "1.5rem", "h3": "1.25rem",
        "note": "1rem", "line-height": "1.6",
    },
    "spacing": {"xs": "0.5rem", "sm": "0.75rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem"},
    "radii": {"sm": "8px", "lg": "16px", "pill": "999px"},
    "interaction": {"target": "48px", "focus-width": "3px", "focus-offset": "3px", "duration": "0ms"},
    "button_roles": {
        "primary": {"background": "primary", "foreground": "surface"},
        "secondary": {"background": "secondary", "foreground": "text"},
        "accent": {"background": "accent", "foreground": "text"},
    },
}
# Alias público conservado para la app existente y sus pruebas.
TOKENS = DESIGN_TOKENS["colors"]


def contrast_ratio(foreground: str, background: str) -> float:
    """Ratio WCAG 2.1 calculado con luminancia relativa sRGB, sin redondear."""
    def luminance(hex_color):
        values = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _tint(color, amount=0.15):
    """Aclara el rojo sobre blanco para admitir texto carbón de tamaño normal."""
    channels = [round(int(color[index:index + 2], 16) * amount + 255 * (1 - amount)) for index in (1, 3, 5)]
    return "#" + "".join(f"{value:02X}" for value in channels)


ERROR_SURFACE = _tint(TOKENS["error"])
# El rojo original no admite texto carbón ni blanco a 4,5:1. Se conserva para
# el borde de alerta; el mensaje usa una superficie aclarada y texto carbón.
TEXT_PAIRS = {
    "texto sobre fondo": (TOKENS["text"], TOKENS["background"]),
    "texto sobre tarjeta": (TOKENS["text"], TOKENS["surface"]),
    "texto sobre menta": (TOKENS["text"], TOKENS["secondary"]),
    "texto sobre acento": (TOKENS["text"], TOKENS["accent"]),
    "texto sobre éxito": (TOKENS["text"], TOKENS["success"]),
    "texto de error": (TOKENS["text"], ERROR_SURFACE),
    "texto blanco sobre azul": (TOKENS["surface"], TOKENS["primary"]),
    "enlace sobre fondo": (TOKENS["primary"], TOKENS["background"]),
    "enlace sobre tarjeta": (TOKENS["primary"], TOKENS["surface"]),
}


def create_theme(*, primary_action="accent"):
    """Tema Soft con overrides explícitos también para el modo oscuro.

    Se conserva la paleta solicitada en ambos modos para evitar inversiones
    inesperadas. No se promete adecuación sensorial universal de este modo.
    """
    t = TOKENS
    if primary_action not in {"primary", "accent"}:
        raise ValueError("El rol principal debe ser primary o accent.")
    role = DESIGN_TOKENS["button_roles"][primary_action]
    action_background, action_text = t[role["background"]], t[role["foreground"]]
    values = {
        "body_background_fill": t["background"],
        "body_text_color": t["text"],
        "body_text_color_subdued": t["text"],
        "background_fill_primary": t["surface"],
        "background_fill_secondary": t["background"],
        "block_background_fill": t["surface"],
        "block_label_background_fill": t["surface"],
        "block_label_text_color": t["text"],
        "block_title_text_color": t["text"],
        "input_background_fill": t["surface"],
        "input_border_color": t["primary"],
        "input_border_color_focus": t["primary"],
        "input_placeholder_color": t["text"],
        "border_color_primary": t["primary"],
        "border_color_accent": t["primary"],
        "color_accent": t["primary"],
        "color_accent_soft": t["secondary"],
        # Primary azul/blanco: 5,72:1. Accent mostaza/carbón: 7,13:1.
        # La app conserva por defecto su llamada a la acción mostaza.
        # Hover estable: no hay destellos ni cambios bruscos de luminosidad.
        "button_primary_background_fill": action_background,
        "button_primary_background_fill_hover": action_background,
        "button_primary_text_color": action_text,
        "button_primary_border_color": t["primary"],
        "button_primary_border_color_hover": t["primary"],
        "button_secondary_background_fill": t["secondary"],
        "button_secondary_background_fill_hover": t["secondary"],
        "button_secondary_text_color": t["text"],
        "button_secondary_border_color": t["primary"],
        "error_background_fill": ERROR_SURFACE,
        "error_border_color": t["error"],
        "error_text_color": t["text"],
        "slider_color": t["primary"],
        "block_info_text_color": t["text"],
        "checkbox_label_text_color": t["text"],
        "checkbox_label_text_color_selected": t["text"],
        "checkbox_label_background_fill": t["surface"],
        "checkbox_label_background_fill_hover": t["surface"],
        "checkbox_label_background_fill_selected": t["secondary"],
        "checkbox_background_color": t["surface"],
        "checkbox_background_color_hover": t["surface"],
        "checkbox_background_color_selected": t["primary"],
        "checkbox_border_color": t["primary"],
        "checkbox_border_color_hover": t["primary"],
        "checkbox_border_color_selected": t["primary"],
    }
    # color_accent es compartido por ambos modos; no existe color_accent_dark.
    overrides = {**values, **{f"{name}_dark": value for name, value in values.items() if name != "color_accent"}}
    return gr.themes.Soft(
        font=["Verdana", "Arial", "sans-serif"], font_mono=["Consolas", "monospace"],
    ).set(**overrides, block_radius=DESIGN_TOKENS["radii"]["lg"], button_large_radius=DESIGN_TOKENS["radii"]["lg"])


TOKEN_CSS = ".gradio-container {" + "".join(f"--pv-{name}:{value};" for name, value in TOKENS.items()) + f"--pv-error-surface:{ERROR_SURFACE};" + "}" + """
.gradio-container {background:var(--pv-background)!important; color:var(--pv-text)!important; font-family:Verdana,Arial,sans-serif;}
.gradio-container .prose,.gradio-container :is(input,textarea,label) {color:var(--pv-text)!important;}
.gradio-container :is(input,textarea,button,select) {font-family:inherit; font-size:1.125rem; line-height:1.6;}
.gradio-container button {min-height:48px; border-width:2px; white-space:normal; transition:none!important;}
.gradio-container :is(input,textarea,select,a,button,[tabindex]):focus-visible {outline:3px solid var(--pv-primary)!important; outline-offset:3px; box-shadow:0 0 0 3px var(--pv-surface)!important;}
.gradio-container a {color:var(--pv-primary); text-decoration:underline;}
.tea-state {padding:16px; border-radius:12px; color:var(--pv-text); background:var(--pv-background); line-height:1.6;}
.tea-state.success {background:var(--pv-success);}
.tea-state.error {background:var(--pv-error-surface); border-left:4px solid var(--pv-error);}
"""


def state_message(message, kind="ready"):
    # El significado del estado también se comunica con palabras, no solo color.
    css_class = kind if kind in {"ready", "success", "error"} else "ready"
    return f'<div class="tea-state {css_class}" role="status" aria-live="polite">{escape(message)}</div>'
