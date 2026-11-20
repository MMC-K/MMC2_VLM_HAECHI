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


def copy_metadata(source: Path, destination: Path) -> None:
    for entry in sorted(source.iterdir()):
        if entry.name.startswith("model") and entry.name.endswith(WEIGHT_SUFFIX):
            continue
        if entry.name == "model.safetensors.index.json":
            continue
        target = destination / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True)
        elif entry.is_file():
            shutil.copy2(entry, target)


def convert_shard(source: Path, destination: Path) -> tuple[int, int]:
    tensors: dict[str, torch.Tensor] = {}
    converted = 0
    with safe_open(source, framework="pt", device="cpu") as handle:
        metadata = handle.metadata()
        for key in handle.keys():
            tensor = handle.get_tensor(key)
            if tensor.is_floating_point() and tensor.dtype != torch.bfloat16:
                tensor = tensor.to(torch.bfloat16)
                converted += 1
            tensors[key] = tensor.contiguous()
    save_file(tensors, destination, metadata=metadata)
    return len(tensors), converted


def inspect_checkpoint(root: Path) -> dict[str, object]:
    files = weight_files(root)
    dtypes: dict[str, int] = {}
    tensor_count = 0
    keys: set[str] = set()
    total_bytes = 0
    for path in files:
        total_bytes += path.stat().st_size
        with safe_open(path, framework="pt", device="cpu") as handle:
            for key in handle.keys():
                if key in keys:
                    raise RuntimeError(f"Duplicate tensor key: {key}")
                keys.add(key)
                tensor_count += 1
                dtype = str(handle.get_slice(key).get_dtype())
                dtypes[dtype] = dtypes.get(dtype, 0) + 1
    return {
        "shards": len(files),
        "tensors": tensor_count,
        "dtypes": dtypes,
        "weight_bytes": total_bytes,
        "keys": keys,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help="Keep already converted destination shards and finish index/verification.",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_dir():
        raise SystemExit(f"Missing source directory: {source}")
    if destination.exists() and any(destination.iterdir()) and not args.resume_existing:
        raise SystemExit(f"Destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    copy_metadata(source, destination)

    source_files = weight_files(source)
    for index, path in enumerate(source_files, start=1):
        target = destination / path.name
        if args.resume_existing and target.is_file():
            print(f"[{index}/{len(source_files)}] {path.name}: existing shard retained", flush=True)
            continue
        count, converted = convert_shard(path, target)
        print(
            f"[{index}/{len(source_files)}] {path.name}: "
            f"{count} tensors, {converted} converted to BF16",
            flush=True,
        )

    source_index = source / "model.safetensors.index.json"
    if source_index.is_file():
        index = json.loads(source_index.read_text(encoding="utf-8"))
        index.setdefault("metadata", {})["total_size"] = sum(
            (destination / path.name).stat().st_size for path in source_files
        )
        (destination / source_index.name).write_text(
            json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    source_info = inspect_checkpoint(source)
    target_info = inspect_checkpoint(destination)
    if source_info["keys"] != target_info["keys"]:
        raise SystemExit("Tensor-key verification failed")
    if target_info["dtypes"] != {"BF16": target_info["tensors"]}:
        raise SystemExit(f"Unexpected destination dtypes: {target_info['dtypes']}")

    provenance = {
        "conversion": "floating tensors converted to torch.bfloat16 shard by shard",
        "source": str(source),
        "destination": str(destination),
        "source_shards": source_info["shards"],
        "destination_shards": target_info["shards"],
        "tensor_count": target_info["tensors"],
        "source_dtypes": source_info["dtypes"],
        "destination_dtypes": target_info["dtypes"],
        "source_weight_bytes": source_info["weight_bytes"],
        "destination_weight_bytes": target_info["weight_bytes"],
    }
    (destination / "BF16_CONVERSION_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(provenance, indent=2, ensure_ascii=False), flush=True)
