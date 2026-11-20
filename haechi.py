"""Download and run KETI HAECHI checkpoints. Physical GPU 3 only."""
import argparse
import os
from pathlib import Path
import sys

# Set before importing torch/transformers; cuda:0 below means physical GPU 3.
os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
os.environ['CUDA_VISIBLE_DEVICES'] = '3'
ROOT = Path(__file__).resolve().parent
MODELS = {
    'qwen': 'KETI-NLP/Qwen3.5-KETI-HAECHI-27B',
    'hyperclova': 'KETI-NLP/HyperCLOVA-X-KETI-HAECHI-32B',
}
SAMPLES = {
    'qwen': 'samples/qualitative/06_cheomseongdae.jpg',
    'hyperclova': 'samples/qualitative/01_gyeongbokgung_gyeonghoeru.jpg',
}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('download', 'run'):
        s = sub.add_parser(command)
        s.add_argument('--model', choices=MODELS, required=True)
        s.add_argument('--model-dir', type=Path, help='Local model directory (default: models/<alias>)')
        if command == 'download':
            s.add_argument('--revision', default='main', help='Hub branch, tag or commit SHA')
        else:
            s.add_argument('--prompt', default='한국의 국가유산에 대해 간단히 설명해 주세요.')
            image = s.add_mutually_exclusive_group()
            image.add_argument('--image', type=Path, help='Local image file')
            image.add_argument('--sample', action='store_true', help='Use downloaded model-card sample image')
            s.add_argument('--max-new-tokens', type=int, default=256)
            s.add_argument('--thinking', action='store_true')
    return p


def run(args, directory):
    if args.max_new_tokens < 1:
        raise ValueError('--max-new-tokens must be positive')
    if not (directory / 'config.json').is_file():
        raise ValueError(f'Model missing: {directory}. Run download first.')
    image_path = directory / SAMPLES[args.model] if args.sample else args.image
    if image_path:
        image_path = image_path.resolve()
        if not image_path.is_file():
            raise ValueError(f'Image missing: {image_path}')
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('GPU 3 is unavailable. Check nvidia-smi and CUDA-enabled PyTorch.')
    from transformers import AutoProcessor
    source = str(directory)
    print(f'GPU: physical 3 / logical cuda:0 ({torch.cuda.get_device_name(0)})', file=sys.stderr)
    if args.model == 'qwen':
        from transformers import AutoModelForMultimodalLM
        processor = AutoProcessor.from_pretrained(source, local_files_only=True)
        model = AutoModelForMultimodalLM.from_pretrained(
            source, dtype=torch.bfloat16, device_map={'': 0}, local_files_only=True,
        ).eval()
        content = []
        if image_path:
            content.append({'type': 'image', 'url': str(image_path)})
        content.append({'type': 'text', 'text': args.prompt})
        inputs = processor.apply_chat_template(
            [{'role': 'user', 'content': content}], add_generation_prompt=True,
            tokenize=True, return_dict=True, return_tensors='pt',
            enable_thinking=args.thinking,
        ).to(model.device)
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
        output = output[:, inputs['input_ids'].shape[1]:]
    else:
        from PIL import Image
        from transformers.dynamic_module_utils import get_class_from_dynamic_module
        processor = AutoProcessor.from_pretrained(
            source, trust_remote_code=True, use_fast=False, local_files_only=True,
        )
        model_class = get_class_from_dynamic_module(
            'modeling_vlm.HCXVisionForCausalLM', source, local_files_only=True,
        )
        # Model-card SDPA fallback: avoid requiring flash-attn on Ampere GPUs.
        sys.modules[model_class.__module__].is_ampere_or_newer = lambda: False
        config = model_class.config_class.from_pretrained(source, local_files_only=True)
        # The checkpoint retains an upstream Hub path in its nested text config.
        # Resolve its bundled custom language-model code from our local snapshot.
        config.text_config._name_or_path = source
        model = model_class.from_pretrained(
            source, config=config, dtype=torch.bfloat16, device_map={'': 0},
            low_cpu_mem_usage=True, local_files_only=True,
        ).eval()
        content = []
        if image_path:
            content.append({'type': 'image_url', 'image_url': {'url': str(image_path)}})
        content.append({'type': 'text', 'text': args.prompt})
        prompt = processor.apply_chat_template(
            [{'role': 'user', 'content': content}], tokenize=False,
            add_generation_prompt=True, thinking=args.thinking,
        )
        kwargs = {}
        if image_path:
            with Image.open(image_path) as image:
                kwargs['images'] = [image.convert('RGB')]
            kwargs.update(min_pixels=65_536, max_pixels=1_048_576)
        inputs = processor(text=[prompt], return_tensors='pt', **kwargs).to(model.device)
        with torch.inference_mode():
            if image_path:
                output = model.inference(
                    **inputs, max_length=args.max_new_tokens, min_length=0,
                    temperature=0.0, do_sample=False, use_cache=True,
                )
            else:
                # The custom multimodal inference() rejects pixel_values=None.
                # Text-only prompts go directly to the bundled language model.
                output = model.language_model.generate(
                    **inputs, max_new_tokens=args.max_new_tokens,
                    do_sample=False, use_cache=True,
                    pad_token_id=model.config.text_config.pad_token_id,
                    eos_token_id=model.config.text_config.eos_token_id,
                )
                output = output[:, inputs['input_ids'].shape[1]:]
    print(processor.batch_decode(output, skip_special_tokens=True)[0].strip())


def main():
    args = parser().parse_args()
    directory = (args.model_dir or ROOT / 'models' / args.model).resolve()
    if args.command == 'download':
        from huggingface_hub import snapshot_download
        # Entire repo: weights, processor, custom code and sample images.
        snapshot_download(repo_id=MODELS[args.model], revision=args.revision, local_dir=str(directory))
        print(directory)
    else:
        run(args, directory)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
