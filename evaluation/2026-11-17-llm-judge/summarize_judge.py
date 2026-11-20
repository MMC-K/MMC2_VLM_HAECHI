from pathlib import Path
import json,collections,math,hashlib
P=Path(__file__).resolve().parent

def load(name):return [json.loads(x) for x in (P/name).read_text().splitlines() if x.strip()]
def ci(k,n):
 z=1.959963984540054;a=(k/n+z*z/(2*n))/(1+z*z/n);b=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n);return [100*max(0,a-b),100*min(1,a+b)]
def main():
 mapping=json.loads((P/'private_mapping.json').read_text());judged={x['blind_id']:x for x in load('main_results.jsonl')};assert len(mapping)==400
 joined=[]
 for m in mapping:
  r=judged[m['blind_id']];assert 'judgment' in r
  joined.append({**m,**r['judgment']})
 summary={'judge_model_requested':'gemini-3.5-flash-lite','judge_models_returned':sorted({x['raw_response'].get('modelVersion') for x in judged.values()}),'primary_metric':'100 * number labeled correct / all 100 questions; partial, incorrect, unjudgeable retained in denominator','calibration':{'n':10,'passed':sum(x['judgment']['label']==x['expected'] for x in load('calibration_results.jsonl'))},'results':{},'paired':{}}
 for alias in ['qwen_base','qwen_haechi','hyperclova_base','hyperclova_haechi']:
  rows=[r for r in joined if r['model_stage']==alias];assert len(rows)==100;counts=dict(collections.Counter(r['label'] for r in rows));k=counts.get('correct',0)
  summary['results'][alias]={'count':100,'counts':{k:counts.get(k,0) for k in ['correct','partial','incorrect','unjudgeable']},'correct_rate_percent':k,'correct_rate_ci95_percent':ci(k,100)}
 for alias in ['qwen','hyperclova']:
  before={r['sample_id']:r for r in joined if r['model_stage']==alias+'_base'};after={r['sample_id']:r for r in joined if r['model_stage']==alias+'_haechi'};counts=collections.Counter(('correct' if before[s]['label']=='correct' else 'not_correct','correct' if after[s]['label']=='correct' else 'not_correct') for s in before)
  summary['paired'][alias]={'improved':counts['not_correct','correct'],'regressed':counts['correct','not_correct'],'both_correct':counts['correct','correct'],'both_not_correct':counts['not_correct','not_correct'],'correct_rate_delta_pp':summary['results'][alias+'_haechi']['correct_rate_percent']-summary['results'][alias+'_base']['correct_rate_percent']}
 if (P/'repeat_results.jsonl').exists():
  repeat={x['blind_id']:x for x in load('repeat_results.jsonl')};valid={k:r for k,r in repeat.items() if 'judgment' in r};summary['repeatability']={'count':len(valid),'all_labels_agreed':sum(r['judgment']['label']==judged[k]['judgment']['label'] for k,r in valid.items()),'binary_correctness_agreed':sum((r['judgment']['label']=='correct')==(judged[k]['judgment']['label']=='correct') for k,r in valid.items()),'disagreement_blind_ids':[k for k,r in valid.items() if r['judgment']['label']!=judged[k]['judgment']['label']]}
 (P/'judgments_joined.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in joined));(P/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
