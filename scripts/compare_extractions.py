"""Agreement between two independent extractions of the same batches.

Reports, per field: Cohen's kappa for single-valued paper fields, and mean
Jaccard similarity of label sets for multi-valued fields (paper level, using
the union over method uses or networks). Lists the papers that disagree on
inclusion or target so the codebook can be clarified.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def load(d):
    recs = {}
    for path in sorted(Path(d).glob("batch_*.jsonl")):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                recs[r["doi"]] = r
    return recs


def kappa(a, b):
    a, b = pd.Series(a, dtype=str), pd.Series(b, dtype=str)
    po = (a.values == b.values).mean()
    cats = set(a) | set(b)
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def jaccard(x, y):
    x, y = set(x), set(y)
    return 1.0 if not x and not y else len(x & y) / len(x | y)


def sets(r):
    uses, nets = r["method_uses"], r["networks"]
    return {
        "targets": r["targets"], "links": r["source_structure_links"], "source_types": r["source_types"],
        "method_family": [m["method_family"] for m in uses],
        "distance": [d for m in uses for d in m["distance_regimes"]],
        "data_type": [d for m in uses for d in m["data_types"]],
        "mag_context": [m["mag_context"] for m in uses],
        "mag_relation": [m["mag_relation"] for m in uses],
        "mag_qualitative": [m["mag_qualitative"] for m in uses if m["mag_qualitative"]],
        "mag_bounds": [(m["mag_min"], m["mag_max"], m["mainshock_mag"]) for m in uses],
        "sensor": [s for n in nets for s in n["sensor_types"]],
        "environment": [s for n in nets for s in n["environments"]],
        "deployment": [n["deployment"] for n in nets],
        "density": [n["density"] for n in nets],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--a", required=True, help="output dir of extraction A")
    p.add_argument("--b", required=True, help="output dir of extraction B")
    p.add_argument("--out", help="optional CSV of per-paper disagreements")
    args = p.parse_args()

    A, B = load(args.a), load(args.b)
    dois = sorted(set(A) & set(B))
    print(f"papers compared: {len(dois)} (A only {len(set(A) - set(B))}, B only {len(set(B) - set(A))})")
    inc_a = [A[d]["include"] for d in dois]
    inc_b = [B[d]["include"] for d in dois]
    print(f"include: agreement {pd.Series(inc_a).eq(pd.Series(inc_b)).mean():.3f}, kappa {kappa(inc_a, inc_b):.3f}, "
          f"included A={sum(inc_a)} B={sum(inc_b)}")
    exc = [d for d in dois if not A[d]["include"] and not B[d]["include"]]
    if exc:
        print(f"exclusion_reason (both excluded, n={len(exc)}): kappa "
              f"{kappa([A[d]['exclusion_reason'] for d in exc], [B[d]['exclusion_reason'] for d in exc]):.3f}")
    both = [d for d in dois if A[d]["include"] and B[d]["include"]]
    rows = []
    for d in both:
        sa, sb = sets(A[d]), sets(B[d])
        row = {"doi": d, "n_uses_a": len(A[d]["method_uses"]), "n_uses_b": len(B[d]["method_uses"]),
               "n_nets_a": len(A[d]["networks"]), "n_nets_b": len(B[d]["networks"])}
        for k in sa:
            row[k] = jaccard(sa[k], sb[k])
        row["study_type"] = A[d]["study_type"] == B[d]["study_type"]
        rows.append(row)
    df = pd.DataFrame(rows)
    print(f"\nboth included: {len(both)}; study_type kappa "
          f"{kappa([A[d]['study_type'] for d in both], [B[d]['study_type'] for d in both]):.3f}")
    print("mean Jaccard per field (1 = identical label sets):")
    cols = [c for c in df.columns if c not in ("doi", "n_uses_a", "n_uses_b", "n_nets_a", "n_nets_b", "study_type")]
    print(df[cols].mean().round(3).to_string())
    print(f"method uses per paper: A {df.n_uses_a.mean():.2f}, B {df.n_uses_b.mean():.2f}; "
          f"networks per paper: A {df.n_nets_a.mean():.2f}, B {df.n_nets_b.mean():.2f}")
    print("\ninclusion disagreements:")
    for d in dois:
        if A[d]["include"] != B[d]["include"]:
            ra, rb = A[d], B[d]
            print(f"  {d}: A={ra['include']}/{ra['exclusion_reason']} B={rb['include']}/{rb['exclusion_reason']}"
                  f" | {ra['screen_note'] or ''} | {rb['screen_note'] or ''}")
    print("target disagreements:")
    for d in both:
        if set(A[d]["targets"]) != set(B[d]["targets"]):
            print(f"  {d}: A={A[d]['targets']} B={B[d]['targets']}")
    if args.out:
        df.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
