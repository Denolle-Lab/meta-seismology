# Observational Seismology Study Graph

**Live page: https://denolle-lab.github.io/meta-seismology/**

A prototype built from observational seismology studies: an interactive map
of how these studies combine targets (seismic source, Earth structure, or
both), methods, magnitudes, distances, sensors, deployments, and study
designs. Each node is a term (for example "DAS / fiber", "M 2–4", or
"Surface-wave tomography"); two terms share an edge when the same paper
carries both. Each edge also shows how many of those papers use the two terms
in the same analysis (one method together with the data and instruments it
uses), and the graph can show only those links. The page also shows a
term-by-term matrix, which can likewise count only pairs in the same
analysis, and the papers that link source and structure.

## Corpus

- Period: 2000–2025 (OpenAlex publication date). Journals that started
  after 2000 are covered from their first year.
- Journals (13): seven specialist journals (BSSA, SRL, The Seismic Record,
  JGR: Solid Earth, GRL, GJI, Seismica) and six from the Nature and Science
  families (Nature, Nature Geoscience, Nature Communications, Communications
  Earth & Environment, Science, Science Advances).
- 39,446 candidate papers screened; 20,558 included as studies of seismic
  sources, Earth structure, or both.

The graph maps seismology tied to observations, not earthquake physics as a
whole:

- Included: rupture and earthquake-cycle simulations constrained by
  observed data (298 papers), and papers that use only synthetic data,
  almost all of them analysis-method papers (983).
- Excluded: laboratory earthquake experiments and models of them (2,040
  candidates), unless mineral-physics results are fitted quantitatively to
  seismic observations; generic theory and simulations not tied to observed
  events or seismic data, such as generic rupture dynamics, friction laws, or
  wave theory (2,772). Other exclusions: non-seismic studies (5,448),
  ground-motion and hazard studies (2,225), non-research items (3,861),
  instruments and data infrastructure (1,340), effects of earthquakes only
  (546), and other topics (656).

## How the labels were made

Bibliographic records came from OpenAlex, with missing abstracts filled from
Semantic Scholar where available. A large language model (Anthropic Claude)
read each title and abstract and assigned terms following the rules in
[codebook.md](codebook.md). Most terms were assigned by Claude Opus. For
10,066 of the 15,286 included papers from 2000–2020, the study-design terms
(primary contribution, spatial scope, time design, data origin, tectonic
setting, focal event) were assigned by the smaller Claude Sonnet, following
the same rules. Every output was checked automatically for format and
allowed values. The stages of the work, with the checks made before each next
stage, are in [docs/roadmap.md](docs/roadmap.md); the commands are in
[docs/pipeline.md](docs/pipeline.md).

To check consistency, 120 papers from 2021–2025 and 120 from 2000–2020 were
labeled twice, independently, before the full runs. The two runs made the
same inclusion decision for 97% and 99% of these papers; for 2021–2025 they
also chose the same primary contribution for 96%. On the other axes, their
terms matched 87–100% on average, depending on the axis. On 120 papers from
2000–2020 labeled by both models, Opus and Sonnet chose the same primary
contribution for 90% and the same spatial scope for 95%; their other
study-design terms matched 90–94% on average.

## Limitations

- **Machine labels.** Every term was assigned by a language model from the
  title and abstract only, not the full text, and was not checked paper by
  paper. The one-line notes on how source and structure are linked are also
  model-written.
- **Two labeling models.** Opus and Sonnet labeled random subsets of the
  2000–2020 papers (5,220 and 10,066). Their shares of each study-design
  term agree within 2 percentage points, except two data-origin terms:
  Sonnet chose "Reanalysis of published results" more often (24% vs. 21%)
  and "New data acquisition" less often (18% vs. 21%). Compare these two
  terms across periods with care.
- **Abstract style of Nature- and Science-family journals.** Their abstracts
  rarely name methods, instruments, networks, or magnitudes, so these papers
  carry fewer terms and their methods are under-counted. Their high share of
  "Explanation & testing" as the primary contribution (30%, vs. 12% in
  specialist journals) partly reflects how these abstracts are written.
- **Missing abstracts.** About 90% of the candidate Nature and Nature
  Geoscience papers have no abstract in OpenAlex or Semantic Scholar. Such
  papers were screened from the title; 392 included papers were labeled from
  the title only (172 Nature Geoscience, 163 Nature, 57 in seven other
  journals).
- **Installation setting.** Onshore networks with no location cue in the
  text were labeled inconsistently, sometimes "Land surface" and sometimes
  "not stated" (not shown): 5,060 papers carry Land surface and 4,919 carry
  "not stated". The Land surface node therefore undercounts land networks; the
  other installation settings are not affected.
- **Citations** per year are from OpenAlex snapshots of 2026-10-22 (papers
  from 2021–2025) and 2026-10-29 to 2026-10-30 (papers from 2000–2020).

## Future directions

The labels now come from titles and abstracts only, and from 13 selected
journals. The graph can grow in several directions:

- Read full texts as well as titles and abstracts, and cover more journals.
- Broaden the scope from observational studies to seismology as a whole,
  adding laboratory earthquake experiments, rock and mineral physics
  experiments, earthquake modeling, and geodynamic and tectonic modeling.
- Extend the corpus further back in time, before 2000.
- Add views that show how research has advanced over time: the development
  of methods, the spatial growth of seismic networks, the use of dense data
  such as DAS and nodal arrays, and the widening range of what is observed,
  such as active (controlled) sources.

Planned next steps, including a check that a smaller model reproduces the
graph made with Claude Opus before it labels a large corpus, are in
[docs/roadmap.md](docs/roadmap.md#next-steps).

## What the terms mean

Click a term on the page for its one-line definition.
[codebook.md](codebook.md) gives the full labeling rules for every axis,
grouped as in the page legend, and the rules applied when the graph is built (for
example, how magnitude classes are assigned).

## Repository

```
index.html        the page (served by GitHub Pages)
codebook.md       labeling rules and build-time rules, by graph axis
docs/             roadmap and pipeline
config/           journals, prefilter, vocabulary, aliases, corrections
labeling/         worker prompt templates and output schemas
scripts/          collection, batching, validation, agreement, database, page
environment.yml   Python environment for the scripts
```

The repository holds no data files; [docs/pipeline.md](docs/pipeline.md)
gives the commands for every stage, from the public APIs to the page.

## Data and rights

- The page contains bibliographic metadata only (DOI, title, journal, year,
  citation counts, field-weighted citation impact) from
  [OpenAlex](https://openalex.org) (CC0), plus the terms assigned by this
  project and, for papers with both targets, a one-line note on how source
  and structure are linked. No abstracts or full texts are redistributed.
- Paper titles link to the publisher's page through doi.org.

## Contact

Denolle Research Lab, University of Washington.
Maintainer: [Seismic-wave-Han](https://github.com/Seismic-wave-Han).
