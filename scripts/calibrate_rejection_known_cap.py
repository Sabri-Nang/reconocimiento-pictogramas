"""Recalibra puntuaciones kNN guardadas con límite5% de rechazo conocido interno."""
import argparse
import hashlib
from pathlib import Path
import sys
import json
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.rejection import calibrate_known_cap, evaluate_rejection
from evaluate_unknown_cv import read,rows,save,write,contained,plot_and_explain


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',default='cv10_unknown_knn_20261018')
    parser.add_argument('--run-id',default=datetime.now(timezone.utc).strftime('cv10_unknown_knn_cap05_%Y%m%d_%H%M%S'))
    args=parser.parse_args()
    for name in [args.source_run,args.run_id]:
        if not name.startswith('cv10_') or any(c in name for c in ['/','\\',':']):parser.error('Identificador inválido')
    source=ROOT/'reports'/args.source_run
    protocol=read(source/'protocol.json')
    assert protocol['method']=='knn' and protocol['neighbors']==5
    assert len(protocol['folds'])==6
    assert hashlib.sha256((ROOT/'data/splits/development.csv').read_bytes()).hexdigest()==protocol['development_sha256']
    out=ROOT/'reports'/args.run_id;out.mkdir(exist_ok=False)
    cap=.05
    selection='Mayor umbral que rechaza como máximo5% de todas las conocidas internas; por monotonía maximiza rechazo de unknown bajo ese límite. Sin consultar externas.'
    newprotocol=dict(protocol)
    newprotocol.update(calibration_source_run=args.source_run,calibration_rule='known_rejection_cap',known_rejection_cap=cap,
        selection=selection,target_unknown_rejection=.7,target_unknown_is_evaluation_goal_not_calibration_constraint=True,
        cached_scores_reused=True,source_protocol_sha256=hashlib.sha256((source/'protocol.json').read_bytes()).hexdigest(),created_utc=datetime.now(timezone.utc).isoformat())
    save(out/'protocol.json',newprotocol)
    results=[];internal_all=[];external_all=[];input_hashes={}
    for fold in protocol['folds']:
        n=fold['fold'];base=source/f'fold_{n:02d}';dest=out/f'fold_{n:02d}';dest.mkdir()
        assert not set(fold['train'])&set(fold['stop']) and not set(fold['train'])&set(fold['outer']) and not set(fold['stop'])&set(fold['outer'])
        assert set(fold['train']+fold['stop']+fold['outer'])=={f's{i:03d}' for i in range(1,7)}
        manifest=read(base/'reference_manifest.json')
        assert manifest['role']=='train' and manifest['sessions']==fold['train'] and manifest['images']==1200
        assert hashlib.sha256(contained(manifest['archive']).read_bytes()).hexdigest()==manifest['archive_sha256']
        save(dest/'reference_manifest.json',manifest)
        old=read(base/'calibration.json');old_result=read(base/'result.json')
        assert hashlib.sha256(contained(old_result['model_path']).read_bytes()).hexdigest()==old['model_sha256']
        internal=rows(base/'internal_predictions.csv')
        assert {r['session_id'] for r in internal}==set(fold['stop'])
        known=[r for r in internal if int(r['known'])]
        assert len(known)==300
        threshold=calibrate_known_cap([float(r['score']) for r in known],cap)
        def metrics(records):
            known=[r for r in records if int(r['known'])];unknown=[r for r in records if not int(r['known'])]
            assert len(known)==300 and len(unknown)==(50 if unknown[0]['session_id']=='s006' else 40)
            return evaluate_rejection([float(r['score']) for r in known],[int(r['correct']) for r in known],[float(r['score']) for r in unknown],threshold)
        internal_metrics=metrics(internal)
        assert internal_metrics['known_rejected']<=15
        calibration=dict(method='knn',calibration_rule='known_rejection_cap',known_rejection_cap=cap,
            threshold=threshold,model_sha256=old['model_sha256'],calibration_session=fold['stop'][0],evaluation_session=fold['outer'][0],
            selection=selection,internal_metrics=internal_metrics,external_used=False)
        save(dest/'calibration.json',calibration)
        # Primer acceso a puntuaciones externas de esta ronda después de congelar umbral.
        external=rows(base/'external_predictions.csv')
        assert {r['session_id'] for r in external}==set(fold['outer'])
        assert not {r['raw_path'] for r in internal}&{r['raw_path'] for r in external}
        for records in [internal,external]:
            for r in records:
                r['threshold']=threshold;r['rejected']=int(float(r['score'])<=threshold)
                assert r['session_id']!='s007'
            assert len(records)==len({r['raw_path'] for r in records})
        write(dest/'internal_predictions.csv',internal);write(dest/'external_predictions.csv',external)
        stats=dict(fold=n,threshold=threshold,calibration_session=fold['stop'][0],evaluation_session=fold['outer'][0],
            model_path=old_result['model_path'],internal=internal_metrics,external=metrics(external))
        save(dest/'result.json',stats);results.append(stats);internal_all.extend(internal);external_all.extend(external)
        for name in ['internal_predictions.csv','external_predictions.csv','calibration.json','reference_manifest.json']:
            path=base/name;input_hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        print(json.dumps(dict(fold=n,threshold=threshold,internal_known_rejected=internal_metrics['known_rejected'],external=stats['external'])),flush=True)
    assert len(external_all)==2050==len({r['raw_path'] for r in external_all})
    write(out/'internal_predictions.csv',internal_all);write(out/'external_predictions.csv',external_all)
    keys=['known_images','unknown_images','known_correct_without_rejection','known_rejected','known_accepted','known_correct_accepted','known_wrong_accepted','unknown_rejected','unknown_false_accepted']
    totals={k:sum(r['external'][k] for r in results) for k in keys}
    assert totals['known_images']==1800 and totals['unknown_images']==250 and totals['known_correct_without_rejection']==1441
    totals.update(known_accuracy_without_rejection=totals['known_correct_without_rejection']/1800,
        known_accuracy_with_rejection=totals['known_correct_accepted']/1800,known_rejection_rate=totals['known_rejected']/1800,
        accuracy_among_accepted_known=totals['known_correct_accepted']/totals['known_accepted'] if totals['known_accepted'] else None,
        unknown_rejection_rate=totals['unknown_rejected']/250,unknown_false_acceptance_rate=totals['unknown_false_accepted']/250)
    save(out/'summary.json',dict(method='knn',calibration_rule='known_rejection_cap',known_rejection_cap=cap,
        source_run=protocol['source_run'],calibration_source_run=args.source_run,folds=results,pooled=totals,test_used=False,final_threshold_selected=False))
    save(out/'verification.json',dict(folds=6,external_images=2050,known_images=1800,unknown_images=250,
        cached_scores_unchanged=True,reference_archives_verified=6,models_verified=6,source_input_hashes=input_hashes,
        internal_known_rejected_limit=15,all_inner_folds_within_limit=True,thresholds_frozen_before_external_read=True,
        external_paths_unique=True,test_used=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    plot_and_explain(out,results,internal_all,totals)
    path=out/'lectura_resultados.md';text=path.read_text(encoding='utf-8')
    old_description='Se calibró un umbral por ronda usando únicamente unknown de la sesión interna. Se eligió el menor que rechaza al menos70% (incluida igualdad). Esa regla minimiza el rechazo de conocidos bajo la restricción elegida. No se fijó un umbral global de aplicación.'
    assert old_description in text
    text=text.replace(old_description,'Se calibró un umbral por ronda con todas las300 conocidas internas: se eligió el mayor umbral que rechaza como máximo15(5%), respetando empates e incluyendo igualdad. Por monotonía maximiza también rechazo de unknown bajo ese límite. No se exigió70% interno de unknown;70% sigue como objetivo de evaluación externa. No se fijó un umbral global de aplicación.')
    text+='\nEl límite5% corresponde a calibración interna, no es garantía sobre sesiones externas. Se reutilizaron las mismas puntuaciones de cinco vecinos y los mismos modelos/referencias; no hubo inferencia nueva ni reentrenamiento.\n'
    path.write_text(text,encoding='utf-8')
    print('SUMMARY '+json.dumps(totals),flush=True)


if __name__=='__main__':main()
