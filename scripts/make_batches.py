"""Split prefiltered candidates into extraction batches.

Candidates are shuffled with a fixed seed so each batch mixes journals;
batch files are written once and not overwritten.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="parquet from build_corpus.py")
    p.add_argument("--out-dir", required=True, help="e.g. data/extraction/2021-2025/input")
    p.add_argument("--batch-size", type=int, default=40)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.glob("batch_*.jsonl")):
        raise SystemExit(f"{out} already has batches; not overwriting")
    df = pd.read_parquet(args.corpus)
    df = df[df.candidate].sample(frac=1, random_state=args.seed).reset_index(drop=True)
    cols = ["doi", "journal_key", "publication_year", "title", "abstract"]
    for b, start in enumerate(range(0, len(df), args.batch_size)):
        chunk = df.iloc[start:start + args.batch_size][cols]
        with open(out / f"batch_{b:03d}.jsonl", "w") as f:
            for rec in chunk.to_dict("records"):
                rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(df)} candidates -> {b + 1} batches in {out}")


if __name__ == "__main__":
    main()
