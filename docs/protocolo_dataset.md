# Protocolo de construcción del dataset

## Objetivo

Construir un conjunto de imágenes variado y equilibrado para entrenar y evaluar
un modelo capaz de reconocer diez pictogramas.

Las imágenes deberán representar condiciones realistas de uso y permitir una
separación confiable entre entrenamiento, validación y prueba.

## Clases

Las clases iniciales son:

1. agua
2. comer
3. ayuda
4. dolor
5. bano
6. jugar
7. si
8. no
9. mama
10. papa

Los nombres de las carpetas deberán coincidir exactamente con los identificadores
definidos en `config/project.json`.

## Cantidad inicial

El objetivo será reunir, como mínimo:

- 200 imágenes por cada clase conocida;
- 2.000 imágenes conocidas en total;
- 300 imágenes negativas o desconocidas.

Las imágenes negativas no formarán inicialmente una clase del modelo. Se
utilizarán para medir falsos reconocimientos y calibrar el umbral de confianza.

## Estructura de carpetas

Las imágenes originales se almacenarán de esta manera:

```text
data/raw/
├── known/
│   ├── agua/
│   ├── comer/
│   ├── ayuda/
│   ├── dolor/
│   ├── bano/
│   ├── jugar/
│   ├── si/
│   ├── no/
│   ├── mama/
│   └── papa/
└── unknown/
```

Las imágenes originales no deberán editarse ni sobrescribirse. Cualquier
transformación se guardará posteriormente en `data/processed`.

## Sesiones de captura

Las fotografías se reunirán en sesiones independientes.

Una sesión representa un grupo de imágenes tomadas:

- durante el mismo período;
- con el mismo dispositivo;
- en un lugar determinado;
- bajo condiciones relacionadas.

Cada sesión tendrá un identificador:

```text
s001
s002
s003
```

Para evitar resultados artificialmente altos, las imágenes de una misma sesión
no se repartirán entre entrenamiento, validación y prueba.

## Condiciones de captura

Para cada pictograma se deberán variar deliberadamente las siguientes condiciones.

### Iluminación

- luz natural;
- luz artificial;
- iluminación frontal;
- iluminación lateral;
- iluminación moderadamente baja;
- presencia de sombras leves.

No se utilizarán imágenes totalmente oscuras en las que el pictograma sea
imposible de identificar.

### Distancia

Se tomarán imágenes aproximadamente desde:

- corta distancia;
- distancia media;
- distancia larga, manteniendo el pictograma visible.

### Perspectiva

Se incluirán:

- captura frontal;
- inclinación hacia la izquierda;
- inclinación hacia la derecha;
- inclinación desde arriba;
- inclinación desde abajo.

Las deformaciones deben ser realistas y no impedir completamente la lectura.

### Fondo

Se utilizarán diferentes fondos:

- pared clara;
- pared oscura;
- mesa;
- tela;
- fondo con objetos;
- fondo de color.

### Posición

El pictograma podrá aparecer:

- centrado;
- desplazado hacia los lados;
- desplazado hacia arriba o abajo;
- ocupando diferentes proporciones de la imagen.

### Orientación

Se permitirán rotaciones pequeñas. No se tomarán imágenes invertidas a menos que
esa situación pueda ocurrir en el uso real.

## Convención de nombres

Cada archivo se nombrará con el siguiente formato:

```text
<clase>_<sesion>_<numero>.<extension>
```

Ejemplos:

```text
agua_s001_0001.jpg
agua_s001_0002.jpg
comer_s002_0001.png
```

Para imágenes negativas:

```text
unknown_s003_0001.jpg
unknown_s003_0002.jpg
```

El número deberá ser único dentro de la combinación de clase y sesión.

## Imágenes desconocidas

El conjunto `unknown` incluirá ejemplos como:

- fotografías sin pictogramas;
- objetos cotidianos;
- habitaciones;
- manos;
- hojas en blanco;
- texto sin pictogramas;
- pictogramas pertenecientes a otras categorías;
- imágenes parcialmente visibles;
- imágenes desenfocadas de manera moderada.

No se incluirán en `unknown` imágenes de las diez clases conocidas con una
etiqueta incorrecta.

## Metadatos

Cada imagen deberá registrarse en:

```text
data/metadata.csv
```

El archivo contendrá estas columnas:

```text
filename,class_id,session_id,device,lighting,background,distance,perspective,source,notes
```

Ejemplo:

```csv
filename,class_id,session_id,device,lighting,background,distance,perspective,source,notes
agua_s001_0001.jpg,agua,s001,telefono,natural,mesa,media,frontal,propia,
```

Para las imágenes negativas, `class_id` tendrá el valor `unknown`.

## Fuentes y licencias

Se deberá registrar la procedencia de cada pictograma y de cada imagen que no sea
propia.

No se incorporarán imágenes descargadas sin conocer su fuente o condiciones de
uso. La fuente y cualquier requisito de atribución deberán documentarse antes de
usar el material.

## Criterios de calidad

Se conservarán imágenes con variaciones realistas aunque no sean perfectas.

Se descartarán imágenes que:

- estén completamente oscuras;
- no permitan identificar visualmente el pictograma;
- estén dañadas o no puedan abrirse;
- sean duplicados exactos;
- tengan una etiqueta incorrecta;
- hayan sido modificadas accidentalmente;
- no tengan una procedencia conocida.

Las imágenes con dificultad realista no deben eliminarse solamente porque el
modelo pueda clasificarlas incorrectamente.

## Separación de datos

La división prevista será:

- 70 % para entrenamiento;
- 15 % para validación;
- 15 % para prueba.

La separación se realizará mediante un script y tendrá en cuenta el
`session_id`. No se copiarán manualmente imágenes a las particiones.

El conjunto de prueba permanecerá apartado y no se utilizará para:

- seleccionar el modelo;
- modificar hiperparámetros;
- elegir aumentos de datos;
- calibrar el umbral de confianza.

## Control antes del entrenamiento

Antes de entrenar se verificará:

- que existan las diez clases;
- que las clases tengan cantidades similares;
- que todos los archivos puedan abrirse;
- que no existan duplicados exactos;
- que cada imagen figure en los metadatos;
- que los nombres respeten la convención;
- que ninguna sesión aparezca en más de una partición;
- que la resolución y los formatos puedan procesarse correctamente.

## Respaldo

Las imágenes están excluidas de Git debido a su tamaño y posible sensibilidad.

El dataset deberá mantenerse en al menos dos ubicaciones controladas. No se
publicarán fotografías que contengan información personal sin revisar previamente
su contenido y autorización.