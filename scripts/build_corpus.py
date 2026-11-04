"""Build the candidate corpus from raw OpenAlex (and optional Semantic Scholar) records.

Reconstructs abstracts, normalizes DOIs, and applies a high-recall keyword
prefilter. Every record is kept with the reason it was dropped, so the
prefilter can be audited and changed later.

Prefilters: a built-in pattern (earthquake-source terms only), or a JSON file
(--prefilter) with 'strong' terms, plus 'weak' terms that count only together
with a 'context' term.

Extra sources (--extra-sources): raw files of another OpenAlex source that holds
one journal's older papers (e.g., pre-2014 JGR, filed as one source for all
sections). Their records are assigned to 'maps_to' and kept only when the DOI
matches 'doi_regex'; records of other sections are not part of the corpus.
"""
import argparse
import gzip
import html
import json
import re
from pathlib import Path

import pandas as pd

# High-recall terms; the LLM screening step makes the actual inclusion decision.
PREFILTER = re.compile(
    r"earthquake|quake|seism|aftershock|foreshock|mainshock|main shock|tremor|"
    r"slow slip|focal mechanism|moment tensor|source time function|stress drop|"
    r"corner frequenc|ground[- ]motion|co-?seismic|tsunami|rupture|fault slip|"
    r"nuclear (?:test|explosion)|rockburst|acoustic emission|"
    r"distributed acoustic sensing",
    re.IGNORECASE,
)
KEEP_TYPES = {"article"}


# Real HTML/JATS tags only: a literal "<" in "M < 3 ... > 2" must survive.
TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9:_.-]*(?:\s[^<>]*)?/?>")


def rebuild_abstract(inv):
    """Turn an OpenAlex abstract_inverted_index into plain text."""
    if not inv:
        return None
    pos = {i: w for w, idx in inv.items() for i in idx}
    text = " ".join(pos[i] for i in sorted(pos))
    # Strip tags, unescape, then strip tags that were escaped (&lt;i&gt;).
    text = html.unescape(TAG.sub(" ", html.unescape(TAG.sub(" ", text))))
    return re.sub(r"\s+", " ", text).strip() or None


def norm_doi(doi):
    if not doi:
        return None
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip()).lower()


def load_prefilter(path):
    """Return a function text -> sorted list of matched terms ('' if not a candidate)."""
    if path is None:
        return lambda t: sorted({m.group(0).lower() for m in PREFILTER.finditer(t)})
    cfg = json.load(open(path))
    pats = {k: re.compile("|".join(f"(?:{x})" for x in cfg[k]), re.IGNORECASE)
            for k in ("strong", "weak", "context")}

    def hits(t):
        strong = {m.group(0).lower() for m in pats["strong"].finditer(t)}
        weak = {m.group(0).lower() for m in pats["weak"].finditer(t)}
        if strong or (weak and pats["context"].search(t)):
            return sorted(strong | weak)
        return []
    return hits


