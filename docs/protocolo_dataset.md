# Protocolo de construcción del dataset

Estado del documento: **vigente**.

## Objetivo

Construir un dataset reproducible para entrenar, validar y evaluar un sistema de
reconocimiento de pictogramas. Las capturas deben representar condiciones de uso
realistas y mantener separadas las sesiones destinadas a entrenamiento,
validación y prueba.

El proyecto se encuentra en la fase `dataset-10`. Las diez clases activas son:

1. `agua`;
2. `comer`;
3. `bano`;
4. `mama`;
5. `dolor`;
6. `papa`;
7. `no`;
8. `si`;
9. `jugar`;
10. `ayuda`.

Los identificadores y nombres de carpetas deben coincidir con
`config/project.json`. Los identificadores internos no llevan tildes.

## Diseño y cantidad del dataset

Cada sesión conocida contiene 30 imágenes por clase:

- 10 clases activas;
- 30 imágenes por clase y sesión;
- 300 imágenes conocidas por sesión;
- 7 sesiones planificadas (`s001` a `s007`);
- 210 imágenes finales por clase;
- 2.100 imágenes conocidas al finalizar el dataset.

Las imágenes `unknown` se distribuyen así:

- 40 imágenes en cada sesión de `s001` a `s005`;
- 50 imágenes en `s006`;
- 50 imágenes en `s007`;
- 300 imágenes `unknown` al finalizar.

El objetivo total es, por lo tanto, 2.400 imágenes: 2.100 conocidas y 300
desconocidas.

Al momento de actualizar este protocolo están completas `s001` a `s006`:

- 180 imágenes por cada clase conocida;
- 1.800 imágenes conocidas;
- 250 imágenes `unknown`;
- 2.050 imágenes registradas en total.

La sesión `s007` permanece pendiente y reservada para la prueba final.

## Dispositivo y configuración común

Las capturas propias se realizaron con un `moto_g75` y las siguientes reglas
comunes:

- cámara trasera principal en 1x;
- modo Foto normal;
- proporción 1:1;
- formato JPEG;
- flash, filtros, modo Retrato y Ultra-Res desactivados;
- lente limpia;
- pictograma completo, enfocado y con margen visible;
- sin ráfagas de imágenes casi idénticas.

La dificultad debe ser realista. No se conservan fotografías completamente
oscuras, corruptas o imposibles de interpretar.

## Estructura de carpetas

Las imágenes originales se almacenan de esta manera:

```text
data/raw/
├── known/
│   ├── agua/
│   ├── comer/
│   ├── bano/
│   ├── mama/
│   ├── dolor/
│   ├── papa/
│   ├── no/
│   ├── si/
│   ├── jugar/
│   └── ayuda/
└── unknown/
```

Las clases conocidas se separan por carpeta. Todas las imágenes desconocidas se
guardan juntas en `data/raw/unknown/`; su sesión se identifica mediante el nombre
del archivo.

Las imágenes originales no deben editarse ni sobrescribirse durante el
preprocesamiento. Las conversiones se generan posteriormente en
`data/processed/`.

## Convención de nombres y orden de captura

Las imágenes conocidas usan:

```text
<clase>_<sesion>_<numero>.<extension>
```

Ejemplos:

```text
agua_s004_0001.jpg
mama_s006_0030.jpg
```

Las imágenes desconocidas usan:

```text
unknown_<sesion>_<numero>.<extension>
```

Ejemplos:

```text
unknown_s005_0001.jpg
unknown_s006_0050.jpg
```

La numeración comienza en `0001` para cada combinación de clase y sesión. Los
archivos se ordenan por `DateTimeOriginal` y `SubsecTimeOriginal` de EXIF antes de
renombrarlos. Esto es necesario porque el número determina las condiciones que
se registran en la metadata.

## Sesiones y separación experimental

Una sesión representa un conjunto de imágenes capturadas en condiciones
relacionadas. Todas las imágenes de una misma sesión deben permanecer juntas:

- `s001` a `s005`: entrenamiento y desarrollo;
- `s006`: validación;
- `s007`: prueba final.

La distribución efectiva por sesiones es aproximadamente 70/15/15. Nunca se
deben repartir imágenes de una misma sesión entre entrenamiento, validación y
prueba.

### s001 - Captura base

Condiciones registradas:

- iluminación natural;
- fondo de madera;
- perspectiva frontal;
- pictograma completo.

Distribución para `agua`, `papa`, `no`, `si`, `jugar` y `ayuda`:

- `0001-0009`: distancia corta;
- `0010-0020`: distancia larga;
- `0021-0030`: distancia media.

Excepciones históricas registradas para las clases iniciales:

- `bano`, `dolor` y `mama`: `0001-0010` corta, `0011-0020` larga y
  `0021-0030` media;
- `comer`: `0001-0010` corta, `0011-0020` media y `0021-0030` larga.

Estas diferencias reflejan el orden real de captura y están representadas como
reglas por clase en `config/session_plans.json`.

