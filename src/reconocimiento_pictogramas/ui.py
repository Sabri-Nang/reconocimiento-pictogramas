"""Interfaz local para el piloto de reconocimiento de pictogramas."""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))
READY = "Cargá una imagen JPEG o PNG para comenzar."
PENDING = "Imagen preparada. El reconocimiento estará disponible cuando se integre el modelo entrenado."


def prepare_image(path: str | None) -> Image.Image:
    if not path:
        raise ValueError("Seleccioná una imagen JPEG o PNG.")
    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Solo se admiten imágenes JPEG y PNG.")
            image.load()
            size = (CONFIG["image"]["width"], CONFIG["image"]["height"])
            return ImageOps.exif_transpose(image).convert("RGB").resize(
                size, Image.Resampling.LANCZOS
            )
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ValueError("No se pudo leer la imagen. Probá con otro archivo.") from error


def load_image(path):
    if path is None:
        return None, READY, "—", "—"
    try:
        return prepare_image(path), PENDING, "Pendiente de modelo", "—"
    except ValueError as error:
        return None, str(error), "—", "—"


def build_app() -> gr.Blocks:
    names = ", ".join(item["display_name"] for item in CONFIG["classes"])
    with gr.Blocks(title="Reconocimiento de pictogramas") as app:
        gr.Markdown("# Reconocimiento de pictogramas\nCargá una imagen para preparar su reconocimiento.")
        gr.Markdown(f"**Piloto de cinco clases:** {names}.")
        gr.Markdown("**En desarrollo:** todavía no hay un modelo entrenado integrado ni un umbral calibrado.")
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
                gr.Button("Reconocer pictograma · pendiente de modelo", interactive=False)
        upload.change(load_image, inputs=upload, outputs=[preview, status, category, confidence])
        clear.click(lambda: (None, None, READY, "—", "—"), outputs=[upload, preview, status, category, confidence])
    return app


def main() -> None:
    build_app().launch(server_name="127.0.0.1", server_port=7860, share=False)


if __name__ == "__main__":
    main()
