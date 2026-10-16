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
Carga el checkpoint definido en `config/selected_model.json` al reconocer una
imagen y muestra categoría y probabilidad del modelo. El rechazo todavía está
pendiente de calibración: mientras el umbral sea null, siempre devuelve una
clase conocida y lo advierte en la pantalla. Los modelos están ignorados por
Git; otra instalación debe entrenarlos o copiar el checkpoint seleccionado.
El checkpoint seleccionado actualmente corresponde al piloto de cinco clases;
debe regenerarse la preparación y entrenarse un modelo de diez salidas antes de
usar las clases incorporadas.

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

## Selección provisional e inferencia

```powershell
uv run python scripts/compare_models.py --runs cnn_20261009_105933 mobilenet_20261009_111839
uv run reconocimiento-pictogramas
```

El comparador comprueba los hashes de ambos manifiestos, ordena por exactitud,
macro F1 y pérdida de validación y guarda config/selected_model.json.
Benchmark: CPU, cuatro threads intra-op y dos inter-op, batch 1,
cinco calentamientos y 30 mediciones; excluye carga del modelo y preprocesamiento.
La selección registrada corresponde al piloto de cinco clases y debe repetirse
después de entrenar los modelos con las diez clases. No confirma hipótesis de prueba.
No se utiliza s007 ni desconocidos para seleccionar el modelo.
Si se cambia la selección o el umbral, reiniciar Gradio para recargar la configuración.

## Auditar desconocidos

```powershell
uv run python scripts/audit_unknown.py
```

Verifica nombres, formato, apertura y duplicados contra conocidas y desconocidas.
Guarda inventario y reporte en reports/, sin modificar capturas ni asignar
particiones. La revisión visual y la independencia de sesiones se comprueban
antes de decidir qué negativos usar en calibración o prueba.
