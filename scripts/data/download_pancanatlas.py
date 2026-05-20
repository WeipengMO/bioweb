#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "data/tcga/pancanatlas/metadata/pancanatlas_registry.json"
PAGE_SNAPSHOT = ROOT / "data/tcga/pancanatlas/manifests/pancanatlas_publication_page.html"
DOWNLOAD_LOG = ROOT / "data/tcga/pancanatlas/metadata/download_log.jsonl"


def load_registry() -> dict:
    with REGISTRY_PATH.open() as handle:
        return json.load(handle)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path, *, overwrite: bool = False) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return {
            "target": str(target.relative_to(ROOT)),
            "status": "exists",
            "bytes": target.stat().st_size,
            "sha256": sha256sum(target),
        }

    temporary = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "BioWeb/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    temporary.replace(target)
    return {
        "target": str(target.relative_to(ROOT)),
        "status": "downloaded",
        "bytes": target.stat().st_size,
        "sha256": sha256sum(target),
    }


def write_log(record: dict) -> None:
    record = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **record}
    DOWNLOAD_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DOWNLOAD_LOG.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def download_page(registry: dict, overwrite: bool) -> None:
    result = download(registry["source_page"], PAGE_SNAPSHOT, overwrite=overwrite)
    write_log({"dataset": "source_page", **result})
    print(f"{result['status']}: {result['target']} ({result['bytes']} bytes)")


def download_dataset(registry: dict, name: str, overwrite: bool) -> None:
    datasets = registry["datasets"]
    if name not in datasets:
        valid = ", ".join(sorted(datasets))
        raise SystemExit(f"Unknown dataset '{name}'. Valid datasets: {valid}")
    spec = datasets[name]
    try:
        result = download(spec["url"], ROOT / spec["target"], overwrite=overwrite)
    except urllib.error.HTTPError as exc:
        write_log({"dataset": name, "target": spec["target"], "status": "failed", "error": str(exc)})
        raise
    write_log({"dataset": name, **result})
    print(f"{name}: {result['status']} {result['target']} ({result['bytes']} bytes)")


def selected_names(registry: dict, command: str, include_large: bool) -> list[str]:
    datasets = registry["datasets"]
    if command == "metadata":
        return registry["metadata_download"]
    if command == "core":
        return registry["core_download"]
    if command == "all-open":
        return [
            name
            for name, spec in datasets.items()
            if spec["access"] == "open" and (include_large or not spec.get("large", False))
        ]
    raise SystemExit(f"Unsupported command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download TCGA PanCanAtlas public data into data/tcga/pancanatlas.")
    parser.add_argument("command", choices=["metadata", "core", "all-open", "dataset"])
    parser.add_argument("dataset", nargs="?", help="Dataset key when command is 'dataset'.")
    parser.add_argument("--include-large", action="store_true", help="Allow large files when using all-open.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing files.")
    args = parser.parse_args(argv)

    registry = load_registry()
    if args.command == "dataset":
        if not args.dataset:
            raise SystemExit("dataset command requires a dataset key")
        download_dataset(registry, args.dataset, args.overwrite)
        return 0

    if args.command == "metadata":
        download_page(registry, args.overwrite)

    for name in selected_names(registry, args.command, args.include_large):
        download_dataset(registry, name, args.overwrite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
