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
