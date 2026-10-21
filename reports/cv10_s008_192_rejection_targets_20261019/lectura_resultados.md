# Recalibracion de rechazo MobileNet192

Se conservaron modelos, referencias y puntuaciones. Todas las reglas internas se guardaron antes de cargar externas. Se compararon75% y80% con limite1% de conocidas internas. Si una ronda no cumple ambas restricciones la variante completa se marca inviable, sin promedio externo parcial.

Referencia70%: unknown208/300; conocidas rechazadas5/2100; conocidas correctas aceptadas1961/2100.
- Objetivo0.75: unknown219/300 (73.00%); conocidas rechazadas6/2100 (0.29%); conocidas correctas aceptadas1961/2100 (93.38%). Cumple criterios externos prefijados:True.
- Objetivo0.8: unknown225/300 (75.00%); conocidas rechazadas6/2100 (0.29%); conocidas correctas aceptadas1961/2100 (93.38%). Cumple criterios externos prefijados:True.

Limites: desarrollo adaptativo con externas ya analizadas; no validacion independiente. Conocidas internas compartidas con parada temprana. No garantia de rechazo en otro entorno ni sobre pictogramas ajenos. No se modificaron la aplicacion, su modelo128 ni su umbral. Un modelo unico192 requiere calibracion propia. s007 reservada.
