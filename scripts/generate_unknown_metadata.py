import argparse
import csv
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLANS_PATH = PROJECT_ROOT / "config" / "unknown_session_plans.json"
UNKNOWN_PATH = PROJECT_ROOT / "data" / "raw" / "unknown"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}
METADATA_FIELDS = [
    "filename",
    "class_id",
    "session_id",
    "device",
    "lighting",
    "background",
    "distance",
    "perspective",
    "source",
    "notes",
]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera metadata para imágenes unknown de una sesión."
    )
    parser.add_argument("--session", required=True, help="Por ejemplo: s001.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Escribe los cambios. Sin esta opción solo muestra una vista previa.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def generate_rows(session_id: str, plan: dict) -> list[dict]:
    if not UNKNOWN_PATH.is_dir():
        raise ValueError(f"No existe la carpeta: {UNKNOWN_PATH}")

    pattern = re.compile(
        rf"^unknown_{re.escape(session_id)}_(\d{{4}})\.(jpg|jpeg|png)$",
        re.IGNORECASE,
    )
    images = []
    for path in UNKNOWN_PATH.iterdir():
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            match = pattern.fullmatch(path.name)
            if match:
                images.append((int(match.group(1)), path))
    images.sort(key=lambda item: item[0])

    expected = plan["expected"]
    expected_numbers = list(range(1, expected + 1))
    numbers = [number for number, _ in images]
    if numbers != expected_numbers:
        raise ValueError(
            f"{session_id}: se esperaban los números 0001-{expected:04d}, "
            f"pero se encontraron {numbers}."
        )

    defaults = plan["defaults"]
    return [
        {
            "filename": path.name,
            "class_id": "unknown",
            "session_id": session_id,
            "device": defaults["device"],
            "lighting": defaults["lighting"],
            "background": defaults["background"],
            "distance": defaults["distance"],
            "perspective": defaults["perspective"],
            "source": defaults["source"],
            "notes": defaults.get("notes", ""),
        }
        for _, path in images
    ]


def load_existing_rows() -> list[dict]:
    if not METADATA_PATH.exists():
        return []
    with METADATA_PATH.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != METADATA_FIELDS:
            raise ValueError("La cabecera de metadata.csv no coincide con la esperada.")
        return list(reader)


def write_metadata(rows: list[dict]) -> None:
    temporary_path = METADATA_PATH.with_suffix(".csv.tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=METADATA_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary_path.replace(METADATA_PATH)


def main() -> None:
    args = parse_arguments()
    try:
        plans = load_json(PLANS_PATH)
        if args.session not in plans:
            raise ValueError(f"No existe un plan unknown para {args.session}.")

        generated = generate_rows(args.session, plans[args.session])
        existing = load_existing_rows()
        preserved = [
            row
            for row in existing
            if not (
                row["session_id"] == args.session
                and row["class_id"] == "unknown"
            )
        ]
        final_rows = preserved + generated
        filenames = [row["filename"] for row in final_rows]
        if len(filenames) != len(set(filenames)):
            raise ValueError("El resultado contiene nombres de archivo duplicados.")
        final_rows.sort(
            key=lambda row: (row["session_id"], row["class_id"], row["filename"])
        )

        print(f"Se generaron {len(generated)} filas unknown para {args.session}.")
        for row in generated[:5]:
            print(
                f"{row['filename']}: {row['lighting']}, "
                f"{row['background']}, {row['perspective']}"
            )

        if not args.apply:
            print("\nVista previa: metadata.csv no fue modificado.")
            print("Agregá --apply para escribir los cambios.")
            return

        write_metadata(final_rows)
        print(f"\nArchivo actualizado: {METADATA_PATH}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
