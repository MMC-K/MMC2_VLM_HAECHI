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
