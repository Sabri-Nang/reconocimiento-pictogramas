# Rechazo: objetivo interno con límite de conocidas

Estado del documento: **desarrollo**.

## Flujo del código

src/reconocimiento_pictogramas/feature_rejection.py, neighbor_similarity:
normaliza características, compara con referencias de train, promedia los cinco
cosenos mayores y escala a [0,1]. No es probabilidad.

src/reconocimiento_pictogramas/inference.py, classify_prepared_image:
extrae características y puntuaciones, calcula similitud y lee el umbral del
detector seleccionado. Rechaza cuando score <= threshold ydevuelve desconocido.
La interfaz lo presenta como pictograma no reconocido. No se cambió esta regla.

src/reconocimiento_pictogramas/rejection.py, calibrate_threshold:
elige el mínimo umbral que alcanza la fracción solicitada de desconocidas
internas, respetando igualdad yempates. No confundir tasa objetivo con umbral0,80.

La nueva calibrate_target_with_known_cap agrega el límite sobre TODAS las
conocidas internas, incluidas las mal clasificadas. Si el umbral mínimo para
unknown ya supera el límite, ningún umbral mayor satisface ambas restricciones:
devuelve feasible=false ythreshold=None. No se activa un umbral inviable.

## Experimento prefijado

scripts/evaluate_rejection_targets.py reutiliza las puntuaciones de
cv10_s008_192_unknown_knn_20261019, sin nuevos pesos ni referencias. Prueba75%
y80% internos con límite1% (máximo3 de300 conocidas internas). Guarda todas
las calibraciones antes de leer puntuaciones externas. Si alguna ronda es
inviable, no produce un promedio externo parcial para esa variante. No ajusta
umbrales para corregir errores concretos de la externa. Se verifican pesos,
archivos de referencia, puntuaciones yseparación de sesiones. s007 no participa.

Los criterios externos prefijados son agrupados: al menos70% de desconocidas
rechazadas, como máximo1% de conocidas rechazadas y al menos93% de conocidas
correctas aceptadas. Se registran además resultados por sesión; un límite
interno o agrupado no garantiza el mismo límite en cada sesión externa.

## Resultados

Referencia con objetivo70%:208/300 desconocidas rechazadas (69,33%),5/2100
conocidas rechazadas (0,24%),1961 conocidas correctas aceptadas (93,38%).
Objetivo75% con límite1%:219/300 (73%),6/2100 (0,29%),1961/2100 (93,38%).
Objetivo80% con límite1%:225/300 (75%),6/2100 (0,29%),1961/2100 (93,38%).
Ambas variantes son viables en todas las rondas y cumplen los criterios externos
agrupados. La del80% agrega17 rechazos correctos de desconocidas respecto de
referencia, sin perder aciertos adicionales de conocidas; rechaza una conocida
más que ya estaba mal clasificada. No mejora los pesos del clasificador.

Se elige objetivo80% con límite1% como candidato para la próxima calibración
del modelo único192. No es un umbral global: cada modelo de CV tiene uno distinto.
La aplicación permanece con su modelo128 anterior ysu umbral original. Para
actualizarla se necesita un modelo único192, sus referencias ycalibración propia.

Persisten diferencias: a80% interno s004 externa rechaza16/40 (40%) ys00122/40
(55%); s006 rechaza5/300 conocidas (1,67%) aunque el límite interno era1%.
Por tanto, no se declara estabilidad en todos los entornos ni cumplimiento final
de hipótesis. Externas ya analizadas yusadas para comparar reglas: desarrollo
adaptativo, no prueba final independiente. Negativos principalmente objetos y
escenas; faltan otros pictogramas desconocidos. s007 continúa reservada.

Evidencia: reports/cv10_s008_192_rejection_targets_20261019/ contiene protocolo,
calibraciones, predicciones, comparación, gráfico yverificación de hashes.
Pruebas:61 aprobadas, incluyendo factibilidad, empates ylímites.
