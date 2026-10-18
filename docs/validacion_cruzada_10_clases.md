# Entrenamiento cruzado de diez pictogramas

## Qué se compara

La CNN aprende sus pesos desde cero. MobileNetV3-Small también es una CNN,
pero parte de pesos ImageNet: primero se entrena su clasificador y luego las
últimas 30 capas de la base con BatchNormalization congelada.

Se comparan procedimientos con parámetros prefijados. Las épocas máximas,
las tasas de aprendizaje, los aumentos y las reglas de parada se fijan antes
de evaluar las sesiones externas. No se busca exhaustivamente hiperparámetros.
La configuración está en config/cross_validation.json.

## Seis rondas

En cada ronda hay cuatro sesiones de entrenamiento (1200 imágenes), una de
validación interna (300) y una externa (300). La externa es s001,s002,...,s006
respectivamente y la interna es la siguiente sesión, con retorno a s001.
Cada sesión es externa una vez e interna una vez. Ninguna ronda incluye s007.
Se generan manifiestos independientes dentro de reports/cv10_*/fold_*/.

La validación interna se consulta al final de cada época para elegir la versión
del modelo y parar. La sesión externa se carga únicamente después de guardar
la versión elegida y nunca se utiliza para elegir la época de esa ronda.
Las puntuaciones externas se usarán para seleccionar el procedimiento, por lo
que son resultados de desarrollo; la comprobación final se reserva para s007.

## Lotes, pasos y épocas

Cada época recorre las MISMAS 1200 imágenes de entrenamiento. Al comenzar cada
recorrido se mezcla su orden. No se mezclan todas otra vez en cada paso.
Se toman 37 lotes de 32 y un último lote de 16: 38 pasos por época.
Cada paso predice, calcula la pérdida y realiza un ajuste de pesos.
Los aumentos aleatorios pueden cambiar la apariencia de la misma foto.
Al pasar de época se conservan los pesos ajustados; al cambiar de ronda se
reinicia la CNN o se vuelve a ImageNet para MobileNet, sin heredar aprendizajes.

## Parada y selección de época

CNN: hasta 30 épocas, Adam 1e-3, paciencia 6. MobileNet: hasta 20 épocas con
base congelada (Adam 1e-3, paciencia 6), y hasta 10 de ajuste fino (Adam 1e-5,
paciencia 4). No hay reducción automática de tasa adicional.
El checkpoint final es el menor val_loss entre todas las épocas y etapas.
Se para si no disminuye val_loss durante la paciencia fijada o se alcanza
el límite de épocas. La parada se decide por época, no por un paso aislado.
La época guardada puede ser anterior a la última ejecutada. Si se llega al
límite, no se debe afirmar que el modelo haya convergido.
La pérdida penaliza también predicciones incorrectas hechas con mucha
confianza; dos épocas con igual exactitud pueden tener pérdidas distintas.

## Gráficos y archivos por entrenamiento

- epochs.csv: pérdida, exactitud, aciertos/errores de validación y paso global
  para cada época; 1 indica la primera época (incluye etapas de MobileNet).
- epoch_curves.png: tres paneles, pérdida, exactitud y cantidad de aciertos y
  errores internos. Línea de mejor época y separación de etapas en MobileNet.
  Se actualiza cada cinco épocas y al finalizar.
- steps.csv: paso global, época, etapa, lote y métricas ACUMULADAS dentro de
  la época, no la pérdida/precisión exclusiva de ese lote. No se decide parada
  comparando directamente estas métricas acumuladas entre lotes.
- stopping.json: época guardada, época final, etapa y motivo de detención.
- outer_predictions.csv y outer_confusion.png: evaluación externa al finalizar.
- result.json: métricas por clase, aciertos y errores de la ronda.

Las métricas de entrenamiento se acumulan con aumentos activos y pesos que
cambian a lo largo de la época. La validación se evalúa con los pesos del final
de esa época, sin aumentos ni dropout; sus valores no son mediciones idénticas.

summary.json y comparison.png comparan las seis rondas. La desviación entre
sesiones describe variabilidad; no es un intervalo de confianza, ya que las
rondas comparten datos de entrenamiento.

## Ejecutar

```powershell
uv run python scripts/train_cross_validation.py
```

Cada ejecución crea carpetas nuevas en reports/ y models/. Los checkpoints
están ignorados por Git. No reemplaza el modelo del piloto seleccionado por
Gradio, no calibra rechazo y no utiliza desconocidos. No ejecuta prueba final.
Conserva las fotos observadas como desenfocadas en la auditoría; no se excluyen
imágenes basándose en resultados de las sesiones externas.

Si se interrumpe, se puede retomar omitiendo rondas completas:

```powershell
uv run python scripts/train_cross_validation.py --resume --run-id cv10_FECHA_HORA
```

Una ronda incompleta se vuelve a entrenar desde su inicio. No se debe alterar
el dataset ni el protocolo de una ejecución al retomarla.

Para verificar las rondas completas y generar la explicación de sus paradas:

```powershell
uv run python scripts/describe_cv_results.py --run-id cv10_FECHA_HORA
```

Las semillas son 42 a 47, con la misma semilla en ambas arquitecturas de cada
ronda. Los identificadores de ejecución usan fecha y hora UTC.

## Experimento de continuación de MobileNet

`extend_mobilenet_cv.py` usa config/cv_mobilenet_extended.json. Retoma cada
checkpoint seleccionado del experimento original, con su estado Adam a 1e-5,
y ejecuta hasta 30 épocas adicionales, con paciencia 4 y las mismas sesiones.
No vuelve a entrenar la CNN ni reinicia MobileNet desde ImageNet. La época 0
es el checkpoint de referencia, evaluado únicamente con la sesión interna.
El orden de lotes se inicializa nuevamente con la semilla de esa ronda.
Se conserva el modelo anterior si no mejora la pérdida interna. Este cambio
se decide usando resultados de desarrollo y no constituye una prueba final.
