"""Fetch abstracts from Semantic Scholar for corpus records lacking one.

Uses the batch endpoint (up to 500 DOIs per request). Output is a new raw
JSONL file (doi, abstract, s2 paperId, retrieval time); existing files are
never overwritten.
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API = "https://api.semanticscholar.org/graph/v1/paper/batch"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="parquet from build_corpus.py")
    p.add_argument("--out", required=True, help="output JSONL (must not exist)")
    p.add_argument("--types", nargs="*", default=["article"], help="OpenAlex types to query")
    args = p.parse_args()

    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} exists; raw files are not overwritten")
    df = pd.read_parquet(args.corpus)
    dois = df.loc[df.abstract.isna() & df.doi.notna() & df.type.isin(args.types), "doi"].unique().tolist()
    print(f"querying {len(dois)} DOIs")

    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_found = 0
    with open(out, "w") as f:
        for i in range(0, len(dois), 500):
            chunk = dois[i:i + 500]
            for attempt in range(6):
                r = requests.post(API, params={"fields": "abstract,externalIds"},
                                  json={"ids": [f"DOI:{d}" for d in chunk]}, timeout=120)
                if r.status_code == 200:
                    break
                time.sleep(5 * 2 ** attempt)
            r.raise_for_status()
            # Match results by DOI, not position: the response can be one short, which shifts
            # positions, and some records carry another paper's DOI and abstract.
            by_doi = {(((rec or {}).get("externalIds") or {}).get("DOI") or "").lower(): rec for rec in r.json()}
            for doi in chunk:
                rec = by_doi.get(doi.lower())
                abstract = (rec or {}).get("abstract")
                n_found += bool(abstract)
                f.write(json.dumps({"doi": doi, "abstract": abstract,
                                    "s2_paper_id": (rec or {}).get("paperId"),
                                    "retrieved_utc": retrieved}) + "\n")
            time.sleep(3)
    print(f"abstracts found: {n_found}/{len(dois)}")


if __name__ == "__main__":
    main()
