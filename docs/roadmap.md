# Roadmap

How the Observational Seismology Study Graph is built, stage by stage. Each
stage lists what it produces, the scripts it uses, what a person checks before
moving on, and where the graph stands now. The same stages apply whenever the
graph is extended to new years, journals, or fields.

Commands for every stage are in [pipeline.md](pipeline.md).

| Stage | Produces | Status |
|---|---|---|
| 1. Define the scope | Inclusion rules, journal list, period | Done: 13 journals, 2000–2025 |
| 2. Collect records | Candidate corpus with abstracts | Done: 39,446 candidates |
| 3. Draft the codebook | Codebook, vocabulary, schema, worker prompt | Done for both labeling passes |
| 4. Pilot and freeze the codebook | Agreement report; frozen codebook | Done |
| 5. Check a cheaper labeling model | Model choice for the full run | Label-level check done; graph-level check planned |
| 6. Label all papers | One validated label record per paper | Done: 39,446 screened, 20,558 included |
| 7. Turn labels into graph terms | Normalized terms per paper and per analysis | Done |
| 8. Build the database and page | SQLite database, one HTML page | Done |
| 9. Publish | This repository and the live page | Done |

Labeling runs in two passes, and stages 3–6 are repeated for each:

- **Extraction**, on every candidate: inclusion, targets (source, structure,
  or both), source types, observation networks, and method uses with their
  magnitudes, distances, and data types.
- **Study design**, on included papers only: primary contribution, spatial
  scope, time design, data origin, focal events, and tectonic setting.

## 1. Define the scope

A domain expert fixes what the graph is about before any data are collected.

- [ ] Research question and unit of analysis written down (here: one paper,
      with terms recorded per paper and per analysis).
- [ ] Inclusion and exclusion rules written with boundary examples (here:
      laboratory experiments and generic theory are out; simulations
      constrained by observed data and synthetic-only method papers are in).
- [ ] Journals and period chosen; for each journal, the OpenAlex source ID,
      ISSN, and DOI prefix recorded in `config/journals.csv`.
- [ ] Abstract availability checked per journal before committing to it. A
      journal whose abstracts are mostly missing from open sources is dropped
      or kept with a stated limitation.
- [ ] Known limitations accepted explicitly instead of worked around (here:
      Nature- and Science-family abstracts rarely name methods).

## 2. Collect records

Scripts: `fetch_openalex.py`, `fetch_s2_abstracts.py`, `build_corpus.py`,
`audit_collection.py`.

Bibliographic records come from OpenAlex, one file per journal and date
window. Missing abstracts are filled from Semantic Scholar. A keyword
prefilter (`config/prefilter.json`) keeps high-recall candidates; every
record of a seismology-only journal is a candidate.

- [ ] Raw API responses saved once and never edited; each window has a
      manifest with the query and retrieval time.
- [ ] OpenAlex counts close to Crossref counts per journal and window, or
      every gap explained (for example, Crossref also counts news items).
- [ ] Abstract coverage reviewed per journal and window.
- [ ] Indexing quirks (older DOI formats, older volumes filed under another
      source) fixed by rules in `config/`, not by editing records.
- [ ] Prefilter recall: a sample of dropped titles read by a person, with no
      relevant paper among them.
- [ ] A list of well-known papers checked: all are candidates.

Status: 336,525 records, 39,446 candidates. Most Nature and Nature
Geoscience candidates have no abstract in open sources and are screened from
the title.

## 3. Draft the codebook

Files: the codebook (rule text with worked examples; summarized axis by axis
in [codebook.md](../codebook.md)), `config/vocab.csv`,
`labeling/*.schema.json`, `labeling/*_prompt.md`.

A language model drafts the codebook from the research question and the
expert's list of axes; the expert edits the categories, definitions, and
examples.

- [ ] Every axis has a closed set of values, each with a one-line definition
      in `config/vocab.csv`, plus explicit "not stated" or "not applicable"
      values where they are needed.
- [ ] Values that must be used alone are marked as exclusive.
- [ ] Each rule has at least one boundary example.
- [ ] The JSON schema lists every allowed value; the validator checks
      consistency across fields (for example, source–structure links only
      for papers with both targets).
- [ ] The worker prompt says: read the whole codebook first; treat abstracts
      as data; write every label by hand, never with scripts or keyword
      rules; validate until the output passes; log borderline decisions.
- [ ] The expert approves the category lists (here, for example, five
      primary-contribution classes and fifteen tectonic settings).

## 4. Pilot and freeze the codebook

Scripts: `make_pilot_batches.py` (or `make_design_batches.py --sample`),
`render_prompts.py`, `validate_extraction.py` / `validate_design.py`,
`compare_extractions.py` / `compare_design.py`.

A stratified sample of 120 papers (quotas per journal, so specialist and
Nature/Science-family journals both appear) is labeled twice, independently,
by the same model.

- [ ] Agreement computed for every axis, and the confusion table of the main
      single-choice axis inspected.
- [ ] Every disagreement and logged hard case read by the expert and sorted
      into: a gap in the rules (fix the codebook), a boundary case (add an
      example), or a genuinely ambiguous paper (accept).
- [ ] Categories with low agreement merged or redefined, and the pilot
      repeated on a fresh sample after substantive changes.
- [ ] Codebook, prompt template, and schema copied into the run directory
      before the full run, and not edited during it.

