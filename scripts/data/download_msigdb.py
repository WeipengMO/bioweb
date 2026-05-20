#!/usr/bin/env python3
"""Download MSigDB gene sets from OmniPath and save a normalized local table.

The output table uses the BioWeb gene-set contract:

- collection
- term
- gene
"""
#
# Usage:
#   python scripts/data/download_msigdb.py [--license academic|commercial|nonprofit] [--out-dir data/msigdb]
#
# The downloaded data is saved as a Parquet file for fast loading in analysis.
# This only needs to be run once, or when you want to refresh the gene sets.

import argparse
import os
from pathlib import Path


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

    parser = argparse.ArgumentParser(description="Download MSigDB gene sets")
    parser.add_argument(
        "--license",
        default="academic",
        choices=["academic", "commercial", "nonprofit"],
        help="License type for OmniPath data (default: academic)",
    )
    parser.add_argument(
        "--out-dir",
        default="data/msigdb",
        help="Output directory (default: data/msigdb)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "msigdb.parquet"

    print(f"Downloading MSigDB (license: {args.license})...")
    import decoupler as dc

    msigdb = dc.op.resource(name="MSigDB", license=args.license, verbose=True)
    msigdb = msigdb.rename(columns={"geneset": "term", "genesymbol": "gene"})
    msigdb = msigdb.loc[:, ["collection", "term", "gene"]]
    msigdb["gene"] = msigdb["gene"].astype(str).str.upper()
    msigdb = msigdb.dropna().drop_duplicates()
    msigdb.to_parquet(out_path)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"Saved to {out_path} ({size_mb:.1f} MB)")
    print(f"Gene sets: {msigdb['term'].nunique()}")
    print(f"Total entries: {len(msigdb)}")


if __name__ == "__main__":
    main()
