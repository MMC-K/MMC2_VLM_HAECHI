from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=json.loads((ROOT/'summary.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(11.2,3.5),constrained_layout=True)
for ax,(task,metric,title) in zip(axes,[('h400_direct','normalized_exact','Heritage name EM'),('ocr','normalized_exact','Korean OCR EM'),('h400_knowledge_image','similarity','Knowledge response similarity')]):
 for stage,offset,color,label in [('base',-.18,'#7B8FA8','Before training'),('haechi',.18,'#1868A5','HAECHI')]:
  values=[100*s['results'][f'{alias}_{stage}']['tasks'][task][metric] for alias in ['qwen','hyperclova']]
  xs=[i+offset for i in range(2)]
  ax.bar(xs,values,width=.34,color=color,label=label)
  if metric=='normalized_exact':
   lo=[];hi=[]
   for alias,v in zip(['qwen','hyperclova'],values):
    ci=s['results'][f'{alias}_{stage}']['tasks'][task]['normalized_exact_ci95'];lo.append(max(0,v-100*ci[0]));hi.append(max(0,100*ci[1]-v))
   ax.errorbar(xs,values,yerr=[lo,hi],fmt='none',ecolor='#444444',capsize=3,linewidth=.8)
  for index,(x,v) in enumerate(zip(xs,values)):
   label_y=(100*s['results'][f'{["qwen","hyperclova"][index]}_{stage}']['tasks'][task]['normalized_exact_ci95'][1]+2) if metric=='normalized_exact' else v+2
   ax.text(x,label_y,f'{v:.1f}',ha='center',fontsize=8)
 ax.set_xticks([0,1],['Qwen 27B','HyperCLOVA 32B'],fontsize=8)
 ax.set_ylim(0,108);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel('%');ax.set_title(title,fontsize=10)
 ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axes[0].legend(loc='upper left',fontsize=8,frameon=False)
(ROOT/'figures').mkdir(exist_ok=True)
fig.savefig(ROOT/'figures/training_comparison.png',dpi=200)
fig.savefig(ROOT/'figures/training_comparison.pdf')
plt.close(fig)
