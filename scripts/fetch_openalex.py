"""Download OpenAlex work records for each journal over a publication-date window.

Raw records are written once and never modified: one gzipped JSONL per journal
under <out-dir>/<from>_<to>/, plus a manifest with the query and retrieval time.
"""
import argparse
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API = "https://api.openalex.org/works"
FIELDS = [
    "id", "doi", "title", "publication_date", "publication_year", "type",
    "primary_location", "abstract_inverted_index", "cited_by_count",
    "authorships", "primary_topic", "is_retracted", "language", "biblio",
    "counts_by_year", "fwci", "citation_normalized_percentile",
    "cited_by_percentile_year", "referenced_works_count",
]


def fetch_source(source_id, date_from, date_to, session, api_key=None, work_type=None):
    """Yield all works of one source in the date window (optionally one OpenAlex type).

    Uses page-number paging (no key needed, max 10,000 results per query);
    cursor paging requires an OpenAlex API key.
    """
    params = {
        "filter": f"primary_location.source.id:{source_id},"
                  f"from_publication_date:{date_from},to_publication_date:{date_to}"
                  + (f",type:{work_type}" if work_type else ""),
        "select": ",".join(FIELDS),
        "per-page": 200,
        "page": 1,
    }
    if api_key:
        params["api_key"] = api_key
    while True:
        for attempt in range(5):
            r = session.get(API, params=params, timeout=60)
            if r.status_code == 200:
                break
            time.sleep(2 ** attempt)
        r.raise_for_status()
        data = r.json()
        yield from data["results"]
        if params["page"] * params["per-page"] >= data["meta"]["count"]:
            return
        params["page"] += 1
        time.sleep(0.2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--journals", required=True, help="config/journals.csv")
    p.add_argument("--from-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--to-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--out-dir", required=True, help="e.g. data/raw/openalex")
    p.add_argument("--only", nargs="*", help="subset of journal_key values")
    p.add_argument("--api-key", help="OpenAlex API key (optional)")
    p.add_argument("--type", help="OpenAlex work type filter, e.g. article (saves calls for journals with "
                                  "many news items; the corpus keeps only articles anyway)")
    args = p.parse_args()

    journals = pd.read_csv(args.journals)
    if args.only:
        journals = journals[journals.journal_key.isin(args.only)]
    out = Path(args.out_dir) / f"{args.from_date}_{args.to_date}"
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    for j in journals.itertuples():
        path = out / f"{j.journal_key}.jsonl.gz"
        old = out / f"{j.journal_key}.jsonl"  # uncompressed files from earlier runs
        if path.exists() or old.exists():
            print(f"skip {j.journal_key}: raw file exists (raw files are not overwritten)")
            continue
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
        tmp = out / f"{j.journal_key}.part"
        n = 0
        with gzip.open(tmp, "wt") as f:
            for rec in fetch_source(j.openalex_source_id, args.from_date, args.to_date,
                                    session, args.api_key, args.type):
                f.write(json.dumps(rec) + "\n")
                n += 1
        tmp.rename(path)
        print(f"{j.journal_key}: {n} works")
        with open(out / "manifest.jsonl", "a") as f:
            f.write(json.dumps({"journal_key": j.journal_key, "source_id": j.openalex_source_id,
                                "from_date": args.from_date, "to_date": args.to_date,
                                "type_filter": args.type, "n_works": n, "retrieved_utc": retrieved,
                                "file": path.name}) + "\n")


if __name__ == "__main__":
    main()
