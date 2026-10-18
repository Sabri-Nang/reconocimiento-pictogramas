# Lectura de los entrenamientos de diez clases

Se completaron seis rondas por arquitectura. Cada ronda utiliza 1200 imágenes para aprender, 300 para seleccionar la época y 300 para evaluar al terminar. s007 y desconocidos no participaron.

Los resultados son de desarrollo: se usan para comparar procedimientos y no sustituyen la prueba final. La división interna es un holdout fijo rotativo, no una búsqueda exhaustiva anidada de parámetros.

## Cómo leer los gráficos

En epoch_curves.png: la pérdida interna decide la parada; la exactitud indica el porcentaje de aciertos; el tercer panel muestra aciertos y errores sobre las 300 imágenes internas. La línea discontinua marca la época guardada y la otra línea la última ejecutada. Una línea de puntos separa el ajuste fino en MobileNet.

Los aciertos de entrenamiento se acumulan con aumentos y pesos que cambian durante la época. No equivalen a evaluar después todas las imágenes con un único checkpoint.

Cada época realiza 38 ajustes (37 lotes de 32 y uno de 16). El paso indicado para la mejor época es su último paso de entrenamiento, antes de medir validación. No se seleccionó el modelo usando la sesión externa por época.

## Resultados y decisiones por ronda

### MOBILENET

Exactitud externa promedio: 80.06%. Desviación entre rondas: 8.75 puntos porcentuales. Esta desviación no es un intervalo de confianza.

- Ronda 1: validación interna s002, evaluación externa s001. Época guardada **29**, paso **1102**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.2675, 273 aciertos y 27 errores internos. Exactitud externa **76.00%** (228/300). Motivo: continuacion_ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_01/mobilenet/epoch_curves.png).
- Ronda 2: validación interna s003, evaluación externa s002. Época guardada **17**, paso **646**; ejecutadas **21** épocas (798 pasos). Pérdida interna mínima 0.8828, 224 aciertos y 76 errores internos. Exactitud externa **89.33%** (268/300). Motivo: continuacion_ajuste_fino: Paciencia agotada sin reducir val_loss. [Gráfico](fold_02/mobilenet/epoch_curves.png).
- Ronda 3: validación interna s004, evaluación externa s003. Época guardada **24**, paso **912**; ejecutadas **28** épocas (1064 pasos). Pérdida interna mínima 0.1632, 279 aciertos y 21 errores internos. Exactitud externa **74.33%** (223/300). Motivo: continuacion_ajuste_fino: Paciencia agotada sin reducir val_loss. [Gráfico](fold_03/mobilenet/epoch_curves.png).
- Ronda 4: validación interna s005, evaluación externa s004. Época guardada **30**, paso **1140**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.5025, 240 aciertos y 60 errores internos. Exactitud externa **93.00%** (279/300). Motivo: continuacion_ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_04/mobilenet/epoch_curves.png).
- Ronda 5: validación interna s006, evaluación externa s005. Época guardada **30**, paso **1140**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 1.0894, 213 aciertos y 87 errores internos. Exactitud externa **75.00%** (225/300). Motivo: continuacion_ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_05/mobilenet/epoch_curves.png).
- Ronda 6: validación interna s001, evaluación externa s006. Época guardada **29**, paso **1102**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.6260, 242 aciertos y 58 errores internos. Exactitud externa **72.67%** (218/300). Motivo: continuacion_ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_06/mobilenet/epoch_curves.png).

## Continuación desde checkpoints

La época 0 es la evaluación interna del checkpoint anterior, sin realizar ajustes. Las demás épocas y pasos son adicionales; no reinician los pesos ni Adam. El orden de lotes se vuelve a inicializar con la semilla de cada ronda. Si ninguna época adicional mejora la pérdida interna, se conserva el checkpoint de referencia. Se trata de un nuevo experimento de desarrollo, no de una ejecución nueva desde ImageNet.

## Límites de esta comparación

Las seis rondas comparten datos de entrenamiento. No se deben interpretar como seis experimentos estadísticamente independientes. Las semillas son 42 a 47, iguales para ambas arquitecturas en cada ronda. No se realizó búsqueda exhaustiva de hiperparámetros.

Alcanzar el máximo de épocas no demuestra convergencia. Los modelos por ronda no son automáticamente un modelo final entrenado con todas las imágenes. No se reemplazó el modelo seleccionado por Gradio. El siguiente paso es revisar el procedimiento elegido y definir su entrenamiento definitivo, la calibración del rechazo y la evaluación final reservada.

Los identificadores de las carpetas usan fecha y hora UTC.
