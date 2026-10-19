# Analisis de errores: siete sesiones a128x128

2100 predicciones externas unicas por arquitectura. s007 no utilizada. Resultados de desarrollo.

## CNN
Aciertos: 1637/2100 (77.95%).

- Distancia corta: 478/564 (84.75%).
- Distancia larga: 365/576 (63.37%).
- Distancia media: 794/960 (82.71%).

Mismas1800 imagenes historicas: 915 antes y 1359 ahora, diferencia 444 aciertos (24.67 puntos). Mismas imagenes externas, pero cambian entrenamiento, algunas sesiones internas y presupuesto MobileNet; no aisla efecto causal de s008.

Confusiones mas frecuentes:
- no -> dolor: 32.
- agua -> ayuda: 31.
- ayuda -> agua: 26.
- ayuda -> no: 23.
- bano -> no: 21.

## MOBILENET
Aciertos: 1777/2100 (84.62%).

- Distancia corta: 533/564 (94.50%).
- Distancia larga: 373/576 (64.76%).
- Distancia media: 871/960 (90.73%).

Mismas1800 imagenes historicas: 1441 antes y 1535 ahora, diferencia 94 aciertos (5.22 puntos). Mismas imagenes externas, pero cambian entrenamiento, algunas sesiones internas y presupuesto MobileNet; no aisla efecto causal de s008.

Confusiones mas frecuentes:
- no -> dolor: 25.
- dolor -> no: 23.
- papa -> bano: 14.
- no -> ayuda: 13.
- papa -> comer: 12.

## Interpretacion
MobileNet es mejor en el conjunto agrupado; CNN supera a MobileNet en s008 (278/300 frente a242/300). No hay un ganador universal por sesion.
La principal limitacion sigue siendo distancia larga. No garantiza resolverse al aumentar resolucion.
Comparar192x192 despues manteniendo las mismas siete rondas, semillas, arquitectura y presupuestos por modelo. Generar desde originales, conservar artefactos128. No modificar la aplicacion antes de elegir y calibrar un modelo unico.
La evaluacion previa de la aplicacion en s008 (247/300) corresponde a otro modelo y particion interna; no comparar directamente con242/300 como si solo hubiese cambiado el entrenamiento con s008.
Las diferencias train/interna son descriptivas: train incluye aumentos y pesos cambiantes. No demostrar sobreajuste solo con dos exactitudes.
Los negativos nuevos solo contienen objetos/escenas; no prueban rechazo general de pictogramas ajenos.

## Parada y estabilidad

CNN agotó paciencia en cinco rondas y alcanzó el máximo de 30 épocas en dos. MobileNet alcanzó el máximo de ajuste fino en seis rondas; la séptima terminó por paciencia. El mejor checkpoint se eligió por pérdida interna, sin consultar la sesión externa. No se demuestra convergencia de todos los modelos ni se garantiza que más épocas mejoren.

Macro-F1: CNN 0,7794 y MobileNet 0,8462. Desviación de exactitud entre sesiones: 14,44 y 7,12 puntos porcentuales respectivamente; no son intervalos de confianza.
