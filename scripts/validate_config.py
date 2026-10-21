"""Valida las configuraciones vigentes sin acceder a modelos ni datos pesados."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reconocimiento_pictogramas.config_validation import validate_files


if __name__ == "__main__":
    validate_files(ROOT)
    print("Configuración válida: dataset y aplicación son compatibles.")
