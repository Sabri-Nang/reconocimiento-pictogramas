# CNN: comparación de tasa de aprendizaje

Mismo dataset de desarrollo, seis rondas, semillas, arquitectura original con
Flatten, aumentos, lotes32, máximo30 épocas y paciencia6. Único cambio:
Adam0.001 por Adam0.0003. Los originales y s007 no se modificaron.

- Referencia: 915/1800 aciertos, 50,83%.
- Tasa menor: 726/1800 aciertos, 40,33%.
- Diferencia: -189 aciertos, -10,50 puntos porcentuales.

No se selecciona como mejora. La conclusión se limita a este presupuesto y
criterio de parada: no demuestra que una tasa menor sea peor con otras
configuraciones o más épocas. Se verificaron seis historiales, doce gráficos,
particiones disjuntas, probabilidades y 1800 predicciones externas.

La CNN con promedio global del experimento previo obtuvo 25,17%; ambos
experimentos quedan por debajo de la CNN original. MobileNet con ajuste
prolongado mantiene su resultado previo de desarrollo de 80,06%.

No se reemplazaron modelos anteriores ni se modificó la selección de la
aplicación. s007 y desconocidos no participaron. Las decisiones de desarrollo
son adaptativas; no representan prueba final independiente.

Se recomienda investigar cuánto detalle conserva el pictograma a128x128 y
la dependencia de fondos/sesiones antes de repetir ajustes de hiperparámetros.
Cualquier recorte debe ser reproducible y aplicarse igual al preprocesamiento
de entrenamiento y de inferencia. No se implementó un recorte en este ensayo.
