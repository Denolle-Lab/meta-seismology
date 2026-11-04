"""Render the pinned extractor prompt for every input batch.

One prompt file per batch, so every extraction worker gets identical
instructions and the exact text used is kept with the outputs.
"""
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--template", required=True, help="labeling/extraction_prompt.md")
    p.add_argument("--run-dir", required=True, help="e.g. data/extraction/2021-2025 (has input/)")
    p.add_argument("--codebook", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--validator", required=True)
    p.add_argument("--python", required=True, help="python of the conda env")
    args = p.parse_args()

    run = Path(args.run_dir).resolve()
    for d in ("output", "hard_cases", "prompts"):
        (run / d).mkdir(exist_ok=True)
    template = Path(args.template).read_text()
    n = 0
    for inp in sorted((run / "input").glob("batch_*.jsonl")):
        text = template.format(
            codebook=Path(args.codebook).resolve(), schema=Path(args.schema).resolve(),
            validator=Path(args.validator).resolve(), python=args.python,
            input=inp, output=run / "output" / inp.name,
            hard_cases=run / "hard_cases" / f"{inp.stem}.md")
        (run / "prompts" / f"{inp.stem}.md").write_text(text)
        n += 1
    print(f"{n} prompts -> {run / 'prompts'}")


if __name__ == "__main__":
    main()
