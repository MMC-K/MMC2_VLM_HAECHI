import os
os.environ['CUDA_DEVICE_ORDER']='PCI_BUS_ID';os.environ['CUDA_VISIBLE_DEVICES']='3'
import torch,json,time
from pathlib import Path
from safetensors import safe_open
from transformers import AutoProcessor
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
r=json.loads((OUT/'inputs.jsonl').read_text().splitlines()[0]);p=AutoProcessor.from_pretrained(str(ROOT/'models/qwen'),local_files_only=True)
i=p.apply_chat_template([{'role':'user','content':[{'type':'image','url':r['image']},{'type':'text','text':r['question']}]}],add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt',enable_thinking=False,processor_kwargs={'images_kwargs':{'min_pixels':65536,'max_pixels':262144}})
x=i['pixel_values'].to(device='cuda',dtype=torch.bfloat16).reshape(-1,3,2,16,16)
rows=[]
for name,source in [('base',Path('/mnt/nfs5/byunggill/2026_llm_data_generation/__kubeflow-training-snippets/downloaded_models/Qwen3.5-27B')),('haechi',ROOT/'models/qwen')]:
 index=source/'model.safetensors.index.json';key='model.visual.patch_embed.proj.weight'
 file=source/json.loads(index.read_text())['weight_map'][key] if index.exists() else source/'model.safetensors'
 with safe_open(str(file),framework='pt',device='cpu') as weights:
  w=weights.get_tensor(key).to(device='cuda',dtype=torch.bfloat16);b=weights.get_tensor('model.visual.patch_embed.proj.bias').to(device='cuda',dtype=torch.bfloat16)
 with torch.inference_mode():
  torch.cuda.synchronize();start=time.perf_counter();a=F.conv3d(x,w,b,stride=(2,16,16));torch.cuda.synchronize();conv_s=time.perf_counter()-start
  start=time.perf_counter();c=F.linear(x.flatten(1),w.flatten(1),b).reshape(x.shape[0],w.shape[0],1,1,1);torch.cuda.synchronize();linear_s=time.perf_counter()-start
 assert torch.allclose(a,c,atol=.025,rtol=.025), (a-c).abs().max().item()
 result={'stage':name,'max_absolute_difference':(a-c).abs().max().item(),'conv3d_seconds':conv_s,'linear_seconds':linear_s,'exactly_equal_fraction':(a==c).float().mean().item()};rows.append(result);print(result,flush=True)
(OUT/'patch_projection_equivalence.json').write_text(json.dumps(rows,indent=2)+'\n')
