"""Paired base/HAECHI evaluation; run one process at a time on physical GPU 3."""
import os
os.environ['CUDA_DEVICE_ORDER']='PCI_BUS_ID'
os.environ['CUDA_VISIBLE_DEVICES']='3'
import argparse,json,time,hashlib,sys,traceback
from pathlib import Path
from datetime import datetime,timezone,timedelta
P=argparse.ArgumentParser();P.add_argument('--model',choices=['qwen','hyperclova'],required=True);P.add_argument('--stage',choices=['base','haechi'],required=True);P.add_argument('--limit',type=int);P.add_argument('--inputs',type=Path);P.add_argument('--output-tag',default='');args=P.parse_args()
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
BASE=Path(os.environ.get('HAECHI_BASE_MODELS', str(ROOT/'base_models')))
source=(BASE/('Qwen3.5-27B' if args.model=='qwen' else 'HyperCLOVAX-SEED-Think-32B')) if args.stage=='base' else ROOT/'models'/args.model
shared=ROOT/'models'/args.model
label=f'{args.model}_{args.stage}'+('_'+args.output_tag if args.output_tag else '');predpath=OUT/f'{label}_predictions.jsonl';metapath=OUT/f'{label}_run.json'
input_file=args.inputs or OUT/'inputs.jsonl'
rows=[json.loads(x) for x in input_file.read_text().splitlines()]
# Archived inputs retain their original absolute paths and hashes. Resolve images locally.
for row in rows:
 if not Path(row['image']).is_file():row['image']=str(OUT/'images'/Path(row['image']).name)
if args.limit:rows=rows[:args.limit];predpath=OUT/f'{label}_smoke_predictions.jsonl';metapath=OUT/f'{label}_smoke_run.json'
if args.model=='qwen' and (OUT/'runtime_kernels').is_dir():
 sys.path.insert(0,str(OUT/'runtime_kernels'))
import torch
from PIL import Image
from transformers import AutoProcessor
import transformers
torch.set_num_threads(8)
assert torch.cuda.device_count()==1,'Exactly physical GPU 3 must be exposed'
start=time.perf_counter()
processor=AutoProcessor.from_pretrained(str(shared),local_files_only=True,**({'trust_remote_code':True,'use_fast':False} if args.model=='hyperclova' else {}))
# Same processor/template inside each base-vs-trained pair. Weights stay unchanged.
if args.model=='qwen':
 from transformers import AutoModelForMultimodalLM
 model=AutoModelForMultimodalLM.from_pretrained(str(source),dtype=torch.bfloat16,device_map={'':0},local_files_only=True).eval()
 # Each input is exactly one convolution kernel-sized patch. F.linear is
 # algebraically equivalent and avoids the slow cuDNN Conv3d path on this node.
 import types
 import torch.nn.functional as F
 projection=model.model.visual.patch_embed.proj
 assert projection.groups==1 and tuple(projection.padding)==(0,0,0) and tuple(projection.dilation)==(1,1,1)
 def patch_projection(conv,x):
  assert tuple(x.shape[-3:])==tuple(conv.kernel_size)
  return F.linear(x.flatten(1),conv.weight.flatten(1),conv.bias).reshape(x.shape[0],conv.out_channels,1,1,1)
 projection.forward=types.MethodType(patch_projection,projection)
else:
 from transformers.dynamic_module_utils import get_class_from_dynamic_module
 cls=get_class_from_dynamic_module('modeling_vlm.HCXVisionForCausalLM',str(shared),local_files_only=True)
 sys.modules[cls.__module__].is_ampere_or_newer=lambda:False
 config=cls.config_class.from_pretrained(str(source),local_files_only=True)
 config.text_config._name_or_path=str(shared)
 model=cls.from_pretrained(str(source),config=config,dtype=torch.bfloat16,device_map={'':0},low_cpu_mem_usage=True,local_files_only=True).eval()
