"""Export the database to the knowledge-graph page (one self-contained HTML file).

Nodes are vocabulary terms (axis, value) carried by included papers; the page
computes co-occurrence links, observed/expected ratios, and source-structure
orientation in the browser under the viewer's filters. Each paper also carries
its analysis units (one per method use, with the attributes of the networks that
use draws on, plus one per network no use refers to), so the page can tell
whether two terms meet in the same analysis or only in the same paper.
"""
import argparse
import json
import re
import sqlite3

import pandas as pd

# (axis id, label, shown by default)
AXES = [("target", "Target", True), ("link", "Source–structure link", False),
        ("contribution", "Primary contribution", True), ("tectonic_setting", "Tectonic setting", True),
        ("focal_event", "Focal event", False),
        ("spatial_scope", "Spatial scope", False), ("time_design", "Time design", False),
        ("data_origin", "Data origin", False), ("method_family", "Method family", True),
        ("method_group", "Method group", False), ("source_type", "Source type", True),
        ("magnitude", "Magnitude", True), ("distance", "Distance", True),
        ("sensor", "Sensor", True), ("environment", "Installation setting", True),
        ("deployment", "Deployment", True), ("density", "Station density", True),
        ("data_type", "Data type", False)]
TARGET_CODE = {"source": 0, "structure": 1, "both": 2}
# Magnitude subscripts lost in title metadata ("M w 8.4", "M W 6.1") -> "Mw 8.4", "ML 3.2".
SPLIT_MAG = re.compile(r"\bM ([wWLsSb]) ?(?=[\d=~≈<>≥≤])")


def fix_title(t):
    return SPLIT_MAG.sub(lambda m: "Mw " if m.group(1) in "wW" else f"M{m.group(1)} ", t)


