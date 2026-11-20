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
