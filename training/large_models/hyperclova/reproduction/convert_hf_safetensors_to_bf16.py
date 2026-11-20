#!/usr/bin/env python3
"""Stream-convert a Hugging Face safetensors checkpoint to BF16."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file


WEIGHT_SUFFIX = ".safetensors"


def weight_files(source: Path) -> list[Path]:
    index_path = source / "model.safetensors.index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        return [source / name for name in sorted(set(index["weight_map"].values()))]
    single = source / "model.safetensors"
    if single.is_file():
        return [single]
    raise SystemExit(f"No safetensors weights found in {source}")
