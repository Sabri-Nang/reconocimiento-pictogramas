import numpy as np
import pytest
from reconocimiento_pictogramas.feature_rejection import neighbor_similarity


def test_identical_orthogonal_and_opposite_vectors():
    result = neighbor_similarity([[1,0],[0,1],[-1,0]], [[2,0]], k=1)
    np.testing.assert_allclose(result, [1,.5,0])


def test_top_neighbors_and_scale_invariance():
    refs = [[1,0],[2,0],[-1,0]]
    assert neighbor_similarity([[3,0]], refs, k=2)[0] == pytest.approx(1)
    assert neighbor_similarity([[3,0]], refs, k=3)[0] == pytest.approx(2/3)


@pytest.mark.parametrize('queries,refs,k', [([[0,0]],[[1,0]],1), ([[np.nan,1]],[[1,0]],1), ([[1,0]],[[1,0]],2), ([[1,0,0]],[[1,0]],1)])
def test_invalid_features_fail(queries,refs,k):
    with pytest.raises(ValueError):
        neighbor_similarity(queries,refs,k)