### s002 - Cambio de iluminación

Condiciones registradas:

- iluminación artificial;
- fondo claro;
- perspectiva frontal.

Distribución por clase:

- `0001-0010`: distancia corta;
- `0011-0020`: distancia media;
- `0021-0030`: distancia larga.

### s003 - Variación de fondos

La iluminación es natural y la perspectiva frontal. Se utilizan los mismos
fondos para las diez clases:

- `0001-0003`: fondo oscuro, distancia corta;
- `0004-0007`: fondo oscuro, distancia media;
- `0008-0010`: fondo oscuro, distancia larga;
- `0011-0013`: fondo de color, distancia corta;
- `0014-0017`: fondo de color, distancia media;
- `0018-0020`: fondo de color, distancia larga;
- `0021-0023`: fondo con objetos, distancia corta;
- `0024-0027`: fondo con objetos, distancia media;
- `0028-0030`: fondo con objetos, distancia larga.

Los objetos del fondo no deben cubrir el pictograma. Todas las clases deben
aparecer bajo las mismas condiciones generales para evitar que el modelo asocie
un fondo con una categoría.

### s004 - Variación de perspectiva y orientación

Condiciones comunes:

- iluminación natural uniforme;
- fondo neutro;
- distancia media;
- tarjeta completa y apoyada sobre la superficie.

Distribución por clase:

- `0001-0005`: cámara desplazada hacia la izquierda;
- `0006-0010`: cámara desplazada hacia la derecha;
- `0011-0015`: cámara desde arriba;
- `0016-0020`: cámara desde abajo;
- `0021-0025`: tarjeta rotada hacia la izquierda;
- `0026-0030`: tarjeta rotada hacia la derecha.

En los bloques laterales se mueve físicamente la cámara y se vuelve a apuntar al
centro. La tarjeta no se gira. En los bloques superior e inferior se modifica la
altura de la cámara. Solo en los dos últimos bloques se rota la tarjeta sobre la
superficie y la cámara permanece aproximadamente frontal.

Dentro de cada bloque de cinco, la variación es progresiva: desde un ángulo muy
leve hasta un máximo aproximado de 20 a 25 grados. No se utilizan perspectivas
extremas.

Los valores de metadata son `lateral_izquierda`, `lateral_derecha`, `superior`,
`inferior`, `rotacion_izquierda` y `rotacion_derecha`.

### s005 - Condiciones combinadas de entrenamiento

Distribución por clase:

- `0001-0003`: luz natural, fondo con objetos, distancia corta;
- `0004-0007`: luz natural, fondo con objetos, distancia media;
- `0008-0010`: luz natural, fondo con objetos, distancia larga;
- `0011-0013`: luz artificial, fondo oscuro o de color, distancia corta;
- `0014-0017`: luz artificial, fondo oscuro o de color, distancia media;
- `0018-0020`: luz artificial, fondo oscuro o de color, distancia larga;
- `0021-0023`: luz natural, superficie alternativa, distancia corta;
- `0024-0027`: luz natural, superficie alternativa, distancia media;
- `0028-0030`: luz natural, superficie alternativa, distancia larga.

La perspectiva registrada es frontal. Se permiten cambios realistas de posición
dentro del encuadre, pero la imagen debe seguir siendo legible.

### s006 - Validación

La sesión fue capturada en otro momento y no debe usarse para entrenar. Se emplea
para comparar modelos, ajustar hiperparámetros y calibrar el umbral de confianza.

Distribución por clase:

- `0001-0003`: luz natural, distancia corta, perspectiva frontal;
- `0004-0007`: luz natural, distancia media, perspectiva frontal;
- `0008-0010`: luz natural, distancia larga, perspectiva frontal;
- `0011-0013`: luz artificial, distancia corta, perspectiva frontal;
- `0014-0017`: luz artificial, distancia media, perspectiva frontal;
- `0018-0020`: luz artificial, distancia larga, perspectiva frontal;
- `0021-0023`: luz mixta, distancia corta, perspectiva leve combinada;
- `0024-0027`: luz mixta, distancia media, perspectiva leve combinada;
- `0028-0030`: luz mixta, distancia larga, perspectiva leve combinada.

Los fondos son variados y realistas. No se deben elegir únicamente las imágenes
que el modelo reconoce bien. Las decisiones tomadas con `s006` deben documentarse
antes de evaluar `s007`.

### s007 - Prueba final pendiente

`s007` debe capturarse otro día o en otro ambiente y mantenerse apartada hasta
finalizar el desarrollo. El plan previsto replica la estructura general de
`s006`, pero utiliza fondos reales variados y no debe copiar sus escenas.

- `0001-0010`: luz natural, perspectiva frontal y tres distancias;
- `0011-0020`: luz artificial, perspectiva frontal y tres distancias;
- `0021-0030`: luz mixta, tres distancias y perspectiva leve combinada.

