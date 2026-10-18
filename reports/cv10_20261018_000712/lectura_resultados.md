# Lectura de los entrenamientos de diez clases

Se completaron seis rondas por arquitectura. Cada ronda utiliza 1200 imágenes para aprender, 300 para seleccionar la época y 300 para evaluar al terminar. s007 y desconocidos no participaron.

Los resultados son de desarrollo: se usan para comparar procedimientos y no sustituyen la prueba final. La división interna es un holdout fijo rotativo, no una búsqueda exhaustiva anidada de parámetros.

## Cómo leer los gráficos

En epoch_curves.png: la pérdida interna decide la parada; la exactitud indica el porcentaje de aciertos; el tercer panel muestra aciertos y errores sobre las 300 imágenes internas. La línea discontinua marca la época guardada y la otra línea la última ejecutada. Una línea de puntos separa el ajuste fino en MobileNet.

Los aciertos de entrenamiento se acumulan con aumentos y pesos que cambian durante la época. No equivalen a evaluar después todas las imágenes con un único checkpoint.

Cada época realiza 38 ajustes (37 lotes de 32 y uno de 16). El paso indicado para la mejor época es su último paso de entrenamiento, antes de medir validación. No se seleccionó el modelo usando la sesión externa por época.

## Resultados y decisiones por ronda

### CNN

Exactitud externa promedio: 50.83%. Desviación entre rondas: 31.73 puntos porcentuales. Esta desviación no es un intervalo de confianza.

- Ronda 1: validación interna s002, evaluación externa s001. Época guardada **1**, paso **38**; ejecutadas **7** épocas (266 pasos). Pérdida interna mínima 2.2990, 39 aciertos y 261 errores internos. Exactitud externa **13.67%** (41/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_01/cnn/epoch_curves.png).
- Ronda 2: validación interna s003, evaluación externa s002. Época guardada **7**, paso **266**; ejecutadas **13** épocas (494 pasos). Pérdida interna mínima 1.4514, 139 aciertos y 161 errores internos. Exactitud externa **46.33%** (139/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_02/cnn/epoch_curves.png).
- Ronda 3: validación interna s004, evaluación externa s003. Época guardada **19**, paso **722**; ejecutadas **25** épocas (950 pasos). Pérdida interna mínima 0.1433, 282 aciertos y 18 errores internos. Exactitud externa **59.67%** (179/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_03/cnn/epoch_curves.png).
- Ronda 4: validación interna s005, evaluación externa s004. Época guardada **16**, paso **608**; ejecutadas **22** épocas (836 pasos). Pérdida interna mínima 0.6745, 244 aciertos y 56 errores internos. Exactitud externa **96.33%** (289/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_04/cnn/epoch_curves.png).
- Ronda 5: validación interna s006, evaluación externa s005. Época guardada **9**, paso **342**; ejecutadas **15** épocas (570 pasos). Pérdida interna mínima 1.2099, 216 aciertos y 84 errores internos. Exactitud externa **71.00%** (213/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_05/cnn/epoch_curves.png).
- Ronda 6: validación interna s001, evaluación externa s006. Época guardada **2**, paso **76**; ejecutadas **8** épocas (304 pasos). Pérdida interna mínima 2.2312, 30 aciertos y 270 errores internos. Exactitud externa **18.00%** (54/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_06/cnn/epoch_curves.png).

### MOBILENET

Exactitud externa promedio: 74.56%. Desviación entre rondas: 11.08 puntos porcentuales. Esta desviación no es un intervalo de confianza.

- Ronda 1: validación interna s002, evaluación externa s001. Época guardada **30**, paso **1140**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.3969, 261 aciertos y 39 errores internos. Exactitud externa **71.00%** (213/300). Motivo: clasificador_congelado: Límite de épocas alcanzado; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_01/mobilenet/epoch_curves.png).
- Ronda 2: validación interna s003, evaluación externa s002. Época guardada **30**, paso **1140**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.9731, 217 aciertos y 83 errores internos. Exactitud externa **86.33%** (259/300). Motivo: clasificador_congelado: Límite de épocas alcanzado; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_02/mobilenet/epoch_curves.png).
- Ronda 3: validación interna s004, evaluación externa s003. Época guardada **29**, paso **1102**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.2451, 276 aciertos y 24 errores internos. Exactitud externa **70.33%** (211/300). Motivo: clasificador_congelado: Límite de épocas alcanzado; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_03/mobilenet/epoch_curves.png).
- Ronda 4: validación interna s005, evaluación externa s004. Época guardada **30**, paso **1140**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 0.7373, 217 aciertos y 83 errores internos. Exactitud externa **90.33%** (271/300). Motivo: clasificador_congelado: Límite de épocas alcanzado; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_04/mobilenet/epoch_curves.png).
- Ronda 5: validación interna s006, evaluación externa s005. Época guardada **22**, paso **836**; ejecutadas **22** épocas (836 pasos). Pérdida interna mínima 1.3577, 179 aciertos y 121 errores internos. Exactitud externa **64.67%** (194/300). Motivo: clasificador_congelado: Paciencia agotada sin reducir val_loss; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_05/mobilenet/epoch_curves.png).
- Ronda 6: validación interna s001, evaluación externa s006. Época guardada **28**, paso **1064**; ejecutadas **28** épocas (1064 pasos). Pérdida interna mínima 0.7925, 226 aciertos y 74 errores internos. Exactitud externa **64.67%** (194/300). Motivo: clasificador_congelado: Paciencia agotada sin reducir val_loss; ajuste_fino: Límite de épocas alcanzado. [Gráfico](fold_06/mobilenet/epoch_curves.png).

## Límites de esta comparación

Las seis rondas comparten datos de entrenamiento. No se deben interpretar como seis experimentos estadísticamente independientes. Las semillas son 42 a 47, iguales para ambas arquitecturas en cada ronda. No se realizó búsqueda exhaustiva de hiperparámetros.

Alcanzar el máximo de épocas no demuestra convergencia. Los modelos por ronda no son automáticamente un modelo final entrenado con todas las imágenes. No se reemplazó el modelo seleccionado por Gradio. El siguiente paso es revisar el procedimiento elegido y definir su entrenamiento definitivo, la calibración del rechazo y la evaluación final reservada.

Los identificadores de las carpetas usan fecha y hora UTC.
