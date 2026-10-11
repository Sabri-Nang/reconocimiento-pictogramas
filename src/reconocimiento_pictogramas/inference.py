"""Inferencia local con el modelo seleccionado y preprocesamiento común."""
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from .preprocessing import prepare_image
ROOT=Path(__file__).resolve().parents[2]

@lru_cache(maxsize=1)
def load_selected_model():
    import tensorflow as tf
    config=json.loads((ROOT/'config/selected_model.json').read_text(encoding='utf-8'))
    project=json.loads((ROOT/'config/project.json').read_text(encoding='utf-8'))
    if config['classes'] != [c['id'] for c in project['classes']]:
        raise ValueError('Las clases del modelo no coinciden con el proyecto.')
    model=tf.keras.models.load_model(ROOT/config['model_path'])
    if model.output_shape[-1] != len(config['classes']):
        raise ValueError('Cantidad de salidas incompatible.')
    return model,config

def classify_image(path):
    model,config=load_selected_model()
    image=prepare_image(path,tuple(config['image_size']))
    probabilities=np.asarray(model(np.asarray(image,dtype=np.uint8)[None],training=False))[0]
    if not np.isfinite(probabilities).all():
        raise ValueError('El modelo produjo una salida inválida.')
    index=int(np.argmax(probabilities));confidence=float(probabilities[index])
    threshold=config.get('confidence_threshold')
    rejected=threshold is not None and confidence <= threshold
    return dict(image=image,label='desconocido' if rejected else config['classes'][index],confidence=confidence,threshold_calibrated=threshold is not None,rejected=rejected)
