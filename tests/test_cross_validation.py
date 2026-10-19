import pytest
from reconocimiento_pictogramas.cross_validation import make_folds, validate_records

def records():
    return [dict(raw_path=f'{s}/{c}/{i}.jpg',processed_path=f'{s}/{c}/{i}.png',sha256=f'{s}-{c}-{i}',session_id=f's{s:03d}',class_id=f'c{c}',class_index=str(c)) for s in range(1,7) for c in range(10) for i in range(30)]

def test_fold_roles_are_disjoint_and_rotate():
    folds=make_folds()
    assert len(folds)==6
    assert {f['outer'][0] for f in folds}=={f's{i:03d}' for i in range(1,7)}
    assert {f['stop'][0] for f in folds}=={f's{i:03d}' for i in range(1,7)}
    for f in folds:
        assert len(f['train'])==4
        assert not set(f['train'])&set(f['stop'])
        assert not set(f['train'])&set(f['outer'])
        assert not set(f['stop'])&set(f['outer'])
        assert 's007' not in f['train']+f['stop']+f['outer']

def test_complete_dataset_and_leaks():
    rows=records();classes=[f'c{i}' for i in range(10)]
    assert validate_records(rows,classes)
    rows[-1]['sha256']=rows[0]['sha256']
    with pytest.raises(ValueError,match='sha256'):validate_records(rows,classes)

def test_final_test_is_rejected():
    rows=records();rows[0]['session_id']='s007'
    with pytest.raises(ValueError,match='s007'):validate_records(rows,[f'c{i}' for i in range(10)])

def test_missing_class_images_rejected():
    with pytest.raises(ValueError,match='Cantidad'):validate_records(records()[:-1],[f'c{i}' for i in range(10)])


def test_seven_sessions_keep_final_test_out_and_rotate():
    sessions=[f's{i:03d}' for i in range(1,7)]+['s008']
    folds=make_folds(sessions)
    assert len(folds)==7
    assert {f['outer'][0] for f in folds}==set(sessions)
    for f in folds:
        assert len(f['train'])==5
        assert len(set(f['train']+f['stop']+f['outer']))==7
        assert 's007' not in f['train']+f['stop']+f['outer']
    rows=records()+[dict(raw_path=f'8/{c}/{i}.jpg',processed_path=f'8/{c}/{i}.png',sha256=f'8-{c}-{i}',session_id='s008',class_id=f'c{c}',class_index=str(c)) for c in range(10) for i in range(30)]
    assert validate_records(rows,[f'c{i}' for i in range(10)],sessions=sessions)
    with pytest.raises(ValueError,match='Cantidad'):
        validate_records(rows[:-1],[f'c{i}' for i in range(10)],sessions=sessions)
    with pytest.raises(ValueError,match='s007'):
        make_folds(sessions+['s007'])
