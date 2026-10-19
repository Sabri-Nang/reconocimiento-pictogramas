import importlib.util
from pathlib import Path
import errno


def test_plot_replacement_retries_and_preserves_previous_until_success(tmp_path,monkeypatch):
    source=Path(__file__).resolve().parents[1]/"scripts/train_cross_validation.py"
    spec=importlib.util.spec_from_file_location("training_artifacts",source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    target=tmp_path/"curve.png";target.write_bytes(b"old")
    actual=module.os.replace;calls=[]
    def replace(src,dst):
        calls.append(1)
        if len(calls)==1:
            assert target.read_bytes()==b"old"
            raise OSError(errno.EINVAL,"temporary access failure")
        actual(src,dst)
    monkeypatch.setattr(module.os,"replace",replace)
    monkeypatch.setattr(module.time,"sleep",lambda _:None)
    class Figure:
        def savefig(self,buffer,**kwargs):buffer.write(b"new PNG")
    module.save_figure(Figure(),target,140)
    assert len(calls)==2 and target.read_bytes()==b"new PNG"
    assert list(tmp_path.iterdir())==[target]


def test_experimental_resolution_keeps_app_configuration_unchanged():
    import pytest
    source=Path(__file__).resolve().parents[1]/"scripts/train_cross_validation.py"
    spec=importlib.util.spec_from_file_location("training_resolution",source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original={"image":{"width":128,"height":128,"channels":3}}
    adjusted=module.experiment_project(original,{"image_size":[192,192]})
    assert adjusted["image"]==dict(width=192,height=192,channels=3)
    assert original["image"]["width"]==128
    assert module.experiment_project(original,{})==original
    for invalid in ([192], [192,"192"], [0,192], [True,192]):
        with pytest.raises(ValueError):module.experiment_project(original,{"image_size":invalid})
