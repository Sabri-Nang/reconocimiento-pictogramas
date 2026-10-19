# Evaluación de rechazo de desconocidos con MobileNet

Se calibró un umbral por ronda con todas las300 conocidas internas: se eligió el mayor umbral que rechaza como máximo15(5%), respetando empates e incluyendo igualdad. Por monotonía maximiza también rechazo de unknown bajo ese límite. No se exigió70% interno de unknown;70% sigue como objetivo de evaluación externa. No se fijó un umbral global de aplicación.

La sesión interna conocida ya se usó para parada temprana. Sus métricas son de calibración, no independientes. La externa no eligió el umbral de su ronda. Las rondas comparten datos y el modelo fue elegido adaptativamente durante el desarrollo. s007 no participó.

## Resultados externos agrupados

- Conocidos sin rechazo: 1441/1800 = 80.06%.
- Desconocidos rechazados: 241/250 = 96.40%.
- Desconocidos aceptados por error: 9/250.
- Conocidos rechazados: 287/1800 = 15.94%.
- Conocidos correctamente clasificados y aceptados: 1279/1800 = 71.06%.
- Exactitud entre conocidos aceptados: 84.53%. Este denominador excluye rechazados y no sustituye la exactitud sobre todos los conocidos.

## Rondas

- Ronda 1: calibración s002, externa s001, umbral 0.85984990; rechazo unknown 40/40 (100.0%); rechazo conocidas 46/300; conocidas correctas aceptadas 213/300.
- Ronda 2: calibración s003, externa s002, umbral 0.83754317; rechazo unknown 39/40 (97.5%); rechazo conocidas 1/300; conocidas correctas aceptadas 268/300.
- Ronda 3: calibración s004, externa s003, umbral 0.91735063; rechazo unknown 40/40 (100.0%); rechazo conocidas 210/300; conocidas correctas aceptadas 86/300.
- Ronda 4: calibración s005, externa s004, umbral 0.85168172; rechazo unknown 36/40 (90.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 279/300.
- Ronda 5: calibración s006, externa s005, umbral 0.80207910; rechazo unknown 36/40 (90.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 225/300.
- Ronda 6: calibración s001, externa s006, umbral 0.84421827; rechazo unknown 50/50 (100.0%); rechazo conocidas 30/300; conocidas correctas aceptadas 208/300.

## Límites y siguiente decisión

El70% solicitado es una tasa de rechazo, no un umbral0.70. Los umbrales no son probabilidades de pertenecer a las diez clases. La confianza puede ser alta en imágenes ajenas.

Los negativos actuales contienen principalmente objetos y fondos: faltan más pictogramas ajenos difíciles. No puede afirmarse rechazo general de cualquier desconocido ni cumplimiento final de hipótesis.

Si no se logra suficiente rechazo externo sin perder demasiados conocidos, comparar otro detector (por ejemplo distancia en características) o mejorar la representación de MobileNet. La regla y sus ajustes se evalúan solo en desarrollo. El modelo final debe tener su propia calibración separada antes de s007.

Este protocolo extiende a unknown la rotación de sesiones de CV; no modifica la partición fija documentada para un entrenamiento final con s006 de calibración. No se modificó selected_model.json.

El límite5% corresponde a calibración interna, no es garantía sobre sesiones externas. Se reutilizaron las mismas puntuaciones de cinco vecinos y los mismos modelos/referencias; no hubo inferencia nueva ni reentrenamiento.

## Decisión tras comparar las reglas

La nueva regla logra241/250(96,4%) de unknown rechazados, frente a166/250
(66,4%) con la regla anterior. Pero rechaza287/1800 conocidos(15,94%), frente
a14/1800(0,78%). Los conocidos correctos y aceptados caen de1439/1800
(79,94%) a1279/1800(71,06%). Se pierden162 de los1441 aciertos originales.

Se cumple el objetivo de rechazo de unknown en estas sesiones de desarrollo,
pero no el límite deseado de5% externo ni el objetivo80% de conocidos. En la
tercera ronda se rechazan210/300 conocidos(70%). No se recomienda desplegar
esta calibración. No hay mejora simultánea: el mayor rechazo de unknown tiene
un costo importante para conocidos. La exactitud84,53% entre aceptados tiene
otro denominador y no reemplaza el71,06% sobre todos los conocidos.

La puntuación de similitud separa mejor los grupos que softmax, pero el umbral
no transfiere de forma estable entre sesiones. Siguiente prioridad: analizar
las condiciones de captura y la representatividad de la calibración; evaluar
un procedimiento con varias sesiones internas separadas de entrenamiento y
evaluación, o nuevas sesiones de calibración. No mezclar externas para elegir
un umbral ni afirmar que el ajuste adicional sigue siendo independiente.

s007 no fue utilizada. Los modelos originales, selección y aplicación no se
modificaron.35 pruebas del código pasaron; se verificaron2050 predicciones
externas, seis umbrales desde datos internos y archivos de referencia/modelo.
