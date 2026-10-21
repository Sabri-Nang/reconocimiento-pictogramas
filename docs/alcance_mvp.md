# Alcance del MVP

Estado del documento: **mixto**. El alcance inicial es histórico; las secciones
de actualización describen decisiones vigentes o de desarrollo. Consultar
[estado actual](estado_actual.md) antes de ejecutar comandos.

## Propósito

Desarrollar una aplicación web local que reciba la imagen de un pictograma y
muestre la categoría predicha y su nivel de confianza.

Cuando la predicción no alcance un nivel mínimo de certeza, la aplicación deberá
mostrar el mensaje "Pictograma no reconocido".

## Estado del dataset

El desarrollo comenzó con cinco clases: agua, comer, baño, mamá y dolor.

Después de validar el proceso de recolección se incorporaron ayuda, jugar, sí,
no y papá. El dataset actual contiene las diez categorías previstas para el MVP,
con las sesiones `s001` a `s006` completas. La sesión `s007`, reservada para la
prueba final, permanece pendiente.

Los modelos entrenados durante el piloto de cinco clases deben volver a
entrenarse antes de considerarlos compatibles con el dataset ampliado.

## Clases del modelo

El modelo reconocerá diez categorías:

1. Agua
2. Comer
3. Ayuda
4. Dolor
5. Baño
6. Jugar
7. Sí
8. No
9. Mamá
10. Papá

## Flujo principal

1. El usuario carga una imagen JPEG o PNG.
2. La aplicación convierte la imagen a RGB.
3. La imagen se redimensiona a 128 por 128 píxeles.
4. El modelo calcula la probabilidad correspondiente a cada clase.
5. Se selecciona la categoría con mayor probabilidad.
6. El detector de aplicación compara características con cinco vecinos conocidos
   de entrenamiento y obtiene una similitud (no una probabilidad).
7. Si la similitud supera el umbral calibrado para ese modelo, se muestra la
   categoría; si no, se informa «Pictograma no reconocido». La puntuación de
   clase se muestra separada de la similitud.

## Criterios de aceptación

- Reconocer las diez clases definidas.
- Alcanzar al menos 70 % de exactitud global en el conjunto de prueba.
- Informar precisión, recall y F1 para cada clase.
- Generar una matriz de confusión.
- Mantener el conjunto de prueba separado del entrenamiento y del ajuste.
- Procesar correctamente imágenes JPEG y PNG.
- Rechazar archivos inválidos.
- Mostrar "Pictograma no reconocido" cuando no se alcance el umbral.
- Poder instalar y ejecutar el proyecto siguiendo el README.

El 70 % de exactitud global es el mínimo académico inicial. También se revisarán
las métricas individuales para detectar clases que presenten un rendimiento bajo.

## Datos desconocidos

"Desconocido" no será inicialmente una de las diez clases del modelo.

Se reunirá un conjunto adicional de imágenes negativas para:

- medir cuántas imágenes ajenas son clasificadas incorrectamente;
- seleccionar un umbral de confianza;
- evaluar si posteriormente conviene entrenar una clase desconocida explícita.

El umbral se ajustará usando datos de validación. El conjunto de prueba no se
utilizará para tomar esta decisión.

## Tecnologías

- Python 3.11.
- uv para dependencias y entorno virtual.
- TensorFlow y Keras para entrenamiento e inferencia.
- Pillow para la carga y transformación inicial de imágenes.
- NumPy y Pandas para procesamiento y registro de resultados.
- scikit-learn para métricas de evaluación.
- Matplotlib y Seaborn para gráficos.
- Gradio para la interfaz web local.
- Pytest para pruebas automatizadas.
- Git y GitHub para control de versiones.

## Fuera del alcance

La primera versión no incluirá:

- captura directa mediante ESP32-CAM;
- reproducción de audio o síntesis de voz;
- API remota;
- despliegue en la nube;
- aplicación móvil nativa;
- construcción de frases con varios pictogramas;
- utilización clínica sin supervisión o validación profesional.

