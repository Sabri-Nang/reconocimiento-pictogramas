"""Validación formal de configuraciones del proyecto y del modelo activo."""
from __future__ import annotations

from pathlib import Path

from .artifacts import read_json


def validate_project_config(config: dict) -> None:
    classes = config.get("classes")
    if not isinstance(classes, list) or len(classes) != 10:
        raise ValueError("project.json debe declarar exactamente diez clases.")
    ids = [item.get("id") for item in classes]
    if any(not isinstance(value, str) or not value.isascii() or not value.islower() for value in ids) or len(set(ids)) != 10:
        raise ValueError("Los IDs de clase deben ser ASCII, minúsculos y únicos.")
    image = config.get("image", {})
    if image.get("channels") != 3 or image.get("color_mode") != "rgb":
        raise ValueError("La configuración de imágenes debe ser RGB de tres canales.")
    split = config.get("split", {})
    if abs(sum(split.get(name, 0) for name in ("train", "validation", "test")) - 1) > 1e-9:
        raise ValueError("Las proporciones de split deben sumar uno.")


def validate_application_config(config: dict, project: dict) -> None:
    validate_project_config(project)
    classes = config.get("classes")
    expected = [item["id"] for item in project["classes"]]
    if classes != expected:
        raise ValueError("El modelo activo no coincide con el orden de clases del proyecto.")
    size = config.get("image_size")
    if not isinstance(size, list) or len(size) != 2 or any(type(value) is not int or value < 32 for value in size):
        raise ValueError("La configuración activa requiere image_size con dos enteros válidos.")
    if config.get("confidence_threshold") is not None:
        raise ValueError("El modelo activo debe usar detector explícito o confidence_threshold nulo.")
    detector = config.get("rejection_detector")
    if not isinstance(detector, dict) or detector.get("method") != "knn_cosine" or not detector.get("calibrated"):
        raise ValueError("El modelo activo requiere un detector kNN calibrado.")


def validate_files(root: str | Path) -> None:
    root = Path(root)
    project = read_json(root / "config/project.json")
    application = read_json(root / "config/application.json")
    validate_application_config(application, project)