Está prohibido usar `s007` para elegir arquitectura, aumentos, épocas o umbral.
Tampoco se deben eliminar fotografías porque el modelo se equivoque ni repetir
la evaluación hasta obtener un resultado favorable.

## Imágenes `unknown`

`unknown` agrupa imágenes válidas que no pertenecen a ninguna de las diez
clases activas. Pueden incluir:

- objetos cotidianos y muebles;
- manos o sectores de una habitación;
- hojas en blanco, texto y tarjetas vacías;
- dibujos u otros pictogramas ajenos a las diez clases;
- fondos sin tarjetas y objetos parcialmente visibles.

No deben incluir ninguno de los diez pictogramas conocidos, imágenes corruptas,
fotografías completamente negras, ráfagas casi idénticas, rostros, documentos,
direcciones ni otra información personal.

No se crean subclases para cada objeto: una silla, una taza y una hoja en blanco
utilizan el mismo `class_id=unknown`. La variedad es deliberada.

Distribución y función:

- `s001`: 40 imágenes, luz natural y fondo de madera;
- `s002`: 40 imágenes, luz artificial y fondo claro;
- `s003`: 40 imágenes, fondos oscuros, de color y con objetos;
- `s004`: 40 imágenes, perspectivas moderadas;
- `s005`: 40 imágenes, condiciones combinadas;
- `s006`: 50 imágenes de validación para calibrar el umbral;
- `s007`: 50 imágenes pendientes para la evaluación final del rechazo.

Las imágenes `unknown` de `s001` a `s005` forman parte del desarrollo; las de
`s006` pertenecen a validación y las de `s007` a prueba.

## Metadatos

Cada imagen se registra en `data/metadata.csv` con las columnas:

```text
filename,class_id,session_id,device,lighting,background,distance,perspective,source,notes
```

Las imágenes conocidas usan su identificador de clase. Las desconocidas usan
`class_id=unknown`. La metadata debe describir la captura real y no condiciones
supuestas.

Las reglas reproducibles se encuentran en:

- `config/session_plans.json` para clases conocidas;
- `config/unknown_session_plans.json` para imágenes desconocidas.

Los generadores son:

```powershell
uv run python scripts/generate_metadata.py --session s006
uv run python scripts/generate_metadata.py --session s006 --apply

uv run python scripts/generate_unknown_metadata.py --session s006
uv run python scripts/generate_unknown_metadata.py --session s006 --apply
```

Sin `--apply`, los scripts solo muestran una vista previa. Ambos reemplazan de
forma idempotente las filas de su propio tipo y conservan el resto de la
metadata.

## Criterios de calidad y auditoría

Antes de incorporar una sesión se debe comprobar:

- cantidad exacta por clase y sesión;
- nombres consecutivos sin números repetidos;
- archivos JPEG o PNG legibles;
- ausencia de duplicados exactos;
- una fila de metadata por imagen;
- coincidencia entre archivos y metadata;
- condiciones iguales entre clases dentro de cada bloque;
- ausencia de filtración entre entrenamiento, validación y prueba.

Las imágenes difíciles pero realistas no se eliminan solamente porque el modelo
las clasifique mal.

## Fuentes, privacidad y respaldo

Las imágenes actuales son propias y registran `source=propia`. Cualquier material
externo futuro debe incluir fuente y licencia antes de incorporarse.

Las imágenes están excluidas de Git por tamaño y sensibilidad. El dataset debe
mantenerse en al menos dos ubicaciones controladas y revisarse antes de compartir
para evitar información personal.

## Incorporación de las cinco clases adicionales

Las clases `papa`, `no`, `si`, `jugar` y `ayuda` se incorporaron después de las
cinco clases iniciales. Para mantener un diseño equilibrado se reprodujeron los
perfiles de captura de `s001` a `s006`, con 30 imágenes por combinación de clase
y sesión. La metadata conserva el identificador del perfil reproducido y el
orden cronológico EXIF de cada carpeta.

Aunque compartan identificador de sesión experimental, las nuevas capturas se
realizaron en fechas posteriores. Esta circunstancia debe considerarse al
interpretar resultados y está documentada en este protocolo; ninguna imagen de
`s006` puede pasar a entrenamiento. Quedan pendientes las 30 imágenes de `s007`
por cada clase y las 50 imágenes `unknown` de prueba para alcanzar las 2.400
imágenes planificadas.

## Ampliación de desarrollo s008

s008 incorpora 300 conocidas (30 por clase) y 50 objetos o escenas sin tarjetas. Es desarrollo, no reemplaza s007. Ayuda conserva numeración de importación: 0001–0008 y0025–0026 cortas;0009–0016 y0027–0028 medias;0017–0024 y0029–0030 largas. Usar metadata, sin inferir distancias por bloques de diez para esa clase. Los planes automáticos históricos no describen s008; no regenerar sus filas con ellos. Ver [revisión y entrenamiento](entrenamiento_s008.md).
