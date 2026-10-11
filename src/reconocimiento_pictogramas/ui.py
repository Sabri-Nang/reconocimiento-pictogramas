"""Interfaz local para el piloto de reconocimiento de pictogramas."""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
from PIL import Image
from .preprocessing import prepare_image as preprocess_image
from .inference import classify_image

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))
READY = "Cargá una imagen JPEG o PNG para comenzar."
PENDING = "Imagen preparada. Presioná Reconocer pictograma."


def prepare_image(path: str | None) -> Image.Image:
    if not path:
        raise ValueError("Seleccioná una imagen JPEG o PNG.")
    size = (CONFIG["image"]["width"], CONFIG["image"]["height"])
    return preprocess_image(path, size)


def load_image(path):
    if path is None:
        return None, READY, "—", "—"
    try:
        return prepare_image(path), PENDING, "—", "—"
    except ValueError as error:
        return None, str(error), "—", "—"


def recognize_image(path):
    if not path:
        return None, "Seleccioná una imagen JPEG o PNG.", "—", "—"
    try:
        result=classify_image(path)
        names={c['id']:c['display_name'] for c in CONFIG['classes']}
        label="Pictograma no reconocido" if result['rejected'] else names[result['label']]
        status="Predicción del piloto. Umbral de rechazo pendiente de calibración." if not result['threshold_calibrated'] else "Pictograma no reconocido" if result['rejected'] else "Pictograma reconocido."
        return result['image'],status,label,f"{result['confidence']:.1%}"
    except (ValueError,OSError) as error:
        return None,str(error),"—","—"


def build_app() -> gr.Blocks:
    names = ", ".join(item["display_name"] for item in CONFIG["classes"])
    with gr.Blocks(title="Reconocimiento de pictogramas") as app:
        gr.Markdown("# Reconocimiento de pictogramas\nCargá una imagen para preparar su reconocimiento.")
        gr.Markdown(f"**Piloto de cinco clases:** {names}.")
        gr.Markdown("**Piloto experimental:** modelo entrenado. El rechazo de desconocidos requiere calibrar el umbral; la confianza mostrada es la probabilidad del modelo.")
        with gr.Row():
            with gr.Column():
                upload = gr.File(label="Imagen del pictograma", file_types=[".jpg", ".jpeg", ".png"], type="filepath")
                preview = gr.Image(label="Vista previa · RGB 128 × 128", interactive=False)
                clear = gr.Button("Limpiar")
            with gr.Column():
                gr.Markdown("### Resultado")
                category = gr.Textbox(label="Categoría", value="—", interactive=False)
                confidence = gr.Textbox(label="Confianza", value="—", interactive=False)
                status = gr.Textbox(label="Estado", value=READY, interactive=False, lines=3)
                recognize = gr.Button("Reconocer pictograma")
        recognize.click(recognize_image, inputs=upload, outputs=[preview, status, category, confidence])
        upload.change(load_image, inputs=upload, outputs=[preview, status, category, confidence])
        clear.click(lambda: (None, None, READY, "—", "—"), outputs=[upload, preview, status, category, confidence])
    return app


def main() -> None:
    build_app().launch(server_name="127.0.0.1", server_port=7860, share=False)


if __name__ == "__main__":
    main()
