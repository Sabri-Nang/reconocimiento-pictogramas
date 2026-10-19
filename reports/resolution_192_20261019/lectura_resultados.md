# Comparacion de resolucion128/192

Mismas siete rondas, muestras, semillas, batch y presupuestos. s007 excluida.

- CNN:128=1637/2100 (77.95%);192=1477/2100 (70.33%); diferencia=-7.62 puntos.
  Corrige139 errores anteriores e introduce299 nuevos. Parametros128/192: 323370/651050. Latencia mediana:10.52/11.57ms.
- MOBILENET:128=1777/2100 (84.62%);192=1964/2100 (93.52%); diferencia=8.90 puntos.
  Corrige219 errores anteriores e introduce32 nuevos. Parametros128/192: 944890/944890. Latencia mediana:96.80/97.52ms.
- Rechazo128: desconocidas197/300 (65.67%); conocidas10/2100 (0.48%); conocidas correctas aceptadas1777/2100.
- Rechazo192: desconocidas208/300 (69.33%); conocidas5/2100 (0.24%); conocidas correctas aceptadas1961/2100.

No activar automaticamente la aplicacion. Elegir procedimiento en desarrollo, preparar modelo unico y calibrarlo antes de s007. No asumir que mas resolucion mejora cada clase, sesion o rechazo.
Los tiempos de entrenamiento dependen de epocas ejecutadas y carga de la maquina. Latencia mide solo cuatro checkpoints fold1, calentados y en CPU; no end-to-end de camara.
CNN cambia capacidad con Flatten: no se aisla resolucion a igual numero de parametros. Negativos principalmente objetos y escenas, sin representar todo pictograma desconocido.
