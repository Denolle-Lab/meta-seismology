"""Agreement between two independent study-design extractions of the same papers.

Cohen's kappa for single-valued fields, mean Jaccard for list fields, and the
confusion table of the primary contribution, so low-agreement categories can
be merged before the full pass.
"""
import argparse
import json
import re
from pathlib import Path

import pandas as pd

from compare_extractions import jaccard, kappa


def load(d):
    out = {}
    for p in sorted(Path(d).glob("batch_*.jsonl")):
        for line in open(p):
            if line.strip():
                r = json.loads(line)
                out[r["doi"]] = r
    return out


def norm_event(e):
    return re.sub(r"[^a-z0-9 ]", "", e.lower()).strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--a", required=True, help="output dir A")
    p.add_argument("--b", required=True, help="output dir B")
    args = p.parse_args()

    A, B = load(args.a), load(args.b)
    dois = sorted(set(A) & set(B))
    print(f"papers compared: {len(dois)}")
    for k in ("contribution", "spatial_scope", "time_design"):
        a, b = [A[d][k] for d in dois], [B[d][k] for d in dois]
        agree = sum(x == y for x, y in zip(a, b)) / len(dois)
        print(f"{k:18s} agreement {agree:.3f}  kappa {kappa(a, b):.3f}")
    for k in ("data_origin", "tectonic_settings"):
        j = sum(jaccard(A[d][k], B[d][k]) for d in dois) / len(dois)
        print(f"{k:18s} mean Jaccard {j:.3f}")
    ev = [(set(map(norm_event, A[d]["focal_events"])), set(map(norm_event, B[d]["focal_events"]))) for d in dois]
    both_empty = sum(not a and not b for a, b in ev)
    either = sum(bool(a) != bool(b) for a, b in ev)
    print(f"focal_events      both empty {both_empty}, one empty {either}, mean Jaccard "
          f"{sum(jaccard(a, b) for a, b in ev) / len(ev):.3f}")
    ct = pd.crosstab(pd.Series([A[d]["contribution"] for d in dois], name="A"),
                     pd.Series([B[d]["contribution"] for d in dois], name="B"))
    print("\ncontribution A (rows) x B (columns):")
    print(ct.to_string())


if __name__ == "__main__":
    main()
