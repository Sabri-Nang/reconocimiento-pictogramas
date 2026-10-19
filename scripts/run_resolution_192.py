"""Ejecuta secuencialmente CV192, rechazo, latencia y comparación contra128."""
import subprocess
import sys
from pathlib import Path
from train_cross_validation import save_json,read_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/resolution_192_20261019'
RUN='cv10_s008_192_20261019'

def main():
    assert (OUT/'preparation.json').exists(),'Preparacion pendiente'
    stage='training'
    def call(script,*args):
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*args],cwd=ROOT,check=True)
    try:
        save_json(OUT/'pipeline.json',dict(status='running',stage=stage,run_id=RUN,test_used=False))
        if not (ROOT/'reports'/RUN/'summary.json').exists():
            args=['--run-id',RUN]
            args+=['--resume'] if (ROOT/'reports'/RUN/'protocol.json').exists() else ['--config','config/cv_s008_192.json']
            call('train_cross_validation.py',*args)
        stage='rejection';save_json(OUT/'pipeline.json',dict(status='running',stage=stage,run_id=RUN,test_used=False))
        rejection_run='cv10_s008_192_unknown_knn_20261019'
        if not (ROOT/'reports'/rejection_run/'summary.json').exists():call('evaluate_unknown_cv.py','--source-run',RUN,'--run-id',rejection_run,'--method','knn')
        stage='benchmark';save_json(OUT/'pipeline.json',dict(status='running',stage=stage,run_id=RUN,test_used=False))
        for size in (128,192):
            for arch in ('cnn','mobilenet'):
                if not (OUT/f'latency_{size}_{arch}.json').exists():call('compare_resolutions.py','--benchmark','--resolution',str(size),'--architecture',arch)
        stage='comparison';save_json(OUT/'pipeline.json',dict(status='running',stage=stage,run_id=RUN,test_used=False));call('compare_resolutions.py')
        save_json(OUT/'pipeline.json',dict(status='completed',stage='completed',run_id=RUN,test_used=False,application_unchanged=True))
    except Exception as error:
        save_json(OUT/'pipeline.json',dict(status='failed',stage=stage,run_id=RUN,error=str(error),test_used=False));raise
if __name__=='__main__':main()
