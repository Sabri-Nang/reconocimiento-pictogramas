# Próxima mejora del entrenamiento y conservación de archivos

Estado del documento: **vigente** como plan; sus resultados descritos son
históricos o de desarrollo según la sección.

## Diagnóstico

El mejor experimento de MobileNet en validación cruzada obtuvo 1441/1800
aciertos (80,06 %). Por distancia: corta 417/464 (89,87 %), media 742/860
(86,28 %) y larga 282/476 (59,24 %). Fuente:
`reports/cv10_mobilenet_extend_20261018/improvement.json`.
Son resultados de desarrollo utilizados para tomar decisiones, no una prueba
final independiente. Tampoco son la exactitud demostrada del modelo único de
la aplicación: ese modelo obtuvo 237/300 (79 %) en su validación interna s006.

Los resultados sugieren investigar el tamaño de la tarjeta en la imagen y la
variación entre sesiones. No demuestran por sí solos que aumentar resolución
resuelva los errores. El rechazo de desconocidos también requiere revisión:
la regla conservadora de similitud rechazó 166/250 desconocidos (66,4 %) y
14/1800 conocidos (0,78 %) en desarrollo. Es una evaluación distinta de la
exactitud de clasificación y requiere su propia calibración.

## Orden recomendado

1. Conservar el experimento de referencia, sus particiones y su modelo. Revisar
   errores de tarjetas lejanas y fallos de localización en video por separado:
   el detector geométrico de tarjetas y el clasificador son etapas distintas.
2. Capturar nuevas sesiones de desarrollo representativas del celular real,
   con otras condiciones de fondo, iluminación, distancia y orientación.
   Usar identificadores nuevos disponibles posteriores a s007; reservar s007
   exclusivamente para la prueba final. Dos sesiones nuevas permiten separar
   mejor ampliación de entrenamiento y calibración, aunque no son requisito
   para comenzar la comparación de resolución. Como punto de partida, mantener
   30 imágenes por clase y sesión, equilibrando distancias y evitando ráfagas
   casi idénticas. Agregar también pictogramas fuera de las diez clases para
   estudiar desconocidos, con separación por sesión.
3. Comparar primero MobileNet a 128 y 192 píxeles con las seis sesiones
   actuales y las mismas rondas externas, sesiones de parada temprana,
   semilla y presupuesto de entrenamiento. Generar 192 desde los originales,
   nunca ampliando los PNG de 128. Guardar preparaciones y experimentos en
   rutas diferentes. No hace falta repetir ahora todos los experimentos CNN.
   Comparar aciertos por sesión, clase y distancia, pérdida y latencia en la
   misma máquina. No seleccionar épocas mediante la sesión externa.
4. Incorporar las nuevas sesiones mediante un protocolo escrito antes del
   siguiente experimento, manteniendo todas las imágenes de una sesión en
   un mismo rol por ronda. Toda sesión usada para elegir cambios pasa a ser
   de desarrollo. La comparación 128/192 inicial aísla el efecto de resolución;
   una comparación posterior con más capturas estudia el efecto de los datos.
5. Elegir la configuración considerando exactitud y velocidad. Preparar un
   modelo para la aplicación y recalibrar similitud con datos representativos
   separados del entrenamiento. Los umbrales y referencias actuales no se
   transfieren automáticamente a otro modelo o resolución.
6. Congelar modelo, preprocesamiento, referencias y umbral. Evaluar s007 una
   sola vez al final, informando métricas por clase y rechazo de desconocidos.

192×192 contiene 2,25 veces más píxeles que 128×128: puede conservar más detalle,
pero no garantiza más exactitud ni implica exactamente 2,25 veces más tiempo.
Si se prueba CNN después, controlar también su capacidad: cambiar resolución
con una capa Flatten puede aumentar los parámetros del clasificador.

No se ha iniciado ningún entrenamiento ni cambiado la resolución de la
aplicación como parte de esta revisión.

## Política del repositorio

Conservar en Git código, pruebas, configuración, documentación, pyproject.toml,
uv.lock, metadatos de captura y evidencia de experimentos: protocolos,
particiones, historiales, predicciones, métricas y gráficos de resultados.
Los experimentos fallidos también justifican decisiones; no borrarlos.

Conservar localmente, fuera del seguimiento de Git: originales y derivados
bajo data/raw, data/processed y data/splits; modelos entrenados; .venv;
cachés Python; registros .log; progreso transitorio; respaldos de preparación;
hojas de contacto de revisión visual; capturas de comprobación de cámara;
.runtime (credenciales) y .gradio (certificados generados).

Quitar del seguimiento las hojas de contacto ya versionadas no borra sus
copias locales ni las elimina del historial anterior de Git. No se reescribe
el historial. Los datos y modelos ignorados necesitan un respaldo separado:
un clon del repositorio no contiene esos artefactos.

Los informes antiguos de cinco clases y auditorías parciales son históricos;
para el conjunto completo usar reports/dataset_10_audit y los experimentos
cv10. No interpretar los informes anteriores como el estado actual.
