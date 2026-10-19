# Candidato MobileNet seleccionado para la aplicación

Este es un nuevo modelo único, no uno de los seis checkpoints de CV. La
validación cruzada identificó MobileNet como mejor procedimiento:80,06%
externo agrupado sobre seis modelos. Esa cifra no es una medición de este
nuevo checkpoint ni garantiza su rendimiento en nuevas capturas.

Se entrenó desde ImageNet con1500 imágenes s001-s005. s006(300 conocidas)
eligió la época por val_loss:20 épocas de clasificador y40 de ajuste fino,
mejor época global60. Llegó al máximo; no se afirma convergencia. La etapa
fina es continua, distinta de la continuación CV desde checkpoints de10+30.

Resultado interno antes de rechazo:237/300=79%. Las referencias del detector
son exclusivamente1500 vectores de train. Regla conservadora elegida por el
usuario: menor umbral que rechaza70% de los50 unknown de s006.
Umbral de similitud:0.7831352047946099. No es probabilidad. Rechaza score<=umbral.

Calibración interna:35/50 unknown rechazados;1/300 conocido rechazado, que ya
era incorrecto;237/300 conocidos correctos y aceptados. Estos resultados
no son prueba independiente, porque s006 también eligió época y umbral.
Se necesita prueba final con s007 después de congelar el procedimiento.

La interfaz separa puntuación de clase de similitud, muestra no reconocido
cuando corresponde y limpia salidas anteriores ante entrada vacía o nueva.
Se verificaron por API local un conocido aceptado, un unknown rechazado y
entrada vacía, contra predicciones de calibración guardadas. Son comprobaciones
de integración, no otra evaluación de rendimiento.

La configuración anterior se conserva en rejection/previous_selection.json.
Modelos y referencias permanecen locales fuera de Git. No se borraron los
seis modelos experimentales. s007 no se utilizó.
