# Modelo único MobileNet192 para la aplicación

Estado del documento: **vigente**. Prueba final s007 completada; ver [métricas y conclusiones](prueba_final_s007.md). La descripción siguiente conserva el protocolo y los resultados internos previos.

Identificador: mobilenet_app_192_20261020. La configuración activa está en
`config/application.json`; `config/project.json` describe el dataset histórico.
Se entrena un modelo nuevo desde
ImageNet; no se selecciona el checkpoint ganador de una ronda de CV.

Entrenamiento: s001–s005 y s008, 1.800 conocidas. Validación interna: s006,
300 conocidas para elegir época, más 50 desconocidas para calibrar. No se usa
s007. Son 57 lotes por época: 56 de 32 y uno de 8. Semilla 42. Hasta 20 épocas
de clasificador congelado con Adam 0,001 y paciencia 6; hasta 40 de ajuste fino
con Adam 0,00001 y paciencia 4. Solo las últimas 30 capas de base, BatchNormalization
congelada. Se selecciona menor val_loss entre ambas etapas.

Se usan los PNG de 192 generados desde originales EXIF/RGB/LANCZOS, sin
normalización externa. Se verifican hashes de los 2.100 originales y PNG correspondientes.
No se sobrescriben modelos previos ni manifiestos históricos.

El detector construye 1.800 referencias exclusivamente conocidas de train. La
similitud promedia cinco vecinos. Se busca el mínimo umbral que rechace al menos
40/50 desconocidas internas (80 %) sin rechazar más de 3/300 conocidas (1 %).
Si no existe, la selección anterior se conserva y se informa que es inviable.
Si es viable, se guardan checkpoint, referencias, orden de clases y hashes compatibles antes
de activar. Se conserva un respaldo de la configuración anterior y se revierte ante
un fallo de carga del paquete seleccionado.

Las métricas de s006 son internas: se comparten la selección de época y la
calibración. No son una prueba independiente ni heredan el 93,52 % de clasificación
ni el 75 % de rechazo de CV. El procedimiento se congeló antes de evaluar s007,
sin usarla para ajustes. Los negativos son principalmente objetos y escenas.

La vista previa toma el tamaño de config/application.json; foto y cámara ya usan
ese tamaño para inferencia. Tras cambiar selección hay que reiniciar el servidor
porque la carga se cachea. La configuración general histórica de 128 se conserva.

```powershell
uv run python scripts/train_app_192.py --activate
uv run python scripts/verify_app_192.py
```

El primer comando crea artefactos nuevos y no debe repetirse sobre el mismo
identificador. Consultar epochs.csv, stopping.json, metrics.json, calibration.json,
verification.json y progress.json bajo `reports/mobilenet_app_192_20261020/`.
La prueba local de foto/RPC no sustituye la prueba física en el celular.

## Resultado y estado actual

Entrenamiento finalizado y paquete activado. El modelo obtuvo 278/300 conocidas
correctas (92,67 %) en validación interna s006. El umbral de similitud propio es
0,8024037084471637: rechaza 40/50 desconocidas (80 %) y 2/300 conocidas (0,67 %).
Una de las dos conocidas rechazadas estaba bien clasificada; quedaron 277/300
correctas aceptadas (92,33 %). Se ejecutaron 20 épocas de cabeza y 40 de ajuste
fino, alcanzando el máximo, sin demostrar convergencia. El checkpoint elegido
está documentado en stopping.json.

Se verificaron las diez clases por foto, una desconocida rechazada, resolución
192 en vista previa e inferencia, y confirmación de tres fotogramas en la RPC de
cámara con una imagen de desarrollo. La API HTTP real reconoció Agua y devolvió
una imagen de 192. Estas son comprobaciones de integración, no nuevas métricas.
No se ha probado todavía la cámara física del celular con este paquete.
63 pruebas automatizadas aprobadas. La aplicación local está en
`http://127.0.0.1:7860`. El servidor nuevo carga el paquete de 192; s007 no se
utilizó durante este entrenamiento. El modelo de 128 y su configuración previa
permanecen respaldados.
