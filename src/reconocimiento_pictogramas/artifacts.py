"""Utilidades compartidas para leer y conservar artefactos experimentales."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: str | Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def contained(relative: str | Path) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Ruta fuera del repositorio")
    return path


def save_figure(fig, path: str | Path, dpi: int) -> None:
    """Reemplaza una figura de forma atómica y tolera bloqueos transitorios."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi)
    for attempt in range(5):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".png", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(buffer.getvalue())
            os.replace(temporary, path)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.25 * (attempt + 1))
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
