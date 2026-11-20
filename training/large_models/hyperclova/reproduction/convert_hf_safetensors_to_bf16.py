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


