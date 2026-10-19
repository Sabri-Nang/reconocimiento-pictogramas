# Reconocimiento de pictogramas

Aplicación local que utiliza aprendizaje automático para reconocer pictogramas
a partir de imágenes.

El usuario cargará una imagen y la aplicación mostrará:

- la categoría reconocida;
- el nivel de confianza;
- un aviso cuando el pictograma no pueda reconocerse con suficiente certeza.

## Alcance del MVP

La primera versión reconocerá diez categorías:

- Agua
- Comer
- Ayuda
- Dolor
- Baño
- Jugar
- Sí
- No
- Mamá
- Papá

El objetivo inicial es alcanzar al menos un 70 % de exactitud sobre imágenes que
no hayan sido utilizadas durante el entrenamiento.

El alcance detallado se encuentra en
[`docs/alcance_mvp.md`](docs/alcance_mvp.md).

## Tecnologías

- Python 3.11
- uv
- TensorFlow y Keras
- Gradio
- Pillow
- NumPy y Pandas
- scikit-learn
- Matplotlib y Seaborn
- Pytest

## Preparación del proyecto

Clonar el repositorio:

```powershell
git clone https://github.com/Sabri-Nang/reconocimiento-pictogramas.git
cd reconocimiento-pictogramas
```

Crear el entorno e instalar las dependencias:

```powershell
uv sync
```

Comprobar la versión de Python:

```powershell
uv run python --version
```

Ejecutar las pruebas:

```powershell
uv run pytest -v
```

## Estructura

```text
config/      Configuración general del proyecto
data/        Imágenes originales, procesadas y particiones
docs/        Alcance y documentación
models/      Modelos entrenados
notebooks/   Exploración y experimentos
reports/     Métricas, gráficos y resultados
scripts/     Procesos ejecutables
src/         Código fuente de la aplicación
tests/       Pruebas automatizadas
```

## Estado del proyecto

Semana 1 completada:

- alcance del MVP definido;
- diez clases seleccionadas;
- estructura del repositorio creada;
- entorno administrado con uv;
- dependencias registradas;
- configuración validada mediante pruebas.

## Funcionalidades futuras

Una vez validado el clasificador podrán evaluarse:

- captura mediante cámara o ESP32-CAM;
- reproducción de audio;
- construcción de frases;
- API remota;
- aplicación móvil.
## Interfaz Gradio

Ejecutar desde la carpeta del proyecto:

```powershell
uv run reconocimiento-pictogramas
```

Abrir http://127.0.0.1:7860. Cargar una imagen JPEG o PNG para ver la
versión RGB de 128 × 128 píxeles. El botón Limpiar reinicia la pantalla.

La interfaz utiliza las diez clases definidas en `config/project.json`.
Carga el MobileNet y el detector definidos en `config/selected_model.json`.
Muestra la categoría, la puntuación softmax de esa clase y, por separado, la
similitud con los cinco ejemplos conocidos más cercanos de entrenamiento.
La similitud no es probabilidad. Si es menor o igual al umbral calibrado,
la respuesta es «Pictograma no reconocido», aunque la puntuación de clase sea alta.

El checkpoint y las referencias de características están ignorados por Git:
otra instalación necesita ambos archivos indicados en la configuración.
Se verifican sus hashes, el orden de clases y dimensiones. Reiniciar Gradio
tras modificar la selección para vaciar las cachés. La prueba s007 sigue pendiente.

## Preparar el dataset piloto

La asignación explícita está en `config/dataset_partitions.json`: s001-s005
para entrenamiento, s006 para validación y s007 para prueba. Esta asignación
por sesiones prevalece sobre las proporciones orientativas de project.json.

Validar capturas, metadata, cantidades y duplicados entre todas las sesiones:

```powershell
uv run python scripts/prepare_dataset.py
```

Generar imágenes procesadas y manifiestos:

```powershell
uv run python scripts/prepare_dataset.py --apply
uv run pytest -q
```

Los originales se conservan. El módulo `preprocessing.py`, también utilizado
por la interfaz, aplica orientación EXIF, RGB y redimensionado LANCZOS a
128 x 128. Guarda PNG sin aumentos ni normalización (uint8 0-255).
La normalización específica de cada modelo debe definirse al entrenarlo.

Se generan `data/splits/train.csv`, `validation.csv`, `test.csv` y
`summary.json`, con rutas relativas, índices de clase y SHA-256 del original.
Si s007 todavía no existe, test.csv solo tiene cabecera y summary.json marca
la prueba como pendiente: no constituye una evaluación final disponible.
Una sesión de prueba parcial provoca un error; no se reemplaza con otras fotos.
Los desconocidos no se incluyen en estos manifiestos de clases conocidas.
Aún deben reunirse y separarse para calibración y evaluación del rechazo.

