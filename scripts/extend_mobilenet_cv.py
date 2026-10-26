"""Ejecuta CNN y MobileNet por sesión, con parada interna y evaluación externa."""
import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.cross_validation import make_folds, validate_records
from reconocimiento_pictogramas.artifacts import contained, read_csv, read_json, save_json, write_csv

def prepare_run(run, config_path):
    project=read_json(ROOT/'config/project.json');cfg=read_json(config_path)
    classes=[c['id'] for c in project['classes']]
    rows=read_csv(ROOT/'data/splits/development.csv')
    validate_records(rows,classes,cfg['expected_per_class_session'])
    # Detecta capturas cambiadas desde la preparación, antes de utilizar los PNG.
    for row in rows:
        if hashlib.sha256(contained(row['raw_path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError(f"Original modificado: {row['raw_path']}. Volver a preparar datos.")
    audit=read_json(ROOT/'reports/dataset_10_audit/integrity.json')
    if audit['errors']:raise ValueError('Hay errores de auditoría pendientes')
    out=ROOT/'reports'/run;out.mkdir(parents=True,exist_ok=False)
    modeldir=ROOT/'models'/run;modeldir.mkdir(parents=True,exist_ok=False)
    protocol=dict(config=cfg,project=project,folds=make_folds(cfg['sessions']),development_sha256=hashlib.sha256((ROOT/'data/splits/development.csv').read_bytes()).hexdigest(),test_used=False,unknown_used=False,visual_findings=audit.get('visual_findings',[]))
    save_json(out/'protocol.json',protocol)
    for fold in protocol['folds']:
        dest=out/f"fold_{fold['fold']:02d}";dest.mkdir()
        for role in ['train','stop','outer']:
            selected=[r for r in rows if r['session_id'] in fold[role]]
            write_csv(dest/f'{role}.csv',selected)
    return protocol

def plot_history(rows,dest,title,phase_boundary=None):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if not rows:return
    epochs=[r['epoch'] for r in rows];best=min(rows,key=lambda r:r['val_loss'])['epoch']
    fig,axes=plt.subplots(1,3,figsize=(16,4.8))
    for key,label in [('loss','Entrenamiento (aumentos activos)'),('val_loss','Validación interna')]:axes[0].plot(epochs,[r[key] for r in rows],label=label)
    axes[0].set(ylabel='Entropía cruzada',title='Pérdida: criterio de parada')
    for key,label in [('accuracy','Entrenamiento (durante los ajustes)'),('val_accuracy','Validación interna')]:axes[1].plot(epochs,[r[key]*100 for r in rows],label=label)
    axes[1].set(ylabel='Exactitud (%)',title='Porcentaje de aciertos',ylim=(0,101))
    axes[2].plot(epochs,[r['val_correct'] for r in rows],label='Aciertos de validación')
    axes[2].plot(epochs,[r['val_errors'] for r in rows],label='Errores de validación')
    axes[2].set(ylabel='Imágenes de 300',title='Aciertos y errores: validación interna',ylim=(0,305))
    for ax in axes:
        ax.set_xlabel('Época adicional (0 = checkpoint de referencia)')
        ax.axvline(best,color='black',linestyle='--',linewidth=1,label=f'Menor pérdida: época {best}')
        ax.axvline(epochs[-1],color='gray',linestyle='-.',linewidth=1,label=f'Última ejecutada: época {epochs[-1]}')
        if phase_boundary:ax.axvline(phase_boundary+.5,color='gray',linestyle=':',label='Comienza ajuste fino')
        ax.legend(fontsize=7);ax.grid(alpha=.15)
    fig.suptitle(title);fig.tight_layout(rect=(0,.06,1,.95))
    fig.text(.02,.02,'Fuente: continuación de ajuste fino de esta ronda. La sesión externa no se consulta por época. La exactitud de entrenamiento se acumula con aumentos y pesos cambiantes.',fontsize=8)
    fig.savefig(dest/'epoch_curves.png',dpi=140);plt.close(fig)

def worker(run,number,architecture):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
    os.environ.setdefault('KERAS_HOME',str(ROOT/'models/.keras_cache'))
    import numpy as np
    import tensorflow as tf
    from PIL import Image
    from sklearn.metrics import classification_report,confusion_matrix
    protocol=read_json(ROOT/'reports'/run/'protocol.json');cfg=protocol['config']
    classes=[c['id'] for c in protocol['project']['classes']]
    fold=protocol['folds'][number-1];seed=cfg['seed']+number-1
    tf.keras.utils.set_random_seed(seed)
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    size=protocol['project']['image'];height,width=size['height'],size['width']
    source=ROOT/'reports'/run/f'fold_{number:02d}'
    dest=source/architecture;dest.mkdir(exist_ok=True)
    modeldir=ROOT/'models'/run/f'fold_{number:02d}'/architecture;modeldir.mkdir(parents=True,exist_ok=True)
    checkpoint=modeldir/'best.keras'
    def load(role):
        rows=read_csv(source/f'{role}.csv');images=[]
        for row in rows:
            with Image.open(contained(row['processed_path'])) as im:
                im.load()
                if im.mode!='RGB' or im.size!=(width,height):raise ValueError('PNG sin preparar')
                images.append(np.asarray(im,dtype=np.uint8))
        return np.stack(images),np.asarray([int(r['class_index']) for r in rows]),rows
    x,y,trainrows=load('train');xv,yv,stoprows=load('stop')
    if len(y)!=1200 or len(yv)!=300:raise ValueError('Cantidades de ronda incorrectas')
    opt=tf.data.Options();opt.threading.private_threadpool_size=2
    train=tf.data.Dataset.from_tensor_slices((x,y)).shuffle(len(y),seed=seed,reshuffle_each_iteration=True).batch(cfg['batch_size']).with_options(opt).prefetch(1)
    stop=tf.data.Dataset.from_tensor_slices((xv,yv)).batch(cfg['batch_size']).with_options(opt).prefetch(1)
    L=tf.keras.layers
    augmentation=[L.RandomRotation(.04,seed=seed),L.RandomTranslation(.05,.05,seed=seed+1),L.RandomZoom(.1,seed=seed+2)]
    if architecture=='cnn':
        model=tf.keras.Sequential([L.Input((height,width,3)),L.Rescaling(1./255),*augmentation,L.Conv2D(16,3,padding='same',activation='relu'),L.MaxPooling2D(),L.Conv2D(32,3,padding='same',activation='relu'),L.MaxPooling2D(),L.Conv2D(64,3,padding='same',activation='relu'),L.MaxPooling2D(),L.Conv2D(64,3,padding='same',activation='relu'),L.MaxPooling2D(),L.Flatten(),L.Dense(64,activation='relu'),L.Dropout(.3,seed=seed),L.Dense(len(classes),activation='softmax')],name='cnn_10')
    else:
        base=tf.keras.applications.MobileNetV3Small(input_shape=(height,width,3),include_top=False,weights='imagenet',include_preprocessing=True,pooling='avg')
        base.trainable=False
        inputs=L.Input((height,width,3));z=inputs
        for layer in augmentation:z=layer(z)
        z=base(z,training=False);z=L.Dropout(.3,seed=seed)(z)
        model=tf.keras.Model(inputs,L.Dense(len(classes),activation='softmax')(z),name='mobilenet_10')
    def compile_model(lr):model.compile(optimizer=tf.keras.optimizers.Adam(lr),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    compile_model(1e-3)
    lines=[];model.summary(print_fn=lambda line:lines.append(line))
    (dest/'architecture.txt').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
    rows=[];stages=[];step=0;boundary=None
    class Tracker(tf.keras.callbacks.Callback):
        def __init__(self,phase,offset):super().__init__();self.phase=phase;self.offset=offset;self.epoch_number=offset
        def on_epoch_begin(self,epoch,logs=None):self.epoch_number=self.offset+epoch+1
        def on_train_batch_end(self,batch,logs=None):
            nonlocal step
            step+=1
            with (dest/'steps.csv').open('a',encoding='utf-8',newline='') as f:
                csv.writer(f).writerow([step,self.epoch_number,self.phase,batch+1,float(logs['loss']),float(logs['accuracy'])])
        def on_epoch_end(self,epoch,logs=None):
            correct=int(round(float(logs['val_accuracy'])*len(yv)))
            row=dict(epoch=self.epoch_number,phase=self.phase,loss=float(logs['loss']),accuracy=float(logs['accuracy']),val_loss=float(logs['val_loss']),val_accuracy=float(logs['val_accuracy']),val_correct=correct,val_errors=len(yv)-correct,global_step=step)
            if not all(math.isfinite(row[k]) for k in ['loss','accuracy','val_loss','val_accuracy']):raise ValueError('Métricas no finitas')
            rows.append(row);write_csv(dest/'epochs.csv',rows)
            if self.epoch_number%5==0:plot_history(rows,dest,f'{architecture.upper()} · ronda {number} · validación {fold["stop"][0]}',boundary)
    with (dest/'steps.csv').open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerow(['global_step','epoch','phase','batch','epoch_running_loss','epoch_running_accuracy'])
    def fit_stage(phase,epochs,patience):
        offset=rows[-1]['epoch'] if rows else 0
        before=len(rows)
        best=min([r['val_loss'] for r in rows],default=float('inf'))
        callbacks=[tf.keras.callbacks.ModelCheckpoint(str(checkpoint),monitor='val_loss',save_best_only=True,initial_value_threshold=best),tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=patience,min_delta=cfg['min_delta']),Tracker(phase,offset)]
        print(f'RUN {run} {architecture} ronda{number} {phase}: train={fold["train"]}, stop={fold["stop"]}, outer reservada={fold["outer"]}',flush=True)
        model.fit(train,validation_data=stop,epochs=epochs,callbacks=callbacks,verbose=2,shuffle=False)
        completed=len(rows)-before
        stages.append(dict(phase=phase,max_epochs=epochs,completed=completed,patience=patience,stop_reason='Paciencia agotada sin reducir val_loss' if completed<epochs else 'Límite de épocas alcanzado',stopped_global_epoch=rows[-1]['epoch']))
    start=time.perf_counter()
    source_model=ROOT/'models'/cfg['source_run']/f'fold_{number:02d}'/'mobilenet/best.keras'
    original_protocol=read_json(ROOT/'reports'/cfg['source_run']/'protocol.json')
    if original_protocol['development_sha256']!=protocol['development_sha256'] or original_protocol['folds'][number-1]!=fold:
        raise ValueError('Las particiones difieren de la referencia')
    model=tf.keras.models.load_model(source_model)
    lines=[];model.summary(print_fn=lambda line:lines.append(line))
    (dest/'architecture.txt').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
    if abs(float(model.optimizer.learning_rate.numpy())-1e-5)>1e-10:
        raise ValueError('El checkpoint no tiene la tasa de ajuste fino esperada')
    initial_loss,initial_accuracy=model.evaluate(stop,verbose=0)
    initial_correct=int(round(float(initial_accuracy)*len(yv)))
    rows.append(dict(epoch=0,phase='checkpoint_referencia',loss=float('nan'),accuracy=float('nan'),val_loss=float(initial_loss),val_accuracy=float(initial_accuracy),val_correct=initial_correct,val_errors=len(yv)-initial_correct,global_step=0))
    model.save(checkpoint)
    write_csv(dest/'epochs.csv',rows)
    fit_stage('continuacion_ajuste_fino',cfg['extra_fine_tune_epochs'],cfg['fine_tune_patience'])
    elapsed=time.perf_counter()-start
    model=tf.keras.models.load_model(checkpoint)
    best=min(rows,key=lambda r:r['val_loss'])
    save_json(dest/'stopping.json',dict(monitor='val_loss',best_epoch=best['epoch'],best_phase=best['phase'],best_val_loss=best['val_loss'],stopped_epoch=rows[-1]['epoch'],best_epoch_last_step=best['global_step'],stopped_training_step=rows[-1]['global_step'],steps_per_epoch=math.ceil(len(y)/cfg['batch_size']),last_batch_images=len(y)%cfg['batch_size'] or cfg['batch_size'],stages=stages,outer_used_for_stopping=False))
    plot_history(rows,dest,f'{architecture.upper()} · ronda {number} · validación {fold["stop"][0]}',boundary)
    # Esta es la primera carga/evaluación de las imágenes externas en esta ronda.
    xo,yo,outerrows=load('outer')
    outer=tf.data.Dataset.from_tensor_slices((xo,yo)).batch(cfg['batch_size']).with_options(opt)
    probabilities=model.predict(outer,verbose=0);predicted=probabilities.argmax(axis=1)
    report=classification_report(yo,predicted,labels=list(range(len(classes))),target_names=classes,output_dict=True,zero_division=0)
    cm=confusion_matrix(yo,predicted,labels=list(range(len(classes))))
    result=dict(architecture=architecture,fold=number,seed=seed,train_sessions=fold['train'],stop_session=fold['stop'][0],outer_session=fold['outer'][0],outer_images=len(yo),outer_accuracy=float((predicted==yo).mean()),outer_correct=int((predicted==yo).sum()),outer_errors=int((predicted!=yo).sum()),macro_f1=report['macro avg']['f1-score'],classification_report=report,confusion_matrix=cm.tolist(),best_epoch=best['epoch'],epochs_executed=rows[-1]['epoch'],source_run=cfg['source_run'],source_checkpoint_sha256=hashlib.sha256(source_model.read_bytes()).hexdigest(),training_seconds=elapsed,model_path=checkpoint.relative_to(ROOT).as_posix(),test_used=False)
    predicted_rows=[]
    for row,prob,index in zip(outerrows,probabilities,predicted):
        predicted_rows.append(dict(raw_path=row['raw_path'],session_id=row['session_id'],class_id=row['class_id'],predicted_class=classes[int(index)],correct=int(classes[int(index)]==row['class_id']),confidence=float(prob.max()),fold=number,**{f'prob_{c}':float(v) for c,v in zip(classes,prob)}))
    write_csv(dest/'outer_predictions.csv',predicted_rows)
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,7));ax.imshow(cm,cmap='Blues')
    ax.set(xticks=range(10),yticks=range(10),xticklabels=classes,yticklabels=classes,xlabel='Clase predicha',ylabel='Clase real',title=f'{architecture.upper()} · evaluación externa {fold["outer"][0]} · 300 imágenes')
    plt.setp(ax.get_xticklabels(),rotation=45,ha='right')
    for i in range(10):
        for j in range(10):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black',fontsize=8)
    fig.tight_layout();fig.savefig(dest/'outer_confusion.png',dpi=140);plt.close(fig)
    save_json(dest/'result.json',result)
    print('RESULT '+json.dumps({k:result[k] for k in ['architecture','fold','outer_accuracy','best_epoch','epochs_executed']}) ,flush=True)

def aggregate(run):
    import numpy as np
    from sklearn.metrics import classification_report
    protocol=read_json(ROOT/'reports'/run/'protocol.json');classes=[c['id'] for c in protocol['project']['classes']]
    out=ROOT/'reports'/run;summary={}
    for architecture in ['mobilenet']:
        results=[read_json(out/f'fold_{i:02d}'/architecture/'result.json') for i in range(1,7)]
        predictions=[r for i in range(1,7) for r in read_csv(out/f'fold_{i:02d}'/architecture/'outer_predictions.csv')]
        if len({r['raw_path'] for r in predictions})!=1800:raise ValueError('Predicciones externas incompletas/repetidas')
        true=[classes.index(r['class_id']) for r in predictions];pred=[classes.index(r['predicted_class']) for r in predictions]
        report=classification_report(true,pred,labels=list(range(10)),target_names=classes,output_dict=True,zero_division=0)
        summary[architecture]=dict(mean_accuracy=float(np.mean([r['outer_accuracy'] for r in results])),std_across_sessions=float(np.std([r['outer_accuracy'] for r in results],ddof=1)),min_accuracy=min(r['outer_accuracy'] for r in results),max_accuracy=max(r['outer_accuracy'] for r in results),pooled_classification_report=report,folds=results)
        write_csv(out/f'{architecture}_out_of_fold_predictions.csv',predictions)
    save_json(out/'summary.json',dict(protocol='6 rondas por sesión con holdout interno fijo rotativo; sin búsqueda exhaustiva de parámetros',results=summary,test_used=False,interpretation='Resultados de desarrollo para comparar procedimientos; no son prueba final ni garantizan hipótesis.',uncertainty='La desviación describe variación entre sesiones; las rondas comparten datos y no son observaciones independientes.'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.7))
    for arch in ['mobilenet']:
        values=[r['outer_accuracy']*100 for r in summary[arch]['folds']]
        axes[0].plot(range(1,7),values,marker='o',label=arch.upper())
    axes[0].set(xticks=range(1,7),xticklabels=protocol['config']['sessions'],xlabel='Sesión de evaluación externa',ylabel='Exactitud (%)',title='Diez clases: resultado externo por sesión',ylim=(0,101));axes[0].legend()
    names=['mobilenet'];axes[1].bar([n.upper() for n in names],[summary[n]['mean_accuracy']*100 for n in names],yerr=[summary[n]['std_across_sessions']*100 for n in names],capsize=5)
    axes[1].set(ylabel='Exactitud (%)',title='Promedio ± desviación entre seis sesiones',ylim=(0,105))
    fig.tight_layout(rect=(0,.07,1,1));fig.text(.02,.02,'Fuente: 1.800 predicciones externas por arquitectura. Barras: desviación entre sesiones, no intervalo de confianza. s007 no utilizada.',fontsize=8)
    fig.savefig(out/'comparison.png',dpi=150);plt.close(fig)
    print('SUMMARY '+json.dumps({k:{m:v[m] for m in ['mean_accuracy','std_across_sessions']} for k,v in summary.items()}),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True,help='Configuración completa del experimento.')
    parser.add_argument('--run-id');parser.add_argument('--worker',action='store_true');parser.add_argument('--fold',type=int);parser.add_argument('--architecture',choices=['mobilenet']);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.worker:
        if not args.run_id or not args.fold or not args.architecture:parser.error('Faltan argumentos del worker')
        worker(args.run_id,args.fold,args.architecture);return
    run=args.run_id or datetime.now(timezone.utc).strftime('cv10_%Y%m%d_%H%M%S')
    if not run.startswith('cv10_') or '/' in run or '\\' in run:parser.error('Identificador inválido')
    if args.resume:
        protocol=read_json(ROOT/'reports'/run/'protocol.json')
        if hashlib.sha256((ROOT/'data/splits/development.csv').read_bytes()).hexdigest()!=protocol['development_sha256']:raise ValueError('El manifiesto cambió; iniciar otro experimento')
    else:protocol=prepare_run(run,args.config)
    print(f'RUN_ID={run}',flush=True)
    for arch in ['mobilenet']:
        for fold in range(1,7):
            if (ROOT/'reports'/run/f'fold_{fold:02d}'/arch/'result.json').exists():continue
            save_json(ROOT/'reports'/run/'progress.json',dict(status='running',architecture=arch,fold=fold))
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--config',str(args.config),'--run-id',run,'--fold',str(fold),'--architecture',arch],check=True,cwd=ROOT)
    aggregate(run)
    save_json(ROOT/'reports'/run/'progress.json',dict(status='completed',test_used=False))
if __name__=='__main__':main()
