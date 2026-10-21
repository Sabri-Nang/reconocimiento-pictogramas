"""El aviso de bienvenida refleja la configuración del modelo activo."""
import json
import pytest
from reconocimiento_pictogramas import ui


@pytest.mark.parametrize("evaluated,expected,absent", [
    (True, "ya se realizó", "pendiente"),
    (False, "sigue pendiente", "ya se realizó"),
])
def test_evaluation_notice_follows_selected_model(tmp_path, monkeypatch, evaluated, expected, absent):
    folder = tmp_path / "config"
    folder.mkdir()
    (folder / "application.json").write_text(json.dumps({"test_evaluated": evaluated}), encoding="utf-8")
    monkeypatch.setattr(ui, "ROOT", tmp_path)
    message = ui.model_evaluation_notice()
    assert expected in message and absent not in message
    assert "puede equivocarse" in message


def test_current_welcome_uses_completed_evaluation():
    selected = json.loads((ui.ROOT / "config/application.json").read_text(encoding="utf-8"))
    assert selected["test_evaluated"] is True
    app = ui.build_app()
    header = next(c["props"]["value"] for c in app.config["components"] if c["type"] == "html" and 'id="welcome-card"' in str(c["props"].get("value", "")))
    assert "La evaluación final del modelo ya se realizó" in header
    assert "sigue pendiente" not in header