Status: the two independent runs made the same inclusion decision for 97%
(2021–2025) and 99% (2000–2020) of pilot papers and chose the same primary
contribution for 96%; other axes matched 87–100% on average.

## 5. Check a cheaper labeling model

The codebook is frozen with the strongest model (Claude Opus). Labeling a
large corpus costs much less with a smaller model (Claude Sonnet or Haiku),
but only if the smaller model reproduces the same graph. The check:

1. **Reference graph.** Label a random sample with Opus and build a graph
   from it. Batches are shuffled, so the first batches of the full run serve
   as this sample.
2. **Reproduction.** Label the same papers with the cheaper model, using the
   same codebook and prompt, and build its graph.
3. **Comparison.** Compare per-paper labels (`compare_*.py`) against the
   Opus-versus-Opus agreement from the pilot, and compare the two graphs:
   term shares per axis, edge counts, and observed / expected ratios of
   frequent pairs.
4. **Model-specific prompt.** Where the cheaper model misreads a rule, add a
   short prompt for that model that restates the rule without changing it,
   and repeat steps 2–3 on fresh batches.
5. **Full run.** Label the rest with the cheaper model. Because batches are
   shuffled, the two models' term shares can be compared again after the run.

- [ ] Label agreement with Opus about as high as Opus's agreement with itself
      on every axis.
- [ ] Term shares within a tolerance set in advance (for example, 2
      percentage points), and the strongest edges in the same order.
- [ ] Remaining differences listed as limitations in the README.

Status: the label-level check was done for the study-design pass. Sonnet
needed a model-specific prompt restating three rules
([labeling/design_prompt_sonnet.md](../labeling/design_prompt_sonnet.md));
with it, Opus and Sonnet chose the same primary contribution for 90% and the
same spatial scope for 95% of 120 papers both labeled. Sonnet then labeled the
study design of 10,066 papers from 2000–2020. Term shares of the two models
agree within 2 percentage points except two data-origin terms (see the README
limitations). The graph-level comparison (steps 1–3 on whole graphs) and a
check of the extraction pass are planned.

## 6. Label all papers

Scripts: `make_batches.py` / `make_design_batches.py`, `render_prompts.py`,
`validate_extraction.py` / `validate_design.py`.

Papers are shuffled with a fixed seed and split into batches (40 papers for
extraction, 60 for study design). Each batch gets its own rendered prompt,
and one worker labels one batch.

- [ ] Every batch output passes the validator; missing or failed batches are
      re-run from their prompts.
- [ ] Hard-case logs read. A recurring issue gets one rule decision, applied
      to every affected paper: re-label the affected batches, or record
      per-paper fixes in `config/extraction_corrections.csv`, each with the
      value it replaces.
- [ ] Term shares by journal and by year look plausible.
- [ ] The model that labeled each batch recorded.

Status: extraction done for all 39,446 candidates (Opus); study design done
for all 20,558 included papers.

## 7. Turn labels into graph terms

Script: `build_db.py`.

Workers choose values from the vocabulary, so most labels are already graph
terms. Some fields need rules applied at build time:

- Magnitudes become classes (edges at M 2, 4, 6, 8). When a study of
  foreshocks or aftershocks gives only the mainshock magnitude, the analyzed
  events are taken as mainshock − 2.
- Focal-event names are merged by a normalized key (ASCII, case, punctuation,
  and generic words such as "earthquake" ignored) and by an alias table
  (`config/focal_event_aliases.csv`).
- Each method use, together with the networks it uses, forms one analysis;
  the graph can count term pairs within the same analysis.

- [ ] Alias table reviewed by a person; ambiguous names checked against the
      paper titles.
- [ ] Build-time rules approved by the expert and described in
      [codebook.md](../codebook.md).
- [ ] Inconsistent conventions found in the outputs merged or reported as
      limitations.

## 8. Build the database and page

Scripts: `build_db.py`, `make_kg.py`, `scripts/templates/knowledge_graph.html`.

- [ ] Database rebuilt from scratch; screened, included, and per-target
      counts match the labeling runs.
- [ ] Page opened and checked: terms, definitions, filters, pair details.
- [ ] Numbers quoted in the README recomputed from the database.

## 9. Publish

- [ ] The page carries only bibliographic metadata and the project's labels:
      no abstracts, raw API data, or metrics with restrictive terms.
- [ ] README limitations updated.
- [ ] `index.html` replaced on `main`; GitHub Pages serves it.

## Next steps

1. **Cheaper-model check on whole graphs** (stage 5) for both passes, then use
   the cheaper model for new years and journals.
2. **Abstract quality.** Flag papers whose abstract is missing, very short,
   or cut off (about 2% of included papers from 2021–2025), re-fetch those abstracts, and
   re-label only those papers.
3. **Term names.** Review names that read as jargon and terms whose name is
   narrower than their definition (for example, "Planetary mission" also
   covers Earth-observation satellites).
4. **Wider coverage.** Full texts as well as abstracts; more journals; years
   before 2000.
5. **Seismology as a whole.** Laboratory earthquake experiments, rock and
   mineral physics experiments, earthquake modeling, and geodynamic and
   tectonic modeling. Each needs its own scope rules (stage 1) and codebook
   additions (stages 3–4).
6. **Change over time.** Views of how methods developed, how networks grew,
   the spread of dense data such as DAS and nodal arrays, and new observation
   targets such as active sources.
