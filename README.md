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

La interfaz utiliza las clases de `config/project.json` (piloto de cinco clases).
Todavía no hay un modelo integrado: categoría y confianza permanecen pendientes,
y el botón de reconocimiento está deshabilitado. No se generan predicciones
simuladas. La inferencia y el rechazo por umbral se incorporarán tras entrenar
el modelo y calibrar el umbral con validación.
