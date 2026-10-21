"""Construye el informe PDF usando únicamente evidencia almacenada."""
import argparse,csv,json,html,math
from pathlib import Path
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--run',required=True);a=p.parse_args();root=a.project;run=root/'reports'/a.run
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
m=read(run/'metrics.json');cat=read(run/'experiment_catalog.json');protocol=read(run/'protocol_frozen.json');classes=m['classes']
with (run/'predictions.csv').open(encoding='utf-8',newline='') as f:preds=list(csv.DictReader(f))
with (run/'experiments_folds.csv').open(encoding='utf-8',newline='') as f:folds=list(csv.DictReader(f))
for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Arial-Italic','ariali.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-Bold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyES',fontName='Arial',fontSize=9.3,leading=13,spaceAfter=8,textColor=colors.HexColor('#20272c')))
styles.add(ParagraphStyle(name='SmallES',fontName='Arial',fontSize=7.3,leading=10,spaceAfter=5,textColor=colors.HexColor('#49565f')))
styles.add(ParagraphStyle(name='TitleES',fontName='Arial-Bold',fontSize=25,leading=31,spaceAfter=17,textColor=colors.black))
styles.add(ParagraphStyle(name='H1ES',fontName='Arial-Bold',fontSize=17,leading=22,spaceAfter=12,textColor=colors.black))
styles.add(ParagraphStyle(name='H2ES',fontName='Arial-Bold',fontSize=11.5,leading=16,spaceBefore=10,spaceAfter=6,textColor=colors.black))
styles.add(ParagraphStyle(name='CellES',fontName='Arial',fontSize=8,leading=10.5))
styles.add(ParagraphStyle(name='CellSmall',fontName='Arial',fontSize=7,leading=9))
styles.add(ParagraphStyle(name='HeaderCell',fontName='Arial-Bold',fontSize=8,leading=10.5,textColor=colors.white))
story=[];sections=[]
def P(t,style='BodyES'):return Paragraph(t,styles[style])
def para(t):story.append(P(t))
def small(t):story.append(P(t,'SmallES'))
def heading(t):story.append(P(t,'H2ES'))
def page(t):
 if story:story.append(PageBreak())
 story.append(P(t,'H1ES'));sections.append(t)
def pct(x):return f'{100*x:.2f} %'.replace('.',',')
def table(headers,rows,widths=None,compact=False):
 style='CellSmall' if compact else 'CellES';cells=[[P(str(x),'HeaderCell') for x in headers]]+[[P(html.escape(str(x)),style) for x in row] for row in rows]
 t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#244c63')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f3f5')]),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4 if compact else 5),('BOTTOMPADDING',(0,0),(-1,-1),4 if compact else 5)]));story.append(t);story.append(Spacer(1,9))
def figure(name,caption,width=490,maxheight=410):
 path=run/'figures'/name;w,h=ImageReader(str(path)).getSize();scale=min(width/w,maxheight/h);story.append(Image(str(path),width=w*scale,height=h*scale,hAlign='LEFT'));small(caption)
def src(path):small('Fuente local: '+html.escape(path))
def metric_table():
 return [('Exactitud en conocidas sin rechazo',f"{m['known_correct_without_rejection']}/300",pct(m['known_accuracy_without_rejection'])),('Conocidas correctas y aceptadas',f"{m['known_correct_accepted']}/300",pct(m['known_accuracy_with_rejection'])),('Conocidas rechazadas',f"{m['known_rejected']}/300",pct(m['known_rejection_rate'])),('Desconocidas rechazadas',f"{m['unknown_rejected']}/50",pct(m['unknown_rejection_rate'])),('Desconocidas aceptadas como conocidas',f"{m['unknown_false_accepted']}/50",pct(m['unknown_false_acceptance_rate'])),('Acierto operativo total',f"{m['overall_operational_correct']}/350",pct(m['overall_operational_accuracy'])),('Acierto entre todas las salidas aceptadas',f"{m['known_correct_accepted']}/{m['all_accepted']}",pct(m['accuracy_among_all_accepted']))]
