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

## Experimento CNN con promedio global

Se cambia únicamente `Flatten` por `GlobalAveragePooling2D`; la capa Dense64,
Dropout0.3, convoluciones, aumentos, Adam0.001, lotes32, semillas, máximo30
épocas y paciencia6 se conservan. Cada ronda comienza desde cero. Se compara
con la CNN de `cv10_20261018_000712`, sin consultar s007. La selección de
checkpoint sigue dependiendo de la pérdida interna, no del acierto externo.
La mejora es una hipótesis: reducir parámetros también puede reducir capacidad.

```powershell
uv run python scripts/train_cross_validation.py --config config/cv_cnn_gap.json --run-id cv10_cnn_gap_20261018
uv run python scripts/describe_cv_results.py --run-id cv10_cnn_gap_20261018
uv run python scripts/compare_cv_experiments.py --architecture cnn --reference cv10_20261018_000712 --candidate cv10_cnn_gap_20261018
```

Para continuar una ejecución interrumpida, usar el mismo identificador con
`--resume`. Los gráficos y métricas quedan en `reports/cv10_cnn_gap_20261018/`;
los checkpoints locales, en `models/cv10_cnn_gap_20261018/`.

## Experimento CNN con tasa de aprendizaje menor

Se conserva la arquitectura original con Flatten y se cambia únicamente
la tasa inicial de Adam: de 0.001 a 0.0003. No se incorpora reducción
automática de tasa ni se modifican los aumentos, lotes, semillas, máximo30
épocas, paciencia6 o criterio val_loss. Se reinicia la CNN en cada ronda.
La referencia es cv10_20261018_000712; no la variante de promedio global.

```powershell
uv run python scripts/train_cross_validation.py --config config/cv_cnn_lr0003.json --run-id cv10_cnn_lr0003_20261018
uv run python scripts/describe_cv_results.py --run-id cv10_cnn_lr0003_20261018
uv run python scripts/compare_cv_experiments.py --architecture cnn --reference cv10_20261018_000712 --candidate cv10_cnn_lr0003_20261018
```

Los resultados son desarrollo adaptativo. s007 y desconocidos siguen excluidos.
Una tasa menor puede requerir más épocas, pero este experimento conserva el
mismo máximo para evaluar el cambio dentro del presupuesto original.

## Rechazo de desconocidos por ronda

```powershell
uv run python scripts/evaluate_unknown_cv.py --source-run cv10_mobilenet_extend_20261018 --run-id cv10_unknown_20261018
```

Se cargan los seis checkpoints ya seleccionados de MobileNet, sin entrenar ni
cambiar sus pesos. En cada ronda unknown sigue los roles de sesión interna y
externa de conocidas. Esta es una extensión explícita del protocolo de desarrollo:
no reemplaza la referencia fija que reserva s006 para calibración del modelo final.
s007 nunca se carga. Se comprueban hashes de los250 unknown auditados, ausencia
de duplicados exactos y separación de sesiones/rutas/hashes por ronda.

La puntuación de rechazo es la máxima salida softmax. La regla fijada antes
de evaluar es: elegir el menor umbral que rechace al menos70% de unknown de
la sesión interna. Se rechaza si puntuación<=umbral. Esto minimiza también
los conocidos rechazados bajo esa restricción; no garantiza una tasa externa.
Se guarda calibration.json antes de cargar las imágenes externas.

La misma sesión interna conocida ya eligió la época; sus métricas son internas,
no una evaluación independiente. Con el umbral congelado se evalúa la sesión
externa: unknown rechazados y falsamente aceptados, conocidos rechazados,
conocidos correctos y aceptados sobre todos los conocidos, y exactitud entre
conocidos aceptados (denominador distinto). Se registra AUROC por ronda como
descripción de separación de puntuaciones, sin elegir con ella un umbral externo.
No se mezclan puntuaciones de modelos distintos para calibrar un umbral global.

