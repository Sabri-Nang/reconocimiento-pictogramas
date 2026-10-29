"""Sistema visual de la aplicación, basado en los tokens compartidos."""
from .sensory_theme import DESIGN_TOKENS, TOKEN_CSS, create_theme


def accessible_theme():
    return create_theme(primary_action="primary")


def design_variables():
    """Publica la misma escala de la guía de componentes en la app real."""
    declarations = [
        f"--pv-{group}-{name}:{value};"
        for group in ("typography", "spacing", "radii", "interaction")
        for name, value in DESIGN_TOKENS[group].items()
    ]
    return ".gradio-container {" + "".join(declarations) + "}"


ACCESSIBLE_CSS = TOKEN_CSS + design_variables() + """
.gradio-container {
 width:100%!important; max-width:880px!important; margin:auto!important;
 padding:clamp(16px,4vw,32px)!important; box-sizing:border-box!important;
 font-family:var(--pv-typography-family)!important; color:var(--pv-text);
}
.gradio-container .main {padding:0!important; gap:var(--pv-spacing-lg)!important;}
.gradio-container :is(.column,.row,.block) {min-width:0!important; box-sizing:border-box;}
.gradio-container :is(.prose,p,label,input,textarea,button,select) {
 font-family:var(--pv-typography-family)!important;
 font-size:var(--pv-typography-body)!important; line-height:var(--pv-typography-line-height)!important;
}
.gradio-container :is(h1,h2,h3,p,label,button,textarea,.prose,span) {
 word-break:normal!important; overflow-wrap:anywhere; hyphens:none!important;
}
.gradio-container :is(h2,.prose h2) {font-size:var(--pv-typography-h2)!important; line-height:1.4!important; margin:0 0 var(--pv-spacing-md);}
.gradio-container :is(input,textarea,.prose) {color:var(--pv-text)!important;}
.gradio-container button {
 min-height:var(--pv-interaction-target); font-weight:600; white-space:normal!important;
 box-sizing:border-box; border-radius:var(--pv-radii-sm)!important;
}
.gradio-container :is(button,input,textarea,select,a,[tabindex]):focus-visible {
 outline:var(--pv-interaction-focus-width) solid var(--pv-primary)!important;
 outline-offset:var(--pv-interaction-focus-offset); box-shadow:0 0 0 3px var(--pv-surface)!important;
}
.gradio-container :is(button,label,input,textarea) {transition:none!important;}
.gradio-container .prose a {color:var(--pv-primary); text-decoration:underline;}
/* Gradio fija el wrapper a 32 px: al envolver pestañas se superponían al título. */
.gradio-container .tab-wrapper {height:auto!important; min-height:var(--pv-interaction-target); align-items:stretch!important;}
.gradio-container [role="tablist"] {
 height:auto!important; overflow:visible!important; display:flex; flex-wrap:wrap;
 gap:var(--pv-spacing-xs); padding:var(--pv-spacing-xs)!important; align-items:stretch!important;
}
.gradio-container [role="tab"] {
 flex:1 1 140px; height:auto!important; min-height:var(--pv-interaction-target);
 padding:12px!important; border:2px solid var(--pv-primary)!important;
 color:var(--pv-text)!important; border-radius:var(--pv-radii-sm)!important;
}
.gradio-container [role="tab"][aria-selected="true"] {
 background:var(--pv-secondary)!important; text-decoration:underline; text-underline-offset:5px; font-weight:700;
}
.gradio-container .gr-accordion {overflow:visible!important;}
.gradio-container .gr-accordion .label-wrap {
 min-height:var(--pv-interaction-target); width:100%!important; margin:0!important;
 box-sizing:border-box; gap:var(--pv-spacing-sm);
}
.gradio-container .gr-accordion .label-wrap span:not(.icon) {flex:1; min-width:0; white-space:normal;}
.gradio-container .gr-accordion .icon {flex:0 0 auto;}
#welcome-card {padding:var(--pv-spacing-lg) 0; border-bottom:2px solid var(--pv-primary);}
#welcome-card h1 {
 font-size:clamp(2rem,6vw,2.75rem)!important; line-height:1.2!important;
 letter-spacing:-0.03em; margin:var(--pv-spacing-xs) 0 var(--pv-spacing-sm);
}
#welcome-card p {max-width:60ch; margin:0 0 var(--pv-spacing-md);}
#welcome-card .brand-note {font-size:var(--pv-typography-note)!important; font-weight:700; letter-spacing:0.08em;}
.task-steps {list-style:none; padding:0; margin:var(--pv-spacing-lg) 0 0; display:flex; flex-wrap:wrap; gap:var(--pv-spacing-md);}
.task-steps li {display:flex; align-items:center; gap:var(--pv-spacing-xs); font-size:var(--pv-typography-note);}
.task-steps span {display:inline-grid; place-items:center; width:2rem; height:2rem; border-radius:50%; background:var(--pv-secondary); font-weight:700; flex-shrink:0;}
.pictovoz-section,#result-card {
 padding:var(--pv-spacing-lg)!important; background:var(--pv-surface);
 border:1px solid var(--pv-primary)!important; border-radius:var(--pv-radii-lg)!important;
 box-shadow:none;
}
#communication-phrase {background:var(--pv-background);}
#communication-phrase :is(p,span) {
 font-size:clamp(1.5rem,4vw,2.25rem)!important; font-weight:700; line-height:1.5!important;
 border:0; background:var(--pv-background);
}
#recognize-upload,#recognize-camera {width:100%; min-height:56px;}
#clear-result {background:var(--pv-surface)!important; color:var(--pv-text)!important; margin-top:var(--pv-spacing-md);}
.result-status {padding:var(--pv-spacing-md); border-radius:var(--pv-radii-sm); background:var(--pv-background); color:var(--pv-text); font-size:var(--pv-typography-body); line-height:1.6;}
.result-status.accepted {background:var(--pv-secondary);}
.result-status.rejected {background:var(--pv-accent);}
.result-status.error {background:var(--pv-error-surface); border-left:4px solid var(--pv-error);}
.skip-link {position:absolute; left:16px; top:-200px; padding:16px; background:var(--pv-surface); color:var(--pv-primary); z-index:100;}
.skip-link:focus {top:8px;}
@media(max-width:640px) {
 .gradio-container {padding:16px 12px!important;}
 .pictovoz-section,#result-card {padding:var(--pv-spacing-md)!important;}
 .task-steps {flex-direction:column; gap:var(--pv-spacing-xs);}
}
@media(prefers-reduced-motion:reduce) {
 .gradio-container * {animation:none!important; transition:none!important; scroll-behavior:auto!important;}
}
@media(forced-colors:active) {
 .gradio-container [role="tab"][aria-selected="true"] {outline:2px solid Highlight!important;}
 .gradio-container :is(button,a,input,textarea):focus-visible {outline:3px solid Highlight!important;}
}
"""