# Apertura
story.append(P('Evaluación final de Pictovoz','TitleES'))
para('Modelo seleccionado y evolución experimental del reconocimiento de diez pictogramas')
small('Fecha de evaluación: 21 de octubre de 2026 | Sesión final: s007 | Destinatario: equipo del proyecto Pictovoz')
heading('Resultado principal')
para(f"El modelo MobileNetV3-Small a 192 × 192 acertó <b>{m['known_correct_without_rejection']} de 300 pictogramas conocidos ({pct(m['known_accuracy_without_rejection'])})</b>. El sistema aceptó las 300 entradas conocidas, incluidas nueve clasificaciones erróneas. Con el umbral fijado antes de la prueba, rechazó <b>{m['unknown_rejected']} de 50 imágenes desconocidas ({pct(m['unknown_rejection_rate'])})</b>.")
para('Se cumple el objetivo de al menos 70 % de exactitud en conocidas. El rechazo de desconocidos no alcanza el 70 % de referencia utilizado durante el desarrollo, ni reproduce el objetivo interno de calibración del 80 %. Por eso la clasificación se considera satisfactoria para esta sesión, mientras que la respuesta ante entradas fuera del catálogo necesita mejoras.')
table(['Indicador final','Cantidad','Resultado'],metric_table()[:5],[270,85,135])
heading('Qué contiene este informe')
para('La prueba final con el paquete seleccionado, el protocolo y su trazabilidad, métricas por clase y matrices de confusión, análisis del rechazo y de los errores, trece resultados históricos de clasificación, nueve ensayos de rechazo y propuestas de mejora. Los anexos conservan resultados por ronda y por clase; el archivo de evidencia reúne las curvas, métricas y predicciones históricas disponibles.')
para('<b>No se reentrenó ni se recalibró después de observar s007.</b> Las curvas ROC se calculan para describir esta prueba; no se usan para cambiar el umbral evaluado.')
small('Alcance: validación técnica local del MVP. Las imágenes provienen de una única sesión final y de un catálogo de diez pictogramas; el resultado no demuestra rendimiento universal en otros dispositivos, usuarios o diseños de pictogramas.')
# Protocolo
page('Diseño de la prueba final')
para('La evaluación se ejecutó una vez con el modelo seleccionado antes de abrir las predicciones de s007. Se usó la misma función classify_image de la aplicación, con corrección EXIF, conversión RGB, redimensionado LANCZOS a 192 × 192 y normalización incorporada en MobileNetV3. La salida del detector es similitud de características, no una probabilidad de que la imagen sea conocida.')
table(['Elemento','Configuración congelada'],[('Checkpoint','models/mobilenet_app_192_20261020/best.keras'),('Entrenamiento del modelo único','s001-s005 y s008: 1800 imágenes conocidas'),('Selección de época y calibración','s006: 300 conocidas y 50 desconocidas'),('Prueba final','s007: 300 conocidas y 50 desconocidas'),('Rechazo','kNN coseno escalado; promedio de 5 vecinos de entrenamiento'),('Umbral fijo',str(m['threshold'])),('Regla de rechazo','Similitud menor o igual al umbral'),('Elección de checkpoint','Mínima pérdida interna; época 60 de 60 ejecutadas'),('Semilla de referencia','42')],[150,340])
heading('Verificaciones previas y posteriores')
para('Se verificaron los hashes SHA-256 del checkpoint y de las referencias, su compatibilidad de clases y tamaño, las 350 filas de metadata y la existencia de cada imagen. Se descartaron duplicados exactos dentro de s007 y coincidencias con 2400 imágenes de desarrollo. Las referencias kNN contienen 1800 entradas solo de entrenamiento. Al terminar, se verificó que imágenes, configuración, checkpoint y referencias mantuvieran sus hashes.')
small('Checkpoint SHA-256: '+m['model_sha256'])
small('Referencias SHA-256: '+protocol['selection']['rejection_detector']['references_sha256'])
para('La independencia comprobada por archivo y hash no descarta semejanzas visuales, repetición de objetos ni correlación por condiciones de captura. No se efectuó una búsqueda automatizada de duplicados perceptuales. Las desconocidas son objetos, texto y escenas; no cubren todo pictograma ajeno al catálogo.')
src(f"reports/{a.run}/protocol_frozen.json; test_inventory.json; verification.json")
# Métricas
page('Métricas finales y criterios de aceptación')
table(['Medida','Numerador y denominador','Resultado'],metric_table(),[240,115,135])
para(f"El macro-F1 de clasificación cerrada es <b>{m['closed_set_report']['macro avg']['f1-score']:.4f}</b>. La precisión macro es {pct(m['closed_set_report']['macro avg']['precision'])} y el recall macro {pct(m['closed_set_report']['macro avg']['recall'])}. Al estar equilibradas las clases, los promedios macro y ponderado coinciden en F1.")
heading('Lectura de los denominadores')
para('El 97 % describe las 300 entradas conocidas. El 58 % describe solo las 50 desconocidas. El 91,43 % operativo total corresponde a 291 conocidas correctas aceptadas más 29 desconocidas rechazadas, sobre 350 entradas; depende de esa mezcla de clases y no sustituye los dos indicadores separados. La precisión entre todas las salidas aceptadas es 291/321: las 21 desconocidas aceptadas también cuentan como errores.')
heading('Incertidumbre descriptiva')
interval=m['wilson95_descriptive'];table(['Proporción','Intervalo Wilson 95 % por imagen'],[('Exactitud conocidas',pct(interval['known_accuracy'][0])+' a '+pct(interval['known_accuracy'][1])),('Rechazo desconocidas',pct(interval['unknown_rejection'][0])+' a '+pct(interval['unknown_rejection'][1])),('Rechazo conocidas',pct(max(0,interval['known_rejection'][0]))+' a '+pct(interval['known_rejection'][1]))],[245,245])
para('Estos intervalos son descriptivos bajo un supuesto binomial por imagen. Las capturas de una misma sesión pueden estar correlacionadas y el intervalo no incorpora variación entre sesiones. Cero rechazos sobre 300 conocidas no prueba una tasa poblacional nula; el rechazo de desconocidos se estima con solo 50 casos.')
para('El objetivo de clasificación se supera tanto antes como después del rechazo. El criterio de rechazo de 70 % no se alcanza: se requerían 35 rechazos y se observaron 29. El objetivo de calibración de 80 % y el límite interno de 1 % eran reglas para s006, no garantías sobre una sesión nueva.')
src(f'reports/{a.run}/metrics.json')
page('Matriz de clasificación de pictogramas conocidos')
figure('04_confusion_cerrada.png','Figura 1. Filas: clase real. Columnas: clase elegida antes de aplicar el detector. Cada fila contiene 30 imágenes. Fuente: 300 predicciones de s007.',maxheight=455)
para('Seis clases tuvieron recall del 100 %: agua, comer, baño, dolor, sí, jugar y ayuda son siete clases en total. Las pérdidas de recall se concentraron en papá, no y mamá. Las clases dolor y jugar recibieron tres falsos positivos cada una desde otras clases conocidas.')
# Reemplaza enumeración para evitar ambigüedad en la lectura.
story[-1]=P('Siete clases tuvieron recall del 100 %: agua, comer, baño, dolor, sí, jugar y ayuda. Las pérdidas de recall se concentraron en papá, no y mamá. Dolor y jugar recibieron tres falsos positivos cada una desde otras clases conocidas.')
para('Papá es la clase con menor recall: 25/30 (83,33 %). Esta concentración justifica recolectar más variación de papá en futuros datos de desarrollo y analizar recortes y encuadres, sin retirar errores de esta prueba final.')
page('Precisión recall y F1 por clase')
table(['Clase','Precisión','Recall','F1','Soporte'],[[c,pct(m['closed_set_report'][c]['precision']),pct(m['closed_set_report'][c]['recall']),f"{m['closed_set_report'][c]['f1-score']:.4f}",'30'] for c in classes],[105,105,105,100,75])
small('Tabla 1. Clasificación cerrada en las 300 conocidas. F1 es adimensional; precisión y recall se muestran en porcentaje.')
figure('06_metricas_clase.png','Figura 2. Métricas de clasificación cerrada por clase. Fuente: s007, n=30 por clase.',maxheight=230)
para('La ausencia de rechazo de conocidas hace que el recall operativo de esas clases sea igual al cerrado. Su precisión operativa puede ser menor, porque incluye desconocidas que fueron aceptadas con esa etiqueta. Por eso la siguiente matriz incorpora una salida adicional unknown.')
page('Matriz operativa con entradas desconocidas')
figure('05_confusion_operativa.png','Figura 3. Resultado del paquete completo: diez clases y salida unknown. Esta salida representa rechazo, no una undécima clase entrenada. Fuente: s007, 350 imágenes.',maxheight=450)
para(f"El macro-F1 operativo sobre once etiquetas es {m['operational_report']['macro avg']['f1-score']:.4f}. Se conserva separado del macro-F1 cerrado porque cambia el conjunto de etiquetas y se incorporan 50 desconocidas. La matriz identifica qué clases reciben falsas aceptaciones desde fuera del catálogo.")
page('Métricas operativas por etiqueta')
table(['Etiqueta','Precisión','Recall','F1','Soporte'],[[c,pct(m['operational_report'][c]['precision']),pct(m['operational_report'][c]['recall']),f"{m['operational_report'][c]['f1-score']:.4f}",str(int(m['operational_report'][c]['support']))] for c in classes+['unknown']],[110,105,105,100,70])
para('Estas métricas incluyen las 350 entradas. Las falsas aceptaciones de desconocidas reducen la precisión de las etiquetas que las reciben. La salida unknown tiene precisión 100 % porque ninguna conocida fue rechazada, pero recall 58 % porque solo detectó 29 de las 50 desconocidas. Esa precisión perfecta no equivale a detección completa.')
para(f"Promedio macro operativo: precisión {pct(m['operational_report']['macro avg']['precision'])}, recall {pct(m['operational_report']['macro avg']['recall'])} y F1 {m['operational_report']['macro avg']['f1-score']:.4f}. Se asigna el mismo peso a cada etiqueta. El promedio ponderado usa los soportes observados: 30 por clase conocida y 50 para unknown.")
src(f'reports/{a.run}/metrics.json; predictions.csv')
page('Funcionamiento del detector de desconocidos')
figure('07_detector_final.png','Figura 4. Histogramas de cantidad por similitud y ROC de detección. El punto operativo rojo usa exclusivamente el umbral fijado en s006; la curva es un diagnóstico posterior, no un procedimiento de ajuste.',maxheight=260)
table(['Indicador del detector','Valor'],[('Desconocidas rechazadas','29/50 = 58,00 %'),('Desconocidas falsas aceptadas','21/50 = 42,00 %'),('Conocidas rechazadas','0/300 = 0,00 %'),('AUROC de detección',f"{m['unknown_auroc']:.4f}"),('Precisión promedio PR para desconocidos',f"{m['unknown_average_precision']:.4f}")],[300,190])
para('La AUROC alta y el rechazo insuficiente no se contradicen. La primera describe el orden relativo de similitudes al recorrer umbrales; el 58 % describe el único umbral desplegado. El detector separa bien las distribuciones en esta muestra, pero la calibración interna no trasladó el nivel de rechazo previsto a s007.')
para('No se eligió un nuevo umbral a partir de esta curva. La hipótesis de desajuste de calibración requiere comprobarse con nuevas sesiones de desarrollo, desconocidos más diversos y un nuevo conjunto final independiente.')
page('Errores de clasificación y salidas aceptadas')
wrong=[r for r in preds if r['true_label']!='unknown' and r['true_label']!=r['predicted_operational']]
table(['Archivo','Real','Salida','Softmax máx.','Similitud'],[[r['filename'],r['true_label'],r['predicted_operational'],f"{float(r['confidence']):.4f}",f"{float(r['similarity']):.4f}"] for r in wrong],[190,55,65,90,90],compact=True)
small('Tabla 2. Los nueve errores conocidos se conservan íntegros. Softmax y similitud son medidas distintas; el rechazo usa solo similitud.')
para('Cinco errores corresponden a papá, tres a no y uno a mamá. Hay errores con softmax máximo superior a 0,97; una confianza alta no garantiza corrección. El detector kNN está destinado a entradas fuera del catálogo y no identifica necesariamente confusiones entre pictogramas conocidos.')
figure('09_resultados_operativos.png','Figura 5. Conteos operativos finales. Fuente: predicciones individuales guardadas.',maxheight=220)
page('Desconocidas aceptadas incorrectamente')
unknown_errors=[r for r in preds if r['true_label']=='unknown' and r['predicted_operational']!='unknown']
table(['Archivo','Clase asignada','Softmax máx.','Similitud'],[[r['filename'],r['predicted_operational'],f"{float(r['confidence']):.4f}",f"{float(r['similarity']):.4f}"] for r in unknown_errors],[200,100,95,95],compact=True)
para('Cada fila es una entrada válida que debería haber producido Pictograma no reconocido. Las fotos no se excluyen del resultado por su dificultad. El análisis posterior sirve para proponer nuevas pruebas; no autoriza a ajustar el paquete con estas mismas muestras y presentar una segunda puntuación como independiente.')
# Experimentos
page('Evolución de los experimentos de clasificación')
para('Se localizaron trece resultados de clasificación y nueve ensayos de rechazo en la evidencia del proyecto. Las primeras pruebas usaron cinco clases; luego se compararon diez clases mediante rondas por sesión. Las dos aplicaciones únicas se calibraron con s006. Solo el paquete seleccionado de 192 × 192 se evaluó aquí sobre s007.')
rows=[]
for i,e in enumerate(cat['classification'],1):rows.append([f'E{i:02d}',e['label'],e['stage'],str(e['n']),f"{e['correct']}/{e['n']}",pct(e['accuracy']),f"{e['macro_f1']:.4f}"])
table(['ID','Experimento','Tipo de evidencia','N','Aciertos','Exactitud','Macro F1'],rows,[30,140,85,35,60,75,65],compact=True)
para('Las validaciones de cinco clases no se comparan directamente con las de diez. Las rondas de seis sesiones y las de siete sesiones cambian la cantidad de entrenamiento por ronda. Las comparaciones de resolución 128/192 con s008 sí conservan las particiones, pero en la CNN con Flatten también cambia el número de parámetros.')
small('Los identificadores completos, resultados por clase y rondas se detallan en los anexos y en experiments_classification.csv, experiments_per_class.csv y experiments_folds.csv.')
page('Resultados cruzados y selección del procedimiento')
figure('01_clasificacion_desarrollo.png','Figura 6. Exactitud agrupada sobre sesiones externas de desarrollo. Los denominadores son 1800 o 2100 según el protocolo. La línea marca 70 %, sin convertir estos ensayos adaptativos en prueba final.',maxheight=340)
para('En seis rondas, la CNN base obtuvo 50,83 % y MobileNet 74,56 %. Cambiar Flatten por promedio global dio 25,17 %; reducir la tasa de aprendizaje de la CNN a 0,0003 dio 40,33 %. Estas variantes no mejoraron la CNN base bajo ese protocolo. La continuación del ajuste fino de MobileNet alcanzó 80,06 %. Son decisiones de desarrollo basadas en sesiones externas reutilizadas.')
para('Con s008 se entrenó con cinco sesiones por ronda en lugar de cuatro. La CNN a 128 alcanzó 77,95 % y MobileNet a 128, 84,62 %. No puede atribuirse toda la mejora al número de fotos: también cambia la distribución de sesiones de entrenamiento y evaluación.')
page('Resolución y variación entre sesiones')
figure('02_sesiones_resoluciones.png','Figura 7. Cada punto usa 300 imágenes de la sesión externa correspondiente. 128 y 192 comparten las mismas particiones de siete rondas.',maxheight=300)
para('MobileNet pasó de 1777/2100 a 1964/2100 aciertos: una mejora de 187 imágenes y 8,90 puntos porcentuales. La CNN pasó de 1637/2100 a 1477/2100: perdió 160 aciertos. La caída se concentra en s001, que pasó de 157 a 46 aciertos (111 de los 160 perdidos). No demuestra que aumentar resolución sea siempre perjudicial.')
table(['Arquitectura','Parámetros 128','Parámetros 192','Mediana 128','Mediana 192'],[('CNN compacta','323370','651050','10,52 ms','11,57 ms'),('MobileNetV3-Small','944890','944890','96,80 ms','97,52 ms')],[125,95,95,87,88])
para('Los tiempos históricos miden solo la llamada al clasificador, batch 1, CPU local, checkpoint de fold 1 y calentamiento. Excluyen preprocesamiento, kNN, red y cámara. La CNN usa Flatten, por lo que aumenta su capa densa; MobileNet mantiene el total de parámetros. La comparación no aísla exclusivamente el efecto de resolución en la CNN.')
src('reports/resolution_192_20261019/comparison.json y latency_*.json')
page('Experimentos de rechazo de desconocidos')
rows=[]
for i,e in enumerate(cat['rejection'],1):rows.append([f'R{i:02d}',e['label'],str(e['known_images'])+'/'+str(e['unknown_images']),f"{e['unknown_rejected']}/{e['unknown_images']}",pct(e['unknown_rejection_rate']),f"{e['known_rejected']}/{e['known_images']}",pct(e['known_rejection_rate'])])
table(['ID','Procedimiento','N con./desc.','Desc. rechaz.','Tasa desc.','Con. rechaz.','Tasa con.'],rows,[28,145,60,65,68,65,59],compact=True)
figure('03_rechazo_desarrollo.png','Figura 8. Resultados externos de desarrollo. Se excluyen de la gráfica las calibraciones de los modelos únicos. Un mayor rechazo de desconocidos puede tener un coste de rechazo de conocidas.',maxheight=245)
para('Softmax rechazó 60 % de desconocidas a costa de 23,06 % de conocidas. kNN con objetivo conservador redujo mucho ese coste. El límite interno del 5 % no garantizó 5 % externo: produjo 15,94 % de rechazo conocido. A 192, el objetivo interno 80 % con límite 1 % alcanzó 75 % de desconocidas externas y 0,29 % de conocidas rechazadas. Ninguno de estos porcentajes se heredó automáticamente al modelo único.')
page('Entrenamiento del modelo seleccionado y calibración')
figure('08_curvas_modelo_seleccionado.png','Figura 9. Modelo único con 1800 imágenes de entrenamiento y 300 de validación s006. Línea discontinua: cambio de etapa; línea punteada: época seleccionada. No contiene métricas s007 durante entrenamiento.',maxheight=240)
para('El modelo único se inició desde pesos ImageNet, con lotes de 32 y semilla 42. Se ejecutaron 20 épocas con base congelada y 40 de ajuste fino de las últimas 30 capas, manteniendo BatchNormalization congelada. Se utilizó Adam 0,001 en la primera etapa y 0,00001 en la segunda. La selección por menor val_loss eligió la época global 60. Se alcanzó el máximo de épocas; esto no demuestra convergencia.')
table(['Indicador','Validación interna s006','Prueba final s007'],[('Conocidas correctas','278/300 = 92,67 %','291/300 = 97,00 %'),('Conocidas correctas aceptadas','277/300 = 92,33 %','291/300 = 97,00 %'),('Conocidas rechazadas','2/300 = 0,67 %','0/300 = 0,00 %'),('Desconocidas rechazadas','40/50 = 80,00 %','29/50 = 58,00 %')],[220,135,135])
para('El objetivo de calibración se cumplía en s006, una sesión compartida con selección de época. La caída a 58 % en rechazo final muestra que esa calibración no aseguró transferencia a otra sesión. El 97 % de s007 es el resultado del modelo único; el 93,52 % histórico pertenece a siete modelos externos de validación cruzada.')
heading('Tiempo observado en la evaluación final')
para(f"Mediana por imagen: {m['latency']['median_seconds']*1000:.2f} ms; percentil 95: {m['latency']['p95_seconds']*1000:.2f} ms. Incluye lectura, preprocesamiento, clasificador y kNN en ejecución serial local; excluye carga inicial del paquete, interfaz, red y cámara. No es una medición de rendimiento móvil ni es comparable directamente con el benchmark histórico del clasificador aislado.")
page('Conclusiones y límites del resultado')
heading('Conclusiones respaldadas por la evidencia')
para('El procedimiento seleccionado reconoce correctamente 97 % de los pictogramas conocidos de la sesión final y supera el mínimo académico de 70 %. Las siete clases con recall perfecto y el macro-F1 de 0,9696 muestran buen desempeño dentro de este catálogo y bajo las condiciones capturadas. Papá concentra cinco de los nueve errores y es la primera clase a revisar en nuevos datos de desarrollo.')
para('La respuesta ante desconocidos es la limitación principal del paquete: 42 % de las entradas ajenas al catálogo se aceptaron como alguna clase conocida. Un clasificador cerrado con buena exactitud no basta para asegurar una respuesta fiable fuera de distribución. Aunque la AUROC es alta, el punto operativo congelado no alcanza el nivel de rechazo buscado.')
para('MobileNetV3-Small a 192 fue el mejor procedimiento de clasificación entre los ensayados en validación cruzada. La resolución mayor benefició a esa arquitectura bajo el protocolo registrado; la CNN compacta empeoró, con cambios simultáneos de capacidad y marcada variación entre sesiones. No se generaliza la conclusión a todas las CNN ni a cualquier conjunto de datos.')
heading('Qué no permite concluir esta prueba')
para('Una sola sesión, 30 fotos por clase y 50 desconocidas no representan toda la variedad de entornos. Las clases corresponden a diseños concretos; no se midió generalización a otros estilos, impresiones o pictogramas alternativos. No se hicieron pruebas con usuarios finales ni se demostró utilidad clínica o mejora comunicativa. Las imágenes correlacionadas reducen la información efectiva frente a una muestra aleatoria independiente.')
para('La búsqueda de arquitectura, resolución y reglas de rechazo fue adaptativa sobre los mismos datos de desarrollo. Por eso sus resultados no son estimaciones finales independientes. s007 conserva el valor de prueba del paquete congelado, pero desde ahora sus errores ya son conocidos: cualquier ajuste guiado por ellos requiere otro conjunto final para una nueva afirmación de generalización.')
heading('Criterio de cierre del MVP')
para('El reconocimiento de las diez clases alcanza el objetivo de exactitud en esta prueba. El requisito de rechazo confiable de entradas ajenas queda parcialmente satisfecho y debe declararse como una limitación, no como un objetivo cumplido. La interfaz puede demostrar el modelo evaluado manteniendo visible el carácter técnico y experimental de los resultados.')
page('Mejoras futuras y plan de verificación')
for title,text in [
 ('Ampliar negativos y sesiones de calibración','Recolectar desconocidos con dibujos, pictogramas parecidos, tarjetas vacías, texto y objetos en diferentes luces y dispositivos. Separar varias sesiones de calibración de las usadas para seleccionar época. Comprobar estabilidad del umbral por sesión y no solo la tasa agrupada.'),
 ('Reducir falsas aceptaciones con una regla fijada de antemano','Definir una tasa máxima de falsas aceptaciones desconocidas y un coste tolerable sobre conocidas. Comparar reglas de rechazo en nuevos datos de desarrollo, por ejemplo combinación de similitud con incertidumbre o distancias por clase. Se trata de hipótesis para ensayar, no de mejoras demostradas; no se elige un umbral con s007.'),
 ('Mejorar las clases con confusiones','Agregar papá, no y mamá en condiciones diversas, documentar tamaño aparente, encuadre y oclusiones. Evaluar recorte o detección de la tarjeta para reducir el peso del fondo. Mantener negativos de objetos relacionados con las clases para comprobar que no se reconoce el fondo en lugar del símbolo.'),
 ('Ampliar la evaluación independiente','Conservar s007 como resultado histórico y recolectar una nueva prueba sellada, idealmente de varias sesiones, dispositivos y personas. Definir previamente métricas por clase y de rechazo, criterios de aceptación y procedimiento. Estimar variación entre sesiones, en vez de tratar fotografías correlacionadas como observaciones independientes.'),
 ('Controlar coste y estabilidad del sistema','Medir tiempos del flujo completo en el dispositivo de uso, memoria y estabilidad de captura. Ensayar cuantización o formatos de despliegue solo después de verificar que clasificación, rechazo y umbrales mantengan compatibilidad. La mediana local actual no garantiza rendimiento en cámara o móvil.'),
 ('Trazabilidad y uso supervisado','Versionar el paquete de modelo, referencias, clases, preprocesamiento y umbral como una unidad. Mantener hashes, dataset, manifiestos y predicciones. Mostrar rechazo claro al usuario y verificar el flujo con personas usuarias en un estudio apropiado antes de afirmar beneficios de accesibilidad.')]:
 heading(title);para(text)
