"""Interfaz local para el piloto de reconocimiento de pictogramas."""
from __future__ import annotations

import json
import argparse
import os
from pathlib import Path

import gradio as gr
from PIL import Image
from .preprocessing import prepare_image as preprocess_image
from .inference import classify_image
from .live import process_live_frame, analyze_camera
from .camera_widget import HTML as CAMERA_HTML, CSS as CAMERA_CSS, JS as CAMERA_JS

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
        return None, READY, "—", "—", "—"
    try:
        return prepare_image(path), PENDING, "—", "—", "—"
    except ValueError as error:
        return None, str(error), "—", "—", "—"


def recognize_image(path):
    if not path:
        return None, "Seleccioná una imagen JPEG o PNG.", "—", "—", "—"
    try:
        result=classify_image(path)
        names={c['id']:c['display_name'] for c in CONFIG['classes']}
        label="Pictograma no reconocido" if result['rejected'] else names[result['label']]
        status="Predicción del piloto. Umbral de rechazo pendiente de calibración." if not result['threshold_calibrated'] else "Pictograma no reconocido" if result['rejected'] else "Pictograma reconocido."
        similarity="—"
        if result.get('rejection_method')=='knn_cosine':
            similarity=f"{result['rejection_score']:.4f} · mínimo para aceptar: mayor que {result['rejection_threshold']:.4f}"
            status="Pictograma no reconocido: similitud insuficiente." if result['rejected'] else "Pictograma reconocido por MobileNet."
        return result['image'],status,label,f"{result['confidence']:.1%}",similarity
    except (ValueError,OSError) as error:
        return None,str(error),"—","—","—"


def recognize_live(frame,state):
    names={c['id']:c['display_name'] for c in CONFIG['classes']}
    return process_live_frame(frame,state,names)


def build_app() -> gr.Blocks:
    names = ", ".join(item["display_name"] for item in CONFIG["classes"])
    with gr.Blocks(title="Reconocimiento de pictogramas") as app:
        gr.Markdown("# Reconocimiento de pictogramas\nCargá una imagen para preparar su reconocimiento.")
        with gr.Accordion("Información del modelo",open=False):
            gr.Markdown(f"**Clases configuradas:** {names}.")
            gr.Markdown("**Versión experimental:** MobileNet reconoce diez pictogramas y comprueba su similitud con ejemplos conocidos. La puntuación de clase y la similitud son distintas. Evaluación final pendiente.")
        with gr.Tabs():
            with gr.Tab("Foto"):
                with gr.Row():
                    with gr.Column():
                        upload = gr.File(label="Imagen del pictograma", file_types=[".jpg", ".jpeg", ".png"], type="filepath")
                        preview = gr.Image(label="Vista previa · RGB 128 × 128", interactive=False)
                        clear = gr.Button("Limpiar")
                    with gr.Column():
                        gr.Markdown("### Resultado")
                        category = gr.Textbox(label="Categoría", value="—", interactive=False)
                        confidence = gr.Textbox(label="Puntuación de la clase", value="—", interactive=False)
                        similarity = gr.Textbox(label="Similitud con pictogramas conocidos · no es probabilidad", value="—", interactive=False)
                        status = gr.Textbox(label="Estado", value=READY, interactive=False, lines=3)
                        recognize = gr.Button("Reconocer pictograma")
                recognize.click(recognize_image, inputs=upload, outputs=[preview, status, category, confidence, similarity],concurrency_limit=1,concurrency_id="pictogram_model")
                upload.change(load_image, inputs=upload, outputs=[preview, status, category, confidence, similarity])
                clear.click(lambda: (None, None, READY, "—", "—", "—"), outputs=[upload, preview, status, category, confidence, similarity])
            with gr.Tab("Cámara en vivo"):
                gr.Markdown("Tocá **Iniciar cámara** y mostrale una tarjeta a la cámara trasera. La palabra aparece sobre el video al confirmar tres imágenes seguidas.")
                gr.HTML(CAMERA_HTML,css_template=CAMERA_CSS,js_on_load=CAMERA_JS,server_functions=[analyze_camera],elem_id='live-camera')
    return app


def main() -> None:
    parser=argparse.ArgumentParser(description='Reconocimiento local de pictogramas con foto y cámara.')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=7860)
    parser.add_argument('--ssl-certfile');parser.add_argument('--ssl-keyfile')
    parser.add_argument('--share',action='store_true',help='Crear enlace HTTPS temporal externo de Gradio; requiere contraseña.')
    parser.add_argument('--auth-user',default='pictogramas')
    args=parser.parse_args()
    if bool(args.ssl_certfile)!=bool(args.ssl_keyfile):parser.error('Se requieren certificado y clave juntos.')
    auth=None
    if args.share:
        password=os.environ.get('PICTOGRAMAS_PASSWORD')
        if not password:parser.error('Definí PICTOGRAMAS_PASSWORD antes de crear el enlace HTTPS externo.')
        auth=(args.auth_user,password)
    build_app().launch(server_name=args.host,server_port=args.port,share=args.share,auth=auth,
        ssl_certfile=args.ssl_certfile,ssl_keyfile=args.ssl_keyfile)


if __name__ == "__main__":
    main()