## Entrenar la CNN base

```powershell
uv run python scripts/train_cnn.py --epochs 30 --batch-size 32
```

Lee exclusivamente train.csv y validation.csv; comprueba que no compartan
sesiones, rutas ni hashes. Recibe PNG RGB 128 x 128 con valores 0-255.
La normalización y los aumentos de entrenamiento están dentro del modelo;
los aumentos se desactivan durante evaluación e inferencia.
Selecciona el checkpoint por mínima pérdida de validación con early stopping.
Cada ejecución crea una carpeta nueva en models/ y reports/ con best.keras,
configuración, hashes de manifiestos, historial, predicciones, métricas por
clase, curvas y matriz de confusión de validación. No calibra rechazo ni evalúa
prueba. La exactitud de validación no acredita el criterio de prueba final.

## Comparar con MobileNetV3-Small

```powershell
uv run python scripts/train_mobilenet.py --epochs 20 --fine-tune-epochs 10
```

Utiliza las mismas particiones y aumentos que la CNN. Descarga los pesos
ImageNet oficiales de Keras y los guarda en models/.keras_cache (ignorado).
Primero congela la base y entrena el clasificador; luego ajusta las últimas
30 capas con Adam 1e-5, manteniendo BatchNormalization congelada.
El checkpoint final es el de menor val_loss entre ambas etapas.
MobileNetV3 incorpora normalización a -1..1 y recibe RGB 128x128 de 0-255:
no aplicar otra normalización antes. Los resultados se guardan en una carpeta
nueva models/mobilenet_* y reports/mobilenet_*. No carga prueba ni desconocidos.

## Modelo de aplicación y calibración

```powershell
uv run python scripts/train_mobilenet.py --run-id mobilenet_app_20261018 --epochs 20 --fine-tune-epochs 40
uv run python scripts/calibrate_app_model.py --run-id mobilenet_app_20261018 --activate
uv run reconocimiento-pictogramas
```

Los comandos documentan esta ejecución: para repetirla, usar otro identificador
en ambos scripts. Entrena un único modelo desde ImageNet con1500 imágenes de
s001-s005; s006 elige la época por val_loss y calibra el detector. No se elige
un checkpoint de CV como modelo de aplicación. Máximo20 épocas con base
congelada y40 de ajuste fino continuo, paciencia6/4; no es una repetición exacta
de la continuación CV de10+30 épocas desde checkpoints intermedios.

El detector conservador se eligió explícitamente: referencia de características
construida solo con train y menor umbral que rechaza al menos70% de los50 unknown
de s006. Los resultados de s006 son internos y no independientes: esa misma
sesión conocida eligió la época. Los porcentajes de CV no son el resultado de
este único modelo. Se conservan configuración anterior, métricas y calibración
en reports/mobilenet_app_20261018/. s007 nunca se utiliza en estos comandos.

## Auditar desconocidos

```powershell
uv run python scripts/audit_unknown.py
```

Verifica nombres, formato, apertura y duplicados contra conocidas y desconocidas.
Guarda inventario y reporte en reports/, sin modificar capturas ni asignar
particiones. La revisión visual y la independencia de sesiones se comprueban
antes de decidir qué negativos usar en calibración o prueba.

## Dataset completo de diez clases (octubre de 2026)

```powershell
uv run python scripts/audit_full_dataset.py
uv run python scripts/prepare_dataset.py --apply --workers 4
```

La auditoría completa abre las capturas conocidas y desconocidas, verifica
metadata, clases, nombres, cantidades de conocidas y duplicados exactos globales.
Escribe reports/dataset_10_audit/integrity.json e inventory.csv.
No determina automáticamente calidad visual ni duplicados aproximados.
Si encuentra s007, se detiene para mantener esa prueba fuera del desarrollo.

La preparación procesa solo conocidas; las filas unknown no son clases de
entrenamiento y se auditan aparte. Conserva los manifiestos previos en
reports/dataset_preparation_backups/. Genera PNG RGB128x128, train.csv con
s001-s005, validation.csv con s006, test.csv vacío mientras falta s007 y
un development.csv con todas las conocidas s001-s006 para preparar las futuras
rondas de validación cruzada. Estas particiones de referencia no implementan
validación cruzada todavía. Los modelos y resultados del piloto se conservan.
No se entrena ni se cambia el modelo seleccionado al preparar datos.

## Validación cruzada con diez clases

```powershell
uv run python scripts/train_cross_validation.py
```

