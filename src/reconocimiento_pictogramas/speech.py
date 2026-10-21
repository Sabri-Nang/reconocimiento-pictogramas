"""Locuciones de frases fijas con gTTS, cacheadas durante la ejecución.

Se envía solo el texto a Google Translate TTS; las imágenes no se envían.
Los MP3 viven en un directorio temporal exclusivo de este proceso.
"""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from gtts import gTTS
from gtts.tts import gTTSError

_AUDIO_DIRECTORY = TemporaryDirectory(prefix="pictovoz-voz-")
_LOCK = Lock()


class AudioGenerationError(RuntimeError):
    """La locución no está disponible; la predicción visual sigue siendo válida."""


def synthesize_phrase(phrase: str) -> str:
    """Devuelve un MP3 completo; reutiliza el audio de la misma frase."""
    if not isinstance(phrase, str) or not phrase.strip():
        raise AudioGenerationError("No hay una frase para pronunciar.")
    path = Path(_AUDIO_DIRECTORY.name) / f"{sha256(phrase.encode('utf-8')).hexdigest()}.mp3"
    with _LOCK:
        if path.is_file() and path.stat().st_size:
            return str(path)
        try:
            # Tiempo de espera acotado: un fallo de red no deja la UI bloqueada.
            gTTS(text=phrase, lang="es", timeout=(3, 8)).save(str(path))
            if not path.is_file() or not path.stat().st_size:
                raise OSError("La síntesis no produjo audio.")
        except (gTTSError, OSError, ValueError) as error:
            path.unlink(missing_ok=True)  # Solo un MP3 temporal creado aquí.
            raise AudioGenerationError("No se pudo generar la locución.") from error
    return str(path)
