"""Inferencia local con modelo y detector compatibles, cacheados por proceso."""
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path
import numpy as np
from .preprocessing import prepare_image
from .feature_rejection import neighbor_similarity, normalize_features
ROOT=Path(__file__).resolve().parents[2]


def artifact_path(relative):
    if not isinstance(relative,str) or not relative:
        raise ValueError('No hay un modelo o archivo de referencia seleccionado.')
    path=(ROOT/relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('No se encontró el modelo o detector seleccionado dentro del proyecto.')
    return path


def validate_probabilities(probabilities, count):
    values=np.asarray(probabilities,dtype=float)
    if values.shape!=(1,count) or not np.isfinite(values).all():
        raise ValueError('El modelo produjo una salida inválida.')
    if (values<0).any() or (values>1).any() or not np.allclose(values.sum(axis=1),1,atol=1e-5):
        raise ValueError('El modelo produjo probabilidades inválidas.')
    return values[0]


@lru_cache(maxsize=1)
def load_selected_model():
    config=json.loads((ROOT/'config/selected_model.json').read_text(encoding='utf-8'))
    project=json.loads((ROOT/'config/project.json').read_text(encoding='utf-8'))
    if config['classes'] != [c['id'] for c in project['classes']]:
        raise ValueError('Las clases del modelo no coinciden con el proyecto.')
    path=artifact_path(config.get('model_path'))
    if config.get('model_sha256') and hashlib.sha256(path.read_bytes()).hexdigest()!=config['model_sha256']:
        raise ValueError('El checkpoint cambió después de calibrar el detector.')
    import tensorflow as tf
    model=tf.keras.models.load_model(path,compile=False)
    if model.output_shape[-1]!=len(config['classes']):
        raise ValueError('Cantidad de salidas incompatible.')
    if list(model.input_shape[1:])!=[config['image_size'][1],config['image_size'][0],3]:
        raise ValueError('Tamaño de entrada incompatible.')
    return model,config


@lru_cache(maxsize=1)
def load_selected_detector():
    model,config=load_selected_model()
    detector=config['rejection_detector']
    if detector.get('method')!='knn_cosine' or not detector.get('calibrated'):
        raise ValueError('Detector de rechazo desconocido o sin calibración.')
    path=artifact_path(detector.get('references_path'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=detector.get('references_sha256'):
        raise ValueError('Las referencias del detector no coinciden con la calibración.')
    if detector.get('model_sha256')!=config.get('model_sha256'):
        raise ValueError('El detector corresponde a otro modelo.')
    threshold=detector.get('threshold')
    if not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or not 0<=threshold<=1:
        raise ValueError('Umbral de similitud inválido.')
    with np.load(path,allow_pickle=False) as data:
        references=np.asarray(data['features'])
        if list(data['classes'])!=config['classes']:
            raise ValueError('Orden de clases incompatible con el detector.')
    normalize_features(references)
    k=detector.get('neighbors')
    if not isinstance(k,int) or not 1<=k<=len(references):
        raise ValueError('Cantidad de vecinos inválida.')
    import tensorflow as tf
    joint=tf.keras.Model(model.input,[model.output,model.layers[-1].input])
    if references.shape[1]!=int(joint.output_shape[1][-1]):
        raise ValueError('Dimensión de referencias incompatible con el modelo.')
    return joint,references


def classify_image(path):
    model,config=load_selected_model()
    image=prepare_image(path,tuple(config['image_size']))
    return classify_prepared_image(image)


def classify_frame(frame):
    from .preprocessing import prepare_pil_image
    _,config=load_selected_model()
    return classify_prepared_image(prepare_pil_image(frame,tuple(config['image_size'])))


def classify_prepared_image(image):
    model,config=load_selected_model()
    inputs=np.asarray(image,dtype=np.uint8)[None]
    detector=config.get('rejection_detector')
    if detector:
        joint,references=load_selected_detector()
        output,features=joint(inputs,training=False)
        probabilities=validate_probabilities(output,len(config['classes']))
        score=float(neighbor_similarity(np.asarray(features),references,k=detector['neighbors'])[0])
        threshold=detector['threshold']
        method='knn_cosine'
    else:
        probabilities=validate_probabilities(model(inputs,training=False),len(config['classes']))
        score=float(probabilities.max())
        threshold=config.get('confidence_threshold')
        if threshold is not None and (not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or not 0<=threshold<=1):
            raise ValueError('Umbral de confianza inválido.')
        method='softmax'
    index=int(probabilities.argmax());confidence=float(probabilities[index])
    rejected=threshold is not None and score<=threshold
    return dict(image=image,label='desconocido' if rejected else config['classes'][index],confidence=confidence,
        threshold_calibrated=threshold is not None,rejected=rejected,rejection_method=method,
        rejection_score=score,rejection_threshold=threshold)
