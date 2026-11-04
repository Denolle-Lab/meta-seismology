"""Audit the collected corpus per journal and date window.

For each journal x window (taken from the raw directory names): OpenAlex
records vs Crossref journal-article count (completeness), article share,
abstract coverage of articles and of candidates, repository/duplicate DOIs,
and candidate share. Rows that miss a threshold are flagged so problems are
fixed by rules in config/, not by hand.
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests

CROSSREF = "https://api.crossref.org/works"


def crossref_count(issn, date_from, date_to, session):
    params = {"filter": f"issn:{issn},from-pub-date:{date_from},until-pub-date:{date_to},"
                        "type:journal-article", "rows": 0}
    for attempt in range(5):
        r = session.get(CROSSREF, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()["message"]["total-results"]
        time.sleep(2 ** attempt)
    r.raise_for_status()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="parquet from build_corpus.py")
    p.add_argument("--raw-dir", nargs="+", required=True, help="raw window dirs (<from>_<to>)")
    p.add_argument("--journals", required=True, help="config/journals.csv")
    p.add_argument("--no-crossref", action="store_true", help="skip Crossref counts")
    p.add_argument("--min-ratio", type=float, default=0.9,
                   help="flag if OpenAlex/Crossref count ratio is outside [min, 1/min]")
    p.add_argument("--min-abstract", type=float, default=0.9,
                   help="flag if abstract coverage of candidates is below this")
    p.add_argument("--out", required=True, help="output CSV")
    args = p.parse_args()

    journals = pd.read_csv(args.journals, dtype={"doi_prefix": str}).set_index("journal_key")
    df = pd.read_parquet(args.corpus)
    session = requests.Session()
    rows = []
    for d in args.raw_dir:
        date_from, date_to = Path(d).name.split("_")
        win = df[(df.publication_date >= date_from) & (df.publication_date <= date_to)]
        for jkey, j in journals.iterrows():
            g = win[win.journal_key == jkey]
            art = g[g.type == "article"]
            cand = g[g.candidate]
            row = {"journal_key": jkey, "window": Path(d).name, "openalex_works": len(g),
                   "articles": len(art),
                   "repository_doi": int((g.drop_reason == "repository_doi").sum()),
                   "duplicate_doi": int((g.drop_reason == "duplicate_doi").sum()),
                   "no_doi": int((g.drop_reason == "no_doi").sum()),
                   "abstract_cov_articles": art.has_abstract.mean() if len(art) else None,
                   "candidates": len(cand),
                   "candidate_share": len(cand) / len(art) if len(art) else None,
                   "abstract_cov_candidates": cand.has_abstract.mean() if len(cand) else None}
            if not args.no_crossref:
                row["crossref_articles"] = crossref_count(j.issn_l, date_from, date_to, session)
                n_doi = len(g) - row["repository_doi"] - row["no_doi"]
                row["openalex_crossref_ratio"] = (n_doi / row["crossref_articles"]
                                                  if row["crossref_articles"] else None)
                time.sleep(0.3)
            flags = []
            ratio = row.get("openalex_crossref_ratio")
            if ratio is not None and not args.min_ratio <= ratio <= 1 / args.min_ratio:
                flags.append("count_mismatch")
            if row["abstract_cov_candidates"] is not None and row["abstract_cov_candidates"] < args.min_abstract:
                flags.append("candidate_abstracts_missing")
            if row["repository_doi"] or row["duplicate_doi"]:
                flags.append("doi_anomalies")
            row["flags"] = ";".join(flags)
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)
    pd.set_option("display.width", 200)
    print(out.round(3).to_string(index=False))
    print(f"\nflagged rows: {(out['flags'] != '').sum()} / {len(out)} -> {args.out}")


if __name__ == "__main__":
    main()
