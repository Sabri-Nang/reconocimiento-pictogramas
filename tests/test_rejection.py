import numpy as np
import pytest
from reconocimiento_pictogramas.rejection import calibrate_threshold, evaluate_rejection


def test_calibration_target_and_ties():
    unknown = [0.1, 0.2, 0.2, 0.9]
    threshold = calibrate_threshold(unknown, 0.7)
    assert threshold == 0.2
    assert sum(v <= threshold for v in unknown) == 3
    assert sum(v < threshold for v in unknown) < 3


def test_rejects_equality_and_keeps_denominators():
    result = evaluate_rejection([0.9, 0.7, 0.8], [1, 1, 0], [0.1, 0.7, 0.99], 0.7)
    assert result['known_rejected'] == 1
    assert result['known_accuracy_with_rejection'] == pytest.approx(1/3)
    assert result['accuracy_among_accepted_known'] == 0.5
    assert result['unknown_rejected'] == 2
    assert result['known_wrong_accepted'] == 1


def test_all_rejected_is_not_perfect_known_accuracy():
    result = evaluate_rejection([0.9], [1], [0.99], 1)
    assert result['known_accuracy_with_rejection'] == 0
    assert result['accuracy_among_accepted_known'] is None
    assert result['unknown_rejection_rate'] == 1


@pytest.mark.parametrize('values', [[], [np.nan], [np.inf], [-0.1], [1.1]])
def test_invalid_calibration_scores(values):
    with pytest.raises(ValueError):
        calibrate_threshold(values)


from reconocimiento_pictogramas.rejection import calibrate_known_cap


def test_known_cap_uses_all_knowns_and_strict_boundary():
    values = np.linspace(.1, 1, 300)
    threshold = calibrate_known_cap(values, .05)
    assert sum(values <= threshold) == 15
    assert threshold < values[15]
    assert sum(values <= values[15]) == 16


def test_known_cap_respects_ties():
    values = [.2, .2, .8, .9]
    threshold = calibrate_known_cap(values, .25)
    assert sum(v <= threshold for v in values) == 0
    assert threshold < .2


def test_known_cap_zero_and_one():
    assert calibrate_known_cap([.2, .7], 0) < .2
    assert calibrate_known_cap([.2, .7], 1) == 1
    with pytest.raises(ValueError):
        calibrate_known_cap([0, 0, .8], 0)


from reconocimiento_pictogramas.rejection import calibrate_target_with_known_cap


def test_target_and_cap_feasible_minimal_threshold():
    result=calibrate_target_with_known_cap([.1,.2,.3,.4],[.3]+[.9]*99,.75,.01)
    assert result['feasible'] and result['threshold']==.3
    assert result['candidate_unknown_rejected']==3
    assert result['candidate_known_rejected']==result['allowed_known_rejected']==1


def test_target_and_cap_infeasible_has_no_deployable_threshold():
    result=calibrate_target_with_known_cap([.1,.2,.3,.4],[.3,.3]+[.9]*98,.75,.01)
    assert not result['feasible'] and result['threshold'] is None
    assert result['candidate_known_rejected']==2


def test_target_and_cap_ties_cannot_bypass_known_limit():
    result=calibrate_target_with_known_cap([.2,.2,.2,.9],[.2,.2,.8,.9],.75,.25)
    assert not result['feasible'] and result['threshold'] is None


@pytest.mark.parametrize('cap',[-.1,1.1,float('nan')])
def test_target_and_cap_invalid_cap(cap):
    with pytest.raises(ValueError):calibrate_target_with_known_cap([.2],[.9],.75,cap)
