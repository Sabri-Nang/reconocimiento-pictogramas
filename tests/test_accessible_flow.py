"""Regresiones de voz voluntaria, formatos y peticiones obsoletas."""
import pytest
from PIL import Image
from reconocimiento_pictogramas import ui


def prediction():
    return dict(label="agua", rejected=False, probabilities={"agua": .9, "comer": .1})


def test_visual_flow_never_requests_external_voice(monkeypatch):
    monkeypatch.setattr(ui, "classify_frame", lambda _: prediction())
    def unexpected(_):
        pytest.fail("Identificar no debe enviar texto al servicio de voz")
    monkeypatch.setattr(ui, "synthesize_phrase", unexpected)
    session = {"revision": 0}
    request = ui.begin_identification(Image.new("RGB", (20, 20)), session)[-1]
    phrase, scores, audio, status = ui.identify_request(request, session)
    assert phrase == session["phrase"] == "Quiero tomar agua"
    assert scores and audio is None
    assert "Tarjeta identificada" in status


@pytest.mark.parametrize("cancel", ["before", "during"])
def test_old_prediction_cannot_return_after_reset(cancel, monkeypatch):
    session = {"revision": 0}
    request = ui.begin_identification(None, session)[-1]
    def infer(_, **kwargs):
        if cancel == "before":
            pytest.fail("Una petición obsoleta no debe ejecutar el modelo")
        ui.reset_for_session(session)
        return "Vieja", {"Agua": 1}, None, "anterior"
    monkeypatch.setattr(ui, "_identify", infer)
    if cancel == "before":
        ui.reset_for_session(session)
    assert ui.identify_request(request, session) == (ui.gr.skip(),) * 4
    assert session["phrase"] == ""


def test_voice_requires_current_identified_phrase(monkeypatch):
    session = {"revision": 1, "phrase": "Quiero tomar agua"}
    calls = []
    monkeypatch.setattr(ui, "synthesize_phrase", lambda text: calls.append(text) or "voz.mp3")
    request = ui.begin_voice(session)[-1]
    assert not calls
    assert ui.speak_request(request, session)[0] == "voz.mp3"
    assert calls == ["Quiero tomar agua"]
    ui.reset_for_session(session)
    assert ui.speak_request(request, session) == (ui.gr.skip(),) * 2
    assert ui.speak_request(ui.begin_voice(session)[-1], session)[0] is None
    assert len(calls) == 1


def test_voice_completed_after_clear_is_discarded(monkeypatch):
    session = {"revision": 0, "phrase": "Necesito ayuda"}
    def synthesize(_):
        ui.reset_for_session(session)
        return "vieja.mp3"
    monkeypatch.setattr(ui, "synthesize_phrase", synthesize)
    assert ui.speak_request(ui.begin_voice(session)[-1], session) == (ui.gr.skip(),) * 2


def test_voice_error_keeps_the_written_phrase(monkeypatch):
    session = {"revision": 1, "phrase": "Necesito ayuda"}
    def fail(_):
        raise ui.AudioGenerationError("sin conexión")
    monkeypatch.setattr(ui, "synthesize_phrase", fail)
    audio, state = ui.speak_request(ui.begin_voice(session)[-1], session)
    assert audio is None and "frase sigue escrita" in state
    assert session["phrase"] == "Necesito ayuda"


def test_upload_rejects_gif_before_inference(tmp_path, monkeypatch):
    path = tmp_path / "imagen.gif"
    Image.new("RGB", (20, 20)).save(path)
    def unexpected(_):
        pytest.fail("Un formato no admitido no debe ejecutar inferencia")
    monkeypatch.setattr(ui, "classify_frame", unexpected)
    session = {"revision": 0, "phrase": "anterior"}
    assert "JPEG o PNG válido" in ui.image_changed(str(path), session)[-1]
    assert session["phrase"] == ""
    assert ui._identify(str(path), with_audio=False)[1:3] == ({}, None)


def test_jpeg_upload_uses_shared_orientation_and_size(tmp_path, monkeypatch):
    path = tmp_path / "foto.jpg"
    Image.new("RGB", (30, 40)).save(path)
    def classify(image):
        assert image.mode == "RGB" and image.size == ui.selected_image_size()
        return prediction()
    monkeypatch.setattr(ui, "classify_frame", classify)
    assert ui._identify(str(path), with_audio=False)[0] == "Quiero tomar agua"


def test_technical_scores_are_collapsed_and_both_tabs_invalidate_results():
    config = ui.build_app().config
    components = config["components"]
    tabs = [c for c in components if c["type"] == "tabitem"]
    assert {c["props"]["label"] for c in tabs} == {"Subir foto", "Tomar foto"}
    selected = {target[0] for d in config["dependencies"] for target in d["targets"] if target[1] == "select"}
    assert {c["id"] for c in tabs} <= selected
    details = next(c for c in components if c["type"] == "accordion" and c["props"]["label"] == "Ayuda y detalles del reconocimiento")
    assert details["props"]["open"] is False
