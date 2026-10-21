# Evaluación final s007 del modelo seleccionado

Estado: **prueba final completada el 21 de octubre de 2026**.

Paquete evaluado: `mobilenet_app_192_20261020`, MobileNetV3-Small 192 × 192,
detector kNN coseno de cinco vecinos y umbral fijo `0.8024037084471637`.
Entrenamiento: s001-s005 y s008; selección y calibración: s006.

## Resultado independiente

- Clasificación conocida: **291/300 (97 %)**; macro-F1 **0,969562**.
- Conocidas rechazadas: **0/300**; las nueve equivocaciones se aceptaron.
- Desconocidas rechazadas: **29/50 (58 %)**.
- Desconocidas aceptadas incorrectamente: **21/50 (42 %)**.
- Acierto operativo total: **320/350 (91,43 %)** con esta mezcla de entradas.
- Precisión entre todas las salidas aceptadas: **291/321 (90,65 %)**.
- Macro-F1 operativo de once etiquetas: **0.918828**.

Se cumple el mínimo de 70 % de clasificación en conocidas. No se cumple el
objetivo de rechazo de 70 % utilizado en desarrollo, ni se reproduce el objetivo
interno de calibración de 80 %. Una AUROC alta (0.998067) no garantiza
un rechazo suficiente con el umbral desplegado. Papá concentra cinco de los
nueve errores conocidos; la clase `no` aporta tres y mamá uno.

La evaluación usó `classify_image`, el mismo preprocesamiento y regla de rechazo
de la aplicación. Se congelaron antes de predecir checkpoint, referencias,
configuraciones y metadata; se verificó aislamiento por hashes frente a 2400
imágenes de desarrollo y ausencia de cambios durante la evaluación. El único
cambio posterior en `application.json` registra estado y `test_evaluated=true`;
no cambia pesos, referencias, clases, dimensiones ni umbral. `selected_model.json`
se conserva como respaldo histórico, no como configuración activa.

## Informe y evidencia

- [Informe PDF con los experimentos y mejoras futuras](../output/pdf/informe_final_pictovoz_final_s007_20261021_124040.pdf).
- [Métricas finales](../reports/final_s007_20261021_124040/metrics.json).
- [Predicciones de las 350 imágenes](../reports/final_s007_20261021_124040/predictions.csv).
- [Protocolo congelado](../reports/final_s007_20261021_124040/protocol_frozen.json).
- [Catálogo de trece resultados de clasificación y nueve ensayos de rechazo](../reports/final_s007_20261021_124040/experiment_catalog.json).
- [Figuras](../reports/final_s007_20261021_124040/figures/).

## Límites y trabajo futuro

Una sola sesión final y 50 desconocidas no cubren otros diseños de tarjetas,
usuarios o dispositivos. No se buscaron duplicados perceptuales. Los intervalos
Wilson por imagen son descriptivos y no incorporan correlación ni variación
entre sesiones. No se demostró utilidad clínica ni rendimiento móvil.

No recalibrar con s007 para presentar una segunda puntuación como independiente.
Para mejorar rechazo, ampliar desconocidos y sesiones de calibración, evaluar
reglas en nuevos datos de desarrollo y reservar otra prueba sellada. Investigar
encuadre y variedad de papá/no/mamá y medir el flujo completo de captura.

## Reproducción de la evidencia

`uv run python scripts/evaluate_final_s007.py` ejecuta la prueba única y bloquea
su repetición si ya encuentra métricas finales. Las tablas y figuras pueden
regenerarse desde predicciones con `scripts/build_final_figures.py`; el PDF se
construye con `scripts/build_final_report.py` en el runtime documental con
ReportLab. No es necesario volver a ejecutar inferencia para revisar resultados.
