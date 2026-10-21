"""Calibración de rechazo por puntuaciones, independiente de TensorFlow."""
import math
import numpy as np


def scores(values):
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or not len(result):
        raise ValueError("Se requieren puntuaciones en un vector no vacío.")
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError("Las puntuaciones deben ser finitas entre cero y uno.")
    return result


def calibrate_threshold(unknown_scores, target=0.7):
    """Menor umbral [0,1] que alcanza la tasa pedida con rechazo <= umbral.

    Solo recibe desconocidos internos. No acepta resultados de la sesión externa.
    El menor umbral también minimiza el rechazo de conocidos para este criterio.
    """
    if not math.isfinite(target) or not 0 < target <= 1:
        raise ValueError("El objetivo debe estar entre cero (excluido) y uno.")
    values = np.sort(scores(unknown_scores))
    required = math.ceil(target * len(values))
    return float(values[required - 1])


def evaluate_rejection(known_scores, known_correct, unknown_scores, threshold):
    known = scores(known_scores)
    unknown = scores(unknown_scores)
    correct = np.asarray(known_correct)
    if correct.shape != known.shape or not np.isin(correct, [0, 1]).all():
        raise ValueError("Indicadores de acierto incompatibles.")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Umbral inválido.")
    accepted = known > threshold
    rejected_unknown = int((unknown <= threshold).sum())
    accepted_count = int(accepted.sum())
    correct_accepted = int((accepted & correct.astype(bool)).sum())
    return dict(known_images=len(known), unknown_images=len(unknown),
        known_correct_without_rejection=int(correct.sum()),
        known_accuracy_without_rejection=float(correct.mean()),
        known_rejected=int((~accepted).sum()), known_rejection_rate=float((~accepted).mean()),
        known_accepted=accepted_count, known_coverage=float(accepted.mean()),
        known_correct_accepted=correct_accepted,
        known_accuracy_with_rejection=correct_accepted / len(known),
        accuracy_among_accepted_known=correct_accepted / accepted_count if accepted_count else None,
        known_wrong_accepted=int((accepted & ~correct.astype(bool)).sum()),
        unknown_rejected=rejected_unknown, unknown_rejection_rate=rejected_unknown / len(unknown),
        unknown_false_accepted=len(unknown)-rejected_unknown,
        unknown_false_acceptance_rate=1-rejected_unknown / len(unknown))


def calibrate_known_cap(known_scores, rejection_cap=0.05):
    """Mayor umbral [0,1] con rechazo <=cap en conocidos internos.

    Al rechazar score<=umbral, se usa el flotante anterior al primer conocido
    que no se puede rechazar. Respeta empates sin interpolar cuantiles.
    Por monotonía maximiza el rechazo de unknown bajo esta restricción.
    """
    if not math.isfinite(rejection_cap) or not 0 <= rejection_cap <= 1:
        raise ValueError("Límite de rechazo inválido.")
    values = np.sort(scores(known_scores))
    allowed = math.floor(rejection_cap * len(values))
    if allowed == len(values):
        return 1.0
    threshold = float(np.nextafter(values[allowed], -np.inf))
    if threshold < 0:
        raise ValueError("No existe umbral [0,1] que respete el límite con score cero.")
    return threshold


def calibrate_target_with_known_cap(unknown_scores, known_scores, target=.75, rejection_cap=.01):
    """Mínimo umbral que cumple el objetivo unknown y el límite known internos.

    Si el mínimo ya rechaza demasiadas conocidas, ningún umbral mayor resuelve
    ambas restricciones. Devuelve threshold=None: no activar una regla inviable.
    No recibe puntuaciones externas ni usa etiquetas de acierto para excluir conocidas.
    """
    if not math.isfinite(rejection_cap) or not 0 <= rejection_cap <= 1:
        raise ValueError("Límite de rechazo inválido.")
    unknown=scores(unknown_scores);known=scores(known_scores)
    candidate=calibrate_threshold(unknown,target)
    allowed=math.floor(rejection_cap*len(known))
    rejected=int((known<=candidate).sum())
    feasible=rejected<=allowed
    return dict(feasible=feasible,threshold=candidate if feasible else None,
        candidate_threshold=candidate,target_unknown_rejection=target,
        known_rejection_cap=rejection_cap,allowed_known_rejected=allowed,
        candidate_known_rejected=rejected,candidate_unknown_rejected=int((unknown<=candidate).sum()))
