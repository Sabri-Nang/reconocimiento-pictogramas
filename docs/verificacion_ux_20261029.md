# Verificación de la revisión UX/UI

Fecha: 29 de octubre de 2026. Entorno existente: Python 3.11.15 y Gradio 6.28.0.

## Comprobaciones realizadas

- `uv run --no-sync pytest -q`: **120 pruebas aprobadas**, en 5,59 s en la
  ejecución final. Incluye nueve nuevas comprobaciones (con parametrización)
  de voz voluntaria, entrada, respuestas obsoletas y organización de controles.
- `uv run --no-sync python scripts/validate_config.py`: configuración de
  dataset y aplicación compatible.
- `uv lock --check --offline`: resolución de dependencias consistente, sin cambios en `uv.lock`.
- `git diff --check`: sin errores de espacios. Git avisa de normalización
  LF/CRLF en archivos locales; no se cambió la política de finales de línea.
- RPC real contra Gradio en `127.0.0.1:7860`: se envió
  `data/raw/known/agua/agua_s001_0001.jpg` al flujo `begin_identification` y
  `identify_request`. Devolvió «Quiero tomar agua», puntuaciones y audio `None`.
  `clear_session` devolvió ambas imágenes y la frase vacías. No se solicitó voz.
  Es una comprobación funcional con una imagen de entrenamiento, no una nueva
  medición de exactitud ni evidencia de generalización.
- Navegador: se verificaron jerarquía y vista de escritorio, error sin imagen,
  botón de voz sin frase, limpieza y ayuda inicialmente plegada.
- Pantalla de 320 px: ancho del documento 305 px (descontada la barra de
  desplazamiento), sin desbordamiento horizontal del documento. Los controles
  principales medidos tenían 239,33 px de ancho, identificación 73,58 px de
  alto al envolver su texto y voz/limpieza 48 px.
- Se detectó y corrigió superposición de pestañas por el wrapper de 32 px
  de Gradio. Tras corregirlo, el título terminaba en y=644,19, las pestañas
  comenzaban en y=660,19 y el panel comenzaba en y=821,77: sin superposición.
- Teclado: Tab alcanzó «Ir a la frase» con contorno visible; Enter trasladó
  el foco al encabezado de resultado. No se impone ese salto al identificar.
- Se observó `lang=es` en el documento. Los mensajes usan región de estado
  y el texto de la frase aceptada se incorpora al anuncio.
- Se guardó una captura de escritorio del flujo vacío como evidencia local
  de la revisión; la ventana quedó disponible en el navegador de la tarea.

## Incidencias de la comprobación

El primer `pytest -q` recolectó pruebas de un SDK de Google dentro de `tmp/`
y falló con 299 errores ajenos a la suite de la aplicación. Se añadió
`[tool.pytest.ini_options] testpaths = ["tests"]` en `pyproject.toml`. El comando
habitual vuelve a ejecutar las pruebas del proyecto sin recorrer el SDK.

Una prueba esperaba el aviso de evaluación dentro del encabezado. Se actualizó
para verificar el aviso vigente en el contenido de la aplicación, dado que ahora
aparece en la ayuda. El aviso visible de posibles errores se conserva.

## Pendiente de validación

- Lector de pantalla real: anuncio de cambios en Gradio, navegación y controles
  internos de carga, captura y reproducción.
- Ampliación de texto al 200 %, zoom, espaciado personalizado, colores forzados
  y preferencias de movimiento en dispositivos reales. Hay estilos previstos,
  pero no se verificó cada combinación.
- Cámara física, permisos y reproducción de voz en celulares/navegadores reales.
  No se activaron cámara ni micrófono durante esta revisión.
- La síntesis y sus errores se comprobaron con dobles en pruebas; no se llamó a
  gTTS durante la comprobación real de la API.
- Las entradas corruptas que Gradio rechaza antes de ejecutar el callback pueden
  producir mensajes propios del componente; requieren revisión manual adicional.
- Pruebas de comprensión, comodidad y recuperación con personas con TEA,
  personas mayores y personas con diferentes discapacidades y apoyos.

No se certifica conformidad integral WCAG ni eficacia clínica. Se preservan los
pesos, umbral, clases, datos y evidencia experimental. No se utilizó s007.
