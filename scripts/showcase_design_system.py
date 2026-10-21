"""Ejecutar: uv run python scripts/showcase_design_system.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from reconocimiento_pictogramas.design_system import main
if __name__ == "__main__":
    main()
