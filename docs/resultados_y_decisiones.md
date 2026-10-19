# Resultados y decisiones de desarrollo

## Datos y roles de cada ronda

Se agregaron300 fotografías conocidas en s008. El desarrollo pasó de 1800 a 2100
conocidas: diez clases y siete sesiones (s001-s006 y s008), con 30 por clase y
sesión. Las300 desconocidas de desarrollo se evalúan aparte; no son una clase.

Antes, cada ronda usaba1200 imágenes train (cuatro sesiones),300 de validación
interna y 300 externas. Ahora usa1500 train (cinco sesiones),300 internas y 300
externas. Las300 nuevas sí aumentaron en300 el entrenamiento por ronda. Los roles
rotan: cada sesión entrena en cinco rondas, valida internamente en una y se evalúa
externamente en otra. s007 está fuera de todas las rondas, reservada para prueba
final.128 y 192 usan exactamente las mismas1500/300/300 imágenes por ronda.

La sesión interna elige época por mínima val_loss y parada temprana. La externa
se consulta después de seleccionar el checkpoint. Sus resultados se usan para
comparar procedimientos y son desarrollo adaptativo, no prueba final.

## Resolución128 frente a 192

CNN compacta:1637/2100 (77,95 %) a 128 y 1477/2100 (70,33 %) a 192:160 aciertos menos.
MobileNetV3-Small:1777/2100 (84,62 %) a 128 y 1964/2100 (93,52 %) a 192:187 más,
una diferencia de 8,90 puntos porcentuales. Macro-F1, resultados por clase, sesión,
distancia y errores corregidos/nuevos están en el informe JSON de comparación.

Los originales se procesaron por separado con EXIF/RGB/LANCZOS. Se conservaron
particiones, orden de clases, semillas, aumentos, batch32, épocas máximas y
paciencias. No se ampliaron imágenes previamente reducidas a 128. No se cambió
la resolución de entrada del modelo actual de la aplicación.

## Qué explica la caída de la CNN

La CNN usa Flatten: a 192 aumentan los mapas y la capa densa, pasando de 323370 a
651050 parámetros. Por ello no se aísla resolución con capacidad constante.
MobileNet conserva944890 parámetros en ambas resoluciones y parte de pesos
ImageNet; la CNN compacta aprende desde cero. Esto puede influir en aprendizaje
y generalización, pero el experimento no identifica una única causa.

La ronda externa s001 perdió111 aciertos (157/300 a 128,46/300 a 192), cerca del 69 %
de la pérdida total de 160. A192 seleccionó la época 1 y paró en 7: aunque subió
la exactitud interna, ninguna pérdida interna posterior fue menor que la inicial.
La pérdida penaliza también la confianza de los errores, por eso puede empeorar
mientras aumenta la exactitud. Es evidencia de inestabilidad entre sesiones y
posible sobreajuste; no demuestra que la resolución mayor sea intrínsecamente
peor. Las otras seis rondas, conjuntamente, perdieron49 aciertos. Se conservan
todas las rondas; no se excluye s001 para mejorar el promedio.

MobileNet también es una CNN. La conclusión se refiere a estas arquitecturas,
puntos de partida y procedimientos, no a CNN en general.

## Rechazo de desconocidos

Misma regla conservadora: cinco vecinos de train; umbral mínimo que rechaza70 %
de desconocidas internas; umbral guardado antes de evaluar la sesión externa.
Cada modelo tiene referencias y umbral propios, sin heredar el umbral de 128.
La validación interna conocida se comparte con selección de época; no es una
calibración independiente.197/300 desconocidas se rechazaron a 128 (65,67 %) y
208/300 a 192 (69,33 %). Todavía faltan dos rechazos para210/300, el objetivo70 %.
Las conocidas rechazadas fueron10/2100 (0,48 %) y 5/2100 (0,24 %), respectivamente.
A192, tres de esas cinco estaban bien clasificadas: quedaron1961/2100 conocidas
correctas y aceptadas (93,38 %), frente a 1964 correctas sin rechazo.

No confundir exactitud con tasa de rechazo ni similitud con probabilidad. Los
negativos son principalmente objetos y escenas; no permiten afirmar rechazo
general de todo pictograma fuera de las diez clases. Las diferencias entre
sesiones siguen siendo relevantes y 69,33 % no se redondea como cumplimiento70 %.

## Tiempos y siguiente decisión

Medianas CPU, batch 1 y checkpoint fold1, con calentamiento: CNN 10,52/11,57ms a
128/192 yMobileNet 96,80/97,52ms. Se midió llamada al clasificador y salida numpy;
no carga del modelo, kNN, red ni video. No es rendimiento garantizado del celular.
El benchmark usa cuatro checkpoints; no mide variación de todas las rondas.

MobileNet a 192 es el mejor candidato de clasificación ensayado. Esto no significa
que la aplicación ya lo use ni que un checkpoint arbitrario de CV tenga93,52 %.
La aplicación conserva mobilenet_app_20261018 a 128 ysu detector previo. Antes de
actualizarla se debe fijar el procedimiento del modelo único y su calibración.
s007 solo se evaluará al final con todo congelado. No se declara cumplimiento
final de hipótesis ni del objetivo de rechazo.

## Evidencia

- reports/cv10_s008_128_20261019: curvas, checkpoints referenciados y 2100 predicciones
  externas por arquitectura.
- reports/cv10_s008_192_20261019: equivalente a 192, sin sobrescribir128.
- reports/cv10_s008_unknown_knn_20261019 y
  reports/cv10_s008_192_unknown_knn_20261019: calibraciones internas y 2400
  predicciones externas de rechazo, con verificaciones.
- reports/resolution_192_20261019/comparison.json y comparison.png: comparación
  emparejada y tiempos; preparation.json conserva hashes de archivos protegidos.
- docs/entrenamiento_s008.md y docs/experimento_resolucion_192.md: protocolos.

Los datasets, pesos, cachés, credenciales yhojas visuales permanecen locales,
ignorados por Git; requieren respaldo separado. Metadatos, código, protocolos,
predicciones y gráficos estadísticos se versionan como evidencia.
