# Comparación CNN: Flatten frente a promedio global

Se completaron las seis rondas de desarrollo con el mismo manifiesto, roles,
semillas y ajustes del experimento cv10_20261018_000712. El único cambio
estructural fue reemplazar Flatten por GlobalAveragePooling2D.

- CNN original: 915/1800 aciertos, 50,83%.
- CNN con promedio global: 453/1800 aciertos, 25,17%.
- Diferencia: -462 aciertos; -25,67 puntos porcentuales.
- Parámetros: de 323370 a 65322 (reducción aproximada del 79,8%).

La variante no se selecciona como mejora. Menos parámetros no implicó mayor
exactitud. El promedio global elimina información espacial explícita; podría
perjudicar esta arquitectura, pero el experimento no identifica por sí solo
la causa. Varias rondas también muestran aprendizaje insuficiente.

Los modelos previos y la selección de la aplicación no se modificaron. s007
y desconocidos no participaron. Esto es desarrollo adaptativo, no prueba final.
Se verificaron seis historiales, sus particiones y las 1800 predicciones; las
18 pruebas automatizadas del código pasaron.

Siguiente experimento propuesto: conservar Flatten y comparar una tasa inicial
Adam0.0003 con la referencia Adam0.001, manteniendo las demás condiciones.
No se ejecutó ese nuevo experimento en esta comparación.