# Anexos por experimento
for idx,e in enumerate(cat['classification'],1):
 page(f"Anexo E{idx:02d} {e['label']}")
 small(f"Identificador: {e['id']} | Arquitectura: {e['architecture']} | Evidencia: {e['stage']}")
 para(f"Aciertos {e['correct']}/{e['n']} ({pct(e['accuracy'])}); macro-F1 {e['macro_f1']:.4f}. "+('Los resultados son validación interna, no prueba final.' if e['stage']!='CV desarrollo' else f"Se agregan {e['folds']} rondas externas. Desviación entre sesiones: {pct(e['std_sessions'])}; no es un intervalo de confianza."))
 if 'history_figure' in e:figure(e['history_figure'],'Trayectorias internas guardadas. Cada línea representa una ronda; épocas y etapas corresponden a ese experimento. No se promedian curvas con diferentes duraciones.',maxheight=158)
 cr=e['report'];table(['Clase','Precisión','Recall','F1','N'],[[c,pct(v['precision']),pct(v['recall']),f"{v['f1-score']:.4f}",str(int(v['support']))] for c,v in cr.items() if c in classes],[110,110,110,90,70],compact=True)
 fs=[r for r in folds if r['experiment']==e['id'] and r['architecture']==e['architecture']]
 if fs:
  table(['Ronda','Sesión','Aciertos','Exactitud','Época elegida','Épocas'],[[r['fold'],r['outer_session'],r['correct']+'/'+r['n'],pct(float(r['accuracy'])),r['best_epoch'],r['epochs_executed']] for r in fs],[55,65,90,95,100,85],compact=True)
 src(e['source'])
