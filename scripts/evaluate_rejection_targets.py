"""Compara reglas75/80% internas con límite1% conocido; sin reentrenar."""
import hashlib
from pathlib import Path
import sys
import json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.rejection import calibrate_target_with_known_cap,evaluate_rejection
from reconocimiento_pictogramas.artifacts import read_json,read_csv,write_csv,save_json,contained,save_figure
SOURCE=ROOT/'reports/cv10_s008_192_unknown_knn_20261019'
OUT=ROOT/'reports/cv10_s008_192_rejection_targets_20261019'
TARGETS=(.75,.80)
CAP=.01

def metrics(records,threshold):
    known=[r for r in records if int(r['known'])];unknown=[r for r in records if not int(r['known'])]
    return evaluate_rejection([float(r['score']) for r in known],[int(r['correct']) for r in known],[float(r['score']) for r in unknown],threshold)

def validate(records,sessions):
    assert {r['session_id'] for r in records}==set(sessions) and 's007' not in sessions
    assert len(records)==len({r['raw_path'] for r in records})
    assert sum(int(r['known']) for r in records)==300
    for r in records:
        assert int(r['known'])==int(r['class_id']!='unknown')
        assert int(r['correct'])==int(r['class_id']==r['predicted_class'])

def main():
    OUT.mkdir(exist_ok=False)
    protocol=read_json(SOURCE/'protocol.json');assert protocol['method']=='knn' and protocol['neighbors']==5 and len(protocol['folds'])==7
    selected=ROOT/'config/application.json';protected=hashlib.sha256(selected.read_bytes()).hexdigest()
    plan=dict(source_run=SOURCE.name,targets=list(TARGETS),known_rejection_cap=CAP,
        calibration='Minimo umbral por objetivo unknown interno, siempre que rechazo conocido interno<=1%. Inviable si no cumple; sin fallback ni ajuste externo.',
        infeasible_variant_policy='Si una ronda es inviable no se calcula un promedio externo parcial para esa variante.',
        acceptance_criteria=dict(all_internal_folds_feasible=True,external_unknown_rejection_min=.70,external_known_rejection_max=.01,external_correct_accepted_min=.93),
        cached_scores_reused=True,external_used_for_threshold=False,inner_shared_with_early_stopping=True,
        interpretation='Desarrollo adaptativo; las externas ya fueron analizadas antes. No prueba independiente. Limites internos no garantizan externos.',test_used=False,application_changed=False,
        source_protocol_sha256=hashlib.sha256((SOURCE/'protocol.json').read_bytes()).hexdigest(),created_utc=datetime.now(timezone.utc).isoformat())
    save_json(OUT/'protocol.json',plan)
    frozen={};inputs={}
    # Todas las calibraciones se guardan ANTES de leer puntuaciones externas.
    for target in TARGETS:
        variant=OUT/f'target_{round(target*100)}';variant.mkdir();frozen[target]=[]
        for fold in protocol['folds']:
            n=fold['fold'];base=SOURCE/f'fold_{n:02d}';dest=variant/f'fold_{n:02d}';dest.mkdir()
            assert not set(fold['train'])&set(fold['stop']) and not set(fold['train'])&set(fold['outer']) and not set(fold['stop'])&set(fold['outer'])
            reference=read_json(base/'reference_manifest.json');assert reference['role']=='train' and reference['sessions']==fold['train'] and reference['images']==1500
            assert hashlib.sha256(contained(reference['archive']).read_bytes()).hexdigest()==reference['archive_sha256']
            calibration=read_json(base/'calibration.json');result=read_json(base/'result.json')
            assert hashlib.sha256(contained(result['model_path']).read_bytes()).hexdigest()==calibration['model_sha256']
            records=read_csv(base/'internal_predictions.csv');validate(records,fold['stop'])
            known=[float(r['score']) for r in records if int(r['known'])];unknown=[float(r['score']) for r in records if not int(r['known'])]
            chosen=calibrate_target_with_known_cap(unknown,known,target,CAP)
            chosen.update(fold=n,calibration_session=fold['stop'][0],evaluation_session=fold['outer'][0],model_sha256=calibration['model_sha256'],external_used=False)
            if chosen['feasible']:chosen['internal_metrics']=metrics(records,chosen['threshold'])
            save_json(dest/'calibration.json',chosen);frozen[target].append(chosen)
            for name in ('internal_predictions.csv','calibration.json','reference_manifest.json'):
                p=base/name;inputs[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    summaries={}
    baseline=None
    for target,calibrations in frozen.items():
        variant=OUT/f'target_{round(target*100)}'
        if not all(c['feasible'] for c in calibrations):
            summaries[str(target)]=dict(status='infeasible',infeasible_folds=[c['fold'] for c in calibrations if not c['feasible']],external_evaluated=False)
            save_json(variant/'summary.json',summaries[str(target)]);continue
        records_all=[];folds=[]
        for fold,calibration in zip(protocol['folds'],calibrations):
            n=fold['fold'];base=SOURCE/f'fold_{n:02d}';dest=variant/f'fold_{n:02d}';threshold=calibration['threshold']
            records=read_csv(base/'external_predictions.csv');validate(records,fold['outer'])
            internal_paths={r['raw_path'] for r in read_csv(base/'internal_predictions.csv')};assert not internal_paths&{r['raw_path'] for r in records}
            for row in records:row.update(threshold=threshold,rejected=int(float(row['score'])<=threshold))
            m=metrics(records,threshold);write_csv(dest/'external_predictions.csv',records)
            stats=dict(fold=n,session=fold['outer'][0],threshold=threshold,external=m);save_json(dest/'result.json',stats);folds.append(stats);records_all+=records
            inputs[(base/'external_predictions.csv').relative_to(ROOT).as_posix()]=hashlib.sha256((base/'external_predictions.csv').read_bytes()).hexdigest()
        assert len(records_all)==len({r['raw_path'] for r in records_all})==2400
        known=[r for r in records_all if int(r['known'])];unknown=[r for r in records_all if not int(r['known'])];assert len(known)==2100 and len(unknown)==300
        correct=sum(int(r['correct']) for r in known);assert correct==1964
        rejected_known=sum(int(r['rejected']) for r in known);rejected_unknown=sum(int(r['rejected']) for r in unknown)
        accepted_correct=sum(int(r['correct']) and not int(r['rejected']) for r in known)
        totals=dict(known_images=2100,unknown_images=300,known_correct_without_rejection=correct,known_rejected=rejected_known,known_rejection_rate=rejected_known/2100,known_correct_accepted=accepted_correct,known_accuracy_with_rejection=accepted_correct/2100,unknown_rejected=rejected_unknown,unknown_rejection_rate=rejected_unknown/300,unknown_false_accepted=300-rejected_unknown)
        accepted=totals['unknown_rejection_rate']>=.7 and totals['known_rejection_rate']<=.01 and totals['known_accuracy_with_rejection']>=.93
        summaries[str(target)]=dict(status='evaluated',pooled=totals,folds=folds,meets_prefixed_external_criteria=accepted)
        save_json(variant/'summary.json',summaries[str(target)]);write_csv(variant/'external_predictions.csv',records_all)
        print(target,json.dumps(totals),flush=True)
    baseline=read_json(SOURCE/'summary.json')['pooled']
    comparison=dict(baseline=baseline,variants=summaries,application_changed=False,test_used=False,thresholds_not_selected_from_external_scores=True)
    save_json(OUT/'comparison.json',comparison)
    assert hashlib.sha256(selected.read_bytes()).hexdigest()==protected
    assert all(hashlib.sha256(contained(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
    save_json(OUT/'verification.json',dict(source_input_hashes=inputs,source_scores_unchanged=True,models_and_references_verified=True,all_thresholds_frozen_before_external_read=True,selected_configuration_unchanged=True,test_used=False,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cases=[('70% interno',baseline)]+[(f'{int(float(k)*100)}% interno',v['pooled']) for k,v in summaries.items() if v['status']=='evaluated']
    fig,axes=plt.subplots(1,3,figsize=(15,5))
    for ax,key,title,limit in zip(axes,('unknown_rejection_rate','known_rejection_rate','known_accuracy_with_rejection'),('Desconocidas rechazadas','Conocidas rechazadas','Conocidas correctas y aceptadas'),(70,1,93)):
        values=[100*v[key] for _,v in cases];ax.bar([k for k,_ in cases],values);ax.axhline(limit,color='black',linestyle='--');ax.set(title=title,ylabel='Porcentaje (%)')
        for i,v in enumerate(values):ax.text(i,v,f'{v:.2f}%',ha='center',va='bottom')
        ax.set_ylim(0,max(max(values)*1.2,limit*1.2));ax.grid(axis='y',alpha=.2)
    fig.tight_layout(rect=(0,.07,1,.94));fig.suptitle('MobileNet192: mismas puntuaciones, nuevas reglas internas');fig.text(.02,.02,'Desarrollo adaptativo, no prueba final. Limite1% interno no garantiza1% externo. s007 excluida.',fontsize=9);save_figure(fig,OUT/'comparison.png',145);plt.close(fig)
    lines=['# Recalibracion de rechazo MobileNet192','','Se conservaron modelos, referencias y puntuaciones. Todas las reglas internas se guardaron antes de cargar externas. Se compararon75% y80% con limite1% de conocidas internas. Si una ronda no cumple ambas restricciones la variante completa se marca inviable, sin promedio externo parcial.','',f"Referencia70%: unknown{baseline['unknown_rejected']}/300; conocidas rechazadas{baseline['known_rejected']}/2100; conocidas correctas aceptadas{baseline['known_correct_accepted']}/2100."]
    for target,v in summaries.items():
        if v['status']=='infeasible':lines += [f"- Objetivo{target}: inviable en rondas{v['infeasible_folds']}; no evaluacion externa agrupada."];continue
        m=v['pooled'];lines += [f"- Objetivo{target}: unknown{m['unknown_rejected']}/300 ({100*m['unknown_rejection_rate']:.2f}%); conocidas rechazadas{m['known_rejected']}/2100 ({100*m['known_rejection_rate']:.2f}%); conocidas correctas aceptadas{m['known_correct_accepted']}/2100 ({100*m['known_accuracy_with_rejection']:.2f}%). Cumple criterios externos prefijados:{v['meets_prefixed_external_criteria']}."]
    lines+=['','Limites: desarrollo adaptativo con externas ya analizadas; no validacion independiente. Conocidas internas compartidas con parada temprana. No garantia de rechazo en otro entorno ni sobre pictogramas ajenos. No se modificaron la aplicacion, su modelo128 ni su umbral. Un modelo unico192 requiere calibracion propia. s007 reservada.']
    (OUT/'lectura_resultados.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':main()
