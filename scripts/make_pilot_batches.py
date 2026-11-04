"""Draw a stratified pilot sample of candidates and split it into extraction batches.

Quotas per journal (journal_key=n) keep high-impact and specialty journals
represented; the sample DOIs are written to sample.csv so the pilot can be
reproduced. Batch files are written once and not overwritten.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="parquet from build_corpus.py")
    p.add_argument("--quota", nargs="+", required=True, help="journal_key=n pairs")
    p.add_argument("--out-dir", required=True, help="e.g. data/extraction/pilot")
    p.add_argument("--batch-size", type=int, default=40)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    out = Path(args.out_dir)
    inp = out / "input"
    inp.mkdir(parents=True, exist_ok=True)
    if any(inp.glob("batch_*.jsonl")):
        raise SystemExit(f"{inp} already has batches; not overwriting")
    df = pd.read_parquet(args.corpus)
    df = df[df.candidate]
    parts = []
    for q in args.quota:
        k, n = q.split("=")
        parts.append(df[df.journal_key == k].sample(int(n), random_state=args.seed))
    sample = pd.concat(parts).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    sample[["doi", "journal_key", "publication_year"]].to_csv(out / "sample.csv", index=False)
    cols = ["doi", "journal_key", "publication_year", "title", "abstract"]
    for b, start in enumerate(range(0, len(sample), args.batch_size)):
        with open(inp / f"batch_{b:03d}.jsonl", "w") as f:
            for rec in sample.iloc[start:start + args.batch_size][cols].to_dict("records"):
                rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(sample.journal_key.value_counts().to_string())
    print(f"{len(sample)} papers -> {b + 1} batches in {inp}")


if __name__ == "__main__":
    main()
