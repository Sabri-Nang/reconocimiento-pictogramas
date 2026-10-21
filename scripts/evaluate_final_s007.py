"""Evaluación final única de s007 con el paquete activo congelado.
No entrena, selecciona ni calibra. Conserva predicciones individuales.
"""
import argparse,csv,hashlib,json,os,platform,sys,time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score,average_precision_score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def wilson(k,n):
 z=1.959963984540054;den=1+z*z/n;mid=(k/n+z*z/(2*n))/den;half=z*((k/n*(1-k/n)/n+z*z/(4*n*n))**.5)/den
 return [mid-half,mid+half]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args();root=args.project.resolve()
 sys.path.insert(0,str(root/'src'))
 from reconocimiento_pictogramas.inference import classify_image,load_selected_model,load_selected_detector
 for old in (root/'reports').glob('final_s007_*/metrics.json'):raise RuntimeError(f'Ya hay una evaluación final: {old}. No se vuelve a evaluar para ajustar.')
 selected=json.loads((root/'config/selected_model.json').read_text(encoding='utf-8'));active=json.loads((root/'config/application.json').read_text(encoding='utf-8'))
 for key in ['model_path','model_sha256','classes','image_size','confidence_threshold','rejection_detector']:assert selected[key]==active[key],key
 classes=active['classes'];assert len(classes)==10;detector=active['rejection_detector'];assert detector['method']=='knn_cosine' and detector['calibrated']
 assert 's007' not in detector['reference_sessions']+detector['calibration_sessions']
 model_path=root/active['model_path'];ref_path=root/detector['references_path']
 assert sha(model_path)==active['model_sha256'];assert sha(ref_path)==detector['references_sha256']
 with (root/'data/metadata.csv').open(encoding='utf-8-sig',newline='') as f:metadata=list(csv.DictReader(f))
 rows=[r for r in metadata if r['session_id']=='s007'];counts=Counter(r['class_id'] for r in rows)
 assert counts==Counter({**{c:30 for c in classes},'unknown':50}),counts
 assert len({r['filename'] for r in rows})==350
 inventory=[]
 for row in sorted(rows,key=lambda r:(classes.index(r['class_id']) if r['class_id'] in classes else 10,r['filename'])):
  cls=row['class_id'];p=root/'data/raw'/('unknown' if cls=='unknown' else 'known/'+cls)/row['filename'];assert p.is_file()
  assert f'{cls}_s007_' in p.name
  inventory.append(dict(raw_path=p.relative_to(root).as_posix(),filename=p.name,true_label=cls,sha256=sha(p)))
 finalpaths={r['raw_path'] for r in inventory};hashes={r['sha256'] for r in inventory};assert len(hashes)==350
 others=[p for p in (root/'data/raw').rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png'} and p.relative_to(root).as_posix() not in finalpaths]
 print('Verificando aislamiento frente a',len(others),'imágenes de desarrollo...',flush=True)
 with ThreadPoolExecutor(max_workers=4) as pool:
  overlap=[p.relative_to(root).as_posix() for p,h in zip(others,pool.map(sha,others)) if h in hashes]
 assert not overlap,overlap
 refmanifest=json.loads((root/active['calibration_path']).with_name('reference_manifest.json').read_text(encoding='utf-8'))
 assert refmanifest['images']==1800 and 's007' not in refmanifest['sessions']
 assert not hashes & {r['sha256'] for r in refmanifest['raw_paths_and_hashes']}
 run='final_s007_'+datetime.now().strftime('%Y%m%d_%H%M%S');out=root/'reports'/run;out.mkdir(exist_ok=False)
 frozen={name:sha(root/name) for name in ['config/application.json','config/selected_model.json','data/metadata.csv',active['model_path'],detector['references_path']]}
 write_json(out/'protocol_frozen.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),selection=active,protected_hashes=frozen,test_counts=dict(counts),development_images_checked=len(others),overlap=[],metrics_planned=['closed_set_accuracy','precision_recall_f1_per_class','confusion_matrix_closed','confusion_matrix_operational_11_labels','known_correct_accepted','known_rejection','unknown_rejection','unknown_false_acceptance','coverage','accuracy_among_accepted','auroc_unknown','auprc_unknown'],threshold_change_allowed=False,training_allowed=False,session='s007',seed=42,uncertainty='Wilson95 descriptivo por imagen; imágenes de una sola sesión no equivalen a observaciones independientes entre entornos.'))
 write_json(out/'test_inventory.json',inventory)
 model,config=load_selected_model();load_selected_detector()
 import tensorflow as tf
 write_json(out/'environment.json',dict(python=sys.version,tensorflow=tf.__version__,numpy=np.__version__,platform=platform.platform(),devices=[str(x) for x in tf.config.list_physical_devices()],script_sha256=sha(Path(__file__))))
 print('Paquete congelado y cargado. Evaluando',run,flush=True)
 predictions=[];columns=['filename','true_label','predicted_raw','predicted_operational','rejected','confidence','similarity','threshold','seconds']+[f'p_{c}' for c in classes]
 with (out/'predictions.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
  for i,row in enumerate(inventory,1):
   t=time.perf_counter();result=classify_image(root/row['raw_path']);elapsed=time.perf_counter()-t
   raw=max(result['probabilities'],key=result['probabilities'].get)
   pred=dict(filename=row['filename'],true_label=row['true_label'],predicted_raw=raw,predicted_operational='unknown' if result['rejected'] else result['label'],rejected=bool(result['rejected']),confidence=result['confidence'],similarity=result['rejection_score'],threshold=result['rejection_threshold'],seconds=elapsed,**{f'p_{c}':result['probabilities'][c] for c in classes})
   assert pred['rejected']==(pred['similarity']<=detector['threshold'])
   writer.writerow(pred);f.flush();predictions.append(pred)
   if i%25==0:print(f'Evaluadas {i}/350',flush=True)
 known=[r for r in predictions if r['true_label']!='unknown'];unknown=[r for r in predictions if r['true_label']=='unknown'];accepted=[r for r in known if not r['rejected']]
 correct=sum(r['predicted_raw']==r['true_label'] for r in known);correctaccepted=sum(r['predicted_operational']==r['true_label'] for r in known);kr=sum(r['rejected'] for r in known);ur=sum(r['rejected'] for r in unknown)
 truth=[r['true_label'] for r in known];raw=[r['predicted_raw'] for r in known];labels=classes+['unknown'];alltruth=[r['true_label'] for r in predictions];oper=[r['predicted_operational'] for r in predictions]
 metrics=dict(run_id=run,test_evaluated=True,model_path=active['model_path'],model_sha256=active['model_sha256'],threshold=detector['threshold'],known_images=300,unknown_images=50,known_correct_without_rejection=correct,known_accuracy_without_rejection=correct/300,known_correct_accepted=correctaccepted,known_accuracy_with_rejection=correctaccepted/300,known_rejected=kr,known_rejection_rate=kr/300,known_coverage=len(accepted)/300,known_wrong_accepted=len(accepted)-correctaccepted,accuracy_among_accepted_known=correctaccepted/len(accepted) if accepted else None,unknown_rejected=ur,unknown_rejection_rate=ur/50,unknown_false_accepted=50-ur,unknown_false_acceptance_rate=(50-ur)/50,overall_operational_correct=correctaccepted+ur,overall_operational_accuracy=(correctaccepted+ur)/350,all_accepted=sum(not r['rejected'] for r in predictions),accuracy_among_all_accepted=correctaccepted/sum(not r['rejected'] for r in predictions),unknown_auroc=float(roc_auc_score([int(r['true_label']=='unknown') for r in predictions],[-r['similarity'] for r in predictions])),unknown_average_precision=float(average_precision_score([int(r['true_label']=='unknown') for r in predictions],[-r['similarity'] for r in predictions])),closed_set_report=classification_report(truth,raw,labels=classes,output_dict=True,zero_division=0),operational_report=classification_report(alltruth,oper,labels=labels,output_dict=True,zero_division=0),closed_confusion_matrix=confusion_matrix(truth,raw,labels=classes).tolist(),operational_confusion_matrix=confusion_matrix(alltruth,oper,labels=labels).tolist(),classes=classes,wilson95_descriptive=dict(known_accuracy=wilson(correct,300),known_operational_accuracy=wilson(correctaccepted,300),unknown_rejection=wilson(ur,50),known_rejection=wilson(kr,300)),latency=dict(median_seconds=float(np.median([r['seconds'] for r in predictions[1:]])),p95_seconds=float(np.percentile([r['seconds'] for r in predictions[1:]],95)),first_image_seconds=predictions[0]['seconds'],scope='Carga de imagen, preprocesamiento, clasificador y kNN; ejecución serial CPU local; excluye carga inicial del modelo, UI y red.'),goals=dict(known_accuracy_at_least_70=correct>=210,operational_known_accuracy_at_least_70=correctaccepted>=210,unknown_rejection_at_least_70=ur>=35,internal_calibration_target_80_reproduced=ur>=40,internal_known_rejection_cap_1_reproduced=kr<=3))
 assert sum(sum(x) for x in metrics['closed_confusion_matrix'])==300
 assert sum(sum(x) for x in metrics['operational_confusion_matrix'])==350
 assert sum(metrics['closed_confusion_matrix'][i][i] for i in range(10))==correct
 assert kr+len(accepted)==300 and correctaccepted+metrics['known_wrong_accepted']==len(accepted)
 for name,h in frozen.items():assert sha(root/name)==h,f'Archivo protegido modificado: {name}'
 for row in inventory:assert sha(root/row['raw_path'])==row['sha256']
 write_json(out/'metrics.json',metrics);write_json(out/'verification.json',dict(protected_files_unchanged=True,test_images_unchanged=True,threshold_unchanged=True,all_350_predictions_saved=True,count_consistency_checked=True,training_performed=False,calibration_performed=False))
 print('FINAL',out,flush=True);print(json.dumps({k:v for k,v in metrics.items() if isinstance(v,(int,float,str))},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
