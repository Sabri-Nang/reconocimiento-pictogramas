# Sistema de diseño accesible de Pictovoz

Versión: 29 de octubre de 2026. Implementado en Gradio, con tokens compartidos
en `sensory_theme.py`, estilos de aplicación en `accessible_theme.py` y guía
interactiva en `design_system.py`.

## Propósito y personas

Facilitar una tarea: pasar de una tarjeta a una frase que la persona pueda revisar
y, si quiere, escuchar. La interfaz se dirige a personas con distintas capacidades
de lectura, atención, visión y movimiento, incluidas personas con TEA y adultos
mayores. No presupone que esas personas tengan necesidades iguales. El diseño
evita infantilizar, apurar o atribuir eficacia terapéutica a una paleta.

La referencia es WCAG 2.2 AA y la guía cognitiva COGA de W3C. Esto define objetivos,
no una certificación de conformidad integral ni validación con usuarios.

## Fundamentos

- Fondo cálido `#F7F5EE`, superficie blanca `#FFFFFF` y texto `#2B2D42`.
- Acción principal azul `#3E6B89` con texto blanco. Menta `#A3C9A8` para
  selección y apoyo; mostaza `#E9B44C` para un rechazo que requiere otra foto.
- Error: texto oscuro sobre una superficie aclarada del rojo `#C86D61`.
  El rojo original no admite texto normal blanco ni oscuro con contraste 4,5:1.
- Las parejas de texto declaradas en `TEXT_PAIRS` se verifican automáticamente
  contra el mínimo de 4,5:1. Esto no prueba todas las combinaciones del DOM.
- Tipografía Verdana/Arial del sistema, cuerpo 1,125 rem, interlineado 1,6.
  La frase usa entre 1,5 y 2,25 rem y crece verticalmente con su contenido.
- Espaciado de 8, 12, 16, 24 y 32 px, expresado en rem; radios de 8 y 16 px.
- Controles principales de al menos 48 px de alto; identificación de 56 px.
  Estos tamaños son una decisión de comodidad, superiores al mínimo de WCAG
  2.5.8. Los controles internos de Gradio requieren revisión aparte.
- Foco de 3 px con separación de 3 px; pestaña elegida marcada también con
  subrayado. No depender únicamente de verde/rojo para comunicar un estado.

La aplicación y la guía utilizan `DESIGN_TOKENS`, sin crear una segunda paleta.
La guía permite probar los roles azul, secundario y acento. Para ejecutarla:

```powershell
uv run python scripts/showcase_design_system.py
```

Se abre localmente en `http://127.0.0.1:7865`. No carga modelos ni activa cámara.

## Componentes y comportamiento

1. **Encabezado:** nombre, propósito breve y tres pasos sin indicador temporal.
2. **Entrada:** pestañas «Subir foto» y «Tomar foto». La segunda describe una
   captura individual; no promete reconocimiento continuo.
3. **Identificación:** una acción explícita y un mensaje escrito de espera.
   El foco se mantiene en el control que la persona utilizó.
4. **Resultado:** primero el estado y la frase como texto legible, seleccionable
   y sin un campo de formulario deshabilitado. La frase aceptada se incluye en
   el anuncio `role=status`, `aria-live=polite`, `aria-atomic=true`.
5. **Voz voluntaria:** identificar no llama a gTTS. «Escuchar frase» prepara
   la voz y permite iniciarla; el reproductor ofrece pausa y repetición. Si el
   navegador bloquea el inicio, se indica usar reproducir. Antes del botón se
   explica que solo la frase se envía a Google y que requiere Internet.
6. **Nueva consulta:** «Empezar de nuevo» borra ambas imágenes, frase, puntuaciones
   y audio. Cambiar imagen o pestaña invalida cualquier resultado pendiente.
7. **Ayuda progresiva:** categorías, puntuaciones e interpretación quedan en
   un acordeón cerrado. El aviso de posibles errores permanece visible.

Los mensajes explican el siguiente paso: elegir otra foto, mejorar luz/enfoque
o volver a intentar la voz. No se muestran excepciones técnicas al usuario.
No se cambia automáticamente de pantalla ni se impone un tiempo para responder.
No hay sonidos al identificar; las transiciones de los controles son inmediatas
y se respeta `prefers-reduced-motion`. Se añaden estilos de foco en colores
forzados para quienes utilizan alto contraste del sistema.

## Errores encontrados y tratados

- La voz se generaba y reproducía automáticamente al identificar. Ahora es una
  acción voluntaria y su fallo conserva la frase escrita.
- «Cámara en Vivo» prometía un flujo distinto del implementado. Se renombra
  «Tomar foto», con ayuda para permisos y una alternativa sin cámara.
- Las puntuaciones técnicas aparecían en el flujo principal. Se pliegan para
  reducir competencia visual y se conserva su aclaración de incertidumbre.
- El archivo subido llegaba como PIL y podía perder la posibilidad de validar
  su formato original. Ahora se conserva la ruta y se valida JPEG/PNG con el
  preprocesamiento compartido antes de la inferencia.
- Una petición obsoleta podía empezar después de limpiar la imagen y tomar la
  revisión nueva como válida. Se captura una revisión antes de encolarla y se
  comprueba tanto antes como después de inferir. La voz tiene el mismo control.
- Cambiar de pestaña podía dejar un resultado de la otra entrada. El cambio
  invalida resultado y voz, conservando las fotos para permitir revisarlas.
- La frase se mostraba en un campo deshabilitado. Ahora es texto normal y se
  incluye en el anuncio del resultado para tecnologías de asistencia.
- A 320 px el contenedor de pestañas de Gradio conservaba una altura fija de
  32 px y las etiquetas se superponían al título y las instrucciones. Se permite
  que el contenedor crezca al envolver sus botones.

La inferencia, las clases, los pesos y el rechazo calibrado se conservan. El
contrato Python histórico `predecir()` sigue devolviendo frase, puntuaciones y
MP3; la interfaz utiliza el nuevo flujo visual sin síntesis implícita.

## Validación y continuidad

Las regresiones automatizadas están en `tests/test_accessible_flow.py`, además
de las pruebas existentes de interfaz, voz, tokens y sistema de diseño. Cubren
voz voluntaria, formatos, fallos y respuestas antiguas antes y durante el trabajo.
Los resultados concretos de la revisión se registran en
`docs/verificacion_ux_20261029.md`.

Antes de declarar conformidad se requiere evaluación manual con lector de
pantalla, ampliación y espaciado de texto, teclado y controles internos de
Gradio, además de cámara física móvil. Con usuarios, comprobar comprensión de
las etiquetas, carga sensorial, alcance de controles y recuperación de errores.
Incluir personas con TEA, personas mayores y personas con necesidades diversas;
permitir acompañamiento si lo solicitan y no medir éxito solo por velocidad.

## Referencias

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/): contraste, teclado, foco,
  redistribución del contenido, tamaños de objetivo y mensajes de estado.
- [Guía suplementaria COGA](https://www.w3.org/WAI/WCAG2/supplemental/):
  propósito claro, jerarquía familiar e instrucciones comprensibles.
- [Personalización y familiaridad](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o8p04-interface/):
  respetar preferencias individuales y capacidades de adaptación del navegador.
