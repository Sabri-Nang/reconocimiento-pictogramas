"""Calibra rechazo en sesiones internas y evalúa sesiones externas de MobileNet."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from reconocimiento_pictogramas.preprocessing import prepare_image
from reconocimiento_pictogramas.rejection import calibrate_threshold, evaluate_rejection
from reconocimiento_pictogramas.artifacts import contained, read_json as read, read_csv as rows, save_json as save, write_csv as write, save_figure


def evaluate(source_run, run, method="softmax"):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    import numpy as np
    import tensorflow as tf
    from sklearn.metrics import roc_auc_score
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    source = ROOT / 'reports' / source_run
    protocol = read(source / 'protocol.json')
    classes = [c['id'] for c in protocol['project']['classes']]
    sessions = protocol['config']['sessions']
    assert len(sessions)>=3 and len(set(sessions))==len(sessions) and 's007' not in sessions
    known_count=len(sessions)*protocol['config']['expected_per_class_session']*len(classes)
    assert len(classes) == len(set(classes)) == 10
    assert hashlib.sha256(contained(protocol.get('development_manifest','data/splits/development.csv')).read_bytes()).hexdigest() == protocol['development_sha256']
    audit = read(contained(protocol['config'].get('audit_path','reports/dataset_10_audit/integrity.json')))
    assert not audit['errors']
    inventory = rows(contained(protocol['config'].get('inventory_path','reports/dataset_10_audit/inventory.csv')))
    unknown = [r for r in inventory if r['class_id']=='unknown' and r['session_id'] in sessions]
    unknown_count=sum(50 if session in {'s006','s008'} else 40 for session in sessions)
    assert len(unknown) == unknown_count and len({r['raw_path'] for r in unknown}) == unknown_count
    assert len({r['sha256'] for r in inventory if r['session_id'] in sessions}) == known_count+unknown_count
    for session in sessions:
        assert sum(r['session_id']==session for r in unknown) == (50 if session in {'s006','s008'} else 40)
    for row in unknown:
        assert Path(row['raw_path']).name.startswith(f"unknown_{row['session_id']}_")
        assert hashlib.sha256(contained(row['raw_path']).read_bytes()).hexdigest() == row['sha256']
    out = ROOT/'reports'/run
    out.mkdir(exist_ok=False)
    target = 0.7
    save(out/'protocol.json', dict(source_run=source_run, source_protocol_sha256=hashlib.sha256((source/'protocol.json').read_bytes()).hexdigest(),
        development_sha256=protocol['development_sha256'], classes=classes, folds=protocol['folds'],
        score='maximum_softmax_probability' if method=='softmax' else 'mean_top5_cosine_similarity_scaled_0_1', method=method, reference_role='train_only' if method=='knn' else None, neighbors=5 if method=='knn' else None, rejection_rule='score <= threshold', target_unknown_rejection=target,
        selection='Menor umbral que rechaza al menos70% de desconocidos de la sesión interna; minimiza rechazo de conocidos para esta restricción.',
        inner_known_reused_for_early_stopping=True, external_used_to_select_threshold=False,
        interpretation='Desarrollo adaptativo. Sesión interna compartida con parada temprana; externa separada de la calibración en cada ronda. No prueba final.',
        unknown_cv_rotation='Extensión explícita del protocolo CV: unknown sigue el rol interno/externo de la sesión. La referencia fija s006 para calibración final no se sustituye.',
        final_threshold_selected=False, test_used=False, created_utc=datetime.now(timezone.utc).isoformat()))
    size=protocol['project']['image']; image_size=(size['width'], size['height'])
    unknown_cache = {r['raw_path']: np.asarray(prepare_image(contained(r['raw_path']), image_size), dtype=np.uint8) for r in unknown}
    results=[]; external_records=[]; internal_records=[]
    for fold in protocol['folds']:
        number=fold['fold']; print(f'Ronda {number}: calibración {fold["stop"]}, evaluación {fold["outer"]}', flush=True)
        assert not set(fold['train']) & set(fold['stop']) and not set(fold['train']) & set(fold['outer']) and not set(fold['stop']) & set(fold['outer'])
        assert set(fold['train']+fold['stop']+fold['outer']) == set(sessions)
        folder=source/f'fold_{number:02d}'
        result=read(folder/'mobilenet/result.json')
        checkpoint=contained(result['model_path'])
        model=tf.keras.models.load_model(checkpoint, compile=False)
        assert model.output_shape[-1]==10 and tuple(model.input_shape[1:])==(image_size[1],image_size[0],3)
        dest=out/f'fold_{number:02d}'; dest.mkdir()
        selected={role:rows(folder/f'{role}.csv') for role in ['train','stop','outer']}
        for field in ['raw_path','processed_path','sha256','session_id']:
            parts=[{r[field] for r in selected[role]} for role in ['train','stop','outer']]
            assert not parts[0]&parts[1] and not parts[0]&parts[2] and not parts[1]&parts[2]
        references=None
        extractor=None
        if method=='knn':
            from reconocimiento_pictogramas.feature_rejection import neighbor_similarity, normalize_features
            reference_count=len(fold['train'])*protocol['config']['expected_per_class_session']*len(classes)
            assert len(selected['train'])==reference_count
            assert {r['session_id'] for r in selected['train']}==set(fold['train'])
            extractor=tf.keras.Model(model.input,[model.output,model.layers[-1].input])
            reference_images=[np.asarray(prepare_image(contained(r['processed_path']),image_size),dtype=np.uint8) for r in selected['train']]
            references=np.concatenate([np.asarray(extractor(np.stack(reference_images[i:i+32]),training=False)[1]) for i in range(0,reference_count,32)])
            normalize_features(references)
            detector_folder=ROOT/'models'/run/f'fold_{number:02d}'
            detector_folder.mkdir(parents=True,exist_ok=False)
            archive=detector_folder/'references.npz'
            np.savez_compressed(archive,features=references,raw_paths=np.array([r['raw_path'] for r in selected['train']]))
            save(dest/'reference_manifest.json',dict(role='train',sessions=fold['train'],images=reference_count,
                feature_dimension=int(references.shape[1]),feature_layer='input_to_final_Dense_after_disabled_dropout',
                k=5,archive=archive.relative_to(ROOT).as_posix(),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                paths_and_hashes=[dict(raw_path=r['raw_path'],sha256=r['sha256']) for r in selected['train']]))
        def predict(role):
            known=selected[role]
            assert len(known)==300 and {r['session_id'] for r in known}==set(fold[role])
            negatives=[r for r in unknown if r['session_id'] in fold[role]]
            images=[np.asarray(prepare_image(contained(r['processed_path']), image_size),dtype=np.uint8) for r in known]
            images += [unknown_cache[r['raw_path']] for r in negatives]
            # Mismo uint8, sin normalización externa ni aumentos de inferencia.
            if method=='knn':
                outputs=[extractor(np.stack(images[i:i+32]),training=False) for i in range(0,len(images),32)]
                probabilities=np.concatenate([np.asarray(o[0]) for o in outputs])
                features=np.concatenate([np.asarray(o[1]) for o in outputs])
                detector_scores=neighbor_similarity(features,references,k=5)
            else:
                probabilities=np.concatenate([np.asarray(model(np.stack(images[i:i+32]),training=False)) for i in range(0,len(images),32)])
                detector_scores=probabilities.max(axis=1)
            assert probabilities.shape==(len(images),10) and np.isfinite(probabilities).all()
            assert (probabilities>=0).all() and (probabilities<=1).all()
            assert np.allclose(probabilities.sum(axis=1),1,atol=1e-5)
            records=[]
            for row,prob,score in zip(known+negatives,probabilities,detector_scores):
                predicted=classes[int(prob.argmax())]
                records.append(dict(raw_path=row['raw_path'],session_id=row['session_id'],class_id=row['class_id'],
                    predicted_class=predicted,known=int(row['class_id']!='unknown'),correct=int(row['class_id']==predicted),
                    confidence=float(prob.max()),score=float(score),fold=number,**{f'prob_{c}':float(p) for c,p in zip(classes,prob)}))
            return records
        internal=predict('stop')
        known_inner=[r for r in internal if r['known']]; unknown_inner=[r for r in internal if not r['known']]
        threshold=calibrate_threshold([r['score'] for r in unknown_inner],target)
        def metrics(records):
            known=[r for r in records if r['known']]; negative=[r for r in records if not r['known']]
            values=evaluate_rejection([r['score'] for r in known],[r['correct'] for r in known],[r['score'] for r in negative],threshold)
            values['unknown_detection_auroc']=float(roc_auc_score([0]*len(known)+[1]*len(negative),[-r['score'] for r in known+negative]))
            return values
        calibration=dict(method=method,threshold=threshold,model_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            calibration_session=fold['stop'][0],evaluation_session=fold['outer'][0],target_unknown_rejection=target,
            internal_metrics=metrics(internal),external_used=False)
        # Persistir el umbral ANTES de cargar o consultar las imágenes externas.
        save(dest/'calibration.json',calibration)
        curve=[]
        for t in sorted({0.0,1.0,*[r['score'] for r in internal]}):
            m=evaluate_rejection([r['score'] for r in known_inner],[r['correct'] for r in known_inner],[r['score'] for r in unknown_inner],t)
            curve.append(dict(threshold=t,unknown_rejection_rate=m['unknown_rejection_rate'],known_rejection_rate=m['known_rejection_rate'],known_accuracy_with_rejection=m['known_accuracy_with_rejection']))
        write(dest/'internal_threshold_curve.csv',curve)
        external=predict('outer')
        previous={r['raw_path']:r for r in rows(folder/'mobilenet/outer_predictions.csv')}
        for r in external:
            if r['known']:
                old=previous[r['raw_path']]
                assert old['predicted_class']==r['predicted_class']
                assert np.allclose([float(old[f'prob_{c}']) for c in classes],[r[f'prob_{c}'] for c in classes],atol=1e-5)
        for records in [internal,external]:
            for r in records:
                r.update(threshold=threshold,rejected=int(r['score']<=threshold))
            assert {r['session_id'] for r in records} <= set(sessions)
        write(dest/'internal_predictions.csv',internal); write(dest/'external_predictions.csv',external)
        stats=dict(fold=number,threshold=threshold,calibration_session=fold['stop'][0],evaluation_session=fold['outer'][0],
            model_path=result['model_path'],internal=calibration['internal_metrics'],external=metrics(external))
        save(dest/'result.json',stats);results.append(stats)
        internal_records.extend(internal);external_records.extend(external)
        print(json.dumps(stats['external'],ensure_ascii=False),flush=True)
        tf.keras.backend.clear_session()
    assert len({r['raw_path'] for r in external_records})==known_count+unknown_count==len(external_records)
    write(out/'external_predictions.csv',external_records)
    write(out/'internal_predictions.csv',internal_records)
    totals={key:sum(r['external'][key] for r in results) for key in ['known_images','unknown_images','known_correct_without_rejection','known_rejected','known_accepted','known_correct_accepted','known_wrong_accepted','unknown_rejected','unknown_false_accepted']}
    totals.update(known_accuracy_without_rejection=totals['known_correct_without_rejection']/totals['known_images'],
        known_accuracy_with_rejection=totals['known_correct_accepted']/totals['known_images'],
        known_rejection_rate=totals['known_rejected']/totals['known_images'],
        accuracy_among_accepted_known=totals['known_correct_accepted']/totals['known_accepted'] if totals['known_accepted'] else None,
        unknown_rejection_rate=totals['unknown_rejected']/totals['unknown_images'],
        unknown_false_acceptance_rate=totals['unknown_false_accepted']/totals['unknown_images'])
    assert totals['known_images']==known_count and totals['unknown_images']==unknown_count
    expected_correct=sum(int(r['correct']) for r in rows(source/'mobilenet_out_of_fold_predictions.csv'))
    assert totals['known_correct_without_rejection']==expected_correct
    save(out/'summary.json',dict(method=method,source_run=source_run,folds=results,pooled=totals,test_used=False,final_threshold_selected=False))
    save(out/'verification.json',dict(folds=len(sessions),external_images=known_count+unknown_count,known_images=known_count,unknown_images=unknown_count,external_paths_unique=True,
        original_external_predictions_match=True,thresholds_saved_before_external_inference=True,unknown_hashes_verified=unknown_count,
        source_manifest_unchanged=True,disjoint_sessions_paths_hashes=True,test_used=False,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),python=sys.version))
    plot_and_explain(out,results,internal_records,totals)
    print('SUMMARY '+json.dumps(totals),flush=True)


def plot_and_explain(out,results,internal,totals):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    method=read(out/'protocol.json')['method']
    fig,axes=plt.subplots(1,2,figsize=(13,4.8))
    for is_known,label in [(1,'Conocidas internas'),(0,'Desconocidas internas')]:
        values=[float(r['score']) for r in internal if int(r['known'])==is_known]
        axes[0].hist(values,bins=np.linspace(0,1,26),density=True,histtype='step',linewidth=2,label=label)
    axes[0].set(xlabel='Similitud con vecinos (no probabilidad)' if method=='knn' else 'Máxima puntuación softmax',ylabel='Densidad (grupos normalizados)',title='Puntuaciones usadas para calibrar');axes[0].legend()
    positions=np.arange(len(results));width=.25
    for offset,key,label in [(-width,'unknown_rejection_rate','Desconocidos rechazados'),(0,'known_rejection_rate','Conocidos rechazados'),(width,'known_accuracy_with_rejection','Conocidos correctos / todos los conocidos')]:
        axes[1].bar(positions+offset,[r['external'][key]*100 for r in results],width,label=label)
    axes[1].axhline(70,color='black',linestyle='--',label='Objetivo de rechazo 70%')
    axes[1].set(xticks=positions,xticklabels=[r['evaluation_session'] for r in results],ylim=(0,101),ylabel='Porcentaje (%)',title='Sesiones externas con umbrales congelados');axes[1].legend(fontsize=7)
    fig.tight_layout(rect=(0,.07,1,1));fig.text(.02,.02,f"Desarrollo: {totals['known_images']} conocidas y {totals['unknown_images']} desconocidas. Cada modelo tiene su propio umbral. s007 no utilizada.",fontsize=9)
    save_figure(fig,out/'rejection_evaluation.png',dpi=150);plt.close(fig)
    lines=['# Evaluación de rechazo de desconocidos con MobileNet','',
        'Se calibró un umbral por ronda usando únicamente unknown de la sesión interna. Se eligió el menor que rechaza al menos70% (incluida igualdad). Esa regla minimiza el rechazo de conocidos bajo la restricción elegida. No se fijó un umbral global de aplicación.','',
        'La sesión interna conocida ya se usó para parada temprana. Sus métricas son de calibración, no independientes. La externa no eligió el umbral de su ronda. Las rondas comparten datos y el modelo fue elegido adaptativamente durante el desarrollo. s007 no participó.','',
        '## Resultados externos agrupados','',
        f"- Conocidos sin rechazo: {totals['known_correct_without_rejection']}/{totals['known_images']} = {totals['known_accuracy_without_rejection']:.2%}.",
        f"- Desconocidos rechazados: {totals['unknown_rejected']}/{totals['unknown_images']} = {totals['unknown_rejection_rate']:.2%}.",
        f"- Desconocidos aceptados por error: {totals['unknown_false_accepted']}/{totals['unknown_images']}.",
        f"- Conocidos rechazados: {totals['known_rejected']}/{totals['known_images']} = {totals['known_rejection_rate']:.2%}.",
        f"- Conocidos correctamente clasificados y aceptados: {totals['known_correct_accepted']}/{totals['known_images']} = {totals['known_accuracy_with_rejection']:.2%}.",
        f"- Exactitud entre conocidos aceptados: {totals['accuracy_among_accepted_known']:.2%}. Este denominador excluye rechazados y no sustituye la exactitud sobre todos los conocidos.",'',
        '## Rondas','']
    for r in results:
        e=r['external'];lines += [f"- Ronda {r['fold']}: calibración {r['calibration_session']}, externa {r['evaluation_session']}, umbral {r['threshold']:.8f}; rechazo unknown {e['unknown_rejected']}/{e['unknown_images']} ({e['unknown_rejection_rate']:.1%}); rechazo conocidas {e['known_rejected']}/300; conocidas correctas aceptadas {e['known_correct_accepted']}/300."]
    lines += ['', '## Límites y siguiente decisión','',
        'El70% solicitado es una tasa de rechazo, no un umbral0.70. Los umbrales no son probabilidades de pertenecer a las diez clases. La confianza puede ser alta en imágenes ajenas.','',
        'Los negativos actuales contienen principalmente objetos y fondos: faltan más pictogramas ajenos difíciles. No puede afirmarse rechazo general de cualquier desconocido ni cumplimiento final de hipótesis.','',
        'Si no se logra suficiente rechazo externo sin perder demasiados conocidos, comparar otro detector (por ejemplo distancia en características) o mejorar la representación de MobileNet. La regla y sus ajustes se evalúan solo en desarrollo. El modelo final debe tener su propia calibración separada antes de s007.','',
         'Este protocolo extiende a unknown la rotación de sesiones de CV; no modifica la partición fija documentada para un entrenamiento final con s006 de calibración. No se modificó application.json.']
    (out/'lectura_resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method',choices=['softmax','knn'],default='softmax')
    parser.add_argument('--source-run',default='cv10_mobilenet_extend_20261018')
    parser.add_argument('--run-id',default=datetime.now(timezone.utc).strftime('cv10_unknown_%Y%m%d_%H%M%S'))
    args=parser.parse_args()
    for value in [args.source_run,args.run_id]:
        if not value.startswith('cv10_') or any(c in value for c in ['/','\\',':']):
            parser.error('Identificador inválido')
    evaluate(args.source_run,args.run_id,args.method)


if __name__=='__main__':
    main()
