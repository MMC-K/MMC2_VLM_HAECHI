from pathlib import Path
import json,re,unicodedata,math,statistics,hashlib
from difflib import SequenceMatcher
OUT=Path(__file__).resolve().parent
inputs=[json.loads(x) for x in (OUT/'inputs.jsonl').read_text().splitlines()]
gold={r['sample_id']:r for r in map(json.loads,(OUT/'answers.jsonl').read_text().splitlines())}

def normalize(x):
 return re.sub(r'[^0-9a-z가-힣]','',unicodedata.normalize('NFKC',str(x)).lower())
def strict(x):return unicodedata.normalize('NFC',str(x)).strip()
def edit(a,b):
 if len(a)<len(b):a,b=b,a
 previous=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  current=[i]
  for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
  previous=current
 return previous[-1]
def quantile(x,q):
 x=sorted(x);pos=(len(x)-1)*q;i=int(pos)
 return x[i]+(x[min(i+1,len(x)-1)]-x[i])*(pos-i)
def wilson(k,n):
 z=1.959963984540054;mid=(k/n+z*z/(2*n))/(1+z*z/n);half=z*math.sqrt((k/n)*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n)
 return [max(0,mid-half),min(1,mid+half)]
def score(label,partial=False):
 path=OUT/f'{label}_predictions.jsonl'
 if not path.exists():return None
 records=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
 assert len({r['sample_id'] for r in records})==len(records),'duplicate records'
 pred={r['sample_id']:r for r in records}
 if not partial:assert len(pred)==300,(label,len(pred))
 meta=json.loads((OUT/f'{label}_run.json').read_text())
 output={'label':label,'run':meta,'completed_count':len(pred),'tasks':{},'details':[]}
 for task in ['h400_direct','h400_knowledge_image','ocr']:
  rows=[r for r in inputs if r['task']==task and (not partial or r['sample_id'] in pred)]
  if not rows:continue
  stats=[]
  for row in rows:
   r=pred.get(row['sample_id'],{});ref=gold[row['sample_id']]['reference'];answer=r.get('prediction','');failed=bool(r.get('error')) or not r
   a,b=normalize(answer),normalize(ref)
   result={'sample_id':row['sample_id'],'task':task,'question':row['question'],'reference':ref,'prediction':answer,'strict_exact':not failed and strict(answer)==strict(ref),'normalized_exact':not failed and bool(b) and a==b,'contains':not failed and bool(b) and b in a,'similarity':0 if failed else SequenceMatcher(None,a,b).ratio(),'edit_distance':edit(strict(answer),strict(ref)),'reference_chars':len(strict(ref)),'normalized_edit_distance':edit(a,b),'normalized_reference_chars':len(b),'error':r.get('error'),'image':row['image']}
   output['details'].append(result);stats.append(result)
  n=len(rows);s={'count':n,'errors':sum(bool(pred.get(r['sample_id'],{}).get('error')) or r['sample_id'] not in pred for r in rows)}
  for metric in ['strict_exact','normalized_exact','contains','similarity']:s[metric]=sum(r[metric] for r in stats)/n
  s['strict_exact_ci95']=wilson(sum(r['strict_exact'] for r in stats),n)
  s['normalized_exact_ci95']=wilson(sum(r['normalized_exact'] for r in stats),n)
  s['cer']=sum(r['edit_distance'] for r in stats)/max(1,sum(r['reference_chars'] for r in stats))
  s['normalized_cer']=sum(r['normalized_edit_distance'] for r in stats)/max(1,sum(r['normalized_reference_chars'] for r in stats))
  success=[pred[r['sample_id']] for r in rows if r['sample_id'] in pred and not pred[r['sample_id']].get('error')]
  if success:
   durations=[r['generation_seconds'] for r in success]
   s.update({'median_generation_seconds':statistics.median(durations),'p95_generation_seconds':quantile(durations,.95),'mean_generation_seconds':statistics.mean(durations),'mean_output_tokens':statistics.mean(r['generated_tokens'] for r in success),'output_tokens_per_second':sum(r['generated_tokens'] for r in success)/sum(durations),'peak_allocated_gib':max(r['peak_allocated_gib'] for r in success),'peak_reserved_gib':max(r['peak_reserved_gib'] for r in success),'hit_token_budget':sum(r['hit_token_budget'] for r in success)})
  output['tasks'][task]=s
 return output

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');args=p.parse_args()
 all_results={}
 for label in ['hyperclova_base','hyperclova_haechi','qwen_base','qwen_haechi']:
  r=score(label,partial=args.partial)
  if r:
   all_results[label]=r
   if not args.partial:(OUT/f'{label}_scores.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
   print(label,r['completed_count'],{k:{m:round(v[m],4) for m in ['strict_exact','normalized_exact','similarity','cer']} for k,v in r['tasks'].items()})
 if not args.partial:
  assert len(all_results)==4
  summary={'dataset':json.loads((OUT/'dataset_manifest.json').read_text()),'results':{k:{'run':v['run'],'tasks':v['tasks']} for k,v in all_results.items()},'comparisons':{}}
  for alias in ['qwen','hyperclova']:
   summary['comparisons'][alias]={}
   a=all_results[f'{alias}_base'];b=all_results[f'{alias}_haechi']
   for task in ['h400_direct','h400_knowledge_image','ocr']:
    summary['comparisons'][alias][task]={m:b['tasks'][task][m]-a['tasks'][task][m] for m in ['strict_exact','normalized_exact','similarity','cer','normalized_cer']}
    ar={r['sample_id']:r for r in a['details'] if r['task']==task};br={r['sample_id']:r for r in b['details'] if r['task']==task}
    summary['comparisons'][alias][task]['paired_normalized_exact']={'improved':sum(not ar[k]['normalized_exact'] and br[k]['normalized_exact'] for k in ar),'regressed':sum(ar[k]['normalized_exact'] and not br[k]['normalized_exact'] for k in ar),'both_correct':sum(ar[k]['normalized_exact'] and br[k]['normalized_exact'] for k in ar),'both_incorrect':sum(not ar[k]['normalized_exact'] and not br[k]['normalized_exact'] for k in ar)}
  (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
  import csv
  with (OUT/'before_after_comparison.csv').open('w',encoding='utf-8-sig',newline='') as stream:
   writer=csv.writer(stream);writer.writerow(['model','task','metric','n','before','after','delta','unit'])
   for alias in ['qwen','hyperclova']:
    for task in ['h400_direct','h400_knowledge_image','ocr']:
     for metric in ['strict_exact','normalized_exact','similarity','cer']:
      a=summary['results'][f'{alias}_base']['tasks'][task][metric];b=summary['results'][f'{alias}_haechi']['tasks'][task][metric]
      writer.writerow([alias,task,metric,100,100*a,100*b,100*(b-a),'percent; delta in percentage points'])

