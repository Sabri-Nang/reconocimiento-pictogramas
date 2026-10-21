"""Catálogo y figuras a partir de evidencia histórica y predicciones finales guardadas."""
import argparse,csv,json,hashlib,zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve,precision_recall_curve
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--run',required=True);a=p.parse_args();root=a.project;reports=root/'reports';out=reports/a.run;fig=out/'figures';fig.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def csvread(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def savecsv(p,rows):
 if not rows:return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':190})
blue='#235b78';red='#b34c43';gray='#647078';green='#367a64'
classes=read(out/'metrics.json')['classes'];classifications=[];folds=[];perclass=[];sources=[]
configs=[('cv10_20261018_000712','CV inicial 128'),('cv10_cnn_gap_20261018','CNN GAP 128'),('cv10_cnn_lr0003_20261018','CNN LR 0,0003'),('cv10_mobilenet_extend_20261018','MobileNet ajuste extendido'),('cv10_s008_128_20261019','CV con s008 a 128'),('cv10_s008_192_20261019','CV con s008 a 192')]
for run,label in configs:
 d=read(reports/run/'summary.json');sources.append(run)
 for arch,v in d['results'].items():
  cr=v['pooled_classification_report'];n=int(cr['macro avg']['support']);acc=cr['accuracy'];correct=sum(f['outer_correct'] for f in v['folds']);assert correct==round(n*acc)
  e=dict(id=run,architecture=arch,label=label+' '+arch,stage='CV desarrollo',n=n,correct=correct,accuracy=acc,macro_f1=cr['macro avg']['f1-score'],std_sessions=v['std_across_sessions'],min_accuracy=v['min_accuracy'],max_accuracy=v['max_accuracy'],folds=len(v['folds']),source=f'reports/{run}/summary.json',report=cr)
  classifications.append(e)
  for cls in classes:perclass.append(dict(experiment=run,architecture=arch,stage=e['stage'],class_id=cls,**cr[cls]))
  for f in v['folds']:
   folds.append(dict(experiment=run,architecture=arch,fold=f['fold'],outer_session=f['outer_session'],accuracy=f['outer_accuracy'],correct=f['outer_correct'],n=f['outer_images'],macro_f1=f['macro_f1'],best_epoch=f['best_epoch'],epochs_executed=f['epochs_executed'],training_seconds=f['training_seconds']))
for run,label,stage in [('cnn_20261009_105933','Piloto CNN cinco clases','Validación piloto'),('mobilenet_20261009_111839','Piloto MobileNet cinco clases','Validación piloto'),('mobilenet_app_20261018','Aplicación MobileNet 128','Validación interna'),('mobilenet_app_192_20261020','Aplicación MobileNet 192','Validación interna')]:
 d=read(reports/run/'metrics.json');sources.append(run);cr=d['classification_report'];n=int(cr['macro avg']['support']);acc=cr['accuracy']
 classifications.append(dict(id=run,architecture='cnn' if run.startswith('cnn_') else 'mobilenet',label=label,stage=stage,n=n,correct=round(acc*n),accuracy=acc,macro_f1=cr['macro avg']['f1-score'],std_sessions=None,min_accuracy=None,max_accuracy=None,folds=1,source=f'reports/{run}/metrics.json',report=cr))
 for cls,v in cr.items():
  if cls in classes:perclass.append(dict(experiment=run,architecture=classifications[-1]['architecture'],stage=stage,class_id=cls,**v))
m=read(out/'metrics.json');sources+=['resolution_192_20261019']
rejections=[]
for run,label in [('cv10_unknown_20261018','Softmax 128 seis sesiones'),('cv10_unknown_knn_20261018','kNN 128 seis sesiones'),('cv10_unknown_knn_cap05_20261018','kNN límite interno 5%'),('cv10_s008_unknown_knn_20261019','kNN 128 con s008'),('cv10_s008_192_unknown_knn_20261019','kNN 192 objetivo interno 70%')]:
 d=read(reports/run/'summary.json');sources.append(run);rejections.append(dict(id=run,label=label,stage='CV desarrollo',source=f'reports/{run}/summary.json',**d['pooled']))
