# Lectura de los entrenamientos de diez clases

Se completaron seis rondas por arquitectura. Cada ronda utiliza 1200 imágenes para aprender, 300 para seleccionar la época y 300 para evaluar al terminar. s007 y desconocidos no participaron.

Los resultados son de desarrollo: se usan para comparar procedimientos y no sustituyen la prueba final. La división interna es un holdout fijo rotativo, no una búsqueda exhaustiva anidada de parámetros.

## Cómo leer los gráficos

En epoch_curves.png: la pérdida interna decide la parada; la exactitud indica el porcentaje de aciertos; el tercer panel muestra aciertos y errores sobre las 300 imágenes internas. La línea discontinua marca la época guardada y la otra línea la última ejecutada. Una línea de puntos separa el ajuste fino en MobileNet.

Los aciertos de entrenamiento se acumulan con aumentos y pesos que cambian durante la época. No equivalen a evaluar después todas las imágenes con un único checkpoint.

Cada época realiza 38 ajustes (37 lotes de 32 y uno de 16). El paso indicado para la mejor época es su último paso de entrenamiento, antes de medir validación. No se seleccionó el modelo usando la sesión externa por época.

## Resultados y decisiones por ronda

### CNN

Exactitud externa promedio: 25.17%. Desviación entre rondas: 18.14 puntos porcentuales. Esta desviación no es un intervalo de confianza.

- Ronda 1: validación interna s002, evaluación externa s001. Época guardada **9**, paso **342**; ejecutadas **15** épocas (570 pasos). Pérdida interna mínima 2.1125, 71 aciertos y 229 errores internos. Exactitud externa **26.67%** (80/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_01/cnn/epoch_curves.png).
- Ronda 2: validación interna s003, evaluación externa s002. Época guardada **8**, paso **304**; ejecutadas **14** épocas (532 pasos). Pérdida interna mínima 2.2108, 48 aciertos y 252 errores internos. Exactitud externa **13.00%** (39/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_02/cnn/epoch_curves.png).
- Ronda 3: validación interna s004, evaluación externa s003. Época guardada **15**, paso **570**; ejecutadas **21** épocas (798 pasos). Pérdida interna mínima 0.9284, 183 aciertos y 117 errores internos. Exactitud externa **34.33%** (103/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_03/cnn/epoch_curves.png).
- Ronda 4: validación interna s005, evaluación externa s004. Época guardada **26**, paso **988**; ejecutadas **30** épocas (1140 pasos). Pérdida interna mínima 1.1185, 169 aciertos y 131 errores internos. Exactitud externa **56.33%** (169/300). Motivo: desde_cero: Límite de épocas alcanzado. [Gráfico](fold_04/cnn/epoch_curves.png).
- Ronda 5: validación interna s006, evaluación externa s005. Época guardada **2**, paso **76**; ejecutadas **8** épocas (304 pasos). Pérdida interna mínima 2.2990, 35 aciertos y 265 errores internos. Exactitud externa **10.00%** (30/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_05/cnn/epoch_curves.png).
- Ronda 6: validación interna s001, evaluación externa s006. Época guardada **1**, paso **38**; ejecutadas **7** épocas (266 pasos). Pérdida interna mínima 2.3025, 17 aciertos y 283 errores internos. Exactitud externa **10.67%** (32/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_06/cnn/epoch_curves.png).

## Límites de esta comparación

Las seis rondas comparten datos de entrenamiento. No se deben interpretar como seis experimentos estadísticamente independientes. Las semillas son 42 a 47, iguales para ambas arquitecturas en cada ronda. No se realizó búsqueda exhaustiva de hiperparámetros.

Alcanzar el máximo de épocas no demuestra convergencia. Los modelos por ronda no son automáticamente un modelo final entrenado con todas las imágenes. No se reemplazó el modelo seleccionado por Gradio. El siguiente paso es revisar el procedimiento elegido y definir su entrenamiento definitivo, la calibración del rechazo y la evaluación final reservada.

Los identificadores de las carpetas usan fecha y hora UTC.