def analysis_units(con, idx):
    """Per paper, the term sets of its analyses: one per method use (its own terms plus the
    terms of the networks it uses) and one per network that no method use refers to."""
    q = lambda s: pd.read_sql(s, con)
    inc = "SELECT doi FROM screening WHERE include"
    uses = q(f"SELECT use_id, doi, target, method_family, mag_node FROM method_uses WHERE doi IN ({inc})")
    use_terms = {u: set() for u in uses.use_id}
    for r in uses.itertuples():
        targets = ["source", "structure"] if r.target == "both" else [r.target]
        use_terms[r.use_id] |= {("method_family", r.method_family), ("magnitude", r.mag_node)} | \
            {("target", t) for t in targets}
    for table, axis, col in [("method_use_distances", "distance", "distance"),
                             ("method_use_data_types", "data_type", "data_type"),
                             ("method_use_source_types", "source_type", "source_type")]:
        for r in q(f"SELECT use_id, {col} AS v FROM {table}").itertuples():
            if r.use_id in use_terms:
                use_terms[r.use_id].add((axis, r.v))
    nets = q(f"SELECT net_id, doi, deployment, density FROM networks WHERE doi IN ({inc})")
    net_terms = {r.net_id: {("deployment", r.deployment), ("density", r.density)} for r in nets.itertuples()}
    for table, axis, col in [("network_sensor_types", "sensor", "sensor_type"),
                             ("network_environments", "environment", "environment")]:
        for r in q(f"SELECT net_id, {col} AS v FROM {table}").itertuples():
            if r.net_id in net_terms:
                net_terms[r.net_id].add((axis, r.v))
    used_nets = set()
    for r in q("SELECT use_id, net_id FROM method_use_networks").itertuples():
        if r.use_id in use_terms and r.net_id in net_terms:
            use_terms[r.use_id] |= net_terms[r.net_id]
            used_nets.add(r.net_id)
    sets = [(d, use_terms[u]) for u, d in zip(uses.use_id, uses.doi)] + \
           [(d, net_terms[n]) for n, d in zip(nets.net_id, nets.doi) if n not in used_nets]
    units = {}
    for doi, terms in sets:
        ids = sorted({idx[t] for t in terms if t in idx})
        if len(ids) > 1 and ids not in units.setdefault(doi, []):
            units[doi].append(ids)
    return units


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="SQLite database from build_db.py")
    p.add_argument("--template", required=True, help="scripts/templates/knowledge_graph.html")
    p.add_argument("--period", required=True, help='e.g. "2021–2025"')
    p.add_argument("--min-event-papers", type=int, default=5,
                   help="focal events studied by fewer papers are not shown as terms")
    p.add_argument("--out", required=True, help="output HTML")
    args = p.parse_args()

    con = sqlite3.connect(args.db)
    pc = pd.read_sql("SELECT DISTINCT doi, axis, value FROM paper_concepts", con)
    vocab = pd.read_sql("SELECT axis, value, label, side, definition, \"order\" FROM vocab", con)
    tables = set(pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con).name)
    if "method_groups" in tables:
        g = pd.read_sql("SELECT DISTINCT method_group AS value, method_family FROM method_groups", con)
        vocab = pd.concat([vocab, g.assign(axis="method_group", label=g.value, side="",
                                           definition="Family: " + g.method_family.fillna(""),
                                           order=10_000)], ignore_index=True)
    if "design_focal_events" in tables:
        ev = pd.read_sql("""SELECT focal_event AS value, COUNT(DISTINCT doi) AS n
                            FROM design_focal_events GROUP BY focal_event""", con)
        ev = ev[ev.n >= args.min_event_papers]
        vocab = pd.concat([vocab, ev.assign(axis="focal_event", label=ev.value, side="", order=20_000,
                                            definition="Specific event or sequence studied")
                           .drop(columns="n")], ignore_index=True)
    papers = pd.read_sql("""
        SELECT s.doi, p.title, p.journal_key, p.publication_year, p.cites_per_year, p.fwci,
               s.target_class, s.link_note
        FROM screening s JOIN papers p USING (doi) WHERE s.include""", con)
    journals = pd.read_sql("SELECT journal_key, journal_name, high_impact FROM journals", con)
    n_screened = con.execute("SELECT COUNT(*) FROM screening").fetchone()[0]
    lo, hi = (d[:10] for d in con.execute("""SELECT MIN(retrieved_utc), MAX(retrieved_utc) FROM papers
                                             WHERE doi IN (SELECT doi FROM screening WHERE include)""").fetchone())
    snapshot = f"snapshot of {lo}" if lo == hi else f"snapshots of {lo} to {hi}"

    axis_ids = [a for a, _, _ in AXES]
    used = pc[pc.axis.isin(axis_ids)][["axis", "value"]].drop_duplicates()
    concepts = vocab.merge(used, on=["axis", "value"]).sort_values(["order", "label"])
    concepts["axis_rank"] = concepts.axis.map({a: i for i, a in enumerate(axis_ids)})
    concepts = concepts.sort_values(["axis_rank", "order", "label"]).reset_index(drop=True)
    idx = {(a, v): i for i, (a, v) in enumerate(zip(concepts.axis, concepts.value))}
    jidx = {k: i for i, k in enumerate(journals.journal_key)}
    ks = (pc.merge(concepts[["axis", "value"]]).assign(i=lambda d: [idx[(a, v)] for a, v in zip(d.axis, d.value)])
          .groupby("doi").i.agg(lambda s: sorted(set(s))).to_dict())

    units = analysis_units(con, idx)

    def num(x, d):
        return None if pd.isna(x) else round(float(x), d)

    data = {
        "meta": {"period": args.period, "n_screened": int(n_screened), "n_included": len(papers),
                 "lede": f"A prototype built from observational seismology studies of seismic "
                         f"sources and Earth structure in 13 journals, "
                         f"{args.period}, labeled from titles and abstracts. "
                         f"Two terms share an edge when the same paper carries both; the edge also "
                         f"counts the papers that use them in the same analysis. "
                         f"Citations per year as of the OpenAlex {snapshot}.",
                 "snapshot": snapshot,
                 "built": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")},
        "axes": [{"id": a, "label": l, "on": on} for a, l, on in AXES
                 if a in set(concepts.axis)],
        "concepts": [{"a": r.axis, "v": r.value, "l": r.label, "d": r.definition, "side": r.side or ""}
                     for r in concepts.itertuples()],
        "journals": [{"k": r.journal_key, "n": r.journal_name, "hi": bool(r.high_impact)}
                     for r in journals.itertuples()],
        "papers": [[r.doi, fix_title(r.title), jidx[r.journal_key], int(r.publication_year), num(r.cites_per_year, 2),
                    num(r.fwci, 2), TARGET_CODE[r.target_class], ks.get(r.doi, []),
                    None if pd.isna(r.link_note) else r.link_note, units.get(r.doi, [])]
                   for r in papers.itertuples()],
    }
    html = open(args.template).read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*__KG_DATA__*/null", payload)
    with open(args.out, "w") as f:
        f.write(html)
    print(f"{len(data['concepts'])} terms, {len(data['papers'])} papers -> {args.out} "
          f"({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