El reporte compara las probabilidades externas conocidas con las del experimento
original y reúne1800 conocidas y250 unknown externos únicos. Incluye curvas de
calibración internas, predicciones, gráficos, protocolo y controles reproducibles.
Las rondas comparten datos; los resultados son desarrollo adaptativo, no prueba
final ni estimación independiente después de elegir el mejor modelo.

No se aplica ninguno de estos seis umbrales a la interfaz. Un modelo final
requiere calibración propia y después una prueba independiente con s007.
Los negativos actuales se concentran en objetos/fondos: conviene ampliar
pictogramas ajenos difíciles antes de afirmar rechazo general.

## Detector por vecinos de características

```powershell
uv run python scripts/evaluate_unknown_cv.py --method knn --source-run cv10_mobilenet_extend_20261018 --run-id cv10_unknown_knn_20261018
uv run python scripts/compare_rejection_results.py --reference cv10_unknown_20261018 --candidate cv10_unknown_knn_20261018
```

Este experimento conserva los seis MobileNet y sus predicciones de clase.
Extrae el vector que entra en la capa Dense final, con training=False (Dropout
y aumentos desactivados). Construye la referencia solo con las1200 conocidas
de train de cada ronda. No incorpora imágenes internas ni externas a esa
referencia. Normaliza los vectores por L2 y calcula el promedio de los cinco
mayores cosenos. La puntuación `(promedio+1)/2` está entre0 y1 y NO es una
probabilidad. Vectores nulos o no finitos producen un error explícito.

Se fijan cinco vecinos antes de consultar las sesiones externas, sin búsqueda
de k. Igual que en el detector softmax, el menor umbral que rechaza al menos70%
de unknown internos se guarda antes de cargar la sesión externa. Rechaza
puntuaciones menores o iguales al umbral. No se cambia la clase predicha.

Las referencias se guardan localmente en models/ID/fold_NN/references.npz
(ignoradas por Git). reference_manifest.json registra su hash, dimensión y
las rutas/hashes/sesiones de entrenamiento. Los gráficos y predicciones de
reports conservan por separado confianza softmax y puntuación de similitud.
La comparación verifica mismos modelos, imágenes y predicciones de clase, y
recalcula cada umbral usando únicamente las puntuaciones internas.

Se evalúa el procedimiento de desarrollo; elegir probarlo después de ver
errores previos es una decisión adaptativa. No hay prueba final independiente
ni selección automática de detector para la interfaz. s007 sigue reservada.

## Recalibración con límite de rechazo de conocidos internos

```powershell
uv run python scripts/calibrate_rejection_known_cap.py --source-run cv10_unknown_knn_20261018 --run-id cv10_unknown_knn_cap05_20261018
uv run python scripts/compare_rejection_results.py --reference cv10_unknown_knn_20261018 --candidate cv10_unknown_knn_cap05_20261018
```

Reutiliza exactamente las puntuaciones de similitud y los seis modelos/referencias
del ensayo anterior, sin nueva inferencia ni entrenamiento. Se verifica el hash
del manifiesto de desarrollo, checkpoints y archivos de referencias. En cada
ronda se calcula el mayor umbral que rechaza como máximo15 de las300 conocidas
internas(5%). Como rechazo aumenta con el umbral, maximiza también el rechazo
de unknown bajo esa restricción. No se exige70% de unknown en calibración;
70% se mantiene como objetivo de evaluación externa.

Se usa el flotante anterior a la puntuación del primer conocido que no se puede
rechazar, porque igualdad también rechaza. Los empates pueden dejar menos15
rechazados. No se usa un cuantil interpolado. El umbral se guarda antes de leer
las puntuaciones externas de esa ronda. El límite5% es interno: no garantiza
5% externo. Todas las conocidas cuentan, incluso las mal clasificadas.

El experimento nuevo conserva ambos ensayos anteriores. El comparador recalcula
las dos reglas desde las puntuaciones internas y verifica que coincidan modelos,
clases, imágenes y puntuaciones externas. No se selecciona un umbral final ni
se modifica la aplicación; s007 permanece reservada.
