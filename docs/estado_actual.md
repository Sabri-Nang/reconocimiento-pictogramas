# Estado actual del proyecto

Estado del documento: **vigente**.

Esta página es la referencia corta para saber qué configuración debe usarse y
qué resultados pueden considerarse actuales.

## Configuración vigente

- Dataset y clases: [config/project.json](../config/project.json).
- Aplicación activa: [config/application.json](../config/application.json).
- Modelo activo: MobileNet192, diez clases, detector `knn_cosine` con cinco
  vecinos.
- Prueba final: **completada**; 291/300 conocidas correctas (97 %), 29/50 desconocidas rechazadas (58 %). Ver [prueba final s007](prueba_final_s007.md).
- La configuración anterior [config/selected_model.json](../config/selected_model.json)
  queda conservada como respaldo histórico y no es la fuente de configuración
  de la aplicación.

## Estado de resultados

- Las métricas de s006 son internas: sirvieron para seleccionar época y calibrar
  el rechazo.
- Las métricas de validación cruzada son resultados de desarrollo, no prueba
  final.
- La prueba final supera el 70 % en clasificación conocida, pero no el objetivo de rechazo de desconocidos. No se recalibró con s007.

## Clasificación de la documentación

| Documento | Estado | Uso |
|---|---|---|
| `docs/estado_actual.md` | Vigente | Referencia principal |
| `docs/modelo_aplicacion_192.md` | Vigente | Paquete activo y calibración |
| `docs/protocolo_dataset.md` | Vigente | Reglas de datos y sesiones |
| `docs/entrenamiento_s008.md` | Desarrollo | Experimento con s008 |
| `docs/experimento_resolucion_192.md` | Desarrollo | Comparación 128/192 |
| `docs/rechazo_objetivo_y_limite.md` | Desarrollo | Calibración experimental |
| `docs/resultados_y_decisiones.md` | Desarrollo | Resultados adaptativos |
| `docs/validacion_cruzada_10_clases.md` | Desarrollo | Protocolo y ejecuciones CV |
| `docs/estrategia_mejora_entrenamiento.md` | Vigente | Plan de próximos experimentos |
| `docs/alcance_mvp.md` | Mixto | Alcance original y actualizaciones; consultar esta página primero |

## Reproducibilidad

Usar Python 3.11, `uv.lock` y siempre indicar una configuración de experimento:

```powershell
uv sync --locked
uv run python scripts/validate_config.py
uv run pytest -v
uv run python scripts/train_cross_validation.py --config config/cv_s008_128.json --run-id ID_NUEVO
```

Los identificadores de experimentos deben ser nuevos. No se modifica s007 ni
se reutilizan sus imágenes para selección, calibración o entrenamiento.
