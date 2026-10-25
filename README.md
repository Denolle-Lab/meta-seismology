# Observational Seismology Study Graph

**Live page: https://denolle-lab.github.io/meta-seismology/**

A prototype built from observational seismology studies: an interactive map
of how these studies combine targets (seismic source, Earth structure, or
both), methods, magnitudes, distances, sensors, deployments, and study
designs. Each node is a term (for example "DAS / fiber", "M 2–4", or
"Surface-wave tomography"); two terms share an edge when the same paper
carries both. The page also shows a term-by-term matrix and the papers that
link source and structure.

## Corpus

- Period: 2021–2025 (OpenAlex publication date).
- Journals (13): seven specialist journals (BSSA, SRL, The Seismic Record,
  JGR: Solid Earth, GRL, GJI, Seismica) and six from the Nature and Science
  families (Nature, Nature Geoscience, Nature Communications, Communications
  Earth & Environment, Science, Science Advances).
- 9,438 candidate papers screened; 5,272 included as studies of seismic
  sources, Earth structure, or both.

The graph maps seismology tied to observations, not earthquake physics as a
whole:

- Included: rupture and earthquake-cycle simulations constrained by
  observed data (114 papers), and papers that use only synthetic data,
  almost all of them analysis-method papers (258).
- Excluded: laboratory earthquake experiments and models of them (607
  candidates), unless mineral-physics results are fitted quantitatively to
  seismic observations; generic theory and simulations not tied to observed
  events or seismic data, such as generic rupture dynamics, friction laws, or
  wave theory (615). Other exclusions: non-seismic studies (1,186),
  ground-motion and hazard studies (546), non-research items (501),
  instruments and data infrastructure (383), effects of earthquakes only
  (102), and other topics (226).

## How the labels were made

Bibliographic records came from OpenAlex, with missing abstracts filled from
Semantic Scholar where available. A large language model (Anthropic Claude)
read each title and abstract and assigned terms following the rules in
[codebook.md](codebook.md). Every output was checked automatically for
format and allowed values.

To check consistency, 120 papers were labeled twice, independently, before
the full run. The two runs made the same inclusion decision for 97% of the
papers and chose the same primary contribution for 96%. On the other axes,
their terms matched 87–100% on average, depending on the axis.

## Limitations

- **Machine labels.** Every term was assigned by a language model from the
  title and abstract only, not the full text, and was not checked paper by
  paper. The one-line notes on how source and structure are linked are also
  model-written.
- **Abstract style of Nature- and Science-family journals.** Their abstracts
  rarely name methods, instruments, networks, or magnitudes, so these papers
  carry fewer terms and their methods are under-counted. Their high share of
  "Explanation & testing" as the primary contribution (35%, vs. 12% in
  specialist journals) partly reflects how these abstracts are written.
- **Missing abstracts.** About 80% of Nature and Nature Geoscience abstracts
  are missing from open metadata sources (OpenAlex, Crossref, Semantic
  Scholar). Such papers were screened from the title; 54 included papers
  were labeled from the title only (44 Nature Geoscience, 9 Nature, 1 SRL).
- **Installation setting.** Onshore networks with no location cue in the
  text were labeled inconsistently, sometimes "Land surface" and sometimes
  "not stated" (not shown): 1,144 papers carry Land surface and 1,292 carry
  "not stated". The Land surface node therefore undercounts land networks; the
  other installation settings are not affected.
- **Citations** per year are from the OpenAlex snapshot of 2026-10-22.

## Future directions

The labels now come from titles and abstracts only, and from 13 selected
journals. The graph can grow in several directions:

- Read full texts as well as titles and abstracts, and cover more journals.
- Broaden the scope from observational studies to seismology as a whole,
  adding laboratory earthquake experiments, rock and mineral physics
  experiments, earthquake modeling, and geodynamic and tectonic modeling.
- Extend the corpus back in time, before 2021.
- Add views that show how research has advanced over time: the development
  of methods, the spatial growth of seismic networks, the use of dense data
  such as DAS and nodal arrays, and the widening range of what is observed,
  such as active (controlled) sources.

## What the terms mean

Click a term on the page for its one-line definition.
[codebook.md](codebook.md) gives the full labeling rules for every axis,
grouped as in the page legend, and the rules applied when the graph is built (for
example, how magnitude classes are assigned).

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
