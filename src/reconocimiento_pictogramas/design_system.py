"""Guía funcional del sistema de diseño de Pictovoz.

Ejecutar: uv run python -m reconocimiento_pictogramas.design_system
No carga el modelo, no activa cámara y no reproduce sonidos de forma inesperada.
"""
import argparse
from html import escape
import gradio as gr

from .sensory_theme import (
    DESIGN_TOKENS, TOKENS, TOKEN_CSS, contrast_ratio, create_theme, state_message,
)


def _css_variables():
    declarations = []
    for group in ("typography", "spacing", "radii", "interaction"):
        for name, value in DESIGN_TOKENS[group].items():
            declarations.append(f"--ds-{group}-{name}:{value};")
    return "#design-system-showcase {" + "".join(declarations) + "}"


SHOWCASE_CSS = TOKEN_CSS + _css_variables() + """
.gradio-container {width:100%!important; max-width:1000px!important; box-sizing:border-box; margin:auto!important; padding:clamp(12px,3vw,24px)!important;}
.gradio-container .main {padding:0!important;}
#design-system-showcase {gap:var(--ds-spacing-lg); color:var(--pv-text);}
#design-system-showcase :is(.column,.row,.block) {min-width:0!important; box-sizing:border-box;}
#design-system-showcase :is(p,label,input,textarea,button,.prose) {font-family:var(--ds-typography-family)!important; font-size:var(--ds-typography-body)!important; line-height:var(--ds-typography-line-height)!important;}
#design-system-showcase :is(h1,h2,h3,p,button,label,span) {word-break:normal!important; overflow-wrap:normal!important; hyphens:none!important;}
#design-system-showcase h1 {font-size:var(--ds-typography-h1)!important; line-height:1.25!important; margin:0 0 var(--ds-spacing-md);}
#design-system-showcase h2 {font-size:var(--ds-typography-h2)!important; line-height:1.35!important; margin:0 0 var(--ds-spacing-md);}
#design-system-showcase h3 {font-size:var(--ds-typography-h3)!important; line-height:1.4!important;}
#design-system-showcase .ds-note {font-size:var(--ds-typography-note)!important; color:var(--pv-text); max-width:65ch;}
#design-system-showcase .ds-card {background:var(--pv-surface); border:1px solid var(--pv-primary); border-radius:var(--ds-radii-lg); padding:var(--ds-spacing-lg); box-shadow:none;}
#design-system-showcase .ds-welcome {background:var(--pv-secondary); border:0;}
#design-system-showcase :is(button,label,input,textarea,.ds-card) {transition:none!important; animation:none!important; transform:none!important;}
#design-system-showcase button {min-height:var(--ds-interaction-target); border:2px solid var(--pv-primary)!important; border-radius:var(--ds-radii-lg); white-space:normal!important;}
#design-system-showcase button.primary:is(:hover,:active) {background:var(--pv-primary)!important; color:var(--pv-surface)!important; filter:none!important;}
#design-system-showcase button.secondary:not(.ds-accent):is(:hover,:active) {background:var(--pv-secondary)!important; color:var(--pv-text)!important; filter:none!important;}
#design-system-showcase .ds-accent,#design-system-showcase .ds-accent:is(:hover,:active) {background:var(--pv-accent)!important; color:var(--pv-text)!important;}
#design-system-showcase button:disabled {background:var(--pv-background)!important; color:var(--pv-text)!important; opacity:1!important; cursor:not-allowed;}
#design-system-showcase .ds-options label {min-height:var(--ds-interaction-target); padding:var(--ds-spacing-sm); gap:var(--ds-spacing-sm); border:2px solid var(--pv-primary); border-radius:var(--ds-radii-sm);}
#design-system-showcase .ds-options label:is(:hover,:active) {background:var(--pv-surface);}
#design-system-showcase .ds-options label:has(input:checked) {background:var(--pv-secondary); color:var(--pv-text);}
#design-system-showcase .ds-options input {accent-color:var(--pv-primary);}
#design-system-showcase .ds-options :is(.wrap,[role=radiogroup]) {gap:var(--ds-spacing-md);}
#design-system-showcase :is(input,textarea)::placeholder {opacity:1; color:var(--pv-text);}
#design-system-showcase .ds-swatches {list-style:none; padding:0; display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:var(--ds-spacing-md);}
#design-system-showcase .ds-swatch {height:32px; border:1px solid var(--pv-primary); border-radius:var(--ds-radii-sm); margin-bottom:var(--ds-spacing-xs);}
#design-system-showcase .ds-warning {background:var(--pv-accent); color:var(--pv-text);}
#design-system-showcase .gr-accordion {overflow:visible!important;}
#design-system-showcase .gr-accordion .label-wrap {height:auto; min-height:var(--ds-interaction-target); margin:0!important; width:100%; box-sizing:border-box; gap:var(--ds-spacing-sm);}
#design-system-showcase .gr-accordion .label-wrap span:not(.icon) {flex:1; min-width:0; white-space:normal;}
@media(max-width:640px) {#design-system-showcase .ds-card {padding:var(--ds-spacing-md);}}
@media(prefers-reduced-motion:reduce) {#design-system-showcase {scroll-behavior:auto!important;}}
"""


