#!/usr/bin/env python3
"""Build and verify a generic ZIP64 release containing HF weights and reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from safetensors import safe_open


CHUNK_SIZE = 16 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def files_below(root: Path) -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for current, dirs, names in os.walk(root, followlinks=True):
        dirs.sort()
        names.sort()
        current_path = Path(current)
        for name in names:
            path = current_path / name
            files.append((path, path.relative_to(root)))
    return files


def verify_hf_model(model: Path) -> dict[str, object]:
    if not (model / "config.json").is_file():
        raise SystemExit(f"Missing config.json in {model}")
    index_path = model / "model.safetensors.index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        names = sorted(set(index["weight_map"].values()))
        expected_keys = set(index["weight_map"])
    elif (model / "model.safetensors").is_file():
        names = ["model.safetensors"]
        expected_keys = None
    else:
        raise SystemExit(f"No safetensors checkpoint in {model}")

    actual_keys: set[str] = set()
    dtypes: dict[str, int] = {}
    total_bytes = 0
    for name in names:
        path = model / name
        if not path.is_file():
            raise SystemExit(f"Missing indexed shard: {path}")
        total_bytes += path.stat().st_size
        with safe_open(path, framework="pt", device="cpu") as handle:
            for key in handle.keys():
                if key in actual_keys:
                    raise SystemExit(f"Duplicate tensor key: {key}")
                actual_keys.add(key)
                dtype = str(handle.get_slice(key).get_dtype())
                dtypes[dtype] = dtypes.get(dtype, 0) + 1
    if expected_keys is not None and actual_keys != expected_keys:
        raise SystemExit("Safetensors index key set does not match shard contents")
    return {
        "shard_count": len(names),
        "tensor_count": len(actual_keys),
        "weight_bytes": total_bytes,
        "dtypes": dtypes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-source", required=True, type=Path)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--training-step", required=True, type=int)
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    output = args.output.resolve()
    model_source = args.model_source.resolve()
    package_dir.mkdir(parents=True, exist_ok=True)
    model_link = package_dir / "model"
    if model_link.exists() or model_link.is_symlink():
        if model_link.is_symlink() or model_link.is_file():
            model_link.unlink()
        else:
            shutil.rmtree(model_link)
    model_link.symlink_to(model_source, target_is_directory=True)

    model_info = verify_hf_model(model_link)
    for generated in (package_dir / "PACKAGE_MANIFEST.json", package_dir / "SHA256SUMS"):
        generated.unlink(missing_ok=True)

    initial_payload = files_below(package_dir)
    manifest = {
        "package": package_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "format": "zip64",
        "model_name": args.model_name,
        "model_source": str(model_source),
        "official_base_model": args.base_model,
        "training_checkpoint": args.training_step,
        "model_validation": model_info,
        "payload_file_count_before_generated_metadata": len(initial_payload),
        "payload_bytes_before_generated_metadata": sum(
            path.stat().st_size for path, _ in initial_payload
        ),
    }
    (package_dir / "PACKAGE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    checksum_path = package_dir / "SHA256SUMS"
    with checksum_path.open("w", encoding="utf-8") as stream:
        for path, relative in files_below(package_dir):
            if relative == Path("SHA256SUMS"):
                continue
            stream.write(f"{sha256_file(path)}  {relative.as_posix()}\n")
            print(f"sha256 {relative}", flush=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
        for path, relative in files_below(package_dir):
            compression = (
                zipfile.ZIP_STORED
                if path.suffix in {".safetensors", ".bin", ".pt", ".pth", ".jpg", ".png"}
                else zipfile.ZIP_DEFLATED
            )
            archive.write(
                path,
                f"{package_dir.name}/{relative.as_posix()}",
                compress_type=compression,
                compresslevel=6,
            )
            print(f"zip {relative}", flush=True)
    temporary.replace(output)

    with zipfile.ZipFile(output, "r", allowZip64=True) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"ZIP CRC validation failed: {bad}")
        entries = len(archive.infolist())
    archive_hash = sha256_file(output)
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{archive_hash}  {output.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "archive": str(output),
                "archive_bytes": output.stat().st_size,
                "archive_sha256": archive_hash,
                "entries": entries,
                "zip_crc": "ok",
                "model_validation": model_info,
            },
            indent=2,
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
