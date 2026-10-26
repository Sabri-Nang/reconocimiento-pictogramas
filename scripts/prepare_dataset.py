"""Valida capturas y metadata, y prepara PNG y manifiestos de referencia."""

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from reconocimiento_pictogramas.preprocessing import prepare_image

ROOT = Path(__file__).resolve().parents[1]

FIELDS = [
    "raw_path",
    "processed_path",
    "class_id",
    "class_index",
    "session_id",
    "sha256",
]


def collect_records(root: Path):
    """Valida conocidas y devuelve solamente la partición base para manifiestos.

    Las sesiones suplementarias se revisan con los mismos controles de nombres,
    cantidades y hashes, pero no se agregan a ``data/splits``. Sus manifiestos
    de desarrollo pertenecen a cada experimento.
    """
    config = json.loads((root / "config/project.json").read_text(encoding="utf-8"))
    plan = json.loads(
        (root / "config/dataset_partitions.json").read_text(encoding="utf-8")
    )
    classes = [item["id"] for item in config["classes"]]
    partitions = plan["sessions"]
    partitioned_sessions = [
        session for group in partitions.values() for session in group
    ]
    supplementary_sessions = plan.get("supplementary_sessions", [])
    if not all(isinstance(session, str) for session in supplementary_sessions):
        raise ValueError("Las sesiones suplementarias deben ser textos.")
    all_sessions = partitioned_sessions + supplementary_sessions
    if len(all_sessions) != len(set(all_sessions)):
        raise ValueError("Una sesión aparece en más de una partición o grupo.")

    with (root / "data/metadata.csv").open(encoding="utf-8-sig", newline="") as handle:
        metadata = list(csv.DictReader(handle))
    names = [row["filename"] for row in metadata]
    if len(names) != len(set(names)):
        raise ValueError("Metadata contiene filenames repetidos.")
    invalid_classes = {row["class_id"] for row in metadata} - set(classes) - {"unknown"}
    if invalid_classes:
        raise ValueError(f"Clases de metadata no admitidas: {invalid_classes}")

    known_metadata = [row for row in metadata if row["class_id"] != "unknown"]
    indexed = {row["filename"]: row for row in known_metadata}
    records = {split: [] for split in partitions}
    seen = set()
    hashes = {}
    counts = Counter()
    split_by_session = {
        session: split for split, sessions in partitions.items() for session in sessions
    }

    for path in sorted((root / "data/raw/known").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        row = indexed.get(path.name)
        if row is None:
            raise ValueError(f"Sin metadata: {path.name}")
        class_id, session = row["class_id"], row["session_id"]
        name_pattern = (
            rf"{re.escape(class_id)}_{re.escape(session)}_\d{{4}}"
            rf"\.(jpg|jpeg|png)"
        )
        if (
            class_id not in classes
            or path.parent.name != class_id
            or not re.fullmatch(name_pattern, path.name, re.IGNORECASE)
        ):
            raise ValueError(f"Clase/sesión/nombre inconsistentes: {path.name}")
        if session not in all_sessions:
            raise ValueError(f"Sesión sin partición o grupo suplementario: {session}")
        if path.name in seen:
            raise ValueError(f"Filename de imagen repetido: {path.name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in hashes:
            raise ValueError(f"Duplicado exacto: {path.name} y {hashes[digest]}")
        hashes[digest] = path.name
        seen.add(path.name)
        counts[(session, class_id)] += 1

        split = split_by_session.get(session)
        if split is None:
            continue
        records[split].append(
            {
                "raw_path": path.relative_to(root).as_posix(),
                "processed_path": f"data/processed/{class_id}/{path.stem}.png",
                "class_id": class_id,
                "class_index": classes.index(class_id),
                "session_id": session,
                "sha256": digest,
            }
        )

    if seen != set(indexed):
        raise ValueError("Hay registros de metadata sin imagen.")

    pending = []
    for split, sessions in partitions.items():
        for session in sessions:
            total = sum(counts[(session, class_id)] for class_id in classes)
            if total == 0 and split == "test":
                pending.append(session)
                continue
            _validate_session_counts(counts, session, classes, plan)
    for session in supplementary_sessions:
        _validate_session_counts(counts, session, classes, plan)
    return config, records, pending


def _validate_session_counts(counts, session, classes, plan):
    for class_id in classes:
        count = counts[(session, class_id)]
        if count != plan["expected_per_class_session"]:
            raise ValueError(f"Cantidad incorrecta: {session}/{class_id}: {count}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Generar PNG y manifiestos; sin esta opción solo validar.",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Conversiones concurrentes (1 a 8)."
    )
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error("workers debe estar entre 1 y 8")

    config, records, pending = collect_records(ROOT)
    for split, rows in records.items():
        print(f"{split}: {len(rows)} imágenes")
    print(f"Prueba pendiente: {', '.join(pending) or 'ninguna'}")
    if not args.apply:
        print("Validación correcta. Para preparar archivos: agregar --apply")
        return

    size = (config["image"]["width"], config["image"]["height"])
    _backup_existing_manifests()
    for split, rows in records.items():
        _convert_rows(rows, size, args.workers, split)
    _write_manifests(records, config, pending)
    print("Preparación completa. Originales conservados.")


def _backup_existing_manifests():
    previous = ROOT / "data/splits"
    if not (previous / "summary.json").exists():
        return
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    backup = ROOT / "reports" / "dataset_preparation_backups" / stamp
    shutil.copytree(previous, backup)
    print(f"Respaldo de manifiestos: {backup}", flush=True)


def _convert_rows(rows, size, workers, split):
    def convert(row):
        target = ROOT / row["processed_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        image = prepare_image(ROOT / row["raw_path"], size)
        temporary = target.with_suffix(".tmp.png")
        image.save(temporary, format="PNG")
        temporary.replace(target)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, _ in enumerate(pool.map(convert, rows), 1):
            if index % 150 == 0 or index == len(rows):
                print(f"{split}: {index}/{len(rows)} procesadas", flush=True)


def _write_manifests(records, config, pending):
    destination = ROOT / "data/splits"
    destination.mkdir(parents=True, exist_ok=True)
    for split, rows in records.items():
        with (destination / f"{split}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    with (destination / "development.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(
            row for split, rows in records.items() if split != "test" for row in rows
        )
    summary = {
        "classes": [item["id"] for item in config["classes"]],
        "image": config["image"],
        "preprocessing": (
            "EXIF transpose -> RGB -> resize LANCZOS -> PNG; valores uint8 "
            "0..255, sin aumentos"
        ),
        "counts": {split: len(rows) for split, rows in records.items()},
        "pending_test_sessions": pending,
        "test_ready": not pending,
    }
    (destination / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
