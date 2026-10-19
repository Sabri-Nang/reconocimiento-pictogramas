"""Calibra detector conservador para un único MobileNet y permite seleccionarlo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.preprocessing import prepare_image
from reconocimiento_pictogramas.feature_rejection import neighbor_similarity
from reconocimiento_pictogramas.rejection import calibrate_threshold,evaluate_rejection
from evaluate_unknown_cv import rows,read,save,write,contained


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id',required=True);p.add_argument('--activate',action='store_true');a=p.parse_args()
    if not a.run_id.startswith('mobilenet_') or any(c in a.run_id for c in ['/','\\',':']):p.error('Identificador inválido')
    import numpy as np
    import tensorflow as tf
    tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
    modeldir=ROOT/'models'/a.run_id;report=ROOT/'reports'/a.run_id
    experiment=read(report/'experiment.json');classes=experiment['classes']
    assert classes==[c['id'] for c in read(ROOT/'config/project.json')['classes']] and len(classes)==10
    train=rows(ROOT/'data/splits/train.csv');validation=rows(ROOT/'data/splits/validation.csv')
    assert len(train)==1500 and len(validation)==300
    assert {r['session_id'] for r in train}=={f's{i:03d}' for i in range(1,6)}
    assert {r['session_id'] for r in validation}=={'s006'}
    for name in ['train','validation']:
        assert hashlib.sha256((ROOT/f'data/splits/{name}.csv').read_bytes()).hexdigest()==experiment['manifests_sha256'][name]
    for field in ['raw_path','processed_path','sha256','session_id']:
        assert not {r[field] for r in train}&{r[field] for r in validation}
    audit=read(ROOT/'reports/dataset_10_audit/integrity.json');assert not audit['errors']
    inventory=rows(ROOT/'reports/dataset_10_audit/inventory.csv')
    unknown=[r for r in inventory if r['class_id']=='unknown' and r['session_id']=='s006']
    assert len(unknown)==50 and not {r['sha256'] for r in unknown}&{r['sha256'] for r in train+validation}
    for row in unknown:
        assert hashlib.sha256(contained(row['raw_path']).read_bytes()).hexdigest()==row['sha256']
    checkpoint=modeldir/'best.keras';model_hash=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    model=tf.keras.models.load_model(checkpoint,compile=False)
    assert model.output_shape[-1]==10 and tuple(model.input_shape[1:])==(128,128,3)
    joint=tf.keras.Model(model.input,[model.output,model.layers[-1].input])
    def extract(records,raw=False):
        images=[np.asarray(prepare_image(contained(r['raw_path'] if raw else r['processed_path'])),dtype=np.uint8) for r in records]
        outputs=[joint(np.stack(images[i:i+32]),training=False) for i in range(0,len(images),32)]
        probs=np.concatenate([np.asarray(o[0]) for o in outputs]);features=np.concatenate([np.asarray(o[1]) for o in outputs])
        assert np.isfinite(probs).all() and np.allclose(probs.sum(axis=1),1,atol=1e-5)
        return probs,features
    print('Construyendo referencias con1500 conocidas de s001-s005...',flush=True)
    _,references=extract(train)
    known_probs,known_features=extract(validation);unknown_probs,unknown_features=extract(unknown,raw=True)
    known_scores=neighbor_similarity(known_features,references,k=5);unknown_scores=neighbor_similarity(unknown_features,references,k=5)
    threshold=calibrate_threshold(unknown_scores,.7)
    correct=[int(classes[int(p.argmax())]==r['class_id']) for r,p in zip(validation,known_probs)]
    metrics=evaluate_rejection(known_scores,correct,unknown_scores,threshold)
    dest=report/'rejection';dest.mkdir(exist_ok=False)
    archive=modeldir/'rejection_references.npz'
    if archive.exists():raise ValueError('Ya existen referencias; usar otro identificador')
    np.savez_compressed(archive,features=references,classes=np.array(classes),raw_paths=np.array([r['raw_path'] for r in train]))
    archive_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
    configuration=dict(model_path=checkpoint.relative_to(ROOT).as_posix(),model_sha256=model_hash,classes=classes,
        image_size=[128,128],confidence_threshold=None,
        rejection_detector=dict(method='knn_cosine',neighbors=5,threshold=threshold,calibrated=True,calibration_rule='unknown_rejection_target',
            target_unknown_rejection=.7,references_path=archive.relative_to(ROOT).as_posix(),references_sha256=archive_hash,
            model_sha256=model_hash,reference_sessions=[f's{i:03d}' for i in range(1,6)],calibration_sessions=['s006']),
        status='MobileNet diez clases; detector conservador calibrado internamente en s006; prueba final s007 pendiente',
        comparison_path='reports/cv10_unknown_knn_20261018/detector_comparison.json',
        calibration_path=(dest/'calibration.json').relative_to(ROOT).as_posix(),test_evaluated=False)
    save(dest/'selected_model_candidate.json',configuration)
    save(dest/'calibration.json',dict(model_sha256=model_hash,references_sha256=archive_hash,method='knn_cosine',neighbors=5,
        threshold=threshold,reference_images=1500,reference_sessions=[f's{i:03d}' for i in range(1,6)],calibration_session='s006',
        calibration_known_images=300,calibration_unknown_images=50,metrics=metrics,rule='Menor umbral que rechaza al menos70% de unknown internos',
        known_validation_reused_for_early_stopping=True,independent_evaluation=False,test_used=False))
    records=[]
    for row,prob,score in zip(validation+unknown,np.concatenate([known_probs,unknown_probs]),np.concatenate([known_scores,unknown_scores])):
        records.append(dict(raw_path=row['raw_path'],session_id=row['session_id'],class_id=row['class_id'],predicted_class=classes[int(prob.argmax())],
            confidence=float(prob.max()),similarity=float(score),threshold=threshold,rejected=int(score<=threshold)))
    write(dest/'calibration_predictions.csv',records)
    save(dest/'reference_manifest.json',dict(images=1500,feature_dimension=int(references.shape[1]),classes=classes,
        raw_paths_and_hashes=[dict(raw_path=r['raw_path'],sha256=r['sha256']) for r in train]))
    if a.activate:
        selected=ROOT/'config/selected_model.json'
        save(dest/'previous_selection.json',read(selected))
        temporary=selected.with_suffix('.tmp.json');save(temporary,configuration);temporary.replace(selected)
    print(json.dumps(dict(activated=a.activate,threshold=threshold,calibration_metrics=metrics,selected_model=configuration['model_path']),indent=2),flush=True)


if __name__=='__main__':main()
