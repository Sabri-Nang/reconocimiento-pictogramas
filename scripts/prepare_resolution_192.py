"""Prepara192 desde originales auditados; conserva particiones y derivados128."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sys
import platform
import importlib.metadata
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.preprocessing import prepare_image
from reconocimiento_pictogramas.cross_validation import validate_records
from train_cross_validation import read_json,read_csv,write_csv,save_json,contained

OUT=ROOT/'reports/resolution_192_20261019'
CONFIG=ROOT/'config/cv_s008_192.json'

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'preparation.json').exists():raise ValueError('Preparacion finalizada: conservarla; no sobrescribir')
    reference=read_json(ROOT/'reports/cv10_s008_128_20261019/protocol.json')
    cfg=reference['config'].copy()
    source=contained(reference['development_manifest'])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==reference['development_sha256']
    records=read_csv(source);classes=[c['id'] for c in reference['project']['classes']]
    assert len(records)==2100 and 's007' not in cfg['sessions']
    validate_records(records,classes,cfg['expected_per_class_session'],sessions=cfg['sessions'])
    def convert(row):
        original=contained(row['raw_path'])
        if hashlib.sha256(original.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Original modificado: '+row['raw_path'])
        destination=ROOT/'data/processed/resolution_192_20261019'/row['class_id']/(original.stem+'.png')
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():raise ValueError('Derivado ya existente: '+str(destination))
        image=prepare_image(original,(192,192));assert image.mode=='RGB' and image.size==(192,192)
        image.save(destination,format='PNG')
        return dict(**{k:v for k,v in row.items() if k!='processed_path'},processed_path=destination.relative_to(ROOT).as_posix(),processed_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    converted=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for record in pool.map(convert,records):
            converted.append(record)
            if len(converted)%150==0:print(f'Preparadas {len(converted)}/2100',flush=True)
    assert [{k:r[k] for k in ('raw_path','class_id','class_index','session_id','sha256')} for r in records]==[{k:r[k] for k in ('raw_path','class_id','class_index','session_id','sha256')} for r in converted]
    manifest=OUT/'development_192.csv';write_csv(manifest,converted)
    audit=dict(images=len(converted),errors=[],size=[192,192],test_used=False,source_manifest_sha256=reference['development_sha256'],original_hashes_verified=True,source='originales, no PNG128')
    save_json(OUT/'integrity.json',audit)
    cfg.update(image_size=[192,192],development_manifest=manifest.relative_to(ROOT).as_posix(),audit_path=(OUT/'integrity.json').relative_to(ROOT).as_posix(),note='Comparacion192 frente a128: mismas siete rondas, semillas, batch32, presupuestos CNN30 y MobileNet20+40, aumentos y parada. Originales EXIF/RGB/LANCZOS. CNN Flatten aumenta parametros; MobileNet usa promedio global. s007 excluida. No modifica aplicacion.')
    save_json(CONFIG,cfg)
    packages={n:importlib.metadata.version(n) for n in ('tensorflow','keras','numpy','pillow','scikit-learn')}
    fingerprints={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('config/project.json','config/selected_model.json','reports/session_s008_review/development_7sessions_128.csv')}
    save_json(OUT/'preparation.json',dict(**audit,development_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),protected_files_sha256=fingerprints,python=sys.version,platform=platform.platform(),packages=packages,source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('scripts/train_cross_validation.py','scripts/evaluate_unknown_cv.py','scripts/prepare_resolution_192.py')},cnn_caveat='La capa Flatten cambia cantidad de parametros; no se aisla solo resolucion con capacidad constante.'))
    print('Preparacion completa:2100 RGB192; originales y128 preservados.',flush=True)
if __name__=='__main__':main()
