"""Similitud con vecinos de entrenamiento para rechazo de entradas ajenas."""
import numpy as np


def normalize_features(values):
    features = np.asarray(values, dtype=np.float64)
    if features.ndim != 2 or not features.shape[0] or not features.shape[1]:
        raise ValueError("Se requiere una matriz de características no vacía.")
    if not np.isfinite(features).all():
        raise ValueError("Características no finitas.")
    lengths = np.linalg.norm(features, axis=1, keepdims=True)
    if (lengths <= 1e-12).any():
        raise ValueError("Vector de características nulo.")
    return features / lengths


def neighbor_similarity(queries, references, k=5):
    """Promedio de los k cosenos mayores, escalado a [0,1]. No es probabilidad."""
    reference = normalize_features(references)
    query = normalize_features(queries)
    if query.shape[1] != reference.shape[1]:
        raise ValueError("Dimensiones incompatibles.")
    if not isinstance(k, int) or not 1 <= k <= len(reference):
        raise ValueError("Cantidad de vecinos inválida.")
    similarity = np.clip(query @ reference.T, -1, 1)
    nearest = np.partition(similarity, len(reference)-k, axis=1)[:, -k:]
    return np.clip((nearest.mean(axis=1)+1)/2, 0, 1)
