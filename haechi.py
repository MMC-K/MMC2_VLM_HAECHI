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