torch.cuda.synchronize();load_s=time.perf_counter()-start
meta={'model':args.model,'stage':args.stage,'source':str(source),'runtime_and_processor':str(shared),'torch':torch.__version__,'transformers':transformers.__version__,'physical_gpu':3,'gpu_name':torch.cuda.get_device_name(0),'load_seconds':load_s,'dtype':'bfloat16','thinking':False,'sampling':False,'max_image_edge':512,'min_pixels':65536,'max_pixels':262144,'cpu_threads':8,'budgets':{'h400_direct':64,'h400_knowledge_image':128,'ocr':128},'inputs_sha256':hashlib.sha256(input_file.read_bytes()).hexdigest(),'started':datetime.now(timezone(timedelta(hours=9))).isoformat(),'status':'running'}
if args.model=='qwen':
 meta['patch_projection']='equivalent_linear; unchanged weights; BF16 equivalence validated'
 import importlib.metadata
 try:meta['flash_linear_attention']=importlib.metadata.version('flash-linear-attention')
 except importlib.metadata.PackageNotFoundError:meta['flash_linear_attention']=None
 try:meta['causal_conv1d']=importlib.metadata.version('causal-conv1d')
 except importlib.metadata.PackageNotFoundError:meta['causal_conv1d']=None
modelconfig=source/'config.json';meta['config_sha256']=hashlib.sha256(modelconfig.read_bytes()).hexdigest()
metadata=source/'.cache/huggingface/download/config.json.metadata'
if metadata.exists():meta['download_config_metadata']=metadata.read_text().splitlines()[:2]
metapath.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('LOADED',label,round(load_s,2),'s',flush=True)

def infer(r,measure=True):
 begin=time.perf_counter()
 if args.model=='qwen':
  content=[{'type':'image','url':r['image']},{'type':'text','text':r['question']}]
  inputs=processor.apply_chat_template([{'role':'user','content':content}],add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt',enable_thinking=False,processor_kwargs={'images_kwargs':{'min_pixels':65536,'max_pixels':262144}}).to(model.device)
 else:
  content=[{'type':'image_url','image_url':{'url':r['image']}},{'type':'text','text':r['question']}]
  prompt=processor.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=True,thinking=False)
  with Image.open(r['image']) as im:image=im.convert('RGB')
  inputs=processor(text=[prompt],images=[image],min_pixels=65536,max_pixels=262144,return_tensors='pt').to(model.device)
 torch.cuda.synchronize();preprocess_s=time.perf_counter()-begin;torch.cuda.reset_peak_memory_stats(0)
 begin=time.perf_counter();budget=meta['budgets'][r['task']]
 with torch.inference_mode():
  if args.model=='qwen':
   ids=model.generate(**inputs,max_new_tokens=budget,do_sample=False,use_cache=True)
   ids=ids[:,inputs['input_ids'].shape[1]:]
  else:
   ids=model.inference(**inputs,max_length=budget,min_length=0,temperature=0.0,do_sample=False,use_cache=True)
 torch.cuda.synchronize();elapsed=time.perf_counter()-begin
 result={'sample_id':r['sample_id'],'task':r['task'],'prediction':processor.batch_decode(ids,skip_special_tokens=True)[0].strip(),'generated_tokens':int(ids.shape[-1]),'input_tokens':int(inputs['input_ids'].shape[-1]),'generation_seconds':elapsed,'preprocess_seconds':preprocess_s,'peak_allocated_gib':torch.cuda.max_memory_allocated(0)/1024**3,'peak_reserved_gib':torch.cuda.max_memory_reserved(0)/1024**3,'hit_token_budget':ids.shape[-1]>=budget,'error':None}
 return result
# Identical unscored warm-up: shape and kernel initialization excluded from steady-state timings.
warm_start=time.perf_counter();infer(rows[0],measure=False);meta['warmup_seconds']=time.perf_counter()-warm_start
existing={}
if predpath.exists():
 for line in predpath.read_text().splitlines():
  if line.strip():r=json.loads(line);existing[r['sample_id']]=r
print('WARMED',label,'resume',len(existing),flush=True)
with predpath.open('a',buffering=1) as stream:
 for i,r in enumerate(rows,1):
  if r['sample_id'] in existing:continue
  try:result=infer(r)
  except Exception as exc:
   result={'sample_id':r['sample_id'],'task':r['task'],'prediction':'','error':str(exc),'traceback':traceback.format_exc()}
   torch.cuda.empty_cache()
  stream.write(json.dumps(result,ensure_ascii=False)+'\n');stream.flush()
  if i%5==0 or result['error']:print(label,i,'/',len(rows),'sec',round(result.get('generation_seconds',0),2),'answer',result['prediction'][:90],'ERROR',result['error'],flush=True)
meta['status']='completed';meta['finished']=datetime.now(timezone(timedelta(hours=9))).isoformat();meta['expected_count']=len(rows)
metapath.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('COMPLETE',label,len(rows),flush=True)
