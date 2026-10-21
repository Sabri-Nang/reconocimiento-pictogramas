"""Comprueba la preferencia trasera y preservación de las etiquetas españolas."""
from reconocimiento_pictogramas import ui


def test_rear_camera_preference_and_no_mirror():
    options = ui.rear_camera_options()
    webcam = options["webcam_options"]
    assert webcam.constraints == {"video": {"facingMode": {"ideal": "environment"}}}
    assert webcam.mirror is False
    camera = next(c for c in ui.build_app().config["components"] if c["type"] == "image" and c["props"].get("sources") == ["webcam"])
    assert camera["props"]["webcam_options"]["constraints"]["video"]["facingMode"] == {"ideal": "environment"}


def test_gradio_five_compatibility(monkeypatch):
    monkeypatch.setattr(ui, "GRADIO_MAJOR", 5)
    assert ui.rear_camera_options() == {"mirror_webcam": False, "webcam_constraints": {"video": {"facingMode": {"ideal": "environment"}}}}


def test_spanish_labels_are_protected_from_automatic_translation():
    assert ui.NAMES["comer"] == "Comer"
    assert "Contendiente" not in ui.NAMES.values()
    assert 'content="notranslate"' in ui.APP_HEAD
    assert 'document.documentElement.lang = "es"' in ui.SPANISH_UI_JS
    assert 'setAttribute("translate", "no")' in ui.SPANISH_UI_JS


def test_video_constraints_reach_the_serialized_frontend_config():
    app = ui.build_app()
    camera = next(c for c in app.config["components"] if c["type"] == "image" and c["props"].get("sources") == ["webcam"])
    media_constraints = camera["props"]["webcam_options"]["constraints"]
    # El frontend consume media_constraints.video: la propiedad no puede ir
    # directamente en la raíz porque entonces Gradio usa su cámara por defecto.
    assert "facingMode" not in media_constraints
    assert media_constraints["video"]["facingMode"]["ideal"] == "environment"
