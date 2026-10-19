import numpy as np
import pytest
from PIL import Image,ImageDraw
from reconocimiento_pictogramas import live


def card_image():
    image=Image.new('RGB',(640,480),'#303030')
    draw=ImageDraw.Draw(image);draw.rectangle((210,100,430,320),fill='white',outline='black',width=4)
    return image


def test_blank_has_no_card_and_square_is_found():
    assert live.detect_card(Image.new('RGB',(640,480),'gray')) is None
    card=live.detect_card(card_image())
    assert card is not None
    assert 190<=card['box'][0]<=230 and 300<=card['box'][3]<=340


def test_stability_needs_three_frames_and_resets_on_switch_movement_or_gap():
    state={};box=[10,10,100,100]
    for now,expected in [(0,False),(.5,False),(1,True)]:
        state,stable=live.advance_state(state,'agua',box,now)
        assert stable is expected
    _,stable=live.advance_state(state,'comer',box,1.5);assert not stable
    _,stable=live.advance_state(state,'agua',[200,200,300,300],1.5);assert not stable
    _,stable=live.advance_state(state,'agua',box,21);assert not stable


def test_live_classifies_whole_frame_then_removes_stale_label(monkeypatch):
    image=card_image();names={'agua':'Agua'};state={}
    def classify(frame):
        assert frame.size==(640,480)  # No recortar el input del clasificador.
        return dict(label='agua',rejected=False)
    monkeypatch.setattr(live,'classify_frame',classify)
    for i in range(3):
        annotated,word,status,state=live.process_live_frame(image,state,names)
        assert word==('Agua' if i==2 else '—')
    annotated,word,status,state=live.process_live_frame(Image.new('RGB',(640,480),'gray'),state,names)
    assert word=='—' and state=={}
    monkeypatch.setattr(live,'classify_frame',lambda frame:dict(label='desconocido',rejected=True))
    annotated,word,status,state=live.process_live_frame(image,{'label':'agua','count':3},names)
    assert word=='—' and state=={} and 'no reconocido' in status


def test_frame_and_error_reset(monkeypatch):
    assert live.process_live_frame(None,{'label':'agua'},{} )[-1]=={}
    def fail(frame):raise ValueError('Modelo ausente')
    monkeypatch.setattr(live,'classify_frame',fail)
    result=live.process_live_frame(card_image(),{'label':'agua'},{} )
    assert result[1]=='—' and result[-1]=={} and result[2]=='Modelo ausente'


def test_slow_mobile_frames_can_confirm_without_lowering_rejection():
    state={};box=[10,10,100,100]
    for now,expected in [(0,False),(4,False),(8,True)]:
        state,stable=live.advance_state(state,'agua',box,now)
        assert stable is expected
    assert state['count']==3


def test_progress_is_visible_and_new_sessions_start_separately(monkeypatch):
    monkeypatch.setattr(live,'classify_frame',lambda frame:dict(label='agua',rejected=False))
    first=live.process_live_frame(card_image(),{}, {'agua':'Agua'})
    assert '1/3' in first[2]
    second=live.process_live_frame(card_image(),first[3], {'agua':'Agua'})
    assert '2/3' in second[2]
    isolated=live.process_live_frame(card_image(),{}, {'agua':'Agua'})
    assert '1/3' in isolated[2]


def test_direct_camera_rpc_keeps_state_and_clears_it(monkeypatch):
    import base64,io
    buffer=io.BytesIO();card_image().save(buffer,format='JPEG')
    frame='data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')
    monkeypatch.setattr(live,'classify_frame',lambda image:dict(label='agua',rejected=False))
    monkeypatch.setattr(live,'camera_names',lambda:{'agua':'Agua'})
    state={}
    for index in range(3):
        result=live.analyze_camera({'frame':frame,'state':state});state=result['state']
        assert result['word']==('Agua' if index==2 else '—')
    assert result['card'] and result['width']==640
    assert live.analyze_camera(None)['state']=={}


@pytest.mark.parametrize('payload',[{}, {'frame':'not-an-image'}, {'frame':'data:image/jpeg;base64,garbage'}])
def test_camera_rpc_rejects_bad_frames(payload):
    with pytest.raises(ValueError):live.analyze_camera(payload)
