"""Interfaz local para el piloto de reconocimiento de pictogramas."""
from __future__ import annotations

import json
import argparse
import os
import logging
from html import escape
from pathlib import Path

import gradio as gr
from PIL import Image
from .preprocessing import prepare_image as preprocess_image
from .inference import classify_image, classify_frame
from .live import process_live_frame, analyze_camera
from .accessible_theme import ACCESSIBLE_CSS, accessible_theme
from .speech import synthesize_phrase, AudioGenerationError

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))
READY = "Cargá una imagen JPEG o PNG para comenzar."
PENDING = "Imagen preparada. Presioná Reconocer pictograma."


def selected_image_size() -> tuple[int,int]:
    selected=json.loads((ROOT/"config/application.json").read_text(encoding="utf-8"))
    size=selected.get("image_size")
    if not isinstance(size,list) or len(size)!=2 or any(type(v) is not int or v<1 for v in size):
        raise ValueError("Tamaño de imagen del modelo inválido.")
    return tuple(size)


def prepare_image(path: str | None) -> Image.Image:
    if not path:
        raise ValueError("Seleccioná una imagen JPEG o PNG.")
    size = selected_image_size()
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


def result_announcement(status: str, category: str) -> str:
    """Estado textual accesible, independiente del color y con HTML escapado."""
    category_text = "" if category == "—" else f"{category}. "
    return escape(category_text + status)


UNRECOGNIZED = "Tarjeta no reconocida. Intenta enfocarla nuevamente."
PHRASES = json.loads((ROOT / "config/communication.json").read_text(encoding="utf-8"))
NAMES = {item["id"]: item["display_name"] for item in CONFIG["classes"]}
GRADIO_MAJOR = int(gr.__version__.split(".")[0])


def status_card(text: str, kind: str = "ready") -> str:
    """El estado se expresa con palabras y se anuncia sin depender del color."""
    return (
        f'<div class="result-status {kind}" role="status" aria-live="polite" '
        f'aria-atomic="true">{escape(text)}</div>'
    )


def _identify(image: Image.Image | None):
    """Adapta la inferencia existente; no cambia su preprocesamiento ni rechazo."""
    if image is None:
        return "Seleccioná o capturá una imagen para continuar.", {}, None, status_card("Falta una imagen.", "error")
    try:
        # classify_frame utiliza exactamente el preprocesamiento y el detector
        # del modelo seleccionado. No se añade un umbral softmax arbitrario.
        result = classify_frame(image)
        phrase = UNRECOGNIZED if result["rejected"] else PHRASES[result["label"]]
        scores = {NAMES[key]: float(value) for key, value in result["probabilities"].items()}
    except (ValueError, OSError, RuntimeError) as error:
        logger.warning("No se pudo identificar la imagen: %s", error)
        return "No se pudo analizar la imagen. Probá con otra foto.", {}, None, status_card("No se pudo completar el reconocimiento. El resultado anterior se ha limpiado.", "error")
    if result["rejected"]:
        state = "Tarjeta no reconocida por el criterio de rechazo del modelo. Intentá mejorar el enfoque y la iluminación."
        kind = "rejected"
    else:
        state = "Tarjeta identificada. Podés escuchar o volver a reproducir la frase."
        kind = "accepted"
    try:
        audio_path = synthesize_phrase(phrase)
    except AudioGenerationError:
        audio_path = None
        state += " La voz no está disponible en este momento. Revisá la conexión a Internet."
    return phrase, scores, audio_path, status_card(state, kind)


def predecir(imagen: Image.Image | None) -> tuple[str, dict[str, float], str | None]:
    """Contrato público: frase, probabilidades por categoría y ruta del MP3.

    Si no hay imagen o falla la inferencia se limpian puntuaciones y audio.
    Si solo falla gTTS se preservan frase y puntuaciones, con audio None.
    """
    phrase, scores, audio_path, _ = _identify(imagen)
    return phrase, scores, audio_path


def reset_result():
    return "", {}, None, status_card("Cuando tengas la imagen lista, presioná Identificar Pictograma.")


def reset_for_session(session):
    """Invalida predicciones y locuciones pendientes solo de esta sesión."""
    session["revision"] += 1
    return reset_result()


def identify_current(image, session):
    revision = session["revision"]
    result = _identify(image)
    # Si el usuario limpió o cambió la imagen durante la inferencia/TTS,
    # se descarta la respuesta antigua en lugar de volver a mostrarla.
    if revision != session["revision"]:
        return (gr.skip(),) * 4
    return result


def clear_session(session):
    return None, None, *reset_for_session(session)


APP_HEAD = '<meta name="google" content="notranslate">'
SPANISH_UI_JS = """() => {
    document.documentElement.lang = "es";
    document.documentElement.setAttribute("translate", "no");
    document.documentElement.classList.add("notranslate");
}"""


def rear_camera_options():
    """Prefiere la trasera sin impedir usar equipos que solo tienen frontal."""
    # Gradio pasa constraints.video a getUserMedia. Un facingMode en la raíz
    # se ignora en su frontend y termina abriendo la cámara predeterminada.
    constraints = {"video": {"facingMode": {"ideal": "environment"}}}
    if GRADIO_MAJOR >= 6:
        return {"webcam_options": gr.WebcamOptions(mirror=False, constraints=constraints)}
    return {"mirror_webcam": False, "webcam_constraints": constraints}


def model_evaluation_notice() -> str:
    """Consulta el estado del modelo activo; no usa una copia histórica fija."""
    selected = json.loads((ROOT / "config/application.json").read_text(encoding="utf-8"))
    if selected.get("test_evaluated") is True:
        return "La evaluación final del modelo ya se realizó. El modelo puede equivocarse."
    return "El modelo puede equivocarse; su evaluación final sigue pendiente."


