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

## Plan de sesiones del piloto

Cada sesión incluirá fotografías de las cinco clases activas:

- agua;
- comer;
- bano;
- mama;
- dolor.

Se tomarán aproximadamente 30 imágenes por clase y por sesión. Cada sesión
contendrá alrededor de 150 imágenes.

### Distribución prevista

- `s001` a `s005`: entrenamiento.
- `s006`: validación.
- `s007`: prueba final.

La asignación se define antes de entrenar para evitar elegir posteriormente las
imágenes que produzcan mejores resultados.

### Condiciones de cada sesión

#### s001 - Captura base

- Luz natural.
- Fondo claro y liso.
- Ambiente interior.
- Imágenes principalmente frontales.
- Distancias corta, media y larga.
- Pictograma completamente visible.

#### s002 - Cambio de iluminación

- Luz artificial.
- Fondo claro.
- Sombras leves.
- Diferentes posiciones dentro de la imagen.
- Variaciones pequeñas de distancia.

#### s003 - Variación de fondos

El objetivo de esta sesión será evitar que el modelo dependa de un fondo
específico para reconocer los pictogramas.

Se utilizarán los mismos tres tipos de fondo para todas las clases:

- fondo oscuro;
- fondo de color;
- fondo con objetos.

La iluminación será principalmente natural y la cámara permanecerá mayormente
frontal. Las perspectivas marcadas se reservarán para la sesión `s004`.

Cada clase tendrá 30 imágenes distribuidas de la siguiente manera:

- `0001-0003`: fondo oscuro y distancia corta;
- `0004-0007`: fondo oscuro y distancia media;
- `0008-0010`: fondo oscuro y distancia larga;
- `0011-0013`: fondo de color y distancia corta;
- `0014-0017`: fondo de color y distancia media;
- `0018-0020`: fondo de color y distancia larga;
- `0021-0023`: fondo con objetos y distancia corta;
- `0024-0027`: fondo con objetos y distancia media;
- `0028-0030`: fondo con objetos y distancia larga.

Dentro de cada grupo se variará ligeramente la posición de la tarjeta y de la
cámara. Los objetos del fondo no deberán cubrir el pictograma.

Todas las clases deberán fotografiarse sobre los mismos fondos para impedir que
un fondo determinado quede asociado a una categoría particular.
#### s004 - Cambio de perspectiva

#### s004 - Variación de perspectiva

El objetivo de esta sesión será comprobar si el modelo puede reconocer los
pictogramas cuando la cámara no se encuentra completamente de frente.

Se utilizarán las siguientes condiciones comunes:

- iluminación natural y uniforme;
- fondo neutro y liso;
- distancia principalmente media;
- cámara trasera principal en 1x;
- proporción de imagen 1:1;
- flash y filtros desactivados.

Se tomarán 30 fotografías por cada clase, distribuidas de la siguiente manera:

- `0001-0005`: cámara desplazada hacia la izquierda;
- `0006-0010`: cámara desplazada hacia la derecha;
- `0011-0015`: cámara inclinada desde arriba;
- `0016-0020`: cámara inclinada desde abajo;
- `0021-0025`: tarjeta rotada hacia la izquierda;
- `0026-0030`: tarjeta rotada hacia la derecha.

La tarjeta permanecerá apoyada horizontalmente y plana sobre la mesa durante
toda la sesión.

En las fotografías laterales se moverá físicamente la cámara hacia la izquierda
o hacia la derecha, manteniéndola por encima de la mesa y apuntando nuevamente
al centro del pictograma. La tarjeta no se levantará ni se rotará. Como resultado,
su forma podrá verse ligeramente trapezoidal por efecto de la perspectiva.

En las fotografías desde arriba o desde abajo se cambiará la altura de la cámara,
manteniendo el pictograma completo dentro del encuadre.

En las fotografías con rotación, la cámara se mantendrá aproximadamente frontal
y se girará la tarjeta sobre la superficie.

Los ángulos serán progresivos y moderados:

- primera fotografía: ángulo muy leve;
- segunda fotografía: ángulo leve;
- tercera fotografía: ángulo intermedio;
- cuarta fotografía: ángulo algo mayor;
- quinta fotografía: ángulo máximo aproximado de 20 a 25 grados.

No se utilizarán perspectivas extremas. La tarjeta deberá permanecer completa,
enfocada y visualmente reconocible.

Los valores del campo `perspective` serán:

- `lateral_izquierda`;
- `lateral_derecha`;
- `superior`;
- `inferior`;
- `rotacion_izquierda`;
- `rotacion_derecha`.

Todas las clases deberán fotografiarse bajo las mismas condiciones para evitar
que una perspectiva o un fondo quede asociado a una categoría particular.

#### s005 - Condiciones combinadas

- Más de una habitación.
- Fondos claros y oscuros.
- Luz natural y artificial.
- Posiciones y distancias variadas.
- Condiciones similares a un uso cotidiano.

#### s006 - Validación

- Capturada en otro momento.
- Condiciones normales y variadas.
- No deberá ser una repetición inmediata de las sesiones anteriores.
- Se utilizará para comparar modelos y calibrar el umbral de confianza.

#### s007 - Prueba final

- Capturada otro día o en otro ambiente.
- Condiciones normales de uso.
- No se utilizará para modificar el modelo.
- Permanecerá reservada hasta finalizar el entrenamiento y la selección.

Las sesiones de validación y prueba no deben ser deliberadamente más difíciles.
Su objetivo es representar imágenes nuevas en condiciones realistas.