run='cv10_s008_192_rejection_targets_20261019';sources.append(run)
for target in ['75','80']:
 d=read(reports/run/f'target_{target}/summary.json');rejections.append(dict(id=run+'/target_'+target,label=f'kNN 192 objetivo {target}% límite 1%',stage='CV desarrollo',source=f'reports/{run}/target_{target}/summary.json',**d['pooled']))
for run,path,label in [('mobilenet_app_20261018','rejection/calibration.json','Aplicación 128 interna'),('mobilenet_app_192_20261020','calibration.json','Aplicación 192 interna')]:
 d=read(reports/run/path);rejections.append(dict(id=run,label=label,stage='Validación interna',source=f'reports/{run}/{path}',**d['metrics']))
for r in rejections:
 r['unknown_rejection_rate']=r['unknown_rejected']/r['unknown_images'];r['known_rejection_rate']=r['known_rejected']/r['known_images'];r['known_accuracy_with_rejection']=r['known_correct_accepted']/r['known_images']
preds=csvread(out/'predictions.csv')
for r in preds:
 for k in ['similarity','confidence','seconds']:r[k]=float(r[k])
 r['rejected']=r['rejected']=='True'
errors=[r for r in preds if r['true_label']!=r['predicted_operational']];savecsv(out/'errors.csv',errors)
savecsv(out/'experiments_classification.csv',[{k:v for k,v in r.items() if k!='report'} for r in classifications]);savecsv(out/'experiments_rejection.csv',rejections);savecsv(out/'experiments_folds.csv',folds);savecsv(out/'experiments_per_class.csv',perclass)
dump(out/'experiment_catalog.json',dict(classification=classifications,rejection=rejections,sources=sources))
# Comparación de CV únicamente; se excluyen validaciones y prueba final.
cv=[r for r in classifications if r['stage']=='CV desarrollo'];f,ax=plt.subplots(figsize=(10,5.6));names=[r['label'] for r in cv];vals=[r['accuracy']*100 for r in cv];bars=ax.barh(names,vals,color=[blue if r['architecture']=='mobilenet' else gray for r in cv]);ax.invert_yaxis();ax.set_xlim(0,108);ax.set_xlabel('Exactitud agrupada externa (%)');ax.set_title('Experimentos de clasificación durante el desarrollo');ax.axvline(70,color=red,ls='--',lw=1)
for b,r in zip(bars,cv):ax.text(b.get_width()+1,b.get_y()+b.get_height()/2,f"{r['accuracy']*100:.2f}%  ({r['correct']}/{r['n']})",va='center',fontsize=8)
f.tight_layout();f.savefig(fig/'01_clasificacion_desarrollo.png');plt.close(f)
# Sesiones y resoluciones comparables.
f,ax=plt.subplots(figsize=(9,4.5))
for run,arch,style in [('cv10_s008_128_20261019','cnn','--'),('cv10_s008_192_20261019','cnn','-'),('cv10_s008_128_20261019','mobilenet','--'),('cv10_s008_192_20261019','mobilenet','-')]:
 rows=[r for r in folds if r['experiment']==run and r['architecture']==arch];ax.plot([r['outer_session'] for r in rows],[100*r['accuracy'] for r in rows],style,marker='o',label=f"{arch} {'192' if '192' in run else '128'}",color=blue if arch=='mobilenet' else red)