Seis rondas por arquitectura, cada una con 1200 imágenes de entrenamiento,
300 de validación interna para parada temprana y 300 externas para evaluar.
s007 queda reservada para la prueba final y no participa en las rondas.
Los modelos se reinician en cada ronda. Se guardan gráficos por época,
historiales por paso, checkpoints y resultados externos. Ver
[el protocolo detallado](docs/validacion_cruzada_10_clases.md).

## Continuación del ajuste fino de MobileNet

```powershell
uv run python scripts/extend_mobilenet_cv.py
uv run python scripts/describe_cv_results.py --run-id IDENTIFICADOR_GENERADO
uv run python scripts/compare_cv_experiments.py --reference cv10_20261018_000712 --candidate IDENTIFICADOR_GENERADO
```

config/cv_mobilenet_extended.json fija el experimento de referencia y el límite
de épocas adicionales. La época 0 representa su checkpoint; conserva el estado
Adam, utiliza las mismas rondas y elige por pérdida interna, sin usar s007.
El objetivo de desarrollo se compara con el conteo exacto (1440/1800 para 80%),
sin redondear un resultado inferior. Los resultados no son prueba final.

## Archivos versionados y artefactos locales

Git conserva código, configuración, documentación y evidencia de los experimentos:
protocolos, manifiestos por ronda, historiales por época y paso, predicciones,
métricas, verificaciones y gráficos. Estos archivos permiten revisar los resultados
sin volver a entrenar. Los checkpoints referenciados se conservan localmente.

`.gitignore` excluye el entorno virtual, cachés, capturas originales, imágenes
procesadas, particiones generadas en `data/splits/`, pesos en `models/`, respaldos
automáticos de particiones, nuevas hojas de contacto de la auditoría y el estado
transitorio `progress.json` de las ejecuciones de validación cruzada.
Las hojas de contacto se regeneran con `scripts/create_dataset_contact_sheets.py`.
Los archivos ignorados permanecen en disco y requieren respaldo separado; Git
no respalda las capturas ni los modelos. Las imágenes históricas ya versionadas
se conservan: agregar una regla no elimina archivos de commits anteriores.

## Evaluar rechazo de desconocidos con MobileNet

```powershell
uv run python scripts/evaluate_unknown_cv.py --source-run cv10_mobilenet_extend_20261018 --run-id cv10_unknown_20261018
```

Calibra un umbral por ronda en la sesión interna y evalúa después la externa.
El objetivo70% se refiere al porcentaje de unknown rechazados; no fija un
umbral0.70. Informa también conocidos rechazados y exactitud sobre todos los
conocidos. No entrena, no usa s007 y no cambia el modelo ni el umbral de la
aplicación. Ver el protocolo y límites en docs/validacion_cruzada_10_clases.md.

Para comparar el rechazo por similitud de características con cinco vecinos
de entrenamiento (sin modificar pesos ni clases):

```powershell
uv run python scripts/evaluate_unknown_cv.py --method knn --run-id cv10_unknown_knn_20261018
uv run python scripts/compare_rejection_results.py --reference cv10_unknown_20261018 --candidate cv10_unknown_knn_20261018
```

La similitud no es una probabilidad. Referencias: train; umbral: sesión interna;
evaluación: sesión externa. Los archivos de referencia quedan en models/,
fuera de Git. El protocolo detallado describe los límites de la comparación.

Para evaluar otra regla de calibración con las mismas puntuaciones de vecinos:

```powershell
uv run python scripts/calibrate_rejection_known_cap.py --source-run cv10_unknown_knn_20261018 --run-id cv10_unknown_knn_cap05_20261018
uv run python scripts/compare_rejection_results.py --reference cv10_unknown_knn_20261018 --candidate cv10_unknown_knn_cap05_20261018
```

Limita el rechazo de conocidos internos al5% y evalúa después la sesión externa.
Ese límite no es garantía externa. No vuelve a entrenar ni modifica la aplicación.

## Cámara en vivo desde el navegador

En «Cámara en vivo», tocar **Iniciar cámara**, aceptar el permiso y mostrar
una tarjeta a la vez. La cámara trasera es una preferencia que resuelve el
navegador. Hay una única vista con el video y el globo superpuesto. «Detener
y limpiar» apaga las pistas de cámara y retira palabra y estado.

El navegador envía un JPEG de hasta640 píxeles de lado mayor por vez mediante
una llamada autenticada del componente HTML. Espera la respuesta antes de
enviar otro; no se acumula una cola de fotogramas ni se utiliza el protocolo
de streaming de Gradio. El video de la cámara sigue visible durante el análisis.
Se muestra el contador de imágenes y el tiempo de respuesta. El intervalo
mínimo tras cada respuesta es0,7s: no equivale a clasificación a30fps.

