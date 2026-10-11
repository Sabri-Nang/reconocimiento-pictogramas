"""Compara candidatos en validación y mide inferencia en CPU; sin prueba."""
import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","2")
import numpy as np
import tensorflow as tf
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs",nargs="+",required=True)
    a=p.parse_args()
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    manifests={key:hashlib.sha256((ROOT/f"data/splits/{key}.csv").read_bytes()).hexdigest() for key in ["train","validation"]}
    with (ROOT/'data/splits/validation.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
    images=[]
    for row in rows[:30]:
        with Image.open(ROOT/row['processed_path']) as im:images.append(np.asarray(im,dtype=np.uint8))
    results=[]
    for run in a.runs:
        folder=ROOT/'models'/run
        exp=json.loads((folder/'experiment.json').read_text(encoding='utf-8'))
        if exp['manifests_sha256']!=manifests:
            raise ValueError(f'Manifiestos distintos: {run}')
        metrics=json.loads((ROOT/'reports'/run/'metrics.json').read_text(encoding='utf-8'))
        path=folder/'best.keras';model=tf.keras.models.load_model(path)
        @tf.function(input_signature=[tf.TensorSpec((1,128,128,3),tf.uint8)])
        def infer(x): return model(x,training=False)
        for _ in range(5):infer(images[0][None]).numpy()
        durations=[]
        for im in images:
            start=time.perf_counter();infer(im[None]).numpy();durations.append((time.perf_counter()-start)*1000)
        results.append(dict(run=run,validation_accuracy=metrics['validation_accuracy'],validation_loss=metrics['validation_loss'],macro_f1=metrics['classification_report']['macro avg']['f1-score'],model_bytes=path.stat().st_size,parameters=model.count_params(),inference_median_ms=float(np.median(durations)),inference_p95_ms=float(np.percentile(durations,95))))
    results.sort(key=lambda r:(-r['validation_accuracy'],-r['macro_f1'],r['validation_loss']))
    winner=results[0]['run']
    output=dict(partition='validation s006',selection_rule='Mayor exactitud, luego macro F1, luego menor pérdida; selección provisional del piloto',benchmark='CPU, cuatro threads intra-op, dos inter-op, tf.function, batch1, 5 calentamientos y 30 mediciones, excluye carga y preprocesamiento',results=results,selected_run=winner,test_evaluated=False)
    dest=ROOT/'reports/model_comparison.json';dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    exp=json.loads((ROOT/'models'/winner/'experiment.json').read_text(encoding='utf-8'))
    selection=dict(model_path=f'models/{winner}/best.keras',classes=exp['classes'],image_size=exp['image_size'],confidence_threshold=None,status='piloto; umbral no calibrado; prueba pendiente',comparison_path='reports/model_comparison.json')
    (ROOT/'config/selected_model.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
