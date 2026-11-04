"""Validate study-design output JSONL against its schema and input batch.

Checks: JSON schema, one output per input DOI in the same order, and that the
exclusive values (data_origin not_stated; tectonic settings not_applicable,
not_stated, global_multi, planetary) are used alone.
"""
import argparse
import json
import sys

import jsonschema

EXCLUSIVE_SETTINGS = {"not_applicable", "not_stated", "global_multi", "planetary"}


def check_logic(r):
    errs = []
    if "not_stated" in r["data_origin"] and len(r["data_origin"]) > 1:
        errs.append("data_origin not_stated combined with other values")
    s = set(r["tectonic_settings"])
    if s & EXCLUSIVE_SETTINGS and len(s) > 1:
        errs.append(f"tectonic setting {sorted(s & EXCLUSIVE_SETTINGS)} must be used alone")
    return errs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema", required=True)
    p.add_argument("--input", required=True, help="input batch JSONL")
    p.add_argument("--output", required=True, help="design output JSONL")
    args = p.parse_args()

    validator = jsonschema.Draft202012Validator(json.load(open(args.schema)))
    in_dois = [json.loads(l)["doi"] for l in open(args.input) if l.strip()]
    errors, out_dois = [], []
    for n, line in enumerate(open(args.output), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {n}: invalid JSON ({e})")
            continue
        out_dois.append(r.get("doi"))
        schema_errs = [f"line {n} ({r.get('doi')}): {e.json_path}: {e.message}" for e in validator.iter_errors(r)]
        errors += schema_errs
        if not schema_errs:
            errors += [f"line {n} ({r.get('doi')}): {e}" for e in check_logic(r)]
    if out_dois != in_dois:
        missing, extra = set(in_dois) - set(out_dois), set(out_dois) - set(in_dois)
        errors.append(f"DOI mismatch: {len(missing)} missing {sorted(missing)[:5]}, "
                      f"{len(extra)} extra {sorted(extra)[:5]}, order_ok={out_dois == in_dois}")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"OK: {len(out_dois)} records")


if __name__ == "__main__":
    main()
