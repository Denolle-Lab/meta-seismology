"""Assemble the SQLite database (seismic source and structure studies).

Fully derived and rebuilt from scratch on every run: corpus parquet files,
extraction and study-design outputs, and config tables (journals, JIF
(optional), vocabulary, method groups, corrections).

Tables
  journals                 journal list + OpenAlex metrics + JIF + high_impact flag
  papers                   every retrieved work (abstracts kept for candidates only),
                           with citations per year since publication
  screening                one row per extracted paper (include, targets, study type)
  paper_links              source-structure link types (papers with both targets)
  paper_source_types       (doi, source_type)
  networks                 one row per observation network described in an abstract
  network_sensor_types     (net_id, sensor_type)
  network_environments     (net_id, environment)
  method_uses              one row per method use + derived magnitude class/node
  method_use_data_types, method_use_source_types, method_use_distances,
  method_use_networks      long tables keyed by use_id
  vocab                    controlled vocabulary (axis, value, label, side, definition)
  method_groups            method_short -> method_group -> method_family (if provided)
  study_design             one row per included paper from the study-design pass
                           (contribution, spatial scope, time design, study area; if given)
  design_data_origins, design_tectonic_settings, design_focal_events
                           long tables keyed by doi
  paper_concepts           long table (doi, axis, value, use_id, net_id): the
                           knowledge-graph incidence list, included papers only
Views
  v_paper_concepts         distinct (paper, axis, value) with year, journal, citations
  v_concept_pairs          concept pairs co-occurring in a paper
"""
import argparse
import bisect
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd

USE_LISTS = {"data_types": "data_type", "source_types": "source_type",
             "distance_regimes": "distance", "network_refs": "net_index"}


def derive_magnitude(m, offset):
    """Representative magnitude, the rule used, and an 'unclear' flag."""
    lo, hi, ms = (None if pd.isna(m[k]) else float(m[k]) for k in ("mag_min", "mag_max", "mainshock_mag"))
    if m["mag_relation"] == "mainshock_reference" and ms is not None:
        rep, rule = ms - offset, f"mainshock_minus_{offset:g}"
    elif lo is not None and hi is not None:
        rep, rule = (lo + hi) / 2, "single" if lo == hi else "range_mid"
    elif lo is not None:
        rep, rule = lo, "lower_bound"
    elif hi is not None:
        rep, rule = hi, "upper_bound"
    else:
        rep, rule = None, "none"
    unclear = not (m["mag_clarity"] == "explicit" and m["mag_relation"] == "direct"
                   and not m["mag_ambiguous"])
    return rep, rule, unclear


MAG_CLASSES = ["micro", "small", "moderate", "large", "great"]


def classify_magnitude(m, edges):
    """Magnitude class from mag_rep (numeric) or the verbal descriptor, with its source label.

    Sources: numeric_abstract (number stated for the analyzed events),
    numeric_estimated (mainshock - offset or external knowledge),
    qualitative (verbal descriptor only), none.
    A verbal descriptor overrides a mainshock - offset estimate, because it
    describes the analyzed events themselves.
    """
    rep, qual = m["mag_rep"], m["mag_qualitative"]
    qual = None if pd.isna(qual) else qual
    estimated = m["mag_rep_rule"].startswith("mainshock_minus") or m["mag_clarity"] == "external_knowledge"
    if pd.notna(rep) and not (qual and m["mag_rep_rule"].startswith("mainshock_minus")):
        return MAG_CLASSES[bisect.bisect_right(edges, rep)], \
            "numeric_estimated" if estimated else "numeric_abstract"
    if qual:
        return qual, "qualitative"
    return None, "none"


def parse_value(v):
    """Corrections CSV values: 'null' -> None, true/false -> bool, numbers -> float."""
    if pd.isna(v) or v == "null":
        return None
    if v in ("true", "false"):
        return v == "true"
    try:
        return float(v)
    except ValueError:
        return v


