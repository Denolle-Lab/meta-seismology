"""Write study-design batches for the included papers of the database.

All included papers (shuffled with a fixed seed), or a stratified pilot sample
(--sample N, half from Nature/Science-family journals). Batch files are
written once and not overwritten.
"""
import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="SQLite database from build_db.py")
    p.add_argument("--out-dir", required=True, help=".../input directory")
    p.add_argument("--batch-size", type=int, default=60)
    p.add_argument("--sample", type=int, help="pilot sample size (stratified by journal tier)")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.glob("batch_*.jsonl")):
        raise SystemExit(f"{out} already has batches; not overwriting")
    con = sqlite3.connect(args.db)
    df = pd.read_sql("""SELECT s.doi, p.journal_key, p.publication_year, p.title, p.abstract, p.high_impact
                        FROM screening s JOIN papers p USING (doi) WHERE s.include""", con)
    if args.sample:
        half = args.sample // 2
        df = pd.concat([df[df.high_impact == 1].sample(half, random_state=args.seed),
                        df[df.high_impact == 0].sample(args.sample - half, random_state=args.seed)])
    df = df.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    cols = ["doi", "journal_key", "publication_year", "title", "abstract"]
    for b, start in enumerate(range(0, len(df), args.batch_size)):
        with open(out / f"batch_{b:03d}.jsonl", "w") as f:
            for rec in df.iloc[start:start + args.batch_size][cols].to_dict("records"):
                rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(df)} papers -> {b + 1} batches in {out}")


if __name__ == "__main__":
    main()
