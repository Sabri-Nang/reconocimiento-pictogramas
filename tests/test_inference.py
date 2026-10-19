import numpy as np
from PIL import Image
import pytest
from reconocimiento_pictogramas import inference

@pytest.mark.parametrize("threshold, expected", [(None,False),(0.7,False),(0.8,True),(0.9,True)])
def test_rejection_threshold_and_raw_input(tmp_path,monkeypatch,threshold,expected):
    path=tmp_path/'input.png'
    Image.new('RGB',(20,20),(255,0,0)).save(path)
    def model(x,training=False):
        assert x.shape==(1,128,128,3)
        assert x.dtype==np.uint8 and x.max()==255
        assert training is False
        return np.array([[0.8,0.2]],dtype=np.float64)
    config={'classes':['agua','comer'],'image_size':[128,128],'confidence_threshold':threshold}
    monkeypatch.setattr(inference,'load_selected_model',lambda:(model,config))
    result=inference.classify_image(path)
    assert result['rejected'] is expected
    assert result['label']==('desconocido' if expected else 'agua')
    assert result['threshold_calibrated'] is (threshold is not None)


@pytest.mark.parametrize("features,threshold,rejected", [([0.,1.],.8,True),([1.,0.],.8,False),([0.,1.],.5,True)])
def test_feature_rejection_is_independent_of_high_class_confidence(tmp_path,monkeypatch,features,threshold,rejected):
    path=tmp_path/'input.png'
    Image.new('RGB',(20,20),'red').save(path)
    config={'classes':['agua','comer'],'image_size':[128,128],
        'rejection_detector':{'method':'knn_cosine','neighbors':1,'threshold':threshold,'calibrated':True}}
    monkeypatch.setattr(inference,'load_selected_model',lambda:(None,config))
    def joint(x,training=False):
        assert x.dtype==np.uint8 and training is False
        return np.array([[.99,.01]]),np.array([features])
    monkeypatch.setattr(inference,'load_selected_detector',lambda:(joint,np.array([[1.,0.]])))
    result=inference.classify_image(path)
    assert result['confidence']==pytest.approx(.99)
    assert result['rejected'] is rejected
    assert result['label']==('desconocido' if rejected else 'agua')
    assert result['rejection_method']=='knn_cosine'


def test_changed_detector_references_are_rejected(tmp_path,monkeypatch):
    archive=tmp_path/'references.npz';archive.write_bytes(b'changed')
    cfg={'rejection_detector':{'method':'knn_cosine','calibrated':True,'references_path':str(archive),'references_sha256':'wrong'}}
    monkeypatch.setattr(inference,'ROOT',tmp_path)
    monkeypatch.setattr(inference,'load_selected_model',lambda:(None,cfg))
    inference.load_selected_detector.cache_clear()
    with pytest.raises(ValueError,match='referencias'):
        inference.load_selected_detector()
    inference.load_selected_detector.cache_clear()


@pytest.mark.parametrize('output', [[[.9,.9]],[[float('nan'),.1]],[[.8,.1,.1]]])
def test_invalid_model_output_fails(output):
    with pytest.raises(ValueError):
        inference.validate_probabilities(output,2)