Estas funciones podrán agregarse después de validar el clasificador.

## Entregables

- Conjunto de imágenes organizado y documentado.
- Scripts reproducibles para preparar los datos.
- Modelo base CNN.
- Modelo basado en MobileNetV3-Small.
- Comparación de modelos.
- Evaluación sobre imágenes no utilizadas durante el entrenamiento.
- Interfaz local desarrollada con Gradio.
- Documentación de instalación, entrenamiento y uso.

## Selección de aplicación de octubre de2026

Se prepara un MobileNet único de diez clases con s001-s005 para entrenamiento,
s006 para parada y calibración conservadora de rechazo, y s007 reservada.
Las referencias son vectores de entrenamiento; no incluyen validación. La
interfaz verifica checkpoint, referencias y orden de clases antes de predecir.
Las métricas de s006 son internas; no confirman criterios de prueba final.

## Extensión solicitada: cámara del navegador

Se incorpora una pestaña de cámara en vivo, también accesible desde navegador
móvil mediante HTTPS. La cámara trasera se solicita como preferencia; el
navegador y el dispositivo determinan su disponibilidad y requieren permiso.
Se procesan fotogramas a intervalos nominales de0,5 segundos; no es video
clasificado a30fps ni se garantiza esa frecuencia en cualquier computadora/red.

Un contorno cuadrilateral activa la clasificación del fotograma completo.
La búsqueda geométrica no es un detector de objetos entrenado: puede perder
tarjetas o detectar otros rectángulos. Se conserva el encuadre completo para
no cambiar el preprocesamiento/modelo/umbral calibrados. No se atribuye clase
a una región recortada ni se afirma localizar múltiples tarjetas correctamente.

La palabra aparece como globo sobre el resultado anotado tras tres predicciones
consecutivas aceptadas de la misma clase y ubicación similar. Si se pierde la
tarjeta, cambia la clase, hay rechazo o error, se retira la palabra y se vuelve
a confirmar. Esta estabilidad no convierte una clasificación errónea repetida
en correcta. La vista móvil actual usa un video único con superposición de coordenadas y palabra.

Los fotogramas se procesan en memoria y no se agregan al dataset; Gradio puede
crear archivos temporales de transporte. No se entrena ni usa s007. No se
modificaron los pesos ni el umbral. Falta evaluar video real y acceso móvil
HTTPS en el dispositivo del usuario; las pruebas por API no sustituyen eso.

Corrección de estabilidad de video: se toleran hasta15 segundos entre
fotogramas aceptados de la misma clase y ubicación similar. El antiguo
límite3s reiniciaba la confirmación cuando la red o inferencia demoraban4s.
La interfaz muestra el progreso1/3 y2/3 y la clase candidata. Se mantienen
las tres observaciones y el mismo umbral; no se rebaja el rechazo.
Se comprobó con la cola real de streaming local, no con cámara móvil.

Corrección por captura móvil con tarjeta no detectada: se añade búsqueda por
superficie clara rectangular como respaldo al borde. La tarjeta de la captura
proporcionada no se detectaba por bordes y sí con el respaldo. Es una
comprobación de integración, no una evaluación general del detector.

La cámara móvil actual usa HTML/getUserMedia y RPC autenticada de Gradio,
con un único fotograma pendiente. Sustituye el componente webcam/cola de
streaming anterior; evita el estado nativo «Esperando» y el desfase de dos
paneles. El navegador dibuja las coordenadas sobre el video; al detener
cancela la captura y descarta las respuestas de la sesión anterior. La
clasificación y el umbral conservan su carácter experimental.

## Actualización del modelo de aplicación192

El paquete mobilenet_app_192_20261020 está seleccionado con referencias y umbral propios. Véase [modelo único192](modelo_aplicacion_192.md) para particiones, métricas internas ypruebas. La comprobación local de laRPC no equivale a prueba física de video. s007 sigue reservada.
