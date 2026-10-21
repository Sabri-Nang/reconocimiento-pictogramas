"""Tema sereno de Pictovoz y estilos responsivos de la aplicación."""
from .sensory_theme import create_theme, TOKEN_CSS


def accessible_theme():
    return create_theme()


ACCESSIBLE_CSS = TOKEN_CSS + """
.gradio-container [role="tablist"] {height:auto!important; min-height:52px; overflow:visible!important; display:flex; flex-wrap:wrap; align-items:stretch!important;}
.gradio-container [role="tab"] {height:auto!important; min-height:52px; flex:1 1 130px; padding:10px 12px!important; font-size:1rem!important; line-height:1.4!important;}
/* El flujo es secuencial: ninguna columna estrecha compite con el resultado. */
.gradio-container .main {padding:0!important;}
.gradio-container {width:100%!important; max-width:960px!important; box-sizing:border-box!important; margin:auto!important; padding:clamp(12px,3vw,24px)!important; font-family:Verdana,Arial,sans-serif!important; color:var(--pv-text);}
.gradio-container :is(.prose,p,label,input,textarea,button,select) {font-family:Verdana,Arial,sans-serif!important; font-size:1.125rem!important; line-height:1.6!important;}
.gradio-container :is(h1,h2,h3,p,label,button,textarea,.prose) {word-break:normal!important; overflow-wrap:normal!important; hyphens:none!important;}
.gradio-container :is(.column,.row,.block) {box-sizing:border-box; min-width:0!important;}
.gradio-container :is(input,textarea) {color:var(--pv-text)!important;}
.gradio-container button {min-height:48px; box-sizing:border-box; white-space:normal!important; font-weight:600;}
.gradio-container :is(button,input,textarea,select,a,[tabindex]):focus-visible {outline:3px solid var(--pv-primary)!important; outline-offset:3px; box-shadow:0 0 0 3px var(--pv-surface)!important;}
.gradio-container .prose {color:var(--pv-text)!important;}
.gradio-container .prose a {color:var(--pv-primary); text-decoration:underline;}
.gradio-container .gr-accordion {overflow:visible!important;}
.gradio-container .gr-accordion .label-wrap {box-sizing:border-box; width:100%!important; margin:0!important; gap:12px;}
.gradio-container .gr-accordion .label-wrap span:not(.icon) {flex:1; min-width:0; white-space:normal; font-size:1rem;}
.gradio-container .gr-accordion .icon {flex:0 0 auto;}
#welcome-card {background:var(--pv-secondary); border:0; border-radius:20px; padding:24px; margin-bottom:8px;}
#welcome-card h1 {font-size:2.4rem!important; line-height:1.15!important; margin:0 0 12px; letter-spacing:-0.03em;}
#welcome-card p {margin:12px 0 0; max-width:65ch;}
.status-badge {display:inline-block; border-radius:999px; padding:6px 14px; background:var(--pv-secondary); color:var(--pv-text); font-weight:700; font-size:1rem;}
.pictovoz-section {padding:20px!important; border:1px solid var(--pv-primary)!important; border-radius:20px!important; background:var(--pv-surface);}
.pictovoz-section h2 {font-size:1.4rem!important; margin:0 0 10px; line-height:1.35!important;}
#result-card {background:var(--pv-surface); border:1px solid var(--pv-primary)!important; box-shadow:none; border-radius:20px; padding:24px!important;}
#communication-phrase textarea {font-size:clamp(1.5rem,4vw,2.25rem)!important; font-weight:700; line-height:1.4!important; resize:none;}
#recognize-upload,#recognize-camera {width:100%;}
.result-status {border-radius:12px; padding:14px 18px; background:var(--pv-background); color:var(--pv-text); font-size:1.125rem; line-height:1.6;}
.result-status.accepted {background:var(--pv-success); color:var(--pv-text);}
.result-status.rejected {background:var(--pv-accent); color:var(--pv-text);}
.result-status.error {border-left:4px solid var(--pv-error);background:var(--pv-error-surface); color:var(--pv-text);}
#class-scores {min-width:0!important;}
#class-scores :is(span,p) {word-break:normal!important; overflow-wrap:normal!important;}
@media(max-width:640px) {
 .gradio-container {padding:16px 12px!important;}
 #welcome-card,#result-card,.pictovoz-section {padding:18px!important; border-radius:16px!important;}
 #welcome-card h1 {font-size:2rem!important;}
 .gradio-container .tab-nav {flex-wrap:wrap;}
}
"""