ax.set(ylabel='Exactitud externa (%)',xlabel='Sesión externa',ylim=(0,105),title='Comparación por sesión con las mismas particiones');ax.legend(ncol=2);ax.grid(axis='y',alpha=.2);f.tight_layout();f.savefig(fig/'02_sesiones_resoluciones.png');plt.close(f)
# Rechazo CV.
rj=[r for r in rejections if r['stage']=='CV desarrollo'];f,(ax,bx)=plt.subplots(1,2,figsize=(11,5.2),sharey=True);ys=np.arange(len(rj));ax.barh(ys,[100*r['unknown_rejection_rate'] for r in rj],color=blue);bx.barh(ys,[100*r['known_rejection_rate'] for r in rj],color=red);ax.set_yticks(ys,[r['label'] for r in rj]);ax.invert_yaxis();ax.set(xlim=(0,105),xlabel='Desconocidas rechazadas (%)');bx.set(xlim=(0,27),xlabel='Conocidas rechazadas (%)');ax.axvline(70,color=gray,ls='--',lw=1);f.suptitle('Rechazo de desconocidos y coste sobre conocidas en desarrollo');f.tight_layout();f.savefig(fig/'03_rechazo_desarrollo.png');plt.close(f)
# Matrices finales.
for key,labels,name,title in [('closed_confusion_matrix',classes,'04_confusion_cerrada.png','Clasificación de 300 conocidas sin aplicar rechazo'),('operational_confusion_matrix',classes+['unknown'],'05_confusion_operativa.png','Resultado operativo de las 350 imágenes s007')]:
 matrix=np.array(m[key]);f,ax=plt.subplots(figsize=(8.5,7.2));im=ax.imshow(matrix,cmap='Blues');ax.set_xticks(range(len(labels)),labels,rotation=40,ha='right');ax.set_yticks(range(len(labels)),labels);ax.set(xlabel='Salida predicha',ylabel='Clase real',title=title)
 for i in range(len(labels)):
  for j in range(len(labels)):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',fontsize=8,color='white' if matrix[i,j]>matrix.max()/2 else 'black')
 f.colorbar(im,ax=ax,label='Cantidad de imágenes');f.tight_layout();f.savefig(fig/name);plt.close(f)
# Métricas por clase antes y después de rechazo.
f,ax=plt.subplots(figsize=(10,4.4));x=np.arange(10);width=.25
for shift,key,label,color in [(-width,'precision','Precisión',blue),(0,'recall','Recall',green),(width,'f1-score','F1',gray)]:ax.bar(x+shift,[100*m['closed_set_report'][c][key] for c in classes],width,label=label,color=color)
ax.set_xticks(x,classes);ax.set(ylabel='Porcentaje (%)',ylim=(0,106),title='Métricas por clase en s007 antes del rechazo');ax.legend(ncol=3,loc='lower left');f.tight_layout();f.savefig(fig/'06_metricas_clase.png');plt.close(f)
f,(ax,bx)=plt.subplots(1,2,figsize=(10,4.3));known=[r['similarity'] for r in preds if r['true_label']!='unknown'];unknown=[r['similarity'] for r in preds if r['true_label']=='unknown'];bins=np.linspace(min(known+unknown),1,24)
ax.hist(known,bins=bins,alpha=.65,color=blue,label='Conocidas n=300');ax.hist(unknown,bins=bins,alpha=.65,color=red,label='Desconocidas n=50');ax.axvline(m['threshold'],ls='--',color='black',label=f"Umbral fijo {m['threshold']:.4f}");ax.set(xlabel='Similitud kNN escalada (no probabilidad)',ylabel='Imágenes',title='Distribución de similitudes');ax.legend(fontsize=8)
y=[int(r['true_label']=='unknown') for r in preds];scores=[-r['similarity'] for r in preds];fpr,tpr,_=roc_curve(y,scores);bx.plot(fpr,tpr,color=blue,label=f"AUROC {m['unknown_auroc']:.4f}");bx.scatter([m['known_rejection_rate']],[m['unknown_rejection_rate']],color=red,label='Punto operativo congelado');bx.plot([0,1],[0,1],'--',color=gray);bx.set(xlabel='Conocidas rechazadas / conocidas',ylabel='Desconocidas rechazadas / desconocidas',title='ROC descriptiva de detección de desconocidos');bx.legend(fontsize=8);f.tight_layout();f.savefig(fig/'07_detector_final.png');plt.close(f)
# Curvas modelo final seleccionado.
h=csvread(reports/'mobilenet_app_192_20261020/epochs.csv');f,(ax,bx)=plt.subplots(1,2,figsize=(10,4.1));epochs=[int(r['epoch']) for r in h]
for key,label,color in [('accuracy','Entrenamiento',blue),('val_accuracy','Validación s006',red)]:ax.plot(epochs,[float(r[key])*100 for r in h],label=label,color=color)
for key,label,color in [('loss','Entrenamiento',blue),('val_loss','Validación s006',red)]:bx.plot(epochs,[float(r[key]) for r in h],label=label,color=color)
for axes in [ax,bx]:axes.axvline(20.5,color=gray,ls='--',lw=1);axes.axvline(60,color=green,ls=':',lw=1);axes.set_xlabel('Época global');axes.legend(fontsize=8)
ax.set(ylabel='Exactitud (%)',title='Modelo seleccionado antes de abrir s007');bx.set(ylabel='Pérdida de entropía cruzada',title='Selección por mínima pérdida interna');f.tight_layout();f.savefig(fig/'08_curvas_modelo_seleccionado.png');plt.close(f)
# Todas las trayectorias disponibles por experimento, sin promediar épocas incompatibles.
for idx,e in enumerate(classifications):
 run=e['id'];arch=e['architecture'];paths=sorted((reports/run).glob(f'fold_*/{arch}/epochs.csv'))
 if not paths:
  for filename in ['epochs.csv','history.csv']:
   if (reports/run/filename).exists():paths=[reports/run/filename];break
 if not paths:continue
 f,(ax,bx)=plt.subplots(1,2,figsize=(10,3.5))
 for path in paths:
  h=csvread(path)
  if not h or 'val_accuracy' not in h[0]:continue
  x=[float(r.get('epoch',i+1)) for i,r in enumerate(h)];label=path.parent.parent.name if 'fold_' in str(path) else 'validación'
  ax.plot(x,[float(r['val_accuracy'])*100 for r in h],label=label,lw=1);bx.plot(x,[float(r['val_loss']) for r in h],label=label,lw=1)
 ax.set(xlabel='Época registrada',ylabel='Exactitud interna (%)',title=e['label']);bx.set(xlabel='Época registrada',ylabel='Pérdida interna',title='Trayectorias guardadas por ronda');ax.legend(ncol=3,fontsize=6);f.tight_layout();filename=f'historial_{idx+1:02d}.png';f.savefig(fig/filename);plt.close(f);e['history_figure']=filename