def build_app() -> gr.Blocks:
    """Flujo secuencial de ancho completo, apto para móvil y escritorio.

    En Gradio 5 el tema y CSS pertenecen a Blocks. Gradio 6 los recibe en
    launch; se conserva el entorno instalado sin rebajar sus dependencias.
    """
    blocks_options = {}
    if GRADIO_MAJOR < 6:
        blocks_options.update(theme=accessible_theme(), css=ACCESSIBLE_CSS, head=APP_HEAD)
    with gr.Blocks(title="Pictovoz · Identificación asistiva", **blocks_options) as app:
        gr.HTML(
            '<header id="welcome-card"><span class="status-badge">Modelo entrenado · versión experimental</span>'
            '<h1>Pictovoz</h1><p>Mostrá un pictograma y transformalo en una frase para comunicarte.</p>'
            f'<p>Elegí una foto o usá la cámara. {escape(model_evaluation_notice())}</p></header>'
        )
        with gr.Accordion("Categorías y detalles del modelo", open=False):
            gr.Markdown("**Categorías disponibles:** " + ", ".join(NAMES.values()) + ".")
            gr.Markdown("Las barras muestran las opciones que propone el modelo. La app también comprueba si la imagen se parece a los pictogramas conocidos antes de aceptar el resultado.")
        with gr.Column(elem_classes=["pictovoz-section"]):
            gr.Markdown("## 1. Elegí cómo mostrar el pictograma")
            with gr.Tabs():
                with gr.Tab("Subir Foto"):
                    upload = gr.Image(
                        type="pil", sources=["upload"], image_mode=None,
                        label="Foto del pictograma", height=320,
                    )
                    identify_upload = gr.Button("Identificar Pictograma", variant="primary", elem_id="recognize-upload")
                with gr.Tab("Cámara en Vivo"):
                    gr.Markdown("Se solicita la cámara trasera si está disponible. Permití el acceso, capturá una imagen y presioná **Identificar Pictograma**. Desde el celular necesitás HTTPS.")
                    camera = gr.Image(
                        type="pil", sources=["webcam"], image_mode=None,
                        label="Captura de cámara", height=320, **rear_camera_options(),
                    )
                    identify_camera = gr.Button("Identificar Pictograma", variant="primary", elem_id="recognize-camera")
        with gr.Column(elem_id="result-card"):
            gr.Markdown("## 2. Tu frase para comunicarte")
            phrase = gr.Textbox(
                label="Frase Comunicativa", value="", placeholder="Tu frase aparecerá acá",
                interactive=False, lines=2, elem_id="communication-phrase",
            )
            state = gr.HTML(status_card("Cargá una foto o capturá una imagen para comenzar."))
            audio = gr.Audio(type="filepath", autoplay=True, label="Locución de Voz", interactive=False)
            gr.Markdown("La voz se reproduce al identificar. Si el navegador no la inicia, tocá el botón de reproducción. gTTS necesita Internet y recibe solo la frase a pronunciar.")
            scores = gr.Label(label="Puntuaciones por categoría · no son certeza de acierto", num_top_classes=3, elem_id="class-scores")
            with gr.Accordion("Cómo interpretar las puntuaciones", open=False):
                gr.Markdown("Una puntuación alta puede acompañar una tarjeta rechazada. La decisión conserva el detector de similitud calibrado del modelo.")
            clear = gr.Button("Limpiar imagen y resultado", variant="secondary")

        session = gr.State(value=lambda: {"revision": 0})
        outputs = [phrase, scores, audio, state]
        # Se limpian los resultados al cambiar la imagen o antes de identificar.
        # Así un error o una nueva captura no conservan una locución anterior.
        for image, button in ((upload, identify_upload), (camera, identify_camera)):
            image.change(reset_for_session, inputs=session, outputs=outputs, queue=False)
            button.click(reset_for_session, inputs=session, outputs=outputs, queue=False).then(
                identify_current, inputs=[image, session], outputs=outputs,
                concurrency_limit=1, concurrency_id="pictogram_model",
            )
        clear.click(
            clear_session, inputs=session,
            outputs=[upload, camera, *outputs], queue=False,
        )
        gr.Markdown("**Consejo:** usá una sola tarjeta por imagen, con buena luz y sin tapar el dibujo.")
        # Español explícito y no traducible: «Comer» es una categoría, no una palabra inglesa.
        app.load(fn=None, js=SPANISH_UI_JS, queue=False)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Pictovoz: foto, cámara y voz.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--ssl-certfile")
    parser.add_argument("--ssl-keyfile")
    parser.add_argument("--share", action="store_true", help="Crear enlace HTTPS temporal protegido con contraseña.")
    parser.add_argument("--auth-user", default="pictogramas")
    args = parser.parse_args()
    if bool(args.ssl_certfile) != bool(args.ssl_keyfile):
        parser.error("Se requieren certificado y clave juntos.")
    auth = None
    if args.share:
        password = os.environ.get("PICTOGRAMAS_PASSWORD")
        if not password:
            parser.error("Definí PICTOGRAMAS_PASSWORD antes de crear el enlace externo.")
        auth = (args.auth_user, password)
    launch_options = {}
    if GRADIO_MAJOR >= 6:
        launch_options.update(theme=accessible_theme(), css=ACCESSIBLE_CSS, head=APP_HEAD)
    build_app().launch(
        server_name=args.host, server_port=args.port, share=args.share, auth=auth,
        ssl_certfile=args.ssl_certfile, ssl_keyfile=args.ssl_keyfile, **launch_options,
    )


if __name__ == "__main__":
    main()
