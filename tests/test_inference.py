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
