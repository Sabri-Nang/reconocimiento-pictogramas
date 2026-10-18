"""Compara dos experimentos sobre las mismas predicciones externas de desarrollo."""
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def csvrows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',required=True);p.add_argument('--candidate',required=True);a=p.parse_args()
    ref=ROOT/'reports'/a.reference;candidate=ROOT/'reports'/a.candidate
    protocols=[read(folder/'protocol.json') for folder in [ref,candidate]]
    assert protocols[0]['development_sha256']==protocols[1]['development_sha256'] and protocols[0]['folds']==protocols[1]['folds']
    values=[read(folder/'summary.json')['results']['mobilenet'] for folder in [ref,candidate]]
    predictions=[csvrows(folder/'mobilenet_out_of_fold_predictions.csv') for folder in [ref,candidate]]
    indexed=[{r['raw_path']:r for r in group} for group in predictions]
    assert len(indexed[0])==len(indexed[1])==1800 and set(indexed[0])==set(indexed[1])
    metadata={r['filename']:r for r in csvrows(ROOT/'data/metadata.csv')}
    conditions=[]
    for group in predictions:
        counts=defaultdict(lambda:[0,0])
        for row in group:
            k=metadata[Path(row['raw_path']).name]['distance'];counts[k][1]+=1;counts[k][0]+=int(row['correct'])
        conditions.append({k:dict(correct=v[0],total=v[1],accuracy=v[0]/v[1]) for k,v in counts.items()})
    old=sum(int(r['correct']) for r in predictions[0]);new=sum(int(r['correct']) for r in predictions[1])
    data=dict(reference=a.reference,candidate=a.candidate,images=1800,reference_correct=old,candidate_correct=new,reference_accuracy=old/1800,candidate_accuracy=new/1800,delta_percentage_points=(new-old)/1800*100,target_accuracy=.8,target_met_on_development=new>=1440,by_distance=dict(reference=conditions[0],candidate=conditions[1]),test_used=False,interpretation='Comparación adaptativa de desarrollo. No es prueba independiente ni confirma H1.')
    (candidate/'improvement.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    for v,label in zip(values,['Referencia','Continuación']):axes[0].plot(range(1,7),[r['outer_accuracy']*100 for r in v['folds']],marker='o',label=label)
    axes[0].set(xticks=range(1,7),xticklabels=protocols[0]['config']['sessions'],xlabel='Sesión externa de la ronda',ylabel='Exactitud (%)',title='MobileNet: comparación en las mismas sesiones',ylim=(0,101));axes[0].axhline(80,color='black',linestyle='--',label='Objetivo 80%');axes[0].legend()
    scores=[old/18,new/18];axes[1].bar(['Referencia','Continuación'],scores,color=['gray','steelblue']);axes[1].axhline(80,color='black',linestyle='--');axes[1].set(ylabel='Exactitud (%)',title='Promedio sobre las seis rondas',ylim=(0,101))
    for i,s in enumerate(scores):axes[1].text(i,s+1,f'{s:.2f}%',ha='center')
    fig.tight_layout(rect=(0,.06,1,1));fig.text(.02,.01,'Fuente: 1.800 predicciones externas por experimento. Comparación de desarrollo; s007 no utilizada.',fontsize=8);fig.savefig(candidate/'improvement.png',dpi=150);plt.close(fig)
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
