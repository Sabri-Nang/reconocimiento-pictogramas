"""Analiza predicciones externas sin volver a entrenar ni consultar s007."""
from pathlib import Path
import csv
import json
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RUN="cv10_s008_128_20261019"

def read_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def summarize(rows,key,metadata):
    groups=defaultdict(lambda:[0,0])
    for row in rows:
        value=metadata[Path(row['raw_path']).name][key] if key=='distance' else row[key]
        groups[value][0]+=row['class_id']==row['predicted_class'];groups[value][1]+=1
    return {k:dict(correct=v[0],total=v[1],accuracy=v[0]/v[1]) for k,v in groups.items()}

def main():
    source=ROOT/'reports'/RUN;dest=source/'error_analysis';dest.mkdir(exist_ok=False)
    metadata={r['filename']:r for r in read_rows(ROOT/'data/metadata.csv')}
    protocol=json.loads((source/'protocol.json').read_text(encoding='utf-8'))
    sessions=set(protocol['config']['sessions']);assert 's007' not in sessions
    classes=[c['id'] for c in protocol['project']['classes']]
    data={};predictions={}
    for arch in ('cnn','mobilenet'):
        rows=read_rows(source/f'{arch}_out_of_fold_predictions.csv');predictions[arch]=rows
        assert len(rows)==len({r['raw_path'] for r in rows})==2100
        assert {r['session_id'] for r in rows}==sessions
        for r in rows:assert int(r['correct'])==int(r['class_id']==r['predicted_class'])
        old=[r for r in rows if r['session_id']!='s008'];new=[r for r in rows if r['session_id']=='s008']
        confusion=Counter((r['class_id'],r['predicted_class']) for r in rows if r['class_id']!=r['predicted_class'])
        stopping=[]
        for fold in protocol['folds']:
            folder=source/f"fold_{fold['fold']:02d}"/arch
            stop=json.loads((folder/'stopping.json').read_text(encoding='utf-8'))
            epochs=read_rows(folder/'epochs.csv');best=next(r for r in epochs if int(r['epoch'])==stop['best_epoch'])
            stopping.append(dict(fold=fold['fold'],best_epoch=stop['best_epoch'],epochs_executed=len(epochs),train_accuracy_at_best=float(best['accuracy']),internal_accuracy_at_best=float(best['val_accuracy']),stages=stop['stages']))
        data[arch]=dict(correct=sum(int(r['correct']) for r in rows),total=len(rows),by_class=summarize(rows,'class_id',metadata),by_session=summarize(rows,'session_id',metadata),by_distance=summarize(rows,'distance',metadata),historical_sessions=dict(correct=sum(int(r['correct']) for r in old),total=len(old),by_distance=summarize(old,'distance',metadata)),new_session=dict(correct=sum(int(r['correct']) for r in new),total=len(new),by_distance=summarize(new,'distance',metadata)),top_confusions=[dict(actual=a,predicted=p,count=n) for (a,p),n in confusion.most_common(12)],stopping=stopping)
    assert {r['raw_path'] for r in predictions['cnn']}=={r['raw_path'] for r in predictions['mobilenet']}
    references={'cnn':ROOT/'reports/cv10_20261018_000712/cnn_out_of_fold_predictions.csv','mobilenet':ROOT/'reports/cv10_mobilenet_extend_20261018/mobilenet_out_of_fold_predictions.csv'}
    for arch,path in references.items():
        before={r['raw_path']:r for r in read_rows(path)};after={r['raw_path']:r for r in predictions[arch] if r['session_id']!='s008'}
        assert set(before)==set(after) and len(before)==1800
        a=sum(int(r['correct']) for r in before.values());b=sum(int(r['correct']) for r in after.values())
        data[arch]['historical_comparison']=dict(reference_correct=a,candidate_correct=b,total=1800,delta_correct=b-a,delta_percentage_points=100*(b-a)/1800,limitation='Mismas imagenes externas, pero cambian entrenamiento, algunas sesiones internas y presupuesto MobileNet; no aisla efecto causal de s008.')
    result=dict(source_run=RUN,architectures=data,selected_model_unchanged=True,test_used=False,interpretation='Desarrollo adaptativo; no prueba independiente. No mide deteccion de tarjetas en video.')
    (dest/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,axes=plt.subplots(2,2,figsize=(15,10));colors={'cnn':'#7b67ae','mobilenet':'#17836e'}
    for offset,arch in enumerate(('cnn','mobilenet')):
        c=data[arch];x=list(range(10));axes[0,0].bar([i+(offset-.5)*.36 for i in x],[c['by_class'][k]['accuracy']*100 for k in classes],width=.36,label=arch.upper(),color=colors[arch])
        distances=['corta','media','larga'];axes[0,1].plot(distances,[c['by_distance'][k]['accuracy']*100 for k in distances],marker='o',label=arch.upper(),color=colors[arch])
        ordered=protocol['config']['sessions'];axes[1,0].plot(ordered,[c['by_session'][k]['accuracy']*100 for k in ordered],marker='o',label=arch.upper(),color=colors[arch])
        comparison=c['historical_comparison'];axes[1,1].plot(['Referencia anterior','Nuevo entrenamiento'],[100*comparison['reference_correct']/1800,100*comparison['candidate_correct']/1800],marker='o',label=arch.upper(),color=colors[arch])
    axes[0,0].set(xticks=range(10),xticklabels=classes,title='Recall por clase: 210 imagenes de cada clase');plt.setp(axes[0,0].get_xticklabels(),rotation=45,ha='right')
    axes[0,1].set(title='Aciertos por distancia declarada')
    axes[1,0].set(title='Sesion externa: 300 imagenes por punto')
    axes[1,1].set(title='Comparacion sobre las mismas 1800 imagenes historicas')
    for ax in axes.flat:ax.set(ylim=(0,101),ylabel='Porcentaje (%)');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('CNN y MobileNet a128x128: siete sesiones de desarrollo');fig.tight_layout(rect=(0,.06,1,.95));fig.text(.02,.02,'No prueba final. Cambian datos de entrenamiento y presupuesto: no atribuir toda mejora exclusivamente a s008. s007 excluida.',fontsize=9)
    fig.savefig(dest/'classification_analysis.png',dpi=145);plt.close(fig)
    lines=['# Analisis de errores: siete sesiones a128x128','','2100 predicciones externas unicas por arquitectura. s007 no utilizada. Resultados de desarrollo.','']
    for arch,c in data.items():
        lines+=[f"## {arch.upper()}",f"Aciertos: {c['correct']}/{c['total']} ({100*c['correct']/c['total']:.2f}%).",'']
        lines += [f"- Distancia {k}: {v['correct']}/{v['total']} ({100*v['accuracy']:.2f}%)." for k,v in c['by_distance'].items()]
        h=c['historical_comparison'];lines += ['',f"Mismas1800 imagenes historicas: {h['reference_correct']} antes y {h['candidate_correct']} ahora, diferencia {h['delta_correct']} aciertos ({h['delta_percentage_points']:.2f} puntos). {h['limitation']}",'','Confusiones mas frecuentes:']
        lines += [f"- {v['actual']} -> {v['predicted']}: {v['count']}." for v in c['top_confusions'][:5]]
        lines+=['']
    lines+=['## Interpretacion','MobileNet es mejor en el conjunto agrupado; CNN supera a MobileNet en s008 (278/300 frente a242/300). No hay un ganador universal por sesion.','La principal limitacion sigue siendo distancia larga. No garantiza resolverse al aumentar resolucion.','Comparar192x192 despues manteniendo las mismas siete rondas, semillas, arquitectura y presupuestos por modelo. Generar desde originales, conservar artefactos128. No modificar la aplicacion antes de elegir y calibrar un modelo unico.','La evaluacion previa de la aplicacion en s008 (247/300) corresponde a otro modelo y particion interna; no comparar directamente con242/300 como si solo hubiese cambiado el entrenamiento con s008.','Las diferencias train/interna son descriptivas: train incluye aumentos y pesos cambiantes. No demostrar sobreajuste solo con dos exactitudes.','Los negativos nuevos solo contienen objetos/escenas; no prueban rechazo general de pictogramas ajenos.']
    (dest/'lectura_resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({a:dict(correct=c['correct'],historical=c['historical_comparison']) for a,c in data.items()},ensure_ascii=False))
if __name__=='__main__':main()