def load_openalex(raw_dir, journal_keys):
    manifest = {}
    for line in open(raw_dir / "manifest.jsonl"):
        m = json.loads(line)
        manifest[m["journal_key"]] = m["retrieved_utc"]
    rows = []
    for path in sorted(raw_dir.glob("*.jsonl*")):
        jkey = path.name.split(".")[0]
        if jkey not in journal_keys:
            continue
        for line in (gzip.open(path, "rt") if path.suffix == ".gz" else open(path)):
            r = json.loads(line)
            topic = r.get("primary_topic") or {}
            pct = r.get("citation_normalized_percentile") or {}
            rows.append({
                "doi": norm_doi(r.get("doi")),
                "openalex_id": r["id"].rsplit("/", 1)[-1],
                "journal_key": jkey,
                "title": re.sub(r"<[^>]+>", "", r.get("title") or "").strip(),
                "abstract": rebuild_abstract(r.get("abstract_inverted_index")),
                "publication_date": r.get("publication_date"),
                "publication_year": r.get("publication_year"),
                "type": r.get("type"),
                "cited_by_count": r.get("cited_by_count"),
                "counts_by_year": json.dumps(r["counts_by_year"]) if "counts_by_year" in r else None,
                "fwci": r.get("fwci"),
                "citation_pct": pct.get("value"),
                "referenced_works_count": r.get("referenced_works_count"),
                "is_retracted": r.get("is_retracted"),
                "language": r.get("language"),
                "oa_topic": topic.get("display_name"),
                "oa_subfield": (topic.get("subfield") or {}).get("display_name"),
                "retrieved_utc": manifest.get(jkey),
            })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-dir", nargs="+", required=True, help="data/raw/openalex/<from>_<to> (one or more)")
    p.add_argument("--journals", required=True,
                   help="config/journals.csv; raw files of journals not listed are ignored")
    p.add_argument("--s2", nargs="*", default=[], help="Semantic Scholar abstract JSONL files")
    p.add_argument("--prefilter", help="prefilter JSON, e.g. config/prefilter.json (default: built-in pattern)")
    p.add_argument("--extra-sources", help="config/openalex_extra_sources.csv (optional)")
    p.add_argument("--out", required=True, help="output parquet path")
    args = p.parse_args()

    journals = pd.read_csv(args.journals, dtype={"doi_prefix": str})
    extra = pd.read_csv(args.extra_sources) if args.extra_sources else pd.DataFrame(columns=["journal_key"])
    df = pd.concat([load_openalex(Path(d), set(journals.journal_key) | set(extra.journal_key)) for d in args.raw_dir],
                   ignore_index=True)
    for e in extra.itertuples():
        own = df.journal_key == e.journal_key
        keep = own & df.doi.fillna("").str.match(e.doi_regex)
        print(f"{e.journal_key}: {int(keep.sum())} of {int(own.sum())} records kept as {e.maps_to}")
        df = df[~own | keep]
        df.loc[df.journal_key == e.journal_key, "journal_key"] = e.maps_to
    df = df.reset_index(drop=True)
    df["abstract_source"] = df.abstract.notna().map({True: "openalex", False: None})

    s2 = {}
    for path in args.s2:
        for line in open(path):
            r = json.loads(line)
            if r.get("abstract"):
                s2[r["doi"]] = r["abstract"].strip()
    fill = df.abstract.isna() & df.doi.isin(s2)
    df.loc[fill, "abstract"] = df.loc[fill, "doi"].map(s2)
    df.loc[fill, "abstract_source"] = "s2"

    text = df.title.fillna("") + " " + df.abstract.fillna("")
    hits = load_prefilter(args.prefilter)
    df["prefilter_hits"] = text.map(lambda t: ";".join(hits(t)))
    # Title-only records in Earth-science topics stay candidates (OpenAlex lacks many
    # Nature-family abstracts); the LLM screens them from the title.
    cfg = json.load(open(args.prefilter)) if args.prefilter else {}
    net = df.abstract.isna() & (df.prefilter_hits == "") & df.oa_subfield.isin(cfg.get("no_abstract_subfields", []))
    df.loc[net, "prefilter_hits"] = "topic:" + df.loc[net, "oa_subfield"]
    # Seismology-only journals: every record goes to screening.
    net = (df.prefilter_hits == "") & df.journal_key.isin(cfg.get("all_candidates_journals", []))
    df.loc[net, "prefilter_hits"] = "journal:all"
    df["has_abstract"] = df.abstract.notna()

    reason = pd.Series(None, index=df.index, dtype=object)
    reason[df.prefilter_hits == ""] = "no_keyword"
    reason[~df.type.isin(KEEP_TYPES)] = "type:" + df.type.astype(str)
    # Repository copies (RWTH, Zenodo, ...) that OpenAlex files under the journal. Earlier
    # publisher DOI formats (doi_extra_regex: GJI 10.1111/10.1046 before 2013, AGU 10.1002 in
    # 2013-2018) belong to the journal.
    prefix = df.journal_key.map(dict(zip(journals.journal_key, journals.doi_prefix)))
    alt = df.journal_key.map(dict(zip(journals.journal_key, journals.get("doi_extra_regex", pd.Series(dtype=str)))))
    own = (df.doi.str.split("/").str[0] == prefix) | pd.Series(
        [isinstance(a, str) and isinstance(d, str) and bool(re.match(a, d)) for a, d in zip(alt, df.doi)], index=df.index)
    reason[~own] = "repository_doi"
    reason[df.doi.isna()] = "no_doi"
    reason[df.doi.duplicated(keep="first") & df.doi.notna()] = "duplicate_doi"
    df["drop_reason"] = reason
    df["candidate"] = reason.isna()

    df.to_parquet(args.out, index=False)
    summ = df.groupby("journal_key").agg(
        works=("doi", "size"), articles=("type", lambda s: (s == "article").sum()),
        abstract=("has_abstract", "sum"), candidates=("candidate", "sum"),
        cand_no_abstract=("candidate", lambda s: (s & ~df.loc[s.index, "has_abstract"]).sum()))
    print(summ.to_string())
    print("total candidates:", int(df.candidate.sum()))


if __name__ == "__main__":
    main()
