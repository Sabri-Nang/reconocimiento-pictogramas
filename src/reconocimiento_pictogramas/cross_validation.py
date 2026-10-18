"""Protocolo por sesiones: cuatro train, una stop, una evaluación externa."""
from collections import Counter

SESSIONS = tuple(f"s{i:03d}" for i in range(1, 7))

def make_folds(sessions=SESSIONS):
    if len(sessions) != 6 or len(set(sessions)) != 6 or "s007" in sessions:
        raise ValueError("Se requieren seis sesiones únicas de desarrollo; s007 está reservada.")
    folds=[]
    for i, outer in enumerate(sessions):
        stop=sessions[(i+1)%6]
        folds.append(dict(fold=i+1, train=[s for s in sessions if s not in {outer,stop}], stop=[stop], outer=[outer]))
    return folds

def validate_records(rows, classes, expected_per_class_session=30):
    if len(classes)!=10 or len(set(classes))!=10:
        raise ValueError("El protocolo requiere diez clases únicas.")
    for field in ["raw_path","processed_path","sha256"]:
        values=[r[field] for r in rows]
        if len(values)!=len(set(values)):
            raise ValueError(f"Registros duplicados en {field}")
    counts=Counter()
    for row in rows:
        if row['session_id'] not in SESSIONS:
            raise ValueError("Sesión fuera de desarrollo; s007 no está permitida.")
        index=int(row['class_index'])
        if index<0 or index>=len(classes) or classes[index]!=row['class_id']:
            raise ValueError("Etiqueta e índice inconsistentes.")
        counts[(row['session_id'],row['class_id'])]+=1
    for session in SESSIONS:
        for cls in classes:
            if counts[(session,cls)]!=expected_per_class_session:
                raise ValueError(f"Cantidad incorrecta: {session}/{cls}")
    return True