def load_extractions(dirs):
    """Long tables from extraction outputs. A DOI extracted again in a later batch (e.g., a
    re-extraction batch after an input fix) replaces its earlier record."""
    latest = {}
    for d in dirs:
        d = Path(d)
        for path in sorted(d.glob("batch_*.jsonl")):
            for line in open(path):
                if line.strip():
                    r = json.loads(line)
                    if r["doi"] in latest:
                        print(f"{r['doi']}: {latest[r['doi']][1].name} replaced by {path.name}")
                    latest[r["doi"]] = (d, path, r)
    t = {k: [] for k in ("screening", "links", "source_types", "networks", "sensors", "envs",
                         "uses", "data_types", "use_source_types", "distances", "use_networks")}
    for d, path, r in latest.values():
        version = d.parts[-3] if len(d.parts) >= 3 else str(d)
        doi = r["doi"]
        tg = r["targets"]
        t["screening"].append({
            **{k: r[k] for k in ("doi", "include", "include_confidence", "exclusion_reason",
                                 "screen_note", "study_type", "uses_real_data", "link_note")},
            "targets": ";".join(sorted(tg)),
            "target_class": None if not tg else ("both" if len(tg) == 2 else tg[0]),
            "extraction_version": version, "batch": f"{d.parent.name}/{path.stem}"})
        t["links"] += [{"doi": doi, "link_type": x} for x in r["source_structure_links"]]
        t["source_types"] += [{"doi": doi, "source_type": x} for x in r["source_types"]]
        for k, n in enumerate(r["networks"]):
            net_id = f"{doi}#n{k}"
            t["networks"].append({"net_id": net_id, "doi": doi, "net_index": k,
                                  **{c: v for c, v in n.items()
                                     if c not in ("sensor_types", "environments")}})
            t["sensors"] += [{"net_id": net_id, "sensor_type": x} for x in n["sensor_types"]]
            t["envs"] += [{"net_id": net_id, "environment": x} for x in n["environments"]]
        for i, m in enumerate(r["method_uses"]):
            use_id = f"{doi}#{i}"
            t["uses"].append({"use_id": use_id, "doi": doi, "use_index": i,
                              **{c: v for c, v in m.items() if c not in USE_LISTS}})
            t["data_types"] += [{"use_id": use_id, "data_type": x} for x in m["data_types"]]
            t["use_source_types"] += [{"use_id": use_id, "source_type": x}
                                      for x in m["source_types"]]
            t["distances"] += [{"use_id": use_id, "distance": x} for x in m["distance_regimes"]]
            t["use_networks"] += [{"use_id": use_id, "net_id": f"{doi}#n{x}"}
                                  for x in m["network_refs"]]
    return {k: pd.DataFrame(v) for k, v in t.items()}


GENERIC_EVENT_WORDS = re.compile(r"\b(earthquakes?|sequences?|eruptions?|unrest|swarms?|mainshocks?)\b", re.I)
# Letters that NFKD does not decompose, plus dashes and quotes, mapped before ASCII folding.
PRE_FOLD = str.maketrans({"ð": "d", "Ð": "D", "þ": "th", "Þ": "Th", "ı": "i", "ø": "o", "Ø": "O",
                          "æ": "ae", "ß": "ss", "–": "-", "—": "-", "‘": "'", "’": "'"})


def to_ascii(name):
    return unicodedata.normalize("NFKD", name.translate(PRE_FOLD)).encode("ascii", "ignore").decode()


