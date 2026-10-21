"""Ejemplo ejecutable: uv run python scripts/demo_tema_tea.py.

No carga el clasificador ni genera audio: demuestra solo el sistema de diseño.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import gradio as gr
from reconocimiento_pictogramas.sensory_theme import create_theme, TOKEN_CSS, state_message


def mostrar_resultado(texto, opcion):
    if not texto or not texto.strip():
        return state_message("Falta el texto. Escribí una palabra para continuar.", "error")
    return state_message(f"Listo. Elegiste {opcion}. Tu texto es: {texto.strip()}", "success")


def build_demo():
    major = int(gr.__version__.split(".")[0])
    options = {"theme": create_theme(), "css": TOKEN_CSS} if major < 6 else {}
    with gr.Blocks(title="Pictovoz · Paleta serena", **options) as demo:
        gr.Markdown("# Pictovoz\nEscribí, elegí una opción y presioná Continuar.")
        texto = gr.Textbox(label="Tu texto", placeholder="Por ejemplo: agua")
        opcion = gr.Dropdown(["Agua", "Comer", "Ayuda"], value="Agua", label="Opción", allow_custom_value=False)
        boton = gr.Button("Continuar", variant="primary")
        resultado = gr.HTML(state_message("Esperando tu elección."))
        boton.click(mostrar_resultado, inputs=[texto, opcion], outputs=resultado)
    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7864)
    args = parser.parse_args()
    options = {"theme": create_theme(), "css": TOKEN_CSS} if int(gr.__version__.split(".")[0]) >= 6 else {}
    build_demo().launch(server_name="127.0.0.1", server_port=args.port, share=False, **options)
