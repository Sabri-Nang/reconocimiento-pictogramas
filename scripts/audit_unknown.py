"""Audita negativos y duplicados frente a conocidas; no asigna particiones."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    hashes={}
    for path in sorted((ROOT/'data/raw/known').rglob('*')):
        if path.is_file() and path.suffix.lower() in {'.jpg','.jpeg','.png'}:
            hashes[hashlib.sha256(path.read_bytes()).hexdigest()]=path.relative_to(ROOT).as_posix()
    rows=[];errors=[];counts=Counter()
    for path in sorted((ROOT/'data/raw/unknown').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.jpg','.jpeg','.png'}:continue
        match=re.fullmatch(r'unknown_(s\d{3})_\d{4}\.(jpg|jpeg|png)',path.name,re.I)
        if not match:
            errors.append(f'Nombre inválido: {path.name}');continue
        session=match.group(1);digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in hashes:errors.append(f'Duplicado: {path.name} y {hashes[digest]}')
        hashes[digest]=path.relative_to(ROOT).as_posix()
        try:
            with Image.open(path) as im:im.verify()
            with Image.open(path) as im:
                width,height=im.size
                if im.format not in {'JPEG','PNG'}:raise ValueError('Formato inválido')
        except (OSError,ValueError) as error:
            errors.append(f'{path.name}: {error}');continue
        counts[session]+=1
        rows.append(dict(raw_path=path.relative_to(ROOT).as_posix(),session_id=session,sha256=digest,width=width,height=height))
    report=dict(images=len(rows),session_counts=dict(counts),errors=errors,partition_assigned=False,visual_quality_reviewed=False)
    target=ROOT/'reports/unknown_audit.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'reports/unknown_inventory.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['raw_path','session_id','sha256','width','height']);writer.writeheader();writer.writerows(rows)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