page('Trazabilidad y archivos de entrega')
para('El PDF resume los resultados y muestra las figuras principales y curvas por experimento. El archivo evidencia_experimentos.zip conserva 964 artefactos históricos de los experimentos identificados, incluidas las gráficas y tablas disponibles. No se incluyen checkpoints de entrenamiento. Los pesos permanecen en models y las imágenes originales en data/raw.')
table(['Archivo de la evaluación final','Contenido'],[('protocol_frozen.json','Selección, hashes, tamaños y métricas previstas antes de predecir'),('test_inventory.json','350 imágenes con clase, ruta y hash'),('predictions.csv','350 salidas completas con probabilidades, similitud y rechazo'),('metrics.json','Métricas finales y matrices de confusión'),('verification.json','Comprobaciones posteriores de inmutabilidad y consistencia'),('errors.csv','Errores operativos conocidos y desconocidos'),('experiment_catalog.json','13 resultados de clasificación y 9 ensayos de rechazo'),('experiments_classification.csv','Resumen numérico de clasificación histórica'),('experiments_per_class.csv','Precisión, recall, F1 y soporte históricos por clase'),('experiments_folds.csv','Resultados, épocas y tiempos de cada ronda'),('experiments_rejection.csv','Métricas históricas de rechazo'),('figures/','22 figuras generadas para esta síntesis'),('evidence_manifest.json','Índice y hashes de las fuentes históricas archivadas')],[195,295])
heading('Fuentes y reproducibilidad')
para('La fuente primaria son los archivos JSON, CSV y protocolos locales del proyecto. No se usaron métricas inferidas desde capturas de pantalla ni se copiaron porcentajes de documentación sin contrastarlos con los artefactos. Los resúmenes históricos conservan su rol de desarrollo, validación interna o piloto. Los valores del informe proceden de esos artefactos y de las 350 predicciones finales guardadas.')
small('Código de evaluación: scripts/evaluate_final_s007.py. Código de síntesis: scripts/build_final_figures.py y scripts/build_final_report.py. La evaluación tiene un bloqueo contra repetir una prueba final completada; la regeneración de tablas y PDF lee predicciones existentes y no vuelve a ejecutar el modelo.')
para('El umbral y los pesos evaluados no cambiaron. Cualquier futura versión entrenada o calibrada con conocimiento de s007 debe tener un identificador distinto y evaluarse sobre nuevos datos independientes.')
# Render
output=root/'output/pdf';output.mkdir(parents=True,exist_ok=True);pdf=output/f'informe_final_pictovoz_{a.run}.pdf'
def footer(canvas,doc):
 canvas.saveState();canvas.setFont('Arial',7);canvas.setFillColor(colors.HexColor('#52616b'));canvas.drawString(42,25,'Pictovoz | Evaluación final s007 | 21 de octubre de 2026');canvas.drawRightString(570,25,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(pdf),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42,title='Evaluación final de Pictovoz y evolución experimental',author='Proyecto Pictovoz')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('PDF',pdf)
