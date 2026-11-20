from pathlib import Path
import json,hashlib,io,os
import pyarrow as pa,pyarrow.ipc as ipc
from PIL import Image,ImageOps
OUT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('HAECHI_DATA_SOURCE', 'data_sources'))
H=SOURCE/'downloaded_models/h400_representative_100x4_20260904'
if (OUT/'inputs.jsonl').exists() or (OUT/'answers.jsonl').exists():
 raise SystemExit('Archived evaluation inputs already exist; use a separate copy to rebuild them.')
(OUT/'images').mkdir(exist_ok=True)
inputs=[];gold=[]
def image_save(image,dest):
 image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((512,512),Image.Resampling.LANCZOS)
 image.save(dest,'PNG');return hashlib.sha256(dest.read_bytes()).hexdigest()
for task in ['h400_direct','h400_knowledge_image']:
 answers={r['sample_id']:r for r in map(json.loads,(H/'answer_keys'/f'{task}_100.jsonl').read_text().splitlines())}
 for r in map(json.loads,(H/'questions'/f'{task}_100.jsonl').read_text().splitlines()):
  content=r['messages'][0]['content'];im=next(x['image_url']['url'] for x in content if x['type']=='image_url')
  question=next(x['text'] for x in content if x['type']=='text');sid=r['sample_id'];dest=OUT/'images'/f'{sid}.png'
  with Image.open(H/im) as image:digest=image_save(image,dest)
  inputs.append({'sample_id':sid,'task':task,'image':str(dest),'image_sha256':digest,'question':question,'record_id':r['metadata']['record_id']})
  a=answers[sid];gold.append({'sample_id':sid,'task':task,'reference':a['reference_answer'],'supporting_facts':a.get('supporting_facts',[])})
arrow=SOURCE/'korean_heritage_eval_package/datasets/korean_character_ocr_test_hf/data-00000-of-00001.arrow'
t=ipc.open_stream(pa.memory_map(str(arrow),'r')).read_all()
for r in t.to_pylist():
 sid=r['sample_id'];dest=OUT/'images'/f'{sid}.png'
 with Image.open(io.BytesIO(r['images'][0]['bytes'])) as image:digest=image_save(image,dest)
 reference=next(m['content'] for m in r['messages'] if m['role']=='assistant')
 if reference.startswith('OCR:'):reference=reference[4:].strip()
 inputs.append({'sample_id':sid,'task':'ocr','image':str(dest),'image_sha256':digest,'question':'이미지에 보이는 한글 텍스트를 그대로 읽어 주세요. 설명 없이 인식한 문자열만 답하세요.'})
 gold.append({'sample_id':sid,'task':'ocr','reference':reference})
for name,rows in [('inputs.jsonl',inputs),('answers.jsonl',gold)]:
 (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
meta={'created':'2026-11-16','counts':{k:sum(r['task']==k for r in inputs) for k in ['h400_direct','h400_knowledge_image','ocr']},'max_image_edge':512,'h400_source':str(H),'ocr_source':str(arrow),'ocr_source_description':'실외 문자 OCR 테스트에서 복원된 기존 간이 평가 100건','h400_limitations':'H400 공통 문화유산 100개. 학습 데이터와 개체·이미지 중복이 없다는 독립 검증은 수행하지 않음. 지식 질문에는 유산 명칭이 포함됨.','inputs_sha256':hashlib.sha256((OUT/'inputs.jsonl').read_bytes()).hexdigest(),'answers_sha256':hashlib.sha256((OUT/'answers.jsonl').read_bytes()).hexdigest()}
(OUT/'dataset_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(meta,ensure_ascii=False,indent=2))
