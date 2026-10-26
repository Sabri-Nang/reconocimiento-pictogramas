"""Verifica resultados completos y prepara una lectura de épocas y paradas."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);args=p.parse_args()
    from reconocimiento_pictogramas.training_artifacts import plot_history
    base=ROOT/'reports'/args.run_id
    protocol=read(base/'protocol.json');summary=read(base/'summary.json')
    extended='source_run' in protocol['config']
    classes=[c['id'] for c in protocol['project']['classes']]
    architectures=list(summary['results'])
    lines=['# Lectura de los entrenamientos de diez clases','',
        'Se completaron seis rondas por arquitectura. Cada ronda utiliza 1200 imágenes para aprender, 300 para seleccionar la época y 300 para evaluar al terminar. s007 y desconocidos no participaron.',
        '', 'Los resultados son de desarrollo: se usan para comparar procedimientos y no sustituyen la prueba final. La división interna es un holdout fijo rotativo, no una búsqueda exhaustiva anidada de parámetros.',
        '', '## Cómo leer los gráficos', '',
        'En epoch_curves.png: la pérdida interna decide la parada; la exactitud indica el porcentaje de aciertos; el tercer panel muestra aciertos y errores sobre las 300 imágenes internas. La línea discontinua marca la época guardada y la otra línea la última ejecutada. Una línea de puntos separa el ajuste fino en MobileNet.',
        '', 'Los aciertos de entrenamiento se acumulan con aumentos y pesos que cambian durante la época. No equivalen a evaluar después todas las imágenes con un único checkpoint.',
        '', 'Cada época realiza 38 ajustes (37 lotes de 32 y uno de 16). El paso indicado para la mejor época es su último paso de entrenamiento, antes de medir validación. No se seleccionó el modelo usando la sesión externa por época.',
        '', '## Resultados y decisiones por ronda','']
    manifest=rows(ROOT/'data/splits/development.csv');manifest_sha=hashlib.sha256((ROOT/'data/splits/development.csv').read_bytes()).hexdigest()
    assert manifest_sha==protocol['development_sha256']
    verified=[]
    for arch in architectures:
        stats=summary['results'][arch]
        lines += [f'### {arch.upper()}','',f"Exactitud externa promedio: {stats['mean_accuracy']:.2%}. Desviación entre rondas: {stats['std_across_sessions']*100:.2f} puntos porcentuales. Esta desviación no es un intervalo de confianza.",'']
        seen=set()
        for fold in protocol['folds']:
            folder=base/f"fold_{fold['fold']:02d}";dest=folder/arch
            history=rows(dest/'epochs.csv');result=read(dest/'result.json');stopping=read(dest/'stopping.json')
            best=min(history,key=lambda r:float(r['val_loss']))
            assert int(best['epoch'])==stopping['best_epoch']==result['best_epoch']
            n_epochs=max(int(r['epoch']) for r in history)
            assert n_epochs==stopping['stopped_epoch']==result['epochs_executed']
            for i,r in enumerate(history,0 if extended else 1):
                assert int(r['epoch'])==i and int(r['global_step'])==i*38
                assert int(r['val_correct'])+int(r['val_errors'])==300
                assert int(r['val_correct'])==round(float(r['val_accuracy'])*300)
            assert len(rows(dest/'steps.csv'))==n_epochs*38
            parts={role:rows(folder/f'{role}.csv') for role in ['train','stop','outer']}
            for role,count in [('train',1200),('stop',300),('outer',300)]:
                assert len(parts[role])==count
                assert {r['session_id'] for r in parts[role]}==set(fold[role])
            for field in ['raw_path','sha256','session_id']:
                sets=[{r[field] for r in parts[role]} for role in ['train','stop','outer']]
                assert not sets[0]&sets[1] and not sets[0]&sets[2] and not sets[1]&sets[2]
            predictions=rows(dest/'outer_predictions.csv');expected={r['raw_path']:r['class_id'] for r in parts['outer']}
            assert {r['raw_path'] for r in predictions}==set(expected)
            assert not seen&set(expected);seen.update(expected)
            correct=0
            for r in predictions:
                assert r['class_id']==expected[r['raw_path']]
                assert int(r['correct'])==int(r['class_id']==r['predicted_class'])
                probabilities=[float(r[f'prob_{cls}']) for cls in classes]
                assert all(math.isfinite(v) and 0<=v<=1 for v in probabilities)
                assert abs(sum(probabilities)-1)<1e-5
                assert classes[max(range(10),key=lambda i:probabilities[i])]==r['predicted_class']
                assert abs(max(probabilities)-float(r['confidence']))<1e-7
                correct+=int(r['correct'])
            assert correct==result['outer_correct'] and correct+result['outer_errors']==300
            assert abs(correct/300-result['outer_accuracy'])<1e-9
            assert sum(sum(r) for r in result['confusion_matrix'])==300
            assert sum(result['confusion_matrix'][i][i] for i in range(10))==correct
            stopping['best_epoch_last_step']=int(best['global_step']);stopping['stopped_training_step']=int(history[-1]['global_step'])
            (dest/'stopping.json').write_text(json.dumps(stopping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            plotrows=[{**r, **{k:float(r[k]) for k in ['loss','accuracy','val_loss','val_accuracy']}, **{k:int(r[k]) for k in ['epoch','val_correct','val_errors','global_step']}} for r in history]
            head=[r['epoch'] for r in plotrows if r['phase']=='clasificador_congelado']
            plot_history(plotrows,dest,f"{arch.upper()} · ronda {fold['fold']} · validación {fold['stop'][0]}",max(head) if head else None)
            for filename in ['epoch_curves.png','outer_confusion.png']:assert (dest/filename).stat().st_size>0
            checkpoint=ROOT/result['model_path'];assert checkpoint.is_file()
            verified.append(dict(architecture=arch,fold=fold['fold'],model_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),epochs=n_epochs,steps=n_epochs*38))
            reasons='; '.join(f"{s['phase']}: {s['stop_reason']}" for s in stopping['stages'])
            lines += [f"- Ronda {fold['fold']}: validación interna {fold['stop'][0]}, evaluación externa {fold['outer'][0]}. Época guardada **{best['epoch']}**, paso **{best['global_step']}**; ejecutadas **{n_epochs}** épocas ({n_epochs*38} pasos). Pérdida interna mínima {float(best['val_loss']):.4f}, {best['val_correct']} aciertos y {best['val_errors']} errores internos. Exactitud externa **{result['outer_accuracy']:.2%}** ({correct}/300). Motivo: {reasons}. [Gráfico](fold_{fold['fold']:02d}/{arch}/epoch_curves.png)."]
        assert len(seen)==1800
        lines+=['']
    if extended:
        lines += ['## Continuación desde checkpoints', '', 'La época 0 es la evaluación interna del checkpoint anterior, sin realizar ajustes. Las demás épocas y pasos son adicionales; no reinician los pesos ni Adam. El orden de lotes se vuelve a inicializar con la semilla de cada ronda. Si ninguna época adicional mejora la pérdida interna, se conserva el checkpoint de referencia. Se trata de un nuevo experimento de desarrollo, no de una ejecución nueva desde ImageNet.', '']
    lines+=['## Límites de esta comparación','', 'Las seis rondas comparten datos de entrenamiento. No se deben interpretar como seis experimentos estadísticamente independientes. Las semillas son 42 a 47, iguales para ambas arquitecturas en cada ronda. No se realizó búsqueda exhaustiva de hiperparámetros.', '', 'Alcanzar el máximo de épocas no demuestra convergencia. Los modelos por ronda no son automáticamente un modelo final entrenado con todas las imágenes. No se reemplazó el modelo seleccionado por Gradio. El siguiente paso es revisar el procedimiento elegido y definir su entrenamiento definitivo, la calibración del rechazo y la evaluación final reservada.', '', 'Los identificadores de las carpetas usan fecha y hora UTC.']
    (base/'lectura_resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (base/'verification.json').write_text(json.dumps(dict(status='passed',trainings=len(verified),models=verified,test_used=False),indent=2)+'\n',encoding='utf-8')
    print(f'Verificados {len(verified)} entrenamientos, {len(verified)*2} gráficos y {len(architectures)*1800} predicciones externas. Lectura guardada.')
if __name__=='__main__':main()
