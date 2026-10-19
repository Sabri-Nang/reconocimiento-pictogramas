"""Preprocesamiento compartido para dataset, interfaz e inferencia."""
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

def prepare_image(path: str | Path, size: tuple[int, int] = (128, 128)) -> Image.Image:
    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("Solo se admiten imágenes JPEG y PNG.")
            image.load()
            return prepare_pil_image(image, size)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ValueError(f"No se pudo leer la imagen: {path}") from error


def prepare_pil_image(image: Image.Image, size: tuple[int, int] = (128, 128)) -> Image.Image:
    """Mismo procesamiento para fotogramas en memoria; no escribe archivos."""
    if not isinstance(image, Image.Image) or image.width < 1 or image.height < 1:
        raise ValueError("Fotograma inválido.")
    return ImageOps.exif_transpose(image).convert("RGB").resize(size, Image.Resampling.LANCZOS)
