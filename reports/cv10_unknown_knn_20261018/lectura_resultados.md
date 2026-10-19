# Evaluación de rechazo de desconocidos con MobileNet

Se calibró un umbral por ronda usando únicamente unknown de la sesión interna. Se eligió el menor que rechaza al menos70% (incluida igualdad). Esa regla minimiza el rechazo de conocidos bajo la restricción elegida. No se fijó un umbral global de aplicación.

La sesión interna conocida ya se usó para parada temprana. Sus métricas son de calibración, no independientes. La externa no eligió el umbral de su ronda. Las rondas comparten datos y el modelo fue elegido adaptativamente durante el desarrollo. s007 no participó.

## Resultados externos agrupados

- Conocidos sin rechazo: 1441/1800 = 80.06%.
- Desconocidos rechazados: 166/250 = 66.40%.
- Desconocidos aceptados por error: 84/250.
- Conocidos rechazados: 14/1800 = 0.78%.
- Conocidos correctamente clasificados y aceptados: 1439/1800 = 79.94%.
- Exactitud entre conocidos aceptados: 80.57%. Este denominador excluye rechazados y no sustituye la exactitud sobre todos los conocidos.

## Rondas

- Ronda 1: calibración s002, externa s001, umbral 0.79829056; rechazo unknown 24/40 (60.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 228/300.
- Ronda 2: calibración s003, externa s002, umbral 0.80766273; rechazo unknown 31/40 (77.5%); rechazo conocidas 0/300; conocidas correctas aceptadas 268/300.
- Ronda 3: calibración s004, externa s003, umbral 0.80915370; rechazo unknown 29/40 (72.5%); rechazo conocidas 5/300; conocidas correctas aceptadas 223/300.
- Ronda 4: calibración s005, externa s004, umbral 0.77333348; rechazo unknown 12/40 (30.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 279/300.
- Ronda 5: calibración s006, externa s005, umbral 0.77809284; rechazo unknown 26/40 (65.0%); rechazo conocidas 0/300; conocidas correctas aceptadas 225/300.
- Ronda 6: calibración s001, externa s006, umbral 0.81041741; rechazo unknown 44/50 (88.0%); rechazo conocidas 9/300; conocidas correctas aceptadas 216/300.

## Límites y siguiente decisión

El70% solicitado es una tasa de rechazo, no un umbral0.70. Los umbrales no son probabilidades de pertenecer a las diez clases. La confianza puede ser alta en imágenes ajenas.

Los negativos actuales contienen principalmente objetos y fondos: faltan más pictogramas ajenos difíciles. No puede afirmarse rechazo general de cualquier desconocido ni cumplimiento final de hipótesis.

Si no se logra suficiente rechazo externo sin perder demasiados conocidos, comparar otro detector (por ejemplo distancia en características) o mejorar la representación de MobileNet. La regla y sus ajustes se evalúan solo en desarrollo. El modelo final debe tener su propia calibración separada antes de s007.

Este protocolo extiende a unknown la rotación de sesiones de CV; no modifica la partición fija documentada para un entrenamiento final con s006 de calibración. No se modificó selected_model.json.

## Detector evaluado y comparación

Se usó la media de similitud coseno de los cinco vecinos más cercanos entre
las1200 conocidas de train, sobre el vector que entra en la Dense final de
MobileNet. La puntuación escalada a[0,1] no es probabilidad ni sustituye la
confianza softmax registrada por separado. No se cambió la clase predicha.

Frente al umbral softmax, desconocidos rechazados:150/250(60%) a166/250(66,4%).
Conocidos rechazados:415/1800(23,06%) a14/1800(0,78%). Conocidos correctos
y aceptados:1256/1800(69,78%) a1439/1800(79,94%). El detector nuevo descarta
solo2 de los1441 aciertos originales. Para alcanzar70% de rechazo se necesitan
175/250: faltan9. El79,94% no alcanza80%; no redondear hacia arriba.

El detector protege mejor los conocidos y mejora el rechazo de desconocidos
en este desarrollo. Sin embargo, acepta347 conocidos mal clasificados frente
a129 del filtro softmax. Detectar imágenes ajenas y detectar confusiones entre
clases conocidas son tareas distintas; no se afirma mejora en todas las métricas.

La cuarta ronda rechaza solo12/40 unknown(30%), aun con AUROC cercana a1.
Es evidencia de sensibilidad del punto de corte a diferencias entre sesiones;
la separación por similitud es prometedora pero no garantiza transferencia
del umbral elegido en otra sesión. No se ajustó el umbral con la externa.

Siguiente experimento propuesto: fijar de antemano una regla de calibración
que maximice rechazo de unknown bajo un límite de rechazo de conocidos
internos (por ejemplo5%), y evaluarla con el mismo aislamiento de sesiones.
No se ejecutó en este ensayo. Será otra comparación adaptativa de desarrollo,
no validación final. Se necesitan más negativos difíciles y la prueba s007.

La aplicación y selected_model.json no se modificaron. Se verificaron los
seis archivos de referencias y modelos, las2050 predicciones externas, la
igualdad de predicciones de clase y la calibración solo interna.32 pruebas
automatizadas del código pasaron.
