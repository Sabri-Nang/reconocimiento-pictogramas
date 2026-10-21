import json
from pathlib import Path

import pytest
from reconocimiento_pictogramas.artifacts import read_json
from reconocimiento_pictogramas.config_validation import validate_application_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "project.json"


@pytest.fixture
def project_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def test_config_file_exists() -> None:
    assert CONFIG_PATH.is_file()


def test_application_config_is_separate_from_dataset_config() -> None:
    application = PROJECT_ROOT / "config" / "application.json"
    assert application.is_file()


def test_application_config_is_compatible_with_project(project_config: dict) -> None:
    application = read_json(PROJECT_ROOT / "config" / "application.json")
    validate_application_config(application, project_config)


def test_project_has_expected_unique_classes(project_config: dict) -> None:
    class_ids = [item["id"] for item in project_config["classes"]]
    expected_count = project_config["acceptance"]["expected_class_count"]

    assert len(class_ids) == expected_count
    assert len(set(class_ids)) == expected_count


def test_class_ids_are_valid_folder_names(project_config: dict) -> None:
    class_ids = [item["id"] for item in project_config["classes"]]

    for class_id in class_ids:
        assert class_id.isascii()
        assert class_id.islower()
        assert class_id.replace("_", "").isalnum()


def test_image_configuration(project_config: dict) -> None:
    image = project_config["image"]

    assert image["width"] == 128
    assert image["height"] == 128
    assert image["channels"] == 3
    assert image["color_mode"] == "rgb"


def test_dataset_split_totals_one(project_config: dict) -> None:
    split = project_config["split"]
    total = split["train"] + split["validation"] + split["test"]

    assert total == pytest.approx(1.0)


def test_minimum_accuracy_is_valid(project_config: dict) -> None:
    minimum_accuracy = project_config["acceptance"]["minimum_test_accuracy"]

    assert 0.0 < minimum_accuracy <= 1.0
