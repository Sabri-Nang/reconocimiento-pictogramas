# Instrucciones para agentes — Reconocimiento de pictogramas

Aplican a todo este repositorio. Comunicarse y documentar en español.

## Contexto y fuentes
- MVP local para reconocer diez pictogramas con TensorFlow/Keras y Gradio. Consultar `README.md`, `docs/alcance_mvp.md`, `docs/protocolo_dataset.md` y `docs/validacion_cruzada_10_clases.md` antes de cambiar el flujo correspondiente.
- Contrastar el estado descrito en documentación con código, configuración y artefactos: algunas secciones del README describen etapas anteriores.
- Cámara/ESP32-CAM, audio, API remota, nube y aplicación móvil son extensiones futuras; incorporarlas solo si el usuario lo solicita.

## Entorno y comandos
- Entorno administrado con uv; dependencias en `pyproject.toml` y resolución en `uv.lock`. Python de referencia: 3.11; respetar `.python-version`.
- Desde la raíz: `uv sync`, `uv run python --version`, `uv run pytest -v`.
- Aplicación: `uv run reconocimiento-pictogramas` en `http://127.0.0.1:7860`. Mantener servicio local por defecto.
- No introducir `requirements.txt` ni otro gestor de dependencias sin una necesidad explícita. No recrear `.venv` automáticamente.

## Mapa del código
- `src/reconocimiento_pictogramas/ui.py`: interfaz; `inference.py`: carga y predicción; `preprocessing.py`: procesamiento común; `cross_validation.py`: utilidades del protocolo cruzado.
- `config/project.json`: clases y parámetros generales; `dataset_partitions.json`: asignación explícita de sesiones; `selected_model.json`: checkpoint, orden de clases y umbral.
- `config/cross_validation.json`, `cv_cnn_gap.json` y `cv_mobilenet_extended.json`: protocolos de experimentos.
- `scripts/`: auditoría, preparación, entrenamiento, selección y comparación; `tests/`: pruebas de configuración, preparación, inferencia y validación cruzada.
- `data/`: originales, procesadas y particiones; `models/`: checkpoints locales; `reports/`: evidencia de experimentos; `docs/`: decisiones y protocolos.

## Inferencia y preprocesamiento
- Reutilizar `preprocessing.py`: orientación EXIF, RGB, redimensionado LANCZOS a 128 × 128. Entradas procesadas uint8 de 0 a 255, sin aumentos ni normalización externa.
- La normalización específica y los aumentos pertenecen al modelo. MobileNetV3 incorpora su normalización: evitar aplicarla dos veces.
- Mantener IDs internos sin tildes y textos visibles acentuados. Preservar exactamente el orden entre clases, manifiestos y salidas del modelo.
- Verificar existencia del checkpoint, coincidencia de clases y cantidad de salidas. No eludir controles de compatibilidad ni completar salidas artificialmente.
- `selected_model.json` selecciona MobileNet de diez clases `mobilenet_app_20261018`, entrenado con s001-s005 y validado/calibrado con s006. Es un candidato de aplicación, no un checkpoint de CV ni garantía del80,06% observado en seis rondas. No volver al piloto de cinco clases.
- La aplicación usa detector knn_cosine con cinco vecinos de entrenamiento y umbral de similitud calibrado internamente en s006. `confidence_threshold` queda null porque no se usa softmax para rechazar. Similitud menor o igual al umbral implica rechazo. No confundir similitud con probabilidad ni métricas internas con prueba independiente.
- La carga se cachea; reiniciar la aplicación tras modificar selección o umbral. Ante errores, no presentar resultados anteriores como actuales.

## Datos y rigor experimental
- Conservar originales y metadata. Auditar nombres, cantidades, sesiones, apertura de imágenes y hashes antes de preparar o entrenar; no excluir muestras por sus resultados externos.
- La asignación explícita de sesiones prevalece sobre proporciones orientativas: referencia train s001–s005, validación s006 y prueba s007.
- s007 está reservada para prueba final. No usarla para entrenamiento, elección de arquitectura, hiperparámetros, época, umbral o comparaciones de desarrollo.
- Los desconocidos se auditan aparte; no son una undécima clase de entrenamiento. Separar negativos de calibración y evaluación conforme al protocolo.
- Preparación: `uv run python scripts/prepare_dataset.py` valida; agregar `--apply --workers 4` genera procesadas y manifiestos. Revisar el alcance antes de ejecutar escrituras sobre datos.
- Validación cruzada: seis rondas s001–s006; cuatro sesiones entrenan, una valida internamente y una evalúa externamente. La interna elige checkpoint por val_loss; la externa se evalúa después de seleccionarlo.
- Reiniciar modelos por ronda, salvo el experimento explícito de continuación de MobileNet. Mantener semillas y protocolo registrados; no alterar datos ni configuración al reanudar una ejecución.
- Comando base: `uv run python scripts/train_cross_validation.py`. Reanudar con `--resume --run-id ID`; una ronda incompleta se reinicia. Usar las configuraciones específicas para variantes.
- Las métricas externas cruzadas son resultados de desarrollo, no prueba final. La desviación entre sesiones no es un intervalo de confianza.
- Distinguir objetivos de resultados: 70 % es el mínimo académico de prueba; 80 % en desarrollo requiere al menos 1440/1800 aciertos, sin redondear hacia arriba. No afirmar convergencia solo por alcanzar el límite de épocas.

## Cambios y comprobaciones
- Preferir cambios acotados, rutas con `pathlib` relativas al proyecto y texto UTF-8. Evitar rutas absolutas de una máquina.
- Ejecutar pruebas pertinentes con `uv run pytest`; para cambios de inferencia revisar errores y correspondencia de clases; para datos o CV comprobar aislamiento por sesión, ruta y hash.
- No lanzar entrenamientos largos como comprobación rutinaria de documentación. Informar comandos ejecutados y limitaciones reales, sin inventar métricas.
- Usar identificadores nuevos para experimentos nuevos. Conservar checkpoints, protocolos, manifiestos, predicciones, historiales y métricas previas; no sobrescribir evidencia para mejorar resultados.
- Para revisar resultados: `scripts/describe_cv_results.py --run-id ID` y `scripts/compare_cv_experiments.py --reference ID --candidate ID`, ejecutados con `uv run python`.
- Respetar `.gitignore`: datos y pesos son locales y requieren respaldo separado; evidencia de experimentos en reports puede estar versionada. No agregar artefactos ignorados por la fuerza ni borrar capturas, modelos o informes sin solicitud explícita.
- Actualizar README y documentación del protocolo cuando cambien ejecución, selección, procesamiento o metodología.