def show_result(text, activity, options):
    """Validación amable y visible; preserva el texto ingresado si falta algo."""
    if not text or not text.strip():
        return state_message("Falta tu texto. Escribí una palabra o una frase y volvé a continuar.", "error")
    if not activity:
        return state_message("Falta elegir una actividad. Elegí una opción para continuar.", "error")
    support = ", ".join(options or []) or "sin apoyos adicionales"
    return state_message(f"Éxito: tu elección está lista. Texto: {text.strip()}. Actividad: {activity}. Apoyos: {support}.", "success")


def palette_markup():
    # Las muestras no llevan texto encima del color: nombre y hexadecimal se
    # leen sobre blanco, evitando combinaciones accidentales de bajo contraste.
    items = [f'<li><div class="ds-swatch" style="background:{color}" aria-hidden="true"></div><strong>{escape(name)}</strong><p>{color}</p></li>' for name, color in TOKENS.items()]
    return '<ul class="ds-swatches">' + "".join(items) + '</ul>'


def build_showcase():
    major = int(gr.__version__.split(".")[0])
    options = {"theme": create_theme(primary_action="primary"), "css": SHOWCASE_CSS} if major < 6 else {}
    with gr.Blocks(title="Pictovoz · Sistema de diseño", **options) as demo:
        with gr.Column(elem_id="design-system-showcase"):
            gr.HTML('<header class="ds-card ds-welcome"><h1>Pictovoz · Sistema de diseño</h1><p>Una guía de colores, textos y controles con un orden estable.</p><p class="ds-note">No hay cámara, sonidos automáticos ni cambios de pantalla inesperados.</p></header>')
            with gr.Column(elem_classes=["ds-card"]):
                gr.Markdown("## 1. Tipografía y lectura\n### Un título claro para cada tarea\nLos párrafos usan un tamaño cómodo y espacio entre líneas. Las instrucciones mantienen un lenguaje directo y una idea por paso.")
                gr.HTML('<p class="ds-note">Nota: esta información complementa la tarea. Mantiene contraste alto y no se oculta en texto gris tenue.</p>')
                with gr.Accordion("Ver los tokens de color", open=False):
                    gr.HTML(palette_markup())
            with gr.Column(elem_classes=["ds-card"]):
                gr.Markdown("## 2. Botones y estados\nEl color indica el rol. El texto explica la acción. Al pasar el cursor o presionar, no hay destellos ni desplazamientos.")
                # Una sola columna evita comprimir etiquetas largas en el móvil.
                primary = gr.Button("Primary · Continuar", variant="primary")
                secondary = gr.Button("Secondary · Volver a revisar", variant="secondary")
                accent = gr.Button("Accent · Preparar mi elección", variant="secondary", elem_classes=["ds-accent"])
                gr.Button("No disponible · Completá primero el paso anterior", interactive=False)
                button_state = gr.HTML(state_message("Podés probar los botones. El resultado aparece aquí."))
                primary.click(lambda: state_message("Continuar: podés completar el formulario de abajo."), outputs=button_state, queue=False)
                secondary.click(lambda: state_message("Revisión: tus datos se mantienen. No se borró ninguna elección."), outputs=button_state, queue=False)
                accent.click(lambda: state_message("Preparación: elegí una actividad en el siguiente bloque."), outputs=button_state, queue=False)
            with gr.Column(elem_classes=["ds-card"]):
                gr.Markdown("## 3. Entradas de datos\nEscribí un texto. Después elegí una actividad y los apoyos que prefieras.")
                text = gr.Textbox(label="Tu palabra o frase", placeholder="Por ejemplo: quiero jugar", lines=2)
                activity = gr.Radio(["Jugar", "Leer", "Descansar"], label="Elegí una actividad", value=None, elem_classes=["ds-options"])
                options = gr.CheckboxGroup(["Instrucciones cortas", "Más tiempo para responder", "Acompañamiento"], label="Apoyos opcionales · podés elegir varios", elem_classes=["ds-options"])
                submit = gr.Button("Confirmar mi elección", variant="primary")
                result = gr.HTML(state_message("Esperando tu elección. Tus respuestas no se guardan en archivos."))
                submit.click(show_result, inputs=[text, activity, options], outputs=result, queue=False)
            gr.HTML('<section class="ds-card"><h2>4. Tarjetas y mensajes</h2><p>El significado siempre aparece escrito, además del color.</p><div class="tea-state success"><strong>Éxito:</strong> el paso está completo.</div><p class="tea-state ds-warning"><strong>Aviso suave:</strong> podés tomarte el tiempo que necesites.</p><p class="tea-state error"><strong>Falta un dato:</strong> revisá el campo indicado y volvé a continuar.</p></section>')
            gr.Markdown("**Teclado:** usá Tab para recorrer los controles, las flechas para las opciones y Espacio para marcar casillas. El foco tiene un contorno visible.\n\nLos contrastes de texto configurados superan 4,5:1. La comodidad sensorial debe validarse con cada usuario; esta guía no certifica conformidad WCAG integral.")
    return demo


def main():
    parser = argparse.ArgumentParser(description="Guía de componentes del sistema de diseño Pictovoz.")
    parser.add_argument("--port", type=int, default=7865)
    args = parser.parse_args()
    options = {"theme": create_theme(primary_action="primary"), "css": SHOWCASE_CSS} if int(gr.__version__.split(".")[0]) >= 6 else {}
    build_showcase().launch(server_name="127.0.0.1", server_port=args.port, share=False, **options)


if __name__ == "__main__":
    main()
