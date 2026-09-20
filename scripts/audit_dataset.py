import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"
KNOWN_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "known"

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audita las imágenes de una sesión del dataset."
    )
    parser.add_argument(
        "--session",
        default="s001",
        help="Sesión que se desea revisar. Valor predeterminado: s001.",
    )
    parser.add_argument(
        "--expected-per-class",
        type=int,
        default=30,
        help="Cantidad esperada de imágenes por clase.",
    )
    return parser.parse_args()


def load_class_ids() -> list[str]:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    return [item["id"] for item in config["classes"]]


def calculate_hash(image_path: Path) -> str:
    digest = hashlib.sha256()

    with image_path.open("rb") as image_file:
        for block in iter(lambda: image_file.read(65536), b""):
            digest.update(block)

    return digest.hexdigest()


def inspect_image(image_path: Path) -> tuple[int, int, str]:
    with Image.open(image_path) as image:
        image.verify()

    with Image.open(image_path) as image:
        return image.width, image.height, image.format or "desconocido"


def audit_session(
    session_id: str,
    expected_per_class: int,
    class_ids: list[str],
) -> int:
    error_count = 0
    image_hashes: dict[str, list[Path]] = defaultdict(list)

    print(f"Auditando sesión: {session_id}")
    print(f"Cantidad esperada por clase: {expected_per_class}\n")

    for class_id in class_ids:
        class_path = KNOWN_DATA_PATH / class_id
        filename_pattern = re.compile(
            rf"^{re.escape(class_id)}_{re.escape(session_id)}_\d{{4}}"
            rf"\.(jpg|jpeg|png)$",
            re.IGNORECASE,
        )

        if not class_path.is_dir():
            print(f"[ERROR] No existe la carpeta: {class_path}")
            error_count += 1
            continue

        session_images = []
        invalid_names = []

        for image_path in sorted(class_path.iterdir()):
            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            if filename_pattern.fullmatch(image_path.name):
                session_images.append(image_path)
            elif f"_{session_id}_" in image_path.name:
                invalid_names.append(image_path)

        print(f"{class_id}: {len(session_images)} imágenes")

        if len(session_images) != expected_per_class:
            print(
                f"  [ERROR] Se esperaban {expected_per_class}, "
                f"pero se encontraron {len(session_images)}."
            )
            error_count += 1

        for image_path in invalid_names:
            print(f"  [ERROR] Nombre inválido: {image_path.name}")
            error_count += 1

        dimensions = []

        for image_path in session_images:
            try:
                width, height, image_format = inspect_image(image_path)
                dimensions.append((width, height))
                image_hashes[calculate_hash(image_path)].append(image_path)

                if image_format.upper() not in {"JPEG", "PNG"}:
                    print(
                        f"  [ERROR] Formato no admitido en "
                        f"{image_path.name}: {image_format}"
                    )
                    error_count += 1

            except (OSError, UnidentifiedImageError) as error:
                print(f"  [ERROR] No se pudo abrir {image_path.name}: {error}")
                error_count += 1

        if dimensions:
            widths = [width for width, _ in dimensions]
            heights = [height for _, height in dimensions]

            print(
                "  Dimensiones: "
                f"{min(widths)}x{min(heights)} a "
                f"{max(widths)}x{max(heights)}"
            )

    duplicate_groups = [
        paths for paths in image_hashes.values() if len(paths) > 1
    ]

    if duplicate_groups:
        print("\nDuplicados exactos encontrados:")

        for duplicate_paths in duplicate_groups:
            error_count += 1
            for duplicate_path in duplicate_paths:
                print(f"  [ERROR] {duplicate_path.relative_to(PROJECT_ROOT)}")
    else:
        print("\nNo se encontraron duplicados exactos.")

    if error_count:
        print(f"\nAuditoría finalizada con {error_count} problema(s).")
        return 1

    print("\nAuditoría finalizada correctamente.")
    return 0


def main() -> None:
    arguments = parse_arguments()
    class_ids = load_class_ids()

    exit_code = audit_session(
        session_id=arguments.session,
        expected_per_class=arguments.expected_per_class,
        class_ids=class_ids,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()