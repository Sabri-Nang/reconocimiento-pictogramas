"""Compara128/192 sobre las mismas muestras y mide latencia en un worker aislado."""
import argparse
import os
import sys
import time
import hashlib
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.artifacts import read_json,read_csv,save_json,save_figure,contained
RUNS={128:'cv10_s008_128_20261019',192:'cv10_s008_192_20261019'}
OUT=ROOT/'reports/resolution_192_20261019'

def benchmark(resolution,arch):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
    import numpy as np
    import tensorflow as tf
    from reconocimiento_pictogramas.preprocessing import prepare_image
    tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
    folder=ROOT/'reports'/RUNS[resolution]/'fold_01'
    result=read_json(folder/arch/'result.json');model=tf.keras.models.load_model(contained(result['model_path']),compile=False)
    row=read_csv(folder/'outer.csv')[0]
    image=prepare_image(contained(row['raw_path']),(resolution,resolution));x=np.asarray(image,dtype=np.uint8)[None]
    assert tuple(model.input_shape[1:])==(resolution,resolution,3)
    for _ in range(3):model(x,training=False).numpy()
    times=[]
    for _ in range(20):
        start=time.perf_counter();model(x,training=False).numpy();times.append((time.perf_counter()-start)*1000)
    preprocessing=[]
    for _ in range(5):
        start=time.perf_counter();prepare_image(contained(row['raw_path']),(resolution,resolution));preprocessing.append((time.perf_counter()-start)*1000)
    save_json(OUT/f'latency_{resolution}_{arch}.json',dict(resolution=resolution,architecture=arch,fold=1,model_parameters=int(model.count_params()),batch_size=1,warmup=3,repetitions=20,median_ms=float(np.median(times)),p95_ms=float(np.percentile(times,95)),preprocessing_median_ms=float(np.median(preprocessing)),scope='CPU local, llamada eager al clasificador y salida numpy; excluye carga del modelo, detector kNN, red y camara. Referencia fold1, no todas las rondas.',raw_path=row['raw_path'],test_used=False))

def compare():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    metadata={r['filename']:r for r in read_csv(ROOT/'data/metadata.csv')}
    summary={};protocols={n:read_json(ROOT/'reports'/run/'protocol.json') for n,run in RUNS.items()}
    assert protocols[128]['folds']==protocols[192]['folds']
    for key in ('sessions','seed','batch_size','cnn_epochs','mobilenet_head_epochs','mobilenet_fine_tune_epochs','patience','fine_tune_patience','monitor','min_delta'):
        assert protocols[128]['config'][key]==protocols[192]['config'][key]
    for arch in ('cnn','mobilenet'):
        variants={}
        for size,run in RUNS.items():
            out=ROOT/'reports'/run;rows=read_csv(out/f'{arch}_out_of_fold_predictions.csv')
            assert len(rows)==len({r['raw_path'] for r in rows})==2100 and all(r['session_id']!='s007' for r in rows)
            by={}
            for field in ('distance','session_id','class_id'):
                counts=defaultdict(lambda:[0,0])
                for row in rows:
                    value=metadata[Path(row['raw_path']).name]['distance'] if field=='distance' else row[field]
                    counts[value][0]+=row['class_id']==row['predicted_class'];counts[value][1]+=1
                by[field]={k:dict(correct=v[0],total=v[1],accuracy=v[0]/v[1]) for k,v in counts.items()}
            results=read_json(out/'summary.json')['results'][arch]
            seconds=sum(f['training_seconds'] for f in results['folds']);epochs=sum(f['epochs_executed'] for f in results['folds'])
            variants[str(size)]=dict(correct=sum(int(r['correct']) for r in rows),total=len(rows),by=by,macro_f1=results['pooled_classification_report']['macro avg']['f1-score'],training_seconds=seconds,epochs=epochs,mean_training_seconds_per_epoch=seconds/epochs,latency=read_json(OUT/f'latency_{size}_{arch}.json'))
        before={r['raw_path']:r for r in read_csv(ROOT/'reports'/RUNS[128]/f'{arch}_out_of_fold_predictions.csv')};after={r['raw_path']:r for r in read_csv(ROOT/'reports'/RUNS[192]/f'{arch}_out_of_fold_predictions.csv')}
        assert before.keys()==after.keys()
        assert all(before[k]['class_id']==after[k]['class_id'] and before[k]['session_id']==after[k]['session_id'] for k in before)
        wins=sum(before[k]['correct']=='0' and after[k]['correct']=='1' for k in before);losses=sum(before[k]['correct']=='1' and after[k]['correct']=='0' for k in before)
        summary[arch]=dict(variants=variants,corrected_errors=wins,new_errors=losses,delta_correct=wins-losses,delta_percentage_points=100*(wins-losses)/2100)
    rejects={str(n):read_json(ROOT/'reports'/('cv10_s008_unknown_knn_20261019' if n==128 else 'cv10_s008_192_unknown_knn_20261019')/'summary.json')['pooled'] for n in RUNS}
    negative_paths=[]
    for n in RUNS:
        negative=read_csv(ROOT/'reports'/('cv10_s008_unknown_knn_20261019' if n==128 else 'cv10_s008_192_unknown_knn_20261019')/'external_predictions.csv')
        assert len(negative)==len({r['raw_path'] for r in negative})==2400
        negative_paths.append({(r['raw_path'],r['class_id'],r['session_id']) for r in negative})
    assert negative_paths[0]==negative_paths[1]
    prep=read_json(OUT/'preparation.json')
    for relative,digest in prep['protected_files_sha256'].items():assert hashlib.sha256(contained(relative).read_bytes()).hexdigest()==digest
    result=dict(architectures=summary,rejection=rejects,folds_equal=True,matched_images=2100,test_used=False,application_unchanged=True,cnn_caveat='Flatten cambia numero de parametros; efecto combinado de resolucion y capacidad.',interpretation='Desarrollo adaptativo, siete rondas compartiendo datos. Desviacion entre sesiones no es intervalo de confianza.')
    save_json(OUT/'comparison.json',result)
    fig,axes=plt.subplots(2,2,figsize=(13,9))
    for arch,c in summary.items():
        v=c['variants'];axes[0,0].plot([128,192],[100*v[str(n)]['correct']/2100 for n in RUNS],marker='o',label=arch.upper())
        axes[1,0].plot([128,192],[v[str(n)]['latency']['median_ms'] for n in RUNS],marker='o',label=arch.upper())
    for n in RUNS:
        d=summary['mobilenet']['variants'][str(n)]['by']['distance'];axes[0,1].plot(['corta','media','larga'],[100*d[k]['accuracy'] for k in ('corta','media','larga')],marker='o',label=f'MobileNet{n}')
    axes[1,1].plot([128,192],[100*rejects[str(n)]['unknown_rejection_rate'] for n in RUNS],marker='o',label='Desconocidas rechazadas')
    axes[1,1].plot([128,192],[100*rejects[str(n)]['known_rejection_rate'] for n in RUNS],marker='o',label='Conocidas rechazadas');axes[1,1].axhline(70,color='gray',linestyle='--')
    for ax in axes.flat:ax.legend(fontsize=8);ax.grid(alpha=.2)
    axes[0,0].set(title='Exactitud externa: mismas2100 fotos',ylabel='Aciertos (%)',ylim=(0,101),xticks=[128,192])
    axes[0,1].set(title='MobileNet por distancia',ylabel='Aciertos (%)',ylim=(0,101))
    axes[1,0].set(title='Latencia CPU: mediana batch1, fold1',ylabel='Milisegundos',xticks=[128,192])
    axes[1,1].set(title='Rechazo con calibracion interna por ronda',ylabel='Porcentaje (%)',ylim=(0,101),xticks=[128,192])
    fig.tight_layout(rect=(0,.05,1,.96));fig.suptitle('Comparacion128 frente a192 - desarrollo');fig.text(.02,.01,'CNN Flatten cambia parametros. Cada modelo recalibra su umbral. Latencia no incluye kNN, red ni video. s007 excluida.',fontsize=9);save_figure(fig,OUT/'comparison.png',145);plt.close(fig)
    lines=['# Comparacion de resolucion128/192','','Mismas siete rondas, muestras, semillas, batch y presupuestos. s007 excluida.','']
    for arch,c in summary.items():
        a,b=c['variants']['128'],c['variants']['192'];lines += [f"- {arch.upper()}:128={a['correct']}/2100 ({100*a['correct']/2100:.2f}%);192={b['correct']}/2100 ({100*b['correct']/2100:.2f}%); diferencia={c['delta_percentage_points']:.2f} puntos.",f"  Corrige{c['corrected_errors']} errores anteriores e introduce{c['new_errors']} nuevos. Parametros128/192: {a['latency']['model_parameters']}/{b['latency']['model_parameters']}. Latencia mediana:{a['latency']['median_ms']:.2f}/{b['latency']['median_ms']:.2f}ms."]
    for n,m in rejects.items():lines += [f"- Rechazo{n}: desconocidas{m['unknown_rejected']}/300 ({100*m['unknown_rejection_rate']:.2f}%); conocidas{m['known_rejected']}/2100 ({100*m['known_rejection_rate']:.2f}%); conocidas correctas aceptadas{m['known_correct_accepted']}/2100."]
    lines+=['','No activar automaticamente la aplicacion. Elegir procedimiento en desarrollo, preparar modelo unico y calibrarlo antes de s007. No asumir que mas resolucion mejora cada clase, sesion o rechazo.','Los tiempos de entrenamiento dependen de epocas ejecutadas y carga de la maquina. Latencia mide solo cuatro checkpoints fold1, calentados y en CPU; no end-to-end de camara.','CNN cambia capacidad con Flatten: no se aisla resolucion a igual numero de parametros. Negativos principalmente objetos y escenas, sin representar todo pictograma desconocido.']
    (OUT/'lectura_resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print({a:c['delta_percentage_points'] for a,c in summary.items()},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--benchmark',action='store_true');p.add_argument('--resolution',type=int,choices=[128,192]);p.add_argument('--architecture',choices=['cnn','mobilenet']);a=p.parse_args()
    if a.benchmark:
        if not a.resolution or not a.architecture:p.error('Faltan resolucion y arquitectura')
        benchmark(a.resolution,a.architecture)
    else:compare()