El detector geométrico busca bordes cuadrilaterales y, si no los encuentra,
una superficie clara de papel aproximadamente rectangular. Puede fallar o
confundir otros rectángulos: no es un detector entrenado. La clasificación
sigue usando el fotograma completo, el MobileNet y el umbral calibrados.
El globo se confirma con tres observaciones consecutivas aceptadas de la misma
clase y posición parecida, tolerando pausas de hasta15s. Se retira ante ausencia,
rechazo o cambio de clase. La estabilización no garantiza que la clase sea correcta.

Los JPEG se decodifican en memoria y se responde con coordenadas, palabra y
estado; no se guardan fotogramas ni se añaden al dataset. La pestaña Foto
conserva el flujo de carga de imágenes y sus archivos temporales de Gradio.
No se utiliza s007 ni se reentrena al usar la cámara.

Servidor local:

```powershell
uv run reconocimiento-pictogramas
```

En el celular se necesita HTTPS confiable. Para certificado y clave propios:

```powershell
uv run reconocimiento-pictogramas --host 0.0.0.0 --port 7861 --ssl-certfile RUTA_CERTIFICADO --ssl-keyfile RUTA_CLAVE
```

El certificado debe ser confiable en el celular. No se instalan certificados
automáticamente. Alternativa autorizada por el usuario: enlace HTTPS temporal
de Gradio con contraseña. Los fotogramas pasan por ese servicio hacia la PC:

```powershell
$env:PICTOGRAMAS_PASSWORD = Read-Host 'Contraseña del enlace temporal'
uv run reconocimiento-pictogramas --port 7862 --share
```

Usuario: pictogramas. El modo local no requiere contraseña. Credenciales y
certificados locales se excluyen de Git bajo .runtime/. Probar en Chrome o
Safari del celular; el navegador requiere permiso de cámara. Tras actualizar
el servidor puede cambiar el enlace temporal: cerrar la página anterior y usar
el nuevo enlace. Las pruebas locales no sustituyen la prueba en el celular.

## Próximos experimentos y limpieza del repositorio

Consultar [la estrategia de mejora y conservación de archivos](docs/estrategia_mejora_entrenamiento.md) para comparar 128×128 con 192×192, planificar nuevas sesiones y mantener s007 reservada para la prueba final.

La incorporación de s008, su evaluación previa y la nueva validación cruzada de siete sesiones se documentan en [entrenamiento s008](docs/entrenamiento_s008.md).

El análisis de errores de las siete rondas está en [el informe de resultados](reports/cv10_s008_128_20261019/error_analysis/lectura_resultados.md), con un [gráfico comparativo](reports/cv10_s008_128_20261019/error_analysis/classification_analysis.png). Son resultados de desarrollo, sin s007.

La [evaluación de rechazo con los nuevos MobileNet](reports/cv10_s008_unknown_knn_20261019/lectura_resultados.md) obtuvo 65,67 % de rechazo de desconocidas y 0,48 % de rechazo de conocidas en desarrollo. El objetivo de rechazo del 70 % todavía no se cumple de forma agrupada; la aplicación conserva su selección anterior.

El [experimento de resolución192](docs/experimento_resolucion_192.md) compara las mismas siete rondas con128, recalibra rechazo y mide latencia, conservando la aplicación actual.

## Resultados actuales de desarrollo

Con siete sesiones (s001–s006 y s008), cada ronda utiliza **1.500 imágenes para
entrenar, 300 para parada temprana y 300 para evaluación externa**. s007 continúa
reservada para la prueba final.

- MobileNet: **84,62 % a128×128 y93,52 % a192×192**.
- CNN compacta: **77,95 % a128×128 y70,33 % a192×192**.
- Rechazo MobileNet192: **208/300 desconocidas (69,33 %)** y5/2100 conocidas
  rechazadas (0,24 %). Todavía no alcanza el objetivo de rechazo70 %.

MobileNet192 es el mejor candidato de clasificación evaluado. **La aplicación
conserva el modelo128 anterior**; el modelo único192 ysu calibración todavía
requieren preparación antes de activarlo. No se hereda el promedio de CV como
rendimiento de un modelo único. Estos resultados no son prueba final.

Ver [resultados y decisiones](docs/resultados_y_decisiones.md),
[comparación completa](reports/resolution_192_20261019/lectura_resultados.md) y
[gráficos128/192](reports/resolution_192_20261019/comparison.png).
