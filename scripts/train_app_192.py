"""Entrena ycalibra MobileNet192 único; activa solo si la regla es viable."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
from pathlib import Path
import sys,time,math,hashlib,json,csv
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('KERAS_HOME',str(ROOT/'models/.keras_cache'))
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.artifacts import read_json,read_csv,save_json,write_csv,contained
from reconocimiento_pictogramas.training_artifacts import plot_history
from reconocimiento_pictogramas.rejection import calibrate_target_with_known_cap,evaluate_rejection
from reconocimiento_pictogramas.feature_rejection import neighbor_similarity
from reconocimiento_pictogramas.preprocessing import prepare_image
RUN='mobilenet_app_192_20261020'
OUT=ROOT/'reports'/RUN
MD=ROOT/'models'/RUN

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--activate',action='store_true');args=parser.parse_args()
 import numpy as np
 import tensorflow as tf
 from sklearn.metrics import classification_report,confusion_matrix
 tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2);tf.keras.utils.set_random_seed(42)
 cfg=read_json(ROOT/'config/cv_s008_192.json');project=read_json(ROOT/'config/project.json');classes=[c['id'] for c in project['classes']]
 records=read_csv(contained(cfg['development_manifest']));train=[r for r in records if r['session_id']!='s006'];val=[r for r in records if r['session_id']=='s006']
 sessions=[f's{i:03d}' for i in range(1,6)]+['s008'];assert len(train)==1800 and len(val)==300 and {r['session_id'] for r in train}==set(sessions)
 for key in ('session_id','raw_path','processed_path','sha256'):assert not {r[key] for r in train}&{r[key] for r in val}
 assert all(r['session_id']!='s007' for r in records)
 for row in records:
  assert hashlib.sha256(contained(row['raw_path']).read_bytes()).hexdigest()==row['sha256']
  assert hashlib.sha256(contained(row['processed_path']).read_bytes()).hexdigest()==row['processed_sha256']
 OUT.mkdir(exist_ok=False);MD.mkdir(exist_ok=False)
 selected=ROOT/'config/application.json';previous=read_json(selected);save_json(OUT/'previous_selection.json',previous)
 write_csv(OUT/'train.csv',train);write_csv(OUT/'validation.csv',val)
 protocol=dict(run=RUN,classes=classes,image_size=[192,192],seed=42,train_sessions=sessions,validation_sessions=['s006'],train_images=1800,validation_images=300,batch_size=32,head_epochs=20,fine_tune_epochs=40,patience=6,fine_tune_patience=4,monitor='val_loss',target_unknown_rejection=.8,known_rejection_cap=.01,inner_shared_with_early_stopping=True,test_used=False,interpretation='Modelo único nuevo desde ImageNet; métricas internas, no hereda93,52%CV. s007 excluida.',manifests_sha256={n:hashlib.sha256((OUT/(n+'.csv')).read_bytes()).hexdigest() for n in ('train','validation')})
 save_json(OUT/'protocol.json',protocol);save_json(OUT/'progress.json',dict(stage='training',status='running'))
 def images(rows):return np.stack([np.asarray(prepare_image(contained(r['processed_path']),(192,192)),dtype=np.uint8) for r in rows])
 x=images(train);xv=images(val);y=np.array([int(r['class_index']) for r in train]);yv=np.array([int(r['class_index']) for r in val]);assert all(classes[int(r['class_index'])]==r['class_id'] for r in records)
 opt=tf.data.Options();opt.threading.private_threadpool_size=2
 tr=tf.data.Dataset.from_tensor_slices((x,y)).shuffle(len(y),seed=42,reshuffle_each_iteration=True).batch(32).with_options(opt).prefetch(1)
 va=tf.data.Dataset.from_tensor_slices((xv,yv)).batch(32).with_options(opt).prefetch(1)
 L=tf.keras.layers;base=tf.keras.applications.MobileNetV3Small(input_shape=(192,192,3),include_top=False,weights='imagenet',include_preprocessing=True,pooling='avg');base.trainable=False
 inp=L.Input((192,192,3));z=L.RandomRotation(.04,seed=42)(inp);z=L.RandomTranslation(.05,.05,seed=43)(z);z=L.RandomZoom(.1,seed=44)(z);z=base(z,training=False);z=L.Dropout(.3,seed=42)(z);model=tf.keras.Model(inp,L.Dense(10,activation='softmax')(z))
 lines=[];model.summary(print_fn=lambda line:lines.append(line));(OUT/'architecture.txt').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
 history=[];stages=[];checkpoint=MD/'best.keras';step=0
 class Tracker(tf.keras.callbacks.Callback):
  def __init__(self,phase,offset):super().__init__();self.phase=phase;self.offset=offset
  def on_epoch_end(self,epoch,logs=None):
   n=self.offset+epoch+1;correct=int(round(logs['val_accuracy']*300));history.append(dict(epoch=n,phase=self.phase,loss=float(logs['loss']),accuracy=float(logs['accuracy']),val_loss=float(logs['val_loss']),val_accuracy=float(logs['val_accuracy']),val_correct=correct,val_errors=300-correct,global_step=n*57))
   write_csv(OUT/'epochs.csv',history);save_json(OUT/'progress.json',dict(stage=self.phase,status='running',epoch=n))
   if n%5==0:plot_history(history,OUT,'MobileNet192 único · validación interna s006',train_images=1800)
 def fit(phase,epochs,patience,lr):
  model.compile(optimizer=tf.keras.optimizers.Adam(lr),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
  offset=len(history);best=min((h['val_loss'] for h in history),default=float('inf'))
  model.fit(tr,validation_data=va,epochs=epochs,verbose=2,callbacks=[tf.keras.callbacks.ModelCheckpoint(str(checkpoint),monitor='val_loss',save_best_only=True,initial_value_threshold=best),tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=patience),Tracker(phase,offset)])
  stages.append(dict(phase=phase,max_epochs=epochs,executed=len(history)-offset,patience=patience))
 start=time.perf_counter();fit('clasificador_congelado',20,6,.001);boundary=len(history);model=tf.keras.models.load_model(checkpoint);base=next(l for l in model.layers if isinstance(l,tf.keras.Model));base.trainable=True
 for layer in base.layers[:-30]:layer.trainable=False
 for layer in base.layers:
  if isinstance(layer,L.BatchNormalization):layer.trainable=False
 fit('ajuste_fino',40,4,.00001);elapsed=time.perf_counter()-start;model=tf.keras.models.load_model(checkpoint,compile=False);joint=tf.keras.Model(model.input,[model.output,model.layers[-1].input])
 best=min(history,key=lambda h:h['val_loss']);plot_history(history,OUT,'MobileNet192 único · validación interna s006',phase_boundary=boundary,train_images=1800);save_json(OUT/'stopping.json',dict(best_epoch=best['epoch'],epochs_executed=len(history),stages=stages,training_seconds=elapsed,steps_per_epoch=57,last_batch_images=8,test_used=False))
 save_json(OUT/'progress.json',dict(stage='calibration',status='running'))
 def extract(array):
  outputs=[joint(array[i:i+32],training=False) for i in range(0,len(array),32)]
  return np.concatenate([np.asarray(o[0]) for o in outputs]),np.concatenate([np.asarray(o[1]) for o in outputs])
 _,refs=extract(x);probs,features=extract(xv);inventory=read_csv(contained(cfg['inventory_path']));unknown=[r for r in inventory if r['class_id']=='unknown' and r['session_id']=='s006'];assert len(unknown)==50
 for r in unknown:assert hashlib.sha256(contained(r['raw_path']).read_bytes()).hexdigest()==r['sha256'] and r['sha256'] not in {t['sha256'] for t in train+val}
 xu=np.stack([np.asarray(prepare_image(contained(r['raw_path']),(192,192)),dtype=np.uint8) for r in unknown]);up,uf=extract(xu);ks=neighbor_similarity(features,refs,k=5);us=neighbor_similarity(uf,refs,k=5);chosen=calibrate_target_with_known_cap(us,ks,.8,.01)
 correct=(probs.argmax(axis=1)==yv);save_json(OUT/'metrics.json',dict(validation_accuracy=float(correct.mean()),validation_correct=int(correct.sum()),validation_images=300,classification_report=classification_report(yv,probs.argmax(axis=1),labels=list(range(10)),target_names=classes,output_dict=True,zero_division=0),confusion_matrix=confusion_matrix(yv,probs.argmax(axis=1),labels=list(range(10))).tolist(),test_used=False,independent_evaluation=False))
 save_json(OUT/'calibration.json',dict(**chosen,calibration_session='s006',unknown_images=50,known_images=300,independent_evaluation=False,test_used=False))
 if not chosen['feasible']:
  save_json(OUT/'progress.json',dict(status='completed',stage='calibration_infeasible',activated=False));print('Regla inviable; aplicación sin cambios',flush=True);return
 threshold=chosen['threshold'];metrics=evaluate_rejection(ks,correct.astype(int),us,threshold);save_json(OUT/'calibration.json',dict(**chosen,metrics=metrics,calibration_session='s006',known_validation_reused_for_early_stopping=True,independent_evaluation=False,test_used=False))
 archive=MD/'rejection_references.npz';np.savez_compressed(archive,features=refs,classes=np.array(classes),raw_paths=np.array([r['raw_path'] for r in train]));model_hash=hashlib.sha256(checkpoint.read_bytes()).hexdigest();ref_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
 candidate=dict(model_path=checkpoint.relative_to(ROOT).as_posix(),model_sha256=model_hash,classes=classes,image_size=[192,192],confidence_threshold=None,rejection_detector=dict(method='knn_cosine',neighbors=5,threshold=threshold,calibrated=True,calibration_rule='unknown_target_with_known_cap',target_unknown_rejection=.8,known_rejection_cap=.01,references_path=archive.relative_to(ROOT).as_posix(),references_sha256=ref_hash,model_sha256=model_hash,reference_sessions=sessions,calibration_sessions=['s006']),status='MobileNet192 único; selección ycalibración internas s006; prueba final pendiente',calibration_path=(OUT/'calibration.json').relative_to(ROOT).as_posix(),test_evaluated=False)
 save_json(OUT/'selected_model_candidate.json',candidate);write_csv(OUT/'calibration_predictions.csv',[dict(raw_path=r['raw_path'],class_id=r['class_id'],predicted_class=classes[int(p.argmax())],similarity=float(s),threshold=threshold,rejected=int(s<=threshold)) for r,p,s in zip(val+unknown,np.concatenate([probs,up]),np.concatenate([ks,us]))])
 # Verificación del paquete antes de activar; no depende de resultados externos.
 assert model.input_shape[1:]==(192,192,3) and model.output_shape[-1]==10
 assert refs.shape[0]==1800 and metrics['unknown_rejected']>=40 and metrics['known_rejected']<=3
 if args.activate:
  temporary=selected.with_suffix('.tmp.json');save_json(temporary,candidate);temporary.replace(selected)
  try:
   from reconocimiento_pictogramas import inference
   inference.load_selected_model.cache_clear();inference.load_selected_detector.cache_clear();inference.load_selected_detector()
   r=inference.classify_image(contained(val[0]['raw_path']));assert r['image'].size==(192,192)
  except Exception:
   save_json(selected,previous);inference.load_selected_model.cache_clear();inference.load_selected_detector.cache_clear();raise
 save_json(OUT/'verification.json',dict(train_images=1800,validation_images=300,unknown_images=50,train_validation_disjoint=True,model_sha256=model_hash,references_sha256=ref_hash,activated=args.activate,test_used=False))
 save_json(OUT/'progress.json',dict(stage='completed',status='completed',activated=args.activate));print(json.dumps(dict(activated=args.activate,validation_correct=int(correct.sum()),threshold=threshold,metrics=metrics)),flush=True)
if __name__=='__main__':main()
