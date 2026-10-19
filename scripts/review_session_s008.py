"""Audita s008, crea hojas visuales y evalúa el modelo seleccionado congelado."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
from collections import Counter
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from PIL import Image, ImageOps, ImageDraw
import numpy as np
from reconocimiento_pictogramas.preprocessing import prepare_image
from reconocimiento_pictogramas.feature_rejection import neighbor_similarity
from reconocimiento_pictogramas.rejection import evaluate_rejection

def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate", action="store_true")
    args=parser.parse_args()
    out=ROOT/"reports/session_s008_review"
    out.mkdir(exist_ok=True)
    if args.evaluate and (out/"evaluation.json").exists():
        raise ValueError("Evaluacion congelada ya existente; conservar evidencia y usar otro experimento.")
    sheets=out/"contact_sheets";sheets.mkdir(exist_ok=True)
    project=json.loads((ROOT/"config/project.json").read_text(encoding="utf-8"))
    classes=[c["id"] for c in project["classes"]]
    with (ROOT/"data/metadata.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=[r for r in csv.DictReader(f) if r["session_id"]=="s008"]
    assert Counter(r["class_id"] for r in rows)==Counter({**dict.fromkeys(classes,30),"unknown":50})
    with (ROOT/"reports/dataset_10_audit/inventory.csv").open(encoding="utf-8-sig",newline="") as f:
        seen={r["sha256"] for r in csv.DictReader(f)}
    inventory=[]
    for cls in classes+["unknown"]:
        group=sorted([r for r in rows if r["class_id"]==cls],key=lambda r:r["filename"])
        sheet=Image.new("RGB",(1200,240*((len(group)+4)//5)),"white");draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(group):
            base=ROOT/"data/raw"/("unknown" if cls=="unknown" else "known/"+cls)
            path=base/row["filename"];digest=hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest not in seen, "Duplicado exacto: "+path.name
            seen.add(digest)
            with Image.open(path) as im:im.verify()
            with Image.open(path) as im:
                width,height=im.size
                thumb=ImageOps.contain(ImageOps.exif_transpose(im).convert("RGB"),(232,205))
            x=(i%5)*240;y=(i//5)*240;sheet.paste(thumb,(x+(240-thumb.width)//2,y))
            draw.text((x+4,y+208),f"{row['filename']} / {row['distance']}",fill="black")
            inventory.append(dict(raw_path=path.relative_to(ROOT).as_posix(),class_id=cls,session_id="s008",sha256=digest,width=width,height=height,distance=row["distance"]))
        sheet.save(sheets/(cls+".jpg"),quality=88)
    write(out/"inventory.csv",inventory)
    audit=dict(session="s008",images=len(inventory),counts=dict(Counter(r["class_id"] for r in inventory)),errors=[],exact_duplicates=0,prior_hash_scope="Inventario previo s001-s006; hashes s008 recalculados",visual_review="Hojas generadas; registrar observaciones humanas por separado",test_used=False)
    (out/"integrity.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Auditoria y hojas visuales generadas",flush=True)
    if not args.evaluate:return
    import tensorflow as tf
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    from reconocimiento_pictogramas.inference import load_selected_model,load_selected_detector
    from sklearn.metrics import classification_report,confusion_matrix
    model,config=load_selected_model();joint,refs=load_selected_detector()
    assert config["classes"]==classes
    selected_bytes=(ROOT/"config/selected_model.json").read_bytes()
    detector=config["rejection_detector"];threshold=detector["threshold"]
    results=[]
    for start in range(0,len(inventory),32):
        batch=inventory[start:start+32]
        images=np.stack([np.asarray(prepare_image(ROOT/r["raw_path"],tuple(config["image_size"])),dtype=np.uint8) for r in batch])
        probs,features=joint(images,training=False)
        similarities=neighbor_similarity(np.asarray(features),refs,k=detector["neighbors"])
        for row,prob,score in zip(batch,np.asarray(probs),similarities):
            pred=classes[int(prob.argmax())]
            results.append(dict(**row,predicted_class=pred,confidence=float(prob.max()),similarity=float(score),threshold=threshold,rejected=int(score<=threshold),correct=int(pred==row["class_id"])))
        print(f"Evaluadas {min(start+32,len(inventory))}/{len(inventory)}",flush=True)
    known=[r for r in results if r["class_id"]!="unknown"];unknown=[r for r in results if r["class_id"]=="unknown"]
    metrics=evaluate_rejection([r["similarity"] for r in known],[r["correct"] for r in known],[r["similarity"] for r in unknown],threshold)
    report=classification_report([r["class_id"] for r in known],[r["predicted_class"] for r in known],labels=classes,output_dict=True,zero_division=0)
    by_distance={d:dict(correct=sum(r["correct"] for r in known if r["distance"]==d),total=sum(r["distance"]==d for r in known)) for d in ("corta","media","larga")}
    summary=dict(model_path=config["model_path"],model_sha256=config["model_sha256"],selected_config_sha256=hashlib.sha256(selected_bytes).hexdigest(),threshold=threshold,metrics=metrics,classification_report=report,by_distance=by_distance,confusion_matrix=confusion_matrix([r["class_id"] for r in known],[r["predicted_class"] for r in known],labels=classes).tolist(),classes=classes,test_used=False,trained_on_s008=False,threshold_recalibrated=False,interpretation="Diagnostico de desarrollo con modelo y umbral congelados antes de usar s008 para entrenar; no prueba final. Desconocidos solo objetos y escenas, sin otros pictogramas.")
    assert (ROOT/"config/selected_model.json").read_bytes()==selected_bytes
    write(out/"predictions.csv",results)
    (out/"evaluation.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(metrics,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
