import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

from reconocimiento_pictogramas.preprocessing import prepare_image

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "prepare_dataset", ROOT / "scripts/prepare_dataset.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_exif_orientation_and_rgb(tmp_path):
    image = Image.new("RGB", (20, 10), "red")
    for x in range(10, 20):
        for y in range(10):
            image.putpixel((x, y), (0, 0, 255))
    exif = image.getexif()
    exif[274] = 6
    path = tmp_path / "oriented.jpg"
    image.save(path, exif=exif)
    result = prepare_image(path, (10, 20))
    assert result.mode == "RGB" and result.size == (10, 20)
    assert result.getpixel((5, 2))[0] > 200
    assert result.getpixel((5, 17))[2] > 200


def test_invalid_image_is_rejected(tmp_path):
    path = tmp_path / "bad.jpg"
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        prepare_image(path)


def test_overlapping_sessions_rejected_before_reading_data(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/project.json").write_text(
        json.dumps({"classes": [{"id": "agua"}]})
    )
    (tmp_path / "config/dataset_partitions.json").write_text(
        json.dumps({"sessions": {"train": ["s001"], "validation": ["s001"]}})
    )
    with pytest.raises(ValueError, match="más de una partición"):
        module.collect_records(tmp_path)


def test_known_preparation_accepts_unknown_metadata(tmp_path):
    import csv

    (tmp_path / "config").mkdir()
    (tmp_path / "data/raw/known/agua").mkdir(parents=True)
    (tmp_path / "config/project.json").write_text(
        json.dumps({"classes": [{"id": "agua"}]})
    )
    (tmp_path / "config/dataset_partitions.json").write_text(
        json.dumps(
            {
                "sessions": {"train": ["s001"], "validation": [], "test": ["s007"]},
                "expected_per_class_session": 1,
            }
        )
    )
    Image.new("RGB", (5, 5), "red").save(
        tmp_path / "data/raw/known/agua/agua_s001_0001.png"
    )
    with (tmp_path / "data/metadata.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["filename", "class_id", "session_id"]
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "filename": "agua_s001_0001.png",
                    "class_id": "agua",
                    "session_id": "s001",
                },
                {
                    "filename": "unknown_s001_0001.png",
                    "class_id": "unknown",
                    "session_id": "s001",
                },
            ]
        )
    _config, records, pending = module.collect_records(tmp_path)
    assert len(records["train"]) == 1 and records["test"] == [] and pending == ["s007"]
    # Las conocidas faltantes siguen siendo un error; no ignorar toda la metadata sobrante.
    (tmp_path / "data/raw/known/agua/agua_s001_0001.png").unlink()
    with pytest.raises(ValueError, match="metadata sin imagen"):
        module.collect_records(tmp_path)


def test_supplementary_session_is_validated_but_not_in_base_manifests(tmp_path):
    import csv

    (tmp_path / "config").mkdir()
    (tmp_path / "data/raw/known/agua").mkdir(parents=True)
    (tmp_path / "config/project.json").write_text(
        json.dumps({"classes": [{"id": "agua"}]}), encoding="utf-8"
    )
    partitions = {
        "sessions": {"train": ["s001"], "validation": [], "test": []},
        "supplementary_sessions": ["s008"],
        "expected_per_class_session": 1,
    }
    (tmp_path / "config/dataset_partitions.json").write_text(
        json.dumps(partitions), encoding="utf-8"
    )
    rows = []
    for session, color in (("s001", "red"), ("s008", "blue")):
        filename = f"agua_{session}_0001.png"
        Image.new("RGB", (5, 5), color).save(
            tmp_path / "data/raw/known/agua" / filename
        )
        rows.append({"filename": filename, "class_id": "agua", "session_id": session})
    with (tmp_path / "data/metadata.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["filename", "class_id", "session_id"]
        )
        writer.writeheader()
        writer.writerows(rows)

    _, records, pending = module.collect_records(tmp_path)

    assert [row["session_id"] for row in records["train"]] == ["s001"]
    assert pending == []