# Reparto de resultados finales.
f,ax=plt.subplots(figsize=(9,3.5));values=[m['known_correct_accepted'],m['known_wrong_accepted'],m['known_rejected'],m['unknown_rejected'],m['unknown_false_accepted']];labels=['Conocidas correctas aceptadas','Conocidas erróneas aceptadas','Conocidas rechazadas','Desconocidas rechazadas','Desconocidas aceptadas'];ax.barh(labels,values,color=[blue,red,gray,green,red]);ax.invert_yaxis();ax.set(xlabel='Cantidad de imágenes',title='Resultados operativos finales con umbral congelado')
for i,v in enumerate(values):ax.text(v+.5,i,str(v),va='center')
ax.set_xlim(0,max(values)*1.1);f.tight_layout();f.savefig(fig/'09_resultados_operativos.png');plt.close(f)
dump(out/'experiment_catalog.json',dict(classification=classifications,rejection=rejections,sources=sources))
# Archivo de evidencia de todos los experimentos, excluye pesos, capturas y respaldos.
manifest=[]
with zipfile.ZipFile(out/'evidencia_experimentos.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for run in sources:
  for path in sorted((reports/run).rglob('*')):
   if not path.is_file() or path.suffix.lower() not in {'.json','.csv','.png','.txt','.md'}:continue
   if path.name.startswith('previous_'):continue
   rel=path.relative_to(root).as_posix();archive.write(path,rel);manifest.append(dict(path=rel,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 for path in sorted((root/'config').glob('*.json')):
  archive.write(path,path.relative_to(root).as_posix())
 for path in sorted((root/'docs').glob('*.md')):archive.write(path,path.relative_to(root).as_posix())
dump(out/'evidence_manifest.json',manifest)
print('CATÁLOGO:',len(classifications),'experimentos de clasificación,',len(rejections),'de rechazo; figuras:',len(list(fig.glob('*.png'))),'archivos históricos:',len(manifest))
