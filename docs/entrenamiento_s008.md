# Sesión s008: revisión y nuevo entrenamiento

Estado del documento: **desarrollo**.

## Evaluación previa congelada

Antes de incorporar s008 al entrenamiento se evaluó el modelo de aplicación
mobilenet_app_20261018 y su umbral original de similitud, sin recalibrar:
247/300 conocidas correctas (82,33 %), 0/300 conocidas rechazadas y 29/50
objetos o escenas desconocidas rechazadas (58 %). Se aceptaron erróneamente
21 desconocidas y se clasificaron incorrectamente 53 conocidas.
Por distancia: corta 92/100, media 85/100, larga 70/100.
Son imágenes nuevas para ese modelo, pero desde esta revisión s008 pasa a ser
desarrollo. No constituyen prueba final ni miden el flujo de video/localización.

Evidencia en reports/session_s008_review: inventory.csv, integrity.json,
visual_review.json, predictions.csv y evaluation.json. Las once hojas visuales
se conservan localmente y quedan ignoradas por Git. Revisión realizada sobre
miniaturas: algunas fotos tienen desenfoque, reflejos y escenas repetidas; no se
excluyeron muestras. No hay duplicados exactos respecto del inventario previo
s001-s006 y los hashes calculados para s008. No se certifica independencia física
ni ausencia de duplicados aproximados. Condiciones no confirmadas de metadata
permanecen sin registrar, sin inferirlas de los resultados.

## Nuevo protocolo

Configuración: config/cv_s008_128.json. Identificador: cv10_s008_128_20261019.
Sesiones: s001-s006 y s008. s007 se mantiene fuera de todo el procedimiento.
Siete rondas; en cada una, cinco sesiones entrenan (1500 imágenes), una sesión
elige época mediante val_loss (300) y una externa evalúa al terminar (300).
La externa rota una vez por sesión, con la siguiente sesión como interna.
Las mismas rondas se usan para CNN compacta y MobileNetV3-Small. Cada modelo
comienza de nuevo por ronda; MobileNet parte de pesos ImageNet.

Lotes de 32: 47 pasos por época, 46 lotes de 32 y un lote de 28. El orden de las 1.500
imágenes se mezcla al comenzar cada época; los aumentos se aplican solo a train.
CNN: Adam 0,001, máximo 30 épocas, paciencia 6. MobileNet: hasta 20 épocas de
clasificador con base congelada y Adam 0,001, luego hasta 40 de ajuste fino con
Adam 0,00001 y paciencia 4, últimas 30 capas con BatchNormalization congelada.
Se selecciona el checkpoint de menor pérdida interna entre etapas. Llegar al
máximo no prueba convergencia. El ajuste fino continuo de 40 no replica exactamente
el anterior experimento de 10 más continuación de 30; la comparación histórica no
aísla causalmente solo el efecto de nuevas imágenes.

La resolución se mantiene 128×128; 192×192 se estudiará después con un protocolo
separado. Los 300 originales nuevos se convierten con EXIF/RGB/LANCZOS a una ruta
nueva data/processed/s008_128. El manifiesto development_7sessions_128.csv y el
inventario inventory_7sessions.csv están dentro del informe de revisión. No se
sobrescriben data/splits históricos, PNG anteriores, modelos ni la selección de
la aplicación. Los hashes de los 2.100 originales conocidos se verifican al
preparar la nueva ejecución.

## Cómo se evaluará

Cada ronda genera curvas de pérdida, exactitud, aciertos y errores por época,
registro de pasos, razón de parada y matriz de confusión externa. La sesión
externa no elige épocas ni umbrales. Al finalizar se agrupan 2.100 predicciones
externas por arquitectura: exactitud, precisión/recall/F1 por clase, matriz de
confusión y dispersión entre sesiones. Comparar también las seis sesiones
históricas por separado: el nuevo promedio de siete sesiones cambia el conjunto
de evaluación y el tamaño de train. No se compara como si fuera idéntico al 80,06 %.

