# Pipeline

Commands to rebuild the graph from nothing, in the order of the
[roadmap](roadmap.md) stages. Every script takes its inputs and outputs on
the command line and prints a short report; run any of them with `--help`
for the full list of options.

## Environment

```bash
mamba env create -f environment.yml
conda activate meta-seismology
```

The scripts need Python 3.11 with pandas, pyarrow, requests, and jsonschema.
Labeling also needs an agent that can read and write files and run a
command (see [Labeling workers](#labeling-workers)).

## Data layout

Data are not part of this repository. The commands below write to `data/`:

```
data/
  raw/openalex/<from>_<to>/   OpenAlex records per journal (gzipped JSONL) + manifest
  raw/s2/                     Semantic Scholar abstracts (JSONL)
  interim/                    corpus parquet files
  audit/                      collection audit tables
  extraction/<run>/           input/, prompts/, output/, hard_cases/
  design/<run>/               same layout, study-design pass
  db/                         SQLite database (rebuilt from scratch)
```

Raw files are written once and never modified; the fetch scripts skip or
refuse an existing file. Everything after `data/raw/` can be regenerated.

## 1. Collect records

```bash
# OpenAlex, one date window at a time. A journal must stay under 10,000
# records per window (OpenAlex page paging); we used half-year windows for
# 2021-2025 and one-year windows for 2000-2020.
python scripts/fetch_openalex.py --journals config/journals.csv \
    --from-date 2021-01-01 --to-date 2021-06-30 --out-dir data/raw/openalex
# Nature and Science: research articles only, to save API calls
python scripts/fetch_openalex.py --journals config/journals.csv \
    --from-date 2005-01-01 --to-date 2005-12-31 --out-dir data/raw/openalex \
    --only Nature Science --type article
```

Without an API key, OpenAlex allows a small number of requests per day from
one IP address. A long backfill can be spread over several days, or run with
`--api-key`.

```bash
T=2021-01-01_2025-12-31
RAW="data/raw/openalex/202[1-5]-*"
# Corpus, Semantic Scholar fill for missing abstracts, corpus again
python scripts/build_corpus.py --raw-dir $RAW --journals config/journals.csv \
    --extra-sources config/openalex_extra_sources.csv --prefilter config/prefilter.json \
    --out data/interim/corpus_${T}_pre_s2.parquet
python scripts/fetch_s2_abstracts.py --corpus data/interim/corpus_${T}_pre_s2.parquet \
    --out data/raw/s2/abstracts_$T.jsonl
python scripts/build_corpus.py --raw-dir $RAW --journals config/journals.csv \
    --extra-sources config/openalex_extra_sources.csv --prefilter config/prefilter.json \
    --s2 data/raw/s2/abstracts_$T.jsonl --out data/interim/corpus_$T.parquet
# Audit: OpenAlex vs Crossref counts, abstract coverage, DOI anomalies
python scripts/audit_collection.py --corpus data/interim/corpus_$T.parquet \
    --raw-dir $RAW --journals config/journals.csv --out data/audit/collection_audit_$T.csv
```

What the corpus builder does:

- Rebuilds abstracts from OpenAlex's inverted index and strips markup.
- Keeps a journal's records by OpenAlex source and DOI pattern
  (`doi_prefix`, `doi_extra_regex` in `config/journals.csv`), and maps older
  volumes filed under another OpenAlex source to the journal
  (`config/openalex_extra_sources.csv`).
- Applies the prefilter (`config/prefilter.json`): a record is a candidate if
  its title or abstract matches a strong term, or a weak term together with a
  context term. Every record of a seismology-only journal is a candidate.
  Records without an abstract in an Earth-science subfield are kept and
  screened from the title.
- Keeps every record with the reason it was dropped, so the prefilter can be
  audited and changed.

## 2. Labeling workers

Each worker is a Claude agent (we used Claude Code agents) that gets one
line:

```
Read and follow data/extraction/<run>/prompts/batch_NNN.md
```

The rendered prompt ([labeling/extraction_prompt.md](../labeling/extraction_prompt.md),
[labeling/design_prompt.md](../labeling/design_prompt.md)) gives the paths of
the codebook, schema, input batch, output file, and hard-case log, and tells
the worker to:

1. read the whole codebook;
2. label each paper in input order, writing the labels itself (no scripts or
   keyword rules), treating abstracts as data, and opening no other files;
3. run the validator and fix the failing lines until it prints `OK`;
4. log at most eight borderline decisions;
5. reply with one summary line.

We ran eight workers in parallel. With Claude Opus, an extraction batch of
40 papers took about 7–14 minutes and 120,000–175,000 tokens. With Claude
Sonnet, a study-design batch of 60 papers took about 2 minutes and
90,000–105,000 tokens.

The workers read the full codebook: the rule text for every axis, with worked
examples. [codebook.md](../codebook.md) summarizes it axis by axis, including
every value and the rules applied at build time.

## 3. Pilot (two independent runs)

```bash
# Stratified sample of 120 candidates
python scripts/make_pilot_batches.py --corpus data/interim/corpus_$T.parquet \
    --out-dir data/extraction/pilot \
    --quota Nature=7 NatGeo=7 NatComms=10 CommsEE=6 Science=6 SciAdv=6 \
            JGR-SE=14 GRL=14 GJI=14 BSSA=12 SRL=12 TSR=6 Seismica=6
# Two run directories over the same input, prompts rendered for each
for R in A B; do
  mkdir -p data/extraction/pilot/$R && cp -r data/extraction/pilot/input data/extraction/pilot/$R/
  python scripts/render_prompts.py --template labeling/extraction_prompt.md \
      --run-dir data/extraction/pilot/$R --codebook <codebook> \
      --schema labeling/extraction.schema.json \
      --validator scripts/validate_extraction.py --python "$(which python)"
done
# ... one worker per prompt in A and in B ...
python scripts/compare_extractions.py --a data/extraction/pilot/A/output \
    --b data/extraction/pilot/B/output --out data/extraction/pilot/disagreements.csv
```

`compare_extractions.py` reports agreement on inclusion, kappa for
single-choice fields, and the mean overlap of label sets for multi-choice
fields, and lists the papers whose inclusion or target differs. Read these
papers and the hard-case logs, revise the codebook, and repeat on a fresh
sample until the remaining disagreements are boundary cases.

## 4. Full extraction

```bash
RUN=data/extraction/2021-2025
python scripts/make_batches.py --corpus data/interim/corpus_$T.parquet --out-dir $RUN/input
# Pin the frozen codebook, template, and schema next to the outputs
cp <codebook> $RUN/codebook_used.md
cp labeling/extraction_prompt.md $RUN/prompt_template_used.md
cp labeling/extraction.schema.json $RUN/schema_used.json
python scripts/render_prompts.py --template $RUN/prompt_template_used.md --run-dir $RUN \
    --codebook $RUN/codebook_used.md --schema $RUN/schema_used.json \
    --validator scripts/validate_extraction.py --python "$(which python)"
# ... one worker per prompt; re-run any batch whose output is missing or invalid:
python scripts/validate_extraction.py --schema $RUN/schema_used.json \
    --input $RUN/input/batch_000.jsonl --output $RUN/output/batch_000.jsonl
```

The validator checks the schema, one output record per input paper in the
same order, and consistency across fields: targets agree with method-use
targets, source–structure links appear only for papers with both targets,
network references exist, and magnitude fields agree with each other.

## 5. Study-design pass

Runs on the included papers of a database built from the extraction outputs
(step 7 without `--design-dirs`).

```bash
# Pilot: 120 papers, half from Nature/Science-family journals; two runs; compare
python scripts/make_design_batches.py --db data/db/seismo_kg.sqlite \
    --out-dir data/design/pilot/A/input --sample 120
mkdir -p data/design/pilot/B && cp -r data/design/pilot/A/input data/design/pilot/B/
# ... render prompts and run workers in A and B as in step 3 ...
python scripts/compare_design.py --a data/design/pilot/A/output --b data/design/pilot/B/output
# Full pass
python scripts/make_design_batches.py --db data/db/seismo_kg.sqlite \
    --out-dir data/design/2021-2025/input
python scripts/render_prompts.py --template labeling/design_prompt.md \
    --run-dir data/design/2021-2025 --codebook <design codebook> \
    --schema labeling/design.schema.json \
    --validator scripts/validate_design.py --python "$(which python)"
```

For a cheaper model, render the batches it will label from its own template
(for Sonnet, [labeling/design_prompt_sonnet.md](../labeling/design_prompt_sonnet.md),
which restates three rules of the codebook without changing them), and record
which model labeled each batch. The check that comes first is described in
[roadmap stage 5](roadmap.md#5-check-a-cheaper-labeling-model).

## 6. From text to terms

The workers write values from a fixed vocabulary, so the labels are already
terms. `build_db.py` turns them into the incidence list the graph is built
from:

| Field in the worker output | Term on the graph |
|---|---|
| Vocabulary values (target, source type, sensor, distance, ...) | Used as they are; labels and definitions from `config/vocab.csv` |
| Magnitude range, verbal size, mainshock magnitude | Magnitude class (M < 2, 2–4, 4–6, 6–8, ≥ 8); mainshock − 2 for foreshock and aftershock studies that give only the mainshock |
| Focal-event names (free text) | Canonical event: normalized key, then `config/focal_event_aliases.csv`; shown when studied by at least five papers |
| Method names (free text) | Kept in the database; the graph uses the method family from the vocabulary |
| "Not stated" values | Kept in the database, hidden on the graph |

The database table `paper_concepts` (doi, axis, value, use_id, net_id) holds
one row per term carried by an included paper. `use_id` and `net_id` tie a
term to one method use or one observation network, so terms that appear in
the same analysis can be told apart from terms that only share a paper.
`config/extraction_corrections.csv` holds per-paper fixes applied at build
time; each row must match the value it replaces, or the build stops.

## 7. Database and page

```bash
python scripts/build_db.py \
    --corpus data/interim/corpus_2000-01-01_2020-12-31.parquet data/interim/corpus_$T.parquet \
    --extraction-dirs data/extraction/2000-2020/output data/extraction/2021-2025/output \
    --design-dirs data/design/2000-2020/output data/design/2021-2025/output \
    --journals config/journals.csv --vocab config/vocab.csv \
    --focal-event-aliases config/focal_event_aliases.csv \
    --corrections config/extraction_corrections.csv \
    --out data/db/seismo_kg.sqlite
python scripts/make_kg.py --db data/db/seismo_kg.sqlite \
    --template scripts/templates/knowledge_graph.html \
    --period "2000–2025" --out index.html
```

The database is rebuilt from scratch on every run. If a paper appears in more
than one batch, its last record is used. The page is one self-contained HTML
file.

## Files

| Path | Role |
|---|---|
| `index.html` | The published page (GitHub Pages) |
| `codebook.md` | Summary of the labeling rules and build-time rules, by graph axis |
| `docs/roadmap.md` | Stages, checks before each next stage, status, next steps |
| `config/journals.csv` | Journals: OpenAlex source, ISSN, DOI patterns, journal group |
| `config/openalex_extra_sources.csv` | OpenAlex sources that hold a journal's older volumes |
| `config/prefilter.json` | Keyword prefilter for candidates |
| `config/vocab.csv` | Every axis value with its page label and definition |
| `config/focal_event_aliases.csv` | Focal-event alias → canonical name |
| `config/extraction_corrections.csv` | Per-paper fixes applied at build time |
| `labeling/*_prompt.md` | Worker prompt templates |
| `labeling/*.schema.json` | JSON schemas of the worker outputs |
| `scripts/fetch_openalex.py` | Download OpenAlex records per journal and date window |
| `scripts/fetch_s2_abstracts.py` | Fill missing abstracts from Semantic Scholar |
| `scripts/build_corpus.py` | Corpus with abstracts and prefilter decisions |
| `scripts/audit_collection.py` | Completeness and abstract coverage per journal and window |
| `scripts/make_pilot_batches.py` | Stratified pilot sample for extraction |
| `scripts/make_batches.py` | Shuffled extraction batches |
| `scripts/make_design_batches.py` | Study-design batches (full or pilot sample) |
| `scripts/render_prompts.py` | One prompt per batch from a template |
| `scripts/validate_extraction.py`, `scripts/validate_design.py` | Output validators run by the workers |
| `scripts/compare_extractions.py`, `scripts/compare_design.py` | Agreement between two runs |
| `scripts/build_db.py` | SQLite database and graph terms |
| `scripts/make_kg.py`, `scripts/templates/knowledge_graph.html` | The page |
