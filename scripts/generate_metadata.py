import argparse
import csv
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"
SESSION_PLANS_PATH = PROJECT_ROOT / "config" / "session_plans.json"
KNOWN_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "known"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"

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

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera metadatos para una sesión de captura."
    )
    parser.add_argument(
        "--session",
        required=True,
        help="Sesión que se procesará, por ejemplo s003.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Escribe los cambios. Sin esta opción solo muestra una vista previa.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def find_range(number: int, ranges: list[dict]) -> dict:
    matches = [
        rule
        for rule in ranges
        if rule["start"] <= number <= rule["end"]
    ]

    if len(matches) != 1:
        raise ValueError(
            f"El número {number:04d} debe coincidir con un único rango."
        )

    return matches[0]


def generate_session_rows(
    session_id: str,
    class_ids: list[str],
    plan: dict,
) -> list[dict]:
    rows = []
    expected = plan["expected_per_class"]
    defaults = plan["defaults"]
    default_ranges = plan["ranges"]
    class_ranges = plan.get("class_ranges", {})

    for class_id in class_ids:
        ranges = class_ranges.get(class_id, default_ranges)
        class_path = KNOWN_DATA_PATH / class_id
        pattern = re.compile(
            rf"^{re.escape(class_id)}_{re.escape(session_id)}_(\d{{4}})"
            rf"\.(jpg|jpeg|png)$",
            re.IGNORECASE,
        )

        session_images = []

        for image_path in class_path.iterdir():
            if (
                image_path.is_file()
                and image_path.suffix.lower() in VALID_EXTENSIONS
            ):
                match = pattern.fullmatch(image_path.name)

                if match:
                    session_images.append(
                        (int(match.group(1)), image_path)
                    )

        session_images.sort(key=lambda item: item[0])

        if len(session_images) != expected:
            raise ValueError(
                f"{class_id}: se esperaban {expected} imágenes de "
                f"{session_id}, pero se encontraron {len(session_images)}."
            )

        numbers = [number for number, _ in session_images]

        if len(numbers) != len(set(numbers)):
            raise ValueError(
                f"{class_id}: existen números repetidos en {session_id}."
            )

        for number, image_path in session_images:
            rule = find_range(number, ranges)
            values = {**defaults, **rule}

            row = {
                "filename": image_path.name,
                "class_id": class_id,
                "session_id": session_id,
                "device": values["device"],
                "lighting": values["lighting"],
                "background": values["background"],
                "distance": values["distance"],
                "perspective": values["perspective"],
                "source": values["source"],
                "notes": values.get("notes", ""),
            }
            rows.append(row)

    return rows


def load_existing_rows() -> list[dict]:
    if not METADATA_PATH.exists():
        return []

    with METADATA_PATH.open(newline="", encoding="utf-8") as metadata_file:
        reader = csv.DictReader(metadata_file)

        if reader.fieldnames != METADATA_FIELDS:
            raise ValueError(
                "La cabecera de metadata.csv no coincide con la esperada."
            )

        return list(reader)


def write_metadata(rows: list[dict]) -> None:
    temporary_path = METADATA_PATH.with_suffix(".csv.tmp")

    with temporary_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as metadata_file:
        writer = csv.DictWriter(
            metadata_file,
            fieldnames=METADATA_FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)

    temporary_path.replace(METADATA_PATH)


def main() -> None:
    arguments = parse_arguments()

    try:
        project_config = load_json(PROJECT_CONFIG_PATH)
        session_plans = load_json(SESSION_PLANS_PATH)

        if arguments.session not in session_plans:
            raise ValueError(
                f"No existe un plan para la sesión {arguments.session}."
            )

        class_ids = [
            item["id"]
            for item in project_config["classes"]
        ]

        generated_rows = generate_session_rows(
            session_id=arguments.session,
            class_ids=class_ids,
            plan=session_plans[arguments.session],
        )

        existing_rows = load_existing_rows()

        preserved_rows = [
            row
            for row in existing_rows
            if (
                row["session_id"] != arguments.session
                or row["class_id"] == "unknown"
            )
        ]

        final_rows = preserved_rows + generated_rows
        filenames = [row["filename"] for row in final_rows]

        if len(filenames) != len(set(filenames)):
            raise ValueError(
                "El resultado contiene nombres de archivo duplicados."
            )

        final_rows.sort(
            key=lambda row: (
                row["session_id"],
                row["class_id"],
                row["filename"],
            )
        )

        print(
            f"Se generaron {len(generated_rows)} filas "
            f"para {arguments.session}."
        )

        for row in generated_rows[:5]:
            print(
                f"{row['filename']}: "
                f"{row['background']}, "
                f"{row['distance']}, "
                f"{row['perspective']}"
            )

        if not arguments.apply:
            print("\nVista previa: metadata.csv no fue modificado.")
            print("Agregá --apply para escribir los cambios.")
            return

        write_metadata(final_rows)
        print(f"\nArchivo actualizado: {METADATA_PATH}")

    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
