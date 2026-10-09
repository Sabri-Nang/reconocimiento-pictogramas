"""Valida capturas y metadata, prepara PNG y manifiestos por sesión."""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from reconocimiento_pictogramas.preprocessing import prepare_image

FIELDS = ["raw_path", "processed_path", "class_id", "class_index", "session_id", "sha256"]

def collect_records(root: Path):
    config = json.loads((root / "config/project.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "config/dataset_partitions.json").read_text(encoding="utf-8"))
    classes = [c["id"] for c in config["classes"]]
    sessions = plan["sessions"]
    flat = [s for group in sessions.values() for s in group]
    if len(flat) != len(set(flat)):
        raise ValueError("Una sesión aparece en más de una partición.")
    with (root / "data/metadata.csv").open(encoding="utf-8-sig", newline="") as handle:
        metadata = list(csv.DictReader(handle))
    names = [row["filename"] for row in metadata]
    if len(names) != len(set(names)):
        raise ValueError("Metadata contiene filenames repetidos.")
    indexed = {row["filename"]: row for row in metadata}
    records = {split: [] for split in sessions}
    seen = set()
    hashes = {}
    counts = Counter()
    for path in sorted((root / "data/raw/known").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        row = indexed.get(path.name)
        if row is None:
            raise ValueError(f"Sin metadata: {path.name}")
        cls, session = row["class_id"], row["session_id"]
        if cls not in classes or path.parent.name != cls or not re.fullmatch(rf"{re.escape(cls)}_{re.escape(session)}_\d{{4}}\.(jpg|jpeg|png)", path.name, re.I):
            raise ValueError(f"Clase/sesión/nombre inconsistentes: {path.name}")
        if session not in flat:
            raise ValueError(f"Sesión sin partición: {session}")
        if path.name in seen:
            raise ValueError(f"Filename de imagen repetido: {path.name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in hashes:
            raise ValueError(f"Duplicado exacto: {path.name} y {hashes[digest]}")
        hashes[digest] = path.name
        seen.add(path.name)
        counts[(session, cls)] += 1
        split = next(k for k, group in sessions.items() if session in group)
        records[split].append(dict(raw_path=path.relative_to(root).as_posix(), processed_path=f"data/processed/{cls}/{path.stem}.png", class_id=cls, class_index=classes.index(cls), session_id=session, sha256=digest))
    if seen != set(names):
        raise ValueError("Hay registros de metadata sin imagen.")
    pending = []
    for split, group in sessions.items():
        for session in group:
            total = sum(counts[(session, cls)] for cls in classes)
            if total == 0 and split == "test":
                pending.append(session)
                continue
            for cls in classes:
                if counts[(session, cls)] != plan["expected_per_class_session"]:
                    raise ValueError(f"Cantidad incorrecta: {session}/{cls}: {counts[(session, cls)]}")
    return config, records, pending

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Generar PNG y manifiestos; sin esta opción solo validar.")
    args = parser.parse_args()
    config, records, pending = collect_records(ROOT)
    for split, rows in records.items():
        print(f"{split}: {len(rows)} imágenes")
    print(f"Prueba pendiente: {', '.join(pending) or 'ninguna'}")
    if not args.apply:
        print("Validación correcta. Para preparar archivos: agregar --apply")
        return
    size = (config["image"]["width"], config["image"]["height"])
    for split, rows in records.items():
        for i, row in enumerate(rows, 1):
            target = ROOT / row["processed_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            prepare_image(ROOT / row["raw_path"], size).save(target, format="PNG")
            if i % 150 == 0:
                print(f"{split}: {i}/{len(rows)} procesadas", flush=True)
    dest = ROOT / "data/splits"
    dest.mkdir(parents=True, exist_ok=True)
    for split, rows in records.items():
        with (dest / f"{split}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    summary = dict(classes=[c["id"] for c in config["classes"]], image=config["image"], preprocessing="EXIF transpose -> RGB -> resize LANCZOS -> PNG; valores uint8 0..255, sin aumentos", counts={k:len(v) for k,v in records.items()}, pending_test_sessions=pending, test_ready=not pending)
    (dest / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Preparación completa. Originales conservados.")

if __name__ == "__main__":
    main()
