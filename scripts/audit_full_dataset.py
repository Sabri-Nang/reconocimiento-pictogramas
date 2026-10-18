"""Audita conocidas y desconocidas con metadata, sin evaluar prueba s007."""
import csv
import hashlib
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    config=json.loads((ROOT/'config/project.json').read_text(encoding='utf-8'))
    classes=[c['id'] for c in config['classes']]
    with (ROOT/'data/metadata.csv').open(encoding='utf-8-sig',newline='') as f:metadata=list(csv.DictReader(f))
    errors=[];seen_names=set();indexed={}
    for row in metadata:
        name=row['filename']
        if name in indexed:errors.append(f'Metadata repetida: {name}')
        indexed[name]=row
        if row['class_id'] not in classes+['unknown']:errors.append(f'Clase inválida: {name}')
    paths=[]
    for group in ['known','unknown']:
        for path in sorted((ROOT/f'data/raw/{group}').rglob('*')):
            if path.is_file() and path.suffix.lower() in {'.jpg','.jpeg','.png'}:
                if '_s007_' in path.name.lower():
                    raise ValueError('s007 presente: excluir explícitamente de esta auditoría de desarrollo antes de continuar.')
                paths.append(path)
    def inspect(path):
        row=indexed.get(path.name)
        if row is None:return path,None,'Sin metadata'
        cls,session=row['class_id'],row['session_id']
        if not re.fullmatch(rf'{re.escape(cls)}_{re.escape(session)}_\d{{4}}\.(jpg|jpeg|png)',path.name,re.I):return path,None,'Nombre/clase/sesión incoherentes'
        expected=ROOT/'data/raw/unknown' if cls=='unknown' else ROOT/f'data/raw/known/{cls}'
        if path.parent!=expected:return path,None,'Carpeta incorrecta'
        if session not in {f's{i:03d}' for i in range(1,7)}:return path,None,'Sesión de desarrollo no admitida'
        try:
            with Image.open(path) as im:
                fmt=im.format;im.load();width,height=im.size
                if fmt not in {'JPEG','PNG'}:raise ValueError('Formato inválido')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            return path,dict(raw_path=path.relative_to(ROOT).as_posix(),class_id=cls,session_id=session,sha256=digest,width=width,height=height),None
        except (OSError,ValueError,Image.DecompressionBombError) as e:return path,None,str(e)
    rows=[];hashes={};counts=Counter();dimensions=Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,(path,row,error) in enumerate(pool.map(inspect,paths),1):
            if path.name in seen_names:errors.append(f'Filename de captura repetido: {path.name}')
            seen_names.add(path.name)
            if error:errors.append(f'{path.name}: {error}')
            else:
                if row['sha256'] in hashes:errors.append(f"Duplicado exacto: {path.name} y {hashes[row['sha256']]}")
                hashes[row['sha256']]=path.name
                rows.append(row);counts[(row['class_id'],row['session_id'])]+=1;dimensions[f"{row['width']}x{row['height']}"]+=1
            if i%300==0:print(f'Auditadas {i}/{len(paths)}',flush=True)
    for name in sorted(set(indexed)-seen_names):errors.append(f'Metadata sin imagen: {name}')
    for cls in classes:
        for i in range(1,7):
            session=f's{i:03d}'
            if counts[(cls,session)]!=30:errors.append(f'{cls}/{session}: se esperaban30, hay{counts[(cls,session)]}')
    report=dict(classes=classes,known_images=sum(r['class_id']!='unknown' for r in rows),unknown_images=sum(r['class_id']=='unknown' for r in rows),metadata_rows=len(metadata),counts_by_class_session={c:{f's{i:03d}':counts[(c,f's{i:03d}')] for i in range(1,7)} for c in classes+['unknown']},dimensions=dict(dimensions),errors=errors,test_evaluated=False,visual_review='pendiente',near_duplicates_checked=False)
    dest=ROOT/'reports/dataset_10_audit';dest.mkdir(parents=True,exist_ok=True)
    (dest/'integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (dest/'inventory.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['raw_path','class_id','session_id','sha256','width','height']);writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in report.items() if k not in ['counts_by_class_session','classes']},ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