def event_key(name):
    """Matching key for a focal-event name: ASCII, no generic words, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", GENERIC_EVENT_WORDS.sub("", to_ascii(name)).lower())


def normalize_events(events, aliases):
    """Map raw focal-event names to one display name per event. Names with the same key
    are merged; an alias table (alias -> canonical) merges names the key cannot (e.g.,
    "2015 Nepal" -> "2015 Gorkha"). Display = canonical, else the most frequent raw form."""
    amap = {event_key(a): c for a, c in aliases} if aliases else {}
    key = events.focal_event_raw.map(lambda e: event_key(amap.get(event_key(e), e)))
    ascii_raw = events.focal_event_raw.map(to_ascii)
    canon = {event_key(c): c for _, c in aliases} if aliases else {}
    display = (pd.DataFrame({"key": key, "raw": ascii_raw}).groupby("key").raw
               .agg(lambda s: s.value_counts().index[0]).to_dict())
    display.update({k: c for k, c in canon.items() if k in display})
    return key.map(display)


def load_design(dirs):
    """Study-design records; a DOI in a later batch replaces its earlier record."""
    latest = {}
    for d in dirs:
        for path in sorted(Path(d).glob("batch_*.jsonl")):
            for line in open(path):
                if line.strip():
                    r = json.loads(line)
                    latest[r["doi"]] = r
    recs = list(latest.values())
    # synthetic_only means no real data: drop it where a real-data origin is also listed.
    mixed = [r for r in recs if "synthetic_only" in r["data_origin"] and len(r["data_origin"]) > 1]
    for r in mixed:
        r["data_origin"] = [x for x in r["data_origin"] if x != "synthetic_only"]
    if mixed:
        print(f"study design: dropped synthetic_only next to real data in {len(mixed)} records")
    design = pd.DataFrame([{**{k: r[k] for k in ("doi", "contribution", "spatial_scope", "time_design",
                                                 "study_area", "evidence")},
                            **{k: ";".join(r[k]) for k in ("data_origin", "tectonic_settings", "focal_events")}}
                           for r in recs])

    def long(field, col):
        return pd.DataFrame([{"doi": r["doi"], col: x} for r in recs for x in r[field]],
                            columns=["doi", col])
    return {"study_design": design, "design_data_origins": long("data_origin", "data_origin"),
            "design_tectonic_settings": long("tectonic_settings", "tectonic_setting"),
            "design_focal_events": long("focal_events", "focal_event_raw")}


def apply_corrections(path, screening, uses, links):
    """Manual fixes from a CSV (doi, use_index, field, old_value, new_value, reason); each row
    must match its old_value. With use_index: a method-use field. Field source_structure_links:
    the paper's link list (JSON). Otherwise: a screening field. Targets of corrected papers are
    then recomputed from their method-use targets. Returns the updated links table."""
    corr = pd.read_csv(path, dtype=str)
    for c in corr.itertuples():
        if c.field == "source_structure_links":
            cur = sorted(links.link_type[links.doi == c.doi])
            if cur != sorted(json.loads(c.old_value)):
                raise SystemExit(f"correction old_value mismatch: {c.doi} links: {cur}")
            links = pd.concat([links[links.doi != c.doi],
                               pd.DataFrame({"doi": c.doi, "link_type": json.loads(c.new_value)})],
                              ignore_index=True)
            continue
        if pd.isna(c.use_index):
            df, mask = screening, screening.doi == c.doi
        else:
            df, mask = uses, uses.use_id == f"{c.doi}#{int(c.use_index)}"
        if mask.sum() != 1:
            raise SystemExit(f"correction target not found: {c.doi} {c.use_index} {c.field}")
        cur, old = df.loc[mask, c.field].iloc[0], parse_value(c.old_value)
        if not ((pd.isna(cur) and old is None) or cur == old):
            raise SystemExit(f"correction old_value mismatch: {c.doi} {c.use_index} {c.field}: {cur!r} != {old!r}")
        df.loc[mask, c.field] = parse_value(c.new_value)
    for doi in set(corr.doi):
        tg = set()
        for t in uses.target[uses.doi == doi]:
            tg |= {"source", "structure"} if t == "both" else {t}
        tg = sorted(tg)
        mask = screening.doi == doi
        screening.loc[mask, "targets"] = ";".join(tg)
        screening.loc[mask, "target_class"] = None if not tg else ("both" if len(tg) == 2 else tg[0])
        if (len(tg) == 2) != (links.doi == doi).any():
            raise SystemExit(f"{doi}: source_structure_links must be non-empty iff both targets")
    print(f"applied {len(corr)} corrections to {corr.doi.nunique()} papers")
    return links


def magnitude_node(m, use_types):
    """Node on the magnitude axis: a class, a reason why no magnitude applies, or not_stated."""
    if pd.notna(m["mag_class"]):
        return m["mag_class"]
    if m["mag_context"] == "not_applicable":
        types = use_types.get(m["use_id"], set())
        if "active_source" in types:
            return "active_source"
        if "ambient_noise" in types:
            return "ambient_noise"
        return "continuous_other"
    return "not_stated"


def citations_per_year(papers, min_age):
    """Citations divided by years since publication (at the retrieval date), floored at min_age."""
    pub = pd.to_datetime(papers.publication_date, errors="coerce")
    snap = pd.to_datetime(papers.retrieved_utc, errors="coerce", utc=True).dt.tz_localize(None)
    age = (snap - pub).dt.days / 365.25
    return age, papers.cited_by_count / age.clip(lower=min_age)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", nargs="+", required=True, help="corpus parquet files")
    p.add_argument("--extraction-dirs", nargs="+", required=True, help="extraction .../output dirs")
    p.add_argument("--journals", required=True, help="config/journals.csv")
    p.add_argument("--journal-metrics", help="OpenAlex journal metrics JSONL (optional)")
    p.add_argument("--jif", help="config/journal_jif.csv (optional)")
    p.add_argument("--vocab", required=True, help="config/vocab.csv")
    p.add_argument("--method-groups", help="method_short -> group -> family CSV (optional)")
    p.add_argument("--corrections", help="extraction corrections CSV (optional)")
    p.add_argument("--design-dirs", nargs="+", help="study-design .../output dirs (optional)")
    p.add_argument("--focal-event-aliases", help="focal-event alias -> canonical CSV (optional)")
    p.add_argument("--mainshock-offset", type=float, default=2.0,
                   help="fore/aftershock magnitude = mainshock - offset when only mainshock is given")
    p.add_argument("--mag-class-edges", default="2,4,6,8",
                   help="upper edges of micro,small,moderate,large (great = above the last)")
    p.add_argument("--cpy-min-age", type=float, default=1.0,
                   help="floor (years) on paper age when computing citations per year")
    p.add_argument("--out", required=True, help="SQLite path (rebuilt from scratch)")
    p.add_argument("--export-dir", help="also write each table (except papers) as CSV here")
    args = p.parse_args()

    journals = pd.read_csv(args.journals, dtype={"doi_prefix": str})
    if args.journal_metrics:
        journals = journals.merge(pd.read_json(args.journal_metrics, lines=True)
                                  .drop(columns="openalex_source_id"), on="journal_key", how="left")
    if args.jif:
        journals = journals.merge(pd.read_csv(args.jif), on="journal_key", how="left")

    papers = pd.concat([pd.read_parquet(c) for c in args.corpus], ignore_index=True)
    papers = papers[~(papers.doi.notna() & papers.doi.duplicated(keep="last"))].copy()
    papers.loc[~papers.candidate, "abstract"] = None
    papers["age_years"], papers["cites_per_year"] = citations_per_year(papers, args.cpy_min_age)
    papers = papers.merge(journals[["journal_key", "high_impact"]], on="journal_key", how="left")

    t = load_extractions(args.extraction_dirs)
    keep = set(papers.doi[papers.candidate])
    dropped = sorted(set(t["screening"].doi) - keep)
    if dropped:
        print(f"dropping {len(dropped)} extracted non-candidates: {dropped[:5]}")
    dup = t["screening"].doi[t["screening"].doi.isin(keep)].duplicated(keep=False)
    if dup.any():
        raise SystemExit(f"DOIs extracted more than once: {t['screening'].doi[dup].unique()[:5]}")
    for k in ("screening", "links", "source_types", "networks", "uses"):
        if len(t[k]):
            t[k] = t[k][t[k].doi.isin(keep)]
    for k, col, parent, pcol in (("sensors", "net_id", "networks", "net_id"),
                                 ("envs", "net_id", "networks", "net_id"),
                                 ("data_types", "use_id", "uses", "use_id"),
                                 ("use_source_types", "use_id", "uses", "use_id"),
                                 ("distances", "use_id", "uses", "use_id"),
                                 ("use_networks", "use_id", "uses", "use_id")):
        if len(t[k]):
            t[k] = t[k][t[k][col].isin(t[parent][pcol])]
    screening, uses = t["screening"], t["uses"]
    if args.corrections:
        t["links"] = apply_corrections(args.corrections, screening, uses, t["links"])

    derived = uses.apply(lambda m: derive_magnitude(m, args.mainshock_offset), axis=1, result_type="expand")
    uses[["mag_rep", "mag_rep_rule", "mag_unclear"]] = derived
    uses["mag_unclear"] = uses.mag_unclear.astype(object)
    uses.loc[uses.mag_context == "not_applicable", "mag_unclear"] = None
    edges = [float(x) for x in args.mag_class_edges.split(",")]
    uses[["mag_class", "mag_class_source"]] = uses.apply(
        lambda m: classify_magnitude(m, edges), axis=1, result_type="expand")
    uses.loc[uses.mag_context == "not_applicable", "mag_class_source"] = "not_applicable"
    use_types = t["use_source_types"].groupby("use_id").source_type.agg(set).to_dict()
    uses["mag_node"] = uses.apply(lambda m: magnitude_node(m, use_types), axis=1)

    vocab = pd.read_csv(args.vocab)
    groups = None
    if args.method_groups:
        groups = pd.read_csv(args.method_groups)
        gmap = dict(zip(groups.method_short.str.strip().str.lower(), groups.method_group))
        uses["method_group"] = uses.method_short.str.strip().str.lower().map(gmap)

    # Knowledge-graph incidence list: included papers only.
    inc = set(screening.doi[screening.include])
    s_inc = screening[screening.include]
    tg = s_inc.assign(value=s_inc.targets.str.split(";")).explode("value")
    rows = [
        tg[["doi", "value"]].assign(axis="target"),
        s_inc[["doi", "study_type"]].rename(columns={"study_type": "value"}).assign(axis="study_type"),
        t["links"].rename(columns={"link_type": "value"}).assign(axis="link"),
        t["source_types"].rename(columns={"source_type": "value"}).assign(axis="source_type"),
        uses[["doi", "use_id", "method_family"]].rename(columns={"method_family": "value"})
        .assign(axis="method_family"),
        uses[["doi", "use_id", "mag_node"]].rename(columns={"mag_node": "value"}).assign(axis="magnitude"),
        t["distances"].merge(uses[["use_id", "doi"]]).rename(columns={"distance": "value"})
        .assign(axis="distance"),
        t["data_types"].merge(uses[["use_id", "doi"]]).rename(columns={"data_type": "value"})
        .assign(axis="data_type"),
        t["sensors"].merge(t["networks"][["net_id", "doi"]]).rename(columns={"sensor_type": "value"})
        .assign(axis="sensor"),
        t["envs"].merge(t["networks"][["net_id", "doi"]]).rename(columns={"environment": "value"})
        .assign(axis="environment"),
        t["networks"][["doi", "net_id", "deployment"]].rename(columns={"deployment": "value"})
        .assign(axis="deployment"),
        t["networks"][["doi", "net_id", "density"]].rename(columns={"density": "value"})
        .assign(axis="density"),
    ]
    if groups is not None:
        rows.append(uses[["doi", "use_id", "method_group"]].dropna()
                    .rename(columns={"method_group": "value"}).assign(axis="method_group"))
    design = None
    if args.design_dirs:
        design = load_design(args.design_dirs)
        aliases = (list(pd.read_csv(args.focal_event_aliases)[["alias", "canonical"]].itertuples(index=False))
                   if args.focal_event_aliases else [])
        fe = design["design_focal_events"]
        fe["focal_event"] = normalize_events(fe, aliases)
        print(f"focal events: {fe.focal_event_raw.nunique()} raw names -> {fe.focal_event.nunique()} events")
        dd = set(design["study_design"].doi)
        print(f"study design: {len(dd & inc)} of {len(inc)} included papers "
              f"({len(dd - inc)} records for papers not included)")
        rows += [design["study_design"][["doi", c]].rename(columns={c: "value"}).assign(axis=c)
                 for c in ("contribution", "spatial_scope", "time_design")]
        rows += [design[k].rename(columns={c: "value"}).assign(axis=a)
                 for k, c, a in (("design_data_origins", "data_origin", "data_origin"),
                                 ("design_tectonic_settings", "tectonic_setting", "tectonic_setting"),
                                 ("design_focal_events", "focal_event", "focal_event"))]
    pc = pd.concat(rows, ignore_index=True)
    pc = pc[pc.doi.isin(inc)].reindex(columns=["doi", "axis", "value", "use_id", "net_id"])
    known = set(zip(vocab.axis, vocab.value)) | ({("method_group", g) for g in groups.method_group}
                                                if groups is not None else set())
    known |= {("focal_event", v) for v in pc.value[pc.axis == "focal_event"]}
    unknown = pc[[(a, v) not in known for a, v in zip(pc.axis, pc.value)]]
    if len(unknown):
        raise SystemExit(f"values missing from vocabulary: {unknown[['axis', 'value']].drop_duplicates().head(10)}")

    tables = {"journals": journals, "papers": papers, "screening": screening,
              "paper_links": t["links"], "paper_source_types": t["source_types"],
              "networks": t["networks"], "network_sensor_types": t["sensors"],
              "network_environments": t["envs"], "method_uses": uses,
              "method_use_data_types": t["data_types"], "method_use_source_types": t["use_source_types"],
              "method_use_distances": t["distances"], "method_use_networks": t["use_networks"],
              "vocab": vocab, "paper_concepts": pc}
    if groups is not None:
        tables["method_groups"] = groups
    if design is not None:
        tables.update({k: df[df.doi.isin(inc)] for k, df in design.items()})
    tables["build_info"] = pd.DataFrame([{
        "mainshock_offset": args.mainshock_offset, "mag_class_edges": args.mag_class_edges,
        "cpy_min_age": args.cpy_min_age, "vocab": args.vocab, "method_groups": args.method_groups,
        "corrections": args.corrections, "extraction_dirs": ";".join(args.extraction_dirs),
        "design_dirs": ";".join(args.design_dirs or []), "focal_event_aliases": args.focal_event_aliases,
        "built_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")}])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    with sqlite3.connect(out) as con:
        for name, df in tables.items():
            df.to_sql(name, con, index=False)
        con.executescript("""
            CREATE INDEX idx_papers_doi ON papers(doi);
            CREATE INDEX idx_uses_doi ON method_uses(doi);
            CREATE INDEX idx_pc_doi ON paper_concepts(doi);
            CREATE VIEW v_paper_concepts AS
              SELECT DISTINCT c.doi, c.axis, c.value, p.publication_year, p.journal_key,
                     p.high_impact, p.cites_per_year, p.fwci, s.target_class
              FROM paper_concepts c JOIN papers p USING (doi) JOIN screening s USING (doi);
            CREATE VIEW v_concept_pairs AS
              WITH pc AS (SELECT DISTINCT doi, axis, value FROM paper_concepts)
              SELECT a.doi, a.axis AS axis_a, a.value AS value_a, b.axis AS axis_b, b.value AS value_b,
                     p.publication_year, p.journal_key, p.high_impact
              FROM pc a JOIN pc b ON a.doi = b.doi AND (a.axis || '|' || a.value) < (b.axis || '|' || b.value)
              JOIN papers p ON p.doi = a.doi;
        """)
    if args.export_dir:
        exp = Path(args.export_dir)
        exp.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            if name != "papers":
                df.to_csv(exp / f"{name}.csv", index=False)
    print(f"papers={len(papers)} screened={len(screening)} included={len(inc)} "
          f"networks={len(t['networks'])} method_uses={len(uses)} concepts={len(pc)} -> {out}")


if __name__ == "__main__":
    main()
