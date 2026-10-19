# Evaluación de rechazo de desconocidos con MobileNet

Se calibró un umbral por ronda usando únicamente unknown de la sesión interna. Se eligió el menor que rechaza al menos70% (incluida igualdad). Esa regla minimiza el rechazo de conocidos bajo la restricción elegida. No se fijó un umbral global de aplicación.

La sesión interna conocida ya se usó para parada temprana. Sus métricas son de calibración, no independientes. La externa no eligió el umbral de su ronda. Las rondas comparten datos y el modelo fue elegido adaptativamente durante el desarrollo. s007 no participó.

## Resultados externos agrupados

- Conocidos sin rechazo: 1441/1800 = 80.06%.
- Desconocidos rechazados: 150/250 = 60.00%.
- Desconocidos aceptados por error: 100/250.
- Conocidos rechazados: 415/1800 = 23.06%.
- Conocidos correctamente clasificados y aceptados: 1256/1800 = 69.78%.
- Exactitud entre conocidos aceptados: 90.69%. Este denominador excluye rechazados y no sustituye la exactitud sobre todos los conocidos.

## Rondas

- Ronda 1: calibración s002, externa s001, umbral 0.72075909; rechazo unknown 24/40 (60.0%); rechazo conocidas 69/300; conocidas correctas aceptadas 207/300.
- Ronda 2: calibración s003, externa s002, umbral 0.76032990; rechazo unknown 28/40 (70.0%); rechazo conocidas 62/300; conocidas correctas aceptadas 233/300.
- Ronda 3: calibración s004, externa s003, umbral 0.62767082; rechazo unknown 14/40 (35.0%); rechazo conocidas 74/300; conocidas correctas aceptadas 190/300.
- Ronda 4: calibración s005, externa s004, umbral 0.76331007; rechazo unknown 26/40 (65.0%); rechazo conocidas 39/300; conocidas correctas aceptadas 254/300.
- Ronda 5: calibración s006, externa s005, umbral 0.65181017; rechazo unknown 26/40 (65.0%); rechazo conocidas 64/300; conocidas correctas aceptadas 197/300.
- Ronda 6: calibración s001, externa s006, umbral 0.75908095; rechazo unknown 32/50 (64.0%); rechazo conocidas 107/300; conocidas correctas aceptadas 175/300.

## Límites y siguiente decisión

El70% solicitado es una tasa de rechazo, no un umbral0.70. Los umbrales no son probabilidades de pertenecer a las diez clases. La confianza puede ser alta en imágenes ajenas.

Los negativos actuales contienen principalmente objetos y fondos: faltan más pictogramas ajenos difíciles. No puede afirmarse rechazo general de cualquier desconocido ni cumplimiento final de hipótesis.

Si no se logra suficiente rechazo externo sin perder demasiados conocidos, comparar otro detector (por ejemplo distancia en características) o mejorar la representación de MobileNet. La regla y sus ajustes se evalúan solo en desarrollo. El modelo final debe tener su propia calibración separada antes de s007.

Este protocolo extiende a unknown la rotación de sesiones de CV; no modifica la partición fija documentada para un entrenamiento final con s006 de calibración. No se modificó selected_model.json.

## Decisión tras el experimento

El umbral simple no satisface el objetivo externo:150/250=60% de unknown
rechazados, inferior a70%. Rechaza además415/1800 conocidos (23,06%), de
los cuales185 eran correctos antes del rechazo. La exactitud de conocidos
correctos y aceptados queda en1256/1800=69,78%. El90,69% entre aceptados
es una métrica condicional y no debe presentarse como mejora del80,06%
original. Persisten129 conocidos mal clasificados y aceptados.

No se selecciona un umbral para la aplicación ni se ajusta usando estas
sesiones externas. Siguiente prioridad: comparar en desarrollo un detector
basado en distancia de características de MobileNet antes de más entrenamiento.
Sus referencias se construirían solo con train; sus parámetros y umbral se
elegirían en la sesión interna y después se evaluaría en la externa. Esto
permitirá comprobar si la representación separa mejor los desconocidos que
la puntuación softmax. No garantiza mejora y no fue ejecutado aquí.

Ampliar negativos con pictogramas ajenos difíciles y nuevas condiciones de
captura sigue pendiente. La configuración actual no justifica afirmar que se
cumple el objetivo final de rechazo.