Las 50 unknown de s008 no son una clase ni entrenan el clasificador. Tras completar
MobileNet, la evaluación de rechazo ajusta un umbral por ronda con desconocidas
internas y lo congela antes de medir la externa. Las referencias de similitud
provienen solo de train. Las 300 unknown de desarrollo (s001-s006 y s008) producen
resultados separados de los 2.100 conocidos. La sesión interna conocida se reutiliza
para parada temprana: sus cifras de calibración no son independientes. El umbral
que obtiene 70 % interno no garantiza 70 % externo. Se informan ambos tipos de error,
particularmente desconocidos aceptados y conocidos rechazados.

Como los negativos nuevos son objetos y escenas, no se puede concluir rechazo
general de cualquier otro pictograma. Después de seleccionar el procedimiento,
un modelo único necesita referencias y calibración propias; no se traslada un
umbral de CV sin recalibrar. Solo entonces se ejecuta la prueba final s007.

## Ejecución y reanudación

```powershell
uv run python scripts/train_cross_validation.py --config config/cv_s008_128.json --run-id cv10_s008_128_20261019
uv run python scripts/train_cross_validation.py --config config/cv_s008_128.json --run-id cv10_s008_128_20261019 --resume
```

Tras terminar las siete rondas MobileNet:

```powershell
uv run python scripts/evaluate_unknown_cv.py --source-run cv10_s008_128_20261019 --run-id cv10_s008_unknown_knn_20261019 --method knn
```

No activar automáticamente el modelo resultante en la aplicación. Mantener
los informes anteriores para futuras conclusiones y señalar desarrollo adaptativo.

## Resultados completos y decisión siguiente

Las siete rondas finalizaron. CNN acertó 1637/2100 (77,95 %) y MobileNet
1.777/2.100 (84,62 %). Sobre las mismas 1.800 fotos históricas: CNN 1.359 frente a 915
anteriores; MobileNet 1.535 frente a 1.441. Cambian datos de entrenamiento, algunas sesiones
internas y el presupuesto MobileNet, por lo que no se atribuye causalmente toda
la diferencia a s008. CNN supera a MobileNet en la sesión s008 externa (278/300
frente a242/300), aunque MobileNet es mejor globalmente. En distancia larga,
MobileNet obtiene 373/576 (64,76 %); corta 533/564 (94,50 %) y media 871/960 (90,73 %).
El análisis y gráfico están en reports/cv10_s008_128_20261019/error_analysis/.

Rechazo conservador kNN5:197/300 desconocidas rechazadas (65,67 %),103 aceptadas
por error. Se rechazaron 10/2.100 conocidas (0,48 %), todas ya mal clasificadas;
se conservaron los1777 aciertos (84,62 % sobre todas las conocidas).
Faltaron 13 rechazos de desconocidas para llegar a 210/300, el 70 % agrupado.
Por sesión, la tasa oscila entre 35 % en s004 y 78 % en s006; s008 obtiene 36/50
(72 %). El objetivo interno del 70 % no garantiza el 70 % externo. No seleccionar un
umbral a partir de esas puntuaciones externas ni promediar umbrales de modelos
para activarlo en la aplicación. Evidencia: reports/cv10_s008_unknown_knn_20261019/.

Se verificaron 2.400 predicciones externas únicas, aislamiento de sesiones y hashes,
umbrales guardados antes de evaluación externa y compatibilidad con predicciones
originales de clasificación. La selección de la aplicación permanece intacta.
Los resultados no prueban las hipótesis finales ni rechazo de todo pictograma ajeno.

El siguiente experimento recomendado compara 128 con 192 desde los originales,
con las mismas siete rondas, semillas y presupuestos y midiendo latencia además
de aciertos. Se deberán recalibrar referencias/umbral por modelo. Su ejecución
no se inició durante este análisis. El rechazo necesita estudiar estabilidad
entre sesiones; subir resolución no garantiza solucionarlo. s007 se mantuvo reservada
hasta la prueba final; consultar [prueba_final_s007.md](prueba_final_s007.md).
