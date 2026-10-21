"""Comprobaciones del flujo de foto y de la presentación accesible."""
from PIL import Image
from reconocimiento_pictogramas import ui
from reconocimiento_pictogramas.accessible_theme import accessible_theme


def test_recognition_keeps_real_class_and_rejection_score(monkeypatch):
    monkeypatch.setattr(ui, "classify_image", lambda _: {
        "image": Image.new("RGB", (192, 192)), "label": "agua",
        "rejected": False, "confidence": 0.91, "threshold_calibrated": True,
        "rejection_method": "knn_cosine", "rejection_score": 0.88,
        "rejection_threshold": 0.8024,
    })
    preview, status, category, confidence, similarity = ui.recognize_image("foto.png")
    assert preview.size == (192, 192)
    assert category == "Agua" and confidence == "91.0%"
    assert "0.8800" in similarity and "0.8024" in similarity
    assert "Agua" in ui.result_announcement(status, category)


def test_error_discards_previous_result_and_escapes_announcement(monkeypatch):
    def fail(_):
        raise ValueError("No se pudo leer la imagen.")
    monkeypatch.setattr(ui, "classify_image", fail)
    assert ui.recognize_image("foto.png") == (None, "No se pudo leer la imagen.", "—", "—", "—")
    assert "<script>" not in ui.result_announcement("<script>", "—")


def test_accessible_app_builds():
    app = ui.build_app()
    assert app.config["title"].startswith("Pictovoz")
    accessible_theme()
