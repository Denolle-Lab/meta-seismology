"""Validate extraction output JSONL against the schema and its input batch.

Checks: JSON schema, one output per input DOI in the same order, and logical
consistency (targets match method-use targets, links only for source+structure
papers, network references exist, magnitude fields agree with each other).
Exits non-zero on any error.
"""
import argparse
import json
import sys

import jsonschema


def check_logic(rec):
    errs = []
    lists = ["targets", "source_structure_links", "source_types"]
    for k in lists:
        if len(set(rec[k])) != len(rec[k]):
            errs.append(f"duplicate values in {k}")
    if rec["include"]:
        if rec["exclusion_reason"] is not None:
            errs.append("included but exclusion_reason set")
        if rec["study_type"] is None or rec["uses_real_data"] is None:
            errs.append("included but study_type/uses_real_data missing")
        if not rec["targets"] or not rec["source_types"]:
            errs.append("included but targets/source_types empty")
    else:
        if rec["exclusion_reason"] is None:
            errs.append("excluded without exclusion_reason")
        if any(rec[k] for k in lists + ["networks", "method_uses"]):
            errs.append("excluded paper has targets/links/source_types/networks/method_uses")
        if any(rec[k] is not None for k in ("study_type", "uses_real_data", "link_note")):
            errs.append("excluded paper has study_type/uses_real_data/link_note")
    both = set(rec["targets"]) == {"source", "structure"}
    if both != bool(rec["source_structure_links"]):
        errs.append("source_structure_links must be non-empty exactly when targets has both")
    if rec["method_uses"]:
        used = set()
        for m in rec["method_uses"]:
            used |= {"source", "structure"} if m["target"] == "both" else {m["target"]}
        if used != set(rec["targets"]):
            errs.append(f"targets {sorted(rec['targets'])} != method-use targets {sorted(used)}")
    for i, n in enumerate(rec["networks"]):
        for k in ("sensor_types", "environments"):
            if len(set(n[k])) != len(n[k]):
                errs.append(f"network {i}: duplicate values in {k}")
        if "not_stated" in n["environments"] and len(n["environments"]) > 1:
            errs.append(f"network {i}: not_stated combined with other environments")
    paper_types = set(rec["source_types"])
    for i, m in enumerate(rec["method_uses"]):
        tag = f"method {i}"
        for k in ("data_types", "source_types", "distance_regimes", "network_refs"):
            if len(set(m[k])) != len(m[k]):
                errs.append(f"{tag}: duplicate values in {k}")
        if not set(m["source_types"]) <= paper_types:
            errs.append(f"{tag}: source_types not a subset of paper source_types")
        if any(r >= len(rec["networks"]) for r in m["network_refs"]):
            errs.append(f"{tag}: network_refs points past the networks list")
        dist = set(m["distance_regimes"])
        if dist & {"not_stated", "not_applicable"} and len(dist) > 1:
            errs.append(f"{tag}: not_stated/not_applicable combined with other distance regimes")
        if (m["distance_basis"] == "not_stated") != bool(dist & {"not_stated", "not_applicable"}):
            errs.append(f"{tag}: distance_basis not_stated must match distance_regimes not_stated/not_applicable")
        ctx, rel = m["mag_context"], m["mag_relation"]
        if m["target"] == "structure" and ctx == "analyzed_events":
            errs.append(f"{tag}: structure target uses mag_context analyzed_events")
        if m["target"] != "structure" and ctx == "source_events":
            errs.append(f"{tag}: source_events context on a non-structure target")
        if ctx == "not_applicable":
            if any(m[k] is not None for k in ("mag_min", "mag_max", "mainshock_mag", "mag_qualitative")) \
                    or rel != "none" or m["mag_clarity"] != "not_stated":
                errs.append(f"{tag}: not_applicable context must have no magnitude information")
        if rel == "mainshock_reference":
            if m["mainshock_mag"] is None:
                errs.append(f"{tag}: mainshock_reference without mainshock_mag")
            if m["mag_min"] is not None or m["mag_max"] is not None:
                errs.append(f"{tag}: mainshock_reference with mag_min/mag_max set")
        if rel == "trigger_reference" and m["mainshock_mag"] is None:
            errs.append(f"{tag}: trigger_reference without mainshock_mag")
        if rel == "direct" and m["mag_min"] is None and m["mag_max"] is None:
            errs.append(f"{tag}: direct without mag_min/mag_max")
        if rel == "none" and m["mag_clarity"] in ("explicit", "external_knowledge"):
            errs.append(f"{tag}: relation none but clarity {m['mag_clarity']}")
        if m["mag_clarity"] == "qualitative" and m["mag_qualitative"] is None:
            errs.append(f"{tag}: qualitative clarity without mag_qualitative")
        if None not in (m["mag_min"], m["mag_max"]) and m["mag_min"] > m["mag_max"]:
            errs.append(f"{tag}: mag_min > mag_max")
    return errs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema", required=True)
    p.add_argument("--input", required=True, help="input batch JSONL")
    p.add_argument("--output", required=True, help="extraction output JSONL")
    args = p.parse_args()

    validator = jsonschema.Draft202012Validator(json.load(open(args.schema)))
    in_dois = [json.loads(l)["doi"] for l in open(args.input) if l.strip()]
    errors = []
    out_dois = []
    for n, line in enumerate(open(args.output), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {n}: invalid JSON ({e})")
            continue
        out_dois.append(rec.get("doi"))
        schema_errs = [f"line {n} ({rec.get('doi')}): {e.json_path}: {e.message}"
                       for e in validator.iter_errors(rec)]
        errors += schema_errs
        if not schema_errs:
            errors += [f"line {n} ({rec.get('doi')}): {e}" for e in check_logic(rec)]
    if out_dois != in_dois:
        missing = set(in_dois) - set(out_dois)
        extra = set(out_dois) - set(in_dois)
        errors.append(f"DOI mismatch: {len(missing)} missing {sorted(missing)[:5]}, "
                      f"{len(extra)} extra {sorted(extra)[:5]}, order_ok={out_dois == in_dois}")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"OK: {len(out_dois)} records")


if __name__ == "__main__":
    main()
