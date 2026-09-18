# Alcance del MVP

## Propósito

Desarrollar una aplicación web local que reciba la imagen de un pictograma y
muestre la categoría predicha y su nivel de confianza.

Cuando la predicción no alcance un nivel mínimo de certeza, la aplicación deberá
mostrar el mensaje "Pictograma no reconocido".

## Clases del modelo

El modelo reconocerá inicialmente diez categorías:

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
6. Si la confianza supera el umbral, se muestra la categoría y su confianza.
7. Si no supera el umbral, se informa que el pictograma no fue reconocido.

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
- aplicación móvil;
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