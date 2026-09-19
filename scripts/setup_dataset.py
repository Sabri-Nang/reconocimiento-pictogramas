import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"

METADATA_COLUMNS = [
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


def load_class_ids() -> list[str]:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    return [item["id"] for item in config["classes"]]


def create_dataset_directories(class_ids: list[str]) -> None:
    known_path = RAW_DATA_PATH / "known"
    known_path.mkdir(parents=True, exist_ok=True)

    for class_id in class_ids:
        class_path = known_path / class_id
        class_path.mkdir(exist_ok=True)
        print(f"Carpeta preparada: {class_path.relative_to(PROJECT_ROOT)}")

    unknown_path = RAW_DATA_PATH / "unknown"
    unknown_path.mkdir(parents=True, exist_ok=True)
    print(f"Carpeta preparada: {unknown_path.relative_to(PROJECT_ROOT)}")


def create_metadata_file() -> None:
    if METADATA_PATH.exists():
        print("El archivo data/metadata.csv ya existe; no se modificó.")
        return

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with METADATA_PATH.open("w", newline="", encoding="utf-8") as metadata_file:
        writer = csv.writer(metadata_file)
        writer.writerow(METADATA_COLUMNS)

    print("Archivo creado: data/metadata.csv")


def main() -> None:
    class_ids = load_class_ids()
    create_dataset_directories(class_ids)
    create_metadata_file()
    print("Estructura del dataset preparada correctamente.")


if __name__ == "__main__":
    main()