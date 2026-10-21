"""Prueba el contrato de presentación y voz sin llamar a servicios externos."""
from pathlib import Path
import pytest
from PIL import Image
from reconocimiento_pictogramas import ui, speech


def result(rejected=False):
    return dict(
        label="desconocido" if rejected else "agua", rejected=rejected,
        confidence=0.99, probabilities={"agua":0.99, "comer":0.01},
        rejection_method="knn_cosine", rejection_score=0.7 if rejected else 0.9,
        rejection_threshold=0.8024037084471637,
    )


def test_prediction_returns_phrase_scores_and_audio(monkeypatch):
    monkeypatch.setattr(ui, "classify_frame", lambda image: result())
    spoken = []
    def speak(phrase):
        spoken.append(phrase)
        return "voz.mp3"
    monkeypatch.setattr(ui, "synthesize_phrase", speak)
    phrase, scores, audio = ui.predecir(Image.new("RGB", (20, 20)))
    assert phrase == "Quiero tomar agua"
    assert scores == {"Agua":0.99, "Comer":0.01}
    assert audio == "voz.mp3" and spoken == [phrase]


def test_rejection_preserves_calibrated_decision_despite_high_softmax(monkeypatch):
    monkeypatch.setattr(ui, "classify_frame", lambda image: result(True))
    monkeypatch.setattr(ui, "synthesize_phrase", lambda phrase: "rechazo.mp3")
    phrase, scores, audio = ui.predecir(Image.new("RGB", (20, 20)))
    assert phrase == "Tarjeta no reconocida. Intenta enfocarla nuevamente."
    assert scores["Agua"] == 0.99 and audio == "rechazo.mp3"


def test_acceptance_does_not_introduce_new_softmax_threshold(monkeypatch):
    prediction = result()
    prediction["probabilities"] = {"agua":0.6, "comer":0.4}
    monkeypatch.setattr(ui, "classify_frame", lambda image: prediction)
    monkeypatch.setattr(ui, "synthesize_phrase", lambda phrase: "voz.mp3")
    assert ui.predecir(Image.new("RGB", (20, 20)))[0] == "Quiero tomar agua"


def test_missing_and_invalid_input_clear_outputs(monkeypatch):
    assert ui.predecir(None)[1:] == ({}, None)
    def fail(image):
        raise ValueError("Fotograma inválido.")
    monkeypatch.setattr(ui, "classify_frame", fail)
    assert ui.predecir("no es una imagen")[1:] == ({}, None)


def test_tts_failure_keeps_visual_prediction(monkeypatch):
    monkeypatch.setattr(ui, "classify_frame", lambda image: result())
    def fail(phrase):
        raise speech.AudioGenerationError("sin conexión")
    monkeypatch.setattr(ui, "synthesize_phrase", fail)
    phrase, scores, audio, state = ui._identify(Image.new("RGB", (20, 20)))
    assert phrase == "Quiero tomar agua" and scores and audio is None
    assert "voz no está disponible" in state


def test_tts_caches_complete_audio_and_removes_partial_failures(tmp_path, monkeypatch):
    class Directory:
        name = str(tmp_path)
    monkeypatch.setattr(speech, "_AUDIO_DIRECTORY", Directory())
    calls = []
    class FakeTTS:
        def __init__(self, **kwargs):
            calls.append(kwargs)
        def save(self, path):
            Path(path).write_bytes(b"audio de prueba")
    monkeypatch.setattr(speech, "gTTS", FakeTTS)
    first = speech.synthesize_phrase("Sí")
    assert speech.synthesize_phrase("Sí") == first and len(calls) == 1
    class FailedTTS(FakeTTS):
        def save(self, path):
            Path(path).write_bytes(b"parcial")
            raise OSError("sin conexión")
    monkeypatch.setattr(speech, "gTTS", FailedTTS)
    with pytest.raises(speech.AudioGenerationError):
        speech.synthesize_phrase("No")
    assert list(tmp_path.iterdir()) == [Path(first)]


def test_phrases_cover_exactly_the_ten_configured_classes():
    assert set(ui.PHRASES) == set(ui.NAMES)


def test_pending_prediction_is_discarded_after_image_change(monkeypatch):
    session = {"revision": 0}
    def late_prediction(image):
        ui.reset_for_session(session)
        return "Resultado anterior", {"Agua": 1.0}, "viejo.mp3", "anterior"
    monkeypatch.setattr(ui, "_identify", late_prediction)
    assert ui.identify_current(None, session) == ({"__type__": "update"},) * 4


def test_clearing_invalidates_only_its_own_session():
    first, second = {"revision": 0}, {"revision": 0}
    cleared = ui.clear_session(first)
    assert first["revision"] == 1 and second["revision"] == 0
    assert cleared[:5] == (None, None, "", {}, None)
