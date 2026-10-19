# Evaluación de rechazo de desconocidos con MobileNet

Se calibró un umbral por ronda usando únicamente unknown de la sesión interna. Se eligió el menor que rechaza al menos70% (incluida igualdad). Esa regla minimiza el rechazo de conocidos bajo la restricción elegida. No se fijó un umbral global de aplicación.

La sesión interna conocida ya se usó para parada temprana. Sus métricas son de calibración, no independientes. La externa no eligió el umbral de su ronda. Las rondas comparten datos y el modelo fue elegido adaptativamente durante el desarrollo. s007 no participó.

## Resultados externos agrupados

- Conocidos sin rechazo: 1964/2100 = 93.52%.
- Desconocidos rechazados: 208/300 = 69.33%.
- Desconocidos aceptados por error: 92/300.
- Conocidos rechazados: 5/2100 = 0.24%.
- Conocidos correctamente clasificados y aceptados: 1961/2100 = 93.38%.
- Exactitud entre conocidos aceptados: 93.60%. Este denominador excluye rechazados y no sustituye la exactitud sobre todos los conocidos.

## Rondas

- Ronda 1: calibración s002, externa s001, umbral 0.80583344; rechazo unknown 21/40 (52.5%); rechazo conocidas 0/300; conocidas correctas aceptadas 275/300.
- Ronda 2: calibración s003, externa s002, umbral 0.81996017; rechazo unknown 34/40 (85.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 278/300.
- Ronda 3: calibración s004, externa s003, umbral 0.82383408; rechazo unknown 30/40 (75.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 280/300.
- Ronda 4: calibración s005, externa s004, umbral 0.79260095; rechazo unknown 12/40 (30.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 300/300.
- Ronda 5: calibración s006, externa s005, umbral 0.79336329; rechazo unknown 30/40 (75.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 283/300.
- Ronda 6: calibración s008, externa s006, umbral 0.81555181; rechazo unknown 40/50 (80.0%); rechazo conocidas 5/300; conocidas correctas aceptadas 256/300.
- Ronda 7: calibración s001, externa s008, umbral 0.82940669; rechazo unknown 41/50 (82.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 289/300.

## Límites y siguiente decisión

El70% solicitado es una tasa de rechazo, no un umbral0.70. Los umbrales no son probabilidades de pertenecer a las diez clases. La confianza puede ser alta en imágenes ajenas.

Los negativos actuales contienen principalmente objetos y fondos: faltan más pictogramas ajenos difíciles. No puede afirmarse rechazo general de cualquier desconocido ni cumplimiento final de hipótesis.

Si no se logra suficiente rechazo externo sin perder demasiados conocidos, comparar otro detector (por ejemplo distancia en características) o mejorar la representación de MobileNet. La regla y sus ajustes se evalúan solo en desarrollo. El modelo final debe tener su propia calibración separada antes de s007.

Este protocolo extiende a unknown la rotación de sesiones de CV; no modifica la partición fija documentada para un entrenamiento final con s006 de calibración. No se modificó selected_model.json.
