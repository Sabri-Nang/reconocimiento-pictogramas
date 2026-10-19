"""Compara detectores de rechazo sobre las mismas sesiones externas."""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.rejection import calibrate_threshold, calibrate_known_cap


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',required=True);p.add_argument('--candidate',required=True)
    a=p.parse_args()
    for name in [a.reference,a.candidate]:
        if not name.startswith('cv10_') or any(c in name for c in ['/','\\',':']):
            p.error('Identificador inválido')
    folders=[ROOT/'reports'/name for name in [a.reference,a.candidate]]
    protocols=[read(folder/'protocol.json') for folder in folders]
    assert protocols[0]['development_sha256']==protocols[1]['development_sha256']
    assert protocols[0]['folds']==protocols[1]['folds'] and protocols[0]['classes']==protocols[1]['classes']
    records=[{r['raw_path']:r for r in rows(folder/'external_predictions.csv')} for folder in folders]
    assert len(records[0])==len(records[1])==2050 and records[0].keys()==records[1].keys()
    for path,old in records[0].items():
        new=records[1][path]
        assert old['class_id']==new['class_id'] and old['session_id']==new['session_id'] and old['fold']==new['fold']
        assert old['predicted_class']==new['predicted_class']
        assert abs(float(old['confidence'])-float(new['confidence']))<1e-5
        if protocols[0].get('method')==protocols[1].get('method')=='knn':
            assert float(old['score'])==float(new['score'])
    for number in range(1,7):
        calibrations=[read(folder/f'fold_{number:02d}/calibration.json') for folder in folders]
        assert calibrations[0]['model_sha256']==calibrations[1]['model_sha256']
        for folder,cal in zip(folders,calibrations):
            internal=rows(folder/f'fold_{number:02d}/internal_predictions.csv')
            if cal.get('calibration_rule')=='known_rejection_cap':
                values=[float(r.get('score',r['confidence'])) for r in internal if int(r['known'])]
                assert calibrate_known_cap(values,cal['known_rejection_cap'])==cal['threshold']
            else:
                values=[float(r.get('score',r['confidence'])) for r in internal if not int(r['known'])]
                assert calibrate_threshold(values,.7)==cal['threshold']
            assert cal['calibration_session']!=cal['evaluation_session'] and not cal['external_used']
    summaries=[read(folder/'summary.json') for folder in folders]
    for indexed,summary in zip(records,summaries):
        values=list(indexed.values());known=[r for r in values if int(r['known'])];unknown=[r for r in values if not int(r['known'])]
        assert len(known)==1800 and len(unknown)==250
        for r in values:
            assert r['session_id']!='s007'
            assert int(r['rejected'])==int(float(r.get('score',r['confidence']))<=float(r['threshold']))
        totals=summary['pooled']
        assert sum(int(r['rejected']) for r in known)==totals['known_rejected']
        assert sum(int(r['rejected']) for r in unknown)==totals['unknown_rejected']
        assert sum(int(r['correct']) and not int(r['rejected']) for r in known)==totals['known_correct_accepted']
    old,new=[s['pooled'] for s in summaries]
    comparison=dict(reference=a.reference,candidate=a.candidate,reference_metrics=old,candidate_metrics=new,
        unknown_rejection_change_pp=100*(new['unknown_rejection_rate']-old['unknown_rejection_rate']),
        known_rejection_change_pp=100*(new['known_rejection_rate']-old['known_rejection_rate']),
        known_accuracy_with_rejection_change_pp=100*(new['known_accuracy_with_rejection']-old['known_accuracy_with_rejection']),
        external_predictions_same_models=True,thresholds_recomputed_from_internal_only=True,test_used=False)
    (folders[1]/'detector_comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    labels=[('Vecinos: límite5% conocidas' if p.get('calibration_rule')=='known_rejection_cap' else ('Vecinos: objetivo70% unknown' if p.get('method')=='knn' else 'Confianza softmax')) for p in protocols]
    fig,axes=plt.subplots(1,3,figsize=(15,4.7))
    for ax,key,title in zip(axes,['unknown_rejection_rate','known_rejection_rate','known_accuracy_with_rejection'],['Desconocidos rechazados (mayor es mejor)','Conocidos rechazados (menor es mejor)','Conocidos correctos y aceptados / todos']):
        for summary,label in zip(summaries,labels):
            ax.plot(range(1,7),[r['external'][key]*100 for r in summary['folds']],marker='o',label=label)
        ax.set(xticks=range(1,7),xticklabels=[f's{i:03d}' for i in range(1,7)],ylim=(0,101),ylabel='Porcentaje (%)',title=title)
        ax.grid(alpha=.2);ax.legend(fontsize=8)
        if key=='unknown_rejection_rate':ax.axhline(70,color='black',linestyle='--')
    fig.tight_layout(rect=(0,.07,1,1));fig.text(.02,.02,'Mismos seis MobileNet,1800 conocidas y250 unknown externos. Calibración interna por ronda. Desarrollo; s007 no utilizada.',fontsize=9)
    fig.savefig(folders[1]/'detector_comparison.png',dpi=150);plt.close(fig)
    print(json.dumps(comparison,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
