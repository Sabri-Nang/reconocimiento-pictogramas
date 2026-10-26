# Experimento de resolución: 128 frente a 192

Estado del documento: **desarrollo**.

Referencia: cv10_s008_128_20261019. Candidato: cv10_s008_192_20261019.
Se generan 2.100 PNG RGB de 192 directamente de los originales, corrigiendo EXIF y
redimensionando con LANCZOS. No se amplían los PNG128. Originales, derivados128,
particiones históricas y aplicación se conservan. Configuración específica:
config/cv_s008_192.json; no se cambia config/project.json.

Siete rondas: s001-s006 y s008; mismas sesiones externas/internas y semillas
por ronda del 128. Cinco sesiones entrenan 1.500 imágenes; una interna de 300 elige
checkpoint y parada por val_loss; una externa300 evalúa al terminar. Batch32,
47 pasos por época; mismos aumentos de entrenamiento. s007 queda excluida.

CNN compacta desde cero: Adam 0,001, máximo 30 épocas, paciencia 6. MobileNetV3Small
ImageNet: hasta 20 épocas de cabeza con base congelada, Adam 0,001, paciencia 6;
hasta 40 de ajuste fino con Adam 0,00001, últimas 30 capas, BatchNormalization
congelada y paciencia4. Se reinicia cada ronda y se selecciona el mejor checkpoint
interno entre etapas. No se ajustan reglas usando resultados externos.

La CNN conserva Flatten: al recibir mapas mayores aumenta los parámetros de su
capa densa. Su comparación mide resolución y capacidad conjuntamente; no se
presentará como un efecto puro de resolución con idéntico número de parámetros.
MobileNet mantiene promedio global. Se registrarán parámetros de ambos modelos.

Se recalibra kNN con cinco vecinos exclusivamente de entrenamiento de cada
MobileNet; umbral mínimo para rechazar70% de desconocidas internas, congelado
antes de la externa. Se evaluarán 300 desconocidas y 2.100 conocidas externas,
con resultados separados. No se hereda ningún umbral del modelo128. La sesión
interna conocida se comparte con parada temprana: calibración no independiente.
Los negativos son principalmente objetos/escenas; no representan todo pictograma
ajeno. Los resultados son desarrollo adaptativo, no prueba final.

La comparación verifica las mismas muestras y roles. Informa exactitud, F1,
errores corregidos/nuevos, clase, sesión y distancia. Registra tiempos totales y
por época: la parada temprana puede cambiar cantidad de épocas ejecutadas.
El benchmark de inferencia se realiza después del entrenamiento, con cuatro
checkpoints de fold 1 (CNN/MobileNet a 128/192), lote de 1, tres calentamientos y 20
repeticiones en CPU local. Informa mediana ypercentil95. Mide llamada al
clasificador y salida numpy; no carga de modelo, kNN, red ni cámara. Se mide
preprocesamiento por separado. No equivale a latencia móvil de extremo a extremo.

## Ejecución

```powershell
uv run python scripts/prepare_resolution_192.py
uv run python scripts/run_resolution_192.py
```

La preparación se ejecuta una sola vez. El segundo comando encadena entrenamiento,
rechazo, benchmark y comparación, con estado en
reports/resolution_192_20261019/pipeline.json. Reanuda rondas de entrenamiento
terminadas; una evaluación de rechazo parcial requiere revisión antes de reintentar
para conservar evidencia. No borrar directorios ni sobrescribir informes anteriores.

Resultados previstos: reports/cv10_s008_192_20261019,
reports/cv10_s008_192_unknown_knn_20261019 y
reports/resolution_192_20261019/comparison.json, comparison.png y lectura_resultados.md.
No se activa automáticamente un modelo en la aplicación. La selección y calibración
del modelo único se resolverán después de comparar; s007 seguirá reservada hasta
congelar todo el procedimiento.
