# Lectura de los entrenamientos de diez clases

Se completaron seis rondas por arquitectura. Cada ronda utiliza 1200 imágenes para aprender, 300 para seleccionar la época y 300 para evaluar al terminar. s007 y desconocidos no participaron.

Los resultados son de desarrollo: se usan para comparar procedimientos y no sustituyen la prueba final. La división interna es un holdout fijo rotativo, no una búsqueda exhaustiva anidada de parámetros.

## Cómo leer los gráficos

En epoch_curves.png: la pérdida interna decide la parada; la exactitud indica el porcentaje de aciertos; el tercer panel muestra aciertos y errores sobre las 300 imágenes internas. La línea discontinua marca la época guardada y la otra línea la última ejecutada. Una línea de puntos separa el ajuste fino en MobileNet.

Los aciertos de entrenamiento se acumulan con aumentos y pesos que cambian durante la época. No equivalen a evaluar después todas las imágenes con un único checkpoint.

Cada época realiza 38 ajustes (37 lotes de 32 y uno de 16). El paso indicado para la mejor época es su último paso de entrenamiento, antes de medir validación. No se seleccionó el modelo usando la sesión externa por época.

## Resultados y decisiones por ronda

### CNN

Exactitud externa promedio: 40.33%. Desviación entre rondas: 18.80 puntos porcentuales. Esta desviación no es un intervalo de confianza.

- Ronda 1: validación interna s002, evaluación externa s001. Época guardada **2**, paso **76**; ejecutadas **8** épocas (304 pasos). Pérdida interna mínima 2.2808, 49 aciertos y 251 errores internos. Exactitud externa **16.33%** (49/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_01/cnn/epoch_curves.png).
- Ronda 2: validación interna s003, evaluación externa s002. Época guardada **13**, paso **494**; ejecutadas **19** épocas (722 pasos). Pérdida interna mínima 1.9735, 123 aciertos y 177 errores internos. Exactitud externa **41.00%** (123/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_02/cnn/epoch_curves.png).
- Ronda 3: validación interna s004, evaluación externa s003. Época guardada **13**, paso **494**; ejecutadas **19** épocas (722 pasos). Pérdida interna mínima 1.0974, 207 aciertos y 93 errores internos. Exactitud externa **30.67%** (92/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_03/cnn/epoch_curves.png).
- Ronda 4: validación interna s005, evaluación externa s004. Época guardada **20**, paso **760**; ejecutadas **26** épocas (988 pasos). Pérdida interna mínima 1.5192, 185 aciertos y 115 errores internos. Exactitud externa **73.00%** (219/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_04/cnn/epoch_curves.png).
- Ronda 5: validación interna s006, evaluación externa s005. Época guardada **6**, paso **228**; ejecutadas **12** épocas (456 pasos). Pérdida interna mínima 1.8836, 113 aciertos y 187 errores internos. Exactitud externa **36.67%** (110/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_05/cnn/epoch_curves.png).
- Ronda 6: validación interna s001, evaluación externa s006. Época guardada **10**, paso **380**; ejecutadas **16** épocas (608 pasos). Pérdida interna mínima 2.0993, 125 aciertos y 175 errores internos. Exactitud externa **44.33%** (133/300). Motivo: desde_cero: Paciencia agotada sin reducir val_loss. [Gráfico](fold_06/cnn/epoch_curves.png).

## Límites de esta comparación

Las seis rondas comparten datos de entrenamiento. No se deben interpretar como seis experimentos estadísticamente independientes. Las semillas son 42 a 47, iguales para ambas arquitecturas en cada ronda. No se realizó búsqueda exhaustiva de hiperparámetros.

Alcanzar el máximo de épocas no demuestra convergencia. Los modelos por ronda no son automáticamente un modelo final entrenado con todas las imágenes. No se reemplazó el modelo seleccionado por Gradio. El siguiente paso es revisar el procedimiento elegido y definir su entrenamiento definitivo, la calibración del rechazo y la evaluación final reservada.

Los identificadores de las carpetas usan fecha y hora UTC.
