# Codebook: what the graph terms mean

Terms were assigned by a large language model from each paper's title and
abstract, in two passes:

1. Screening and extraction, on all 9,438 candidates: inclusion, targets,
   source types, observation networks, and method uses with their
   magnitudes, distances, and data types.
2. Study design, on the 5,272 included papers: primary contribution,
   spatial scope, time design, data origin, focal events, and tectonic
   setting.

The rules below are those given to the model, shortened and grouped as in
the page legend. Terms appear here under the labels used on the page.

General rules:

- Only the title and abstract are used. Outside knowledge is allowed only
  for magnitudes and years of well-known named events, attributes of
  well-known named networks or missions, and the tectonic setting of named
  regions.
- Labels describe what the paper itself does, not prior work it cites.
- Papers without a usable abstract (missing, under 30 words, or not an
  abstract) are judged from the title with low confidence, and methods are
  recorded only if the available text names them or states results that
  imply them.

## 1. Which papers are included

A paper is included when it analyzes seismic sources, Earth or planetary
structure, or both:

- **Source**: characterizes seismic sources themselves: occurrence
  (detection, location, catalogs, seismicity patterns, statistics,
  forecasting, triggering), size, mechanism, rupture process, source spectra
  and stress drop, directivity, slip, and the physics of observed events. Any
  seismic source counts: earthquakes, induced events, tremor, LFEs, slow slip,
  volcanic events, explosions, landslides, glacial events, impacts, and
  continuous or environmental sources (microseisms, rivers, storms, traffic,
  animals) when the study characterizes the generating process.
- **Structure**: infers properties of the medium from seismic observations
  or from existing seismic models: velocity, attenuation, anisotropy,
  scattering, interfaces, fault-zone structure, fluids and melt, near-surface
  shear-wave velocity, ice or planetary interiors, and temporal changes of
  the medium (e.g., dv/v).

Also included: method papers (on real or synthetic data only); earthquake
early warning that estimates source parameters; ground-motion analyses that
infer source or medium properties; geodetic, tsunami, paleoseismic, or
macroseismic analyses of specific earthquakes and their postseismic
processes; rupture or cycle simulations constrained by data from a specific
earthquake; interpretations of existing seismic models or catalogs that use
them as quantitative constraints; and method or instrument evaluations that
report any source or structure result.

Excluded, with the first reason that applies:

1. Non-research items: editorials, news, comments and replies, corrections,
   reviews, perspectives, meeting reports.
2. Laboratory experiments (stick-slip, acoustic emission, rock physics) and
   models of them.
3. Ground-motion and hazard studies that infer no source or medium property:
   ground-motion models, site response for hazard, hazard and risk,
   engineering response, and empirical relations built as hazard input.
   Seismicity forecasting and forecast testing are source studies and are
   included.
4. Effects only: triggered landslides, liquefaction, hydrology, ionosphere,
   damage, society.
5. Instruments, network operations, and data infrastructure, without source
   or structure results.
6. Generic theory or simulations not tied to observed events or seismic
   data.
7. Non-seismic studies, with no seismic observations, no seismic models,
   and no specific earthquake: structure from magnetotellurics, gravity, or
   geology; geodynamics; interseismic strain or coupling.
8. Other (e.g., helioseismology, seismic metamaterials).

## 2. Target and study design

### Target

**Source** and **Structure**, as defined in section 1. A paper with results
on both carries both terms and is counted under "Both" in the Target filter.
Fault geometry outlined by hypocenters or mechanisms (fault planes, slab
surfaces lit up by seismicity) is a source result. Rheology or viscosity
inferred from postseismic or loading deformation is a structure result.

### Source–structure link

Only for papers with both targets; one or more of:

- **Joint estimation**: one inversion estimates source and structure
  parameters together (e.g., simultaneous hypocenter–velocity inversion).
- **Structure → source**: structure results are used to obtain or interpret
  source results (e.g., a new 3-D model improves locations; velocity
  anomalies explain rupture segmentation or swarms).
- **Source → structure**: source results are used to obtain or interpret
  structure results (e.g., relocated events or repeaters used for imaging or
  monitoring; source parameters needed for attenuation; postseismic slip
  used to infer viscosity).
- **Source changes medium**: the events change the medium and the study
  measures it (e.g., coseismic velocity drop and healing, damage zones).
- **Parallel**: both analyzed side by side, neither feeding the other.

Each of these papers also has a one-line note on the link, shown in the
"Source ↔ structure" tab.

### Primary contribution (one per paper)

What the paper mainly adds, as emphasized by its title and main conclusion:

- **Observation & discovery**: characterizes what is observed: images a
  structure; characterizes an earthquake, sequence, or region; detects or
  reports a phenomenon. Most case studies and regional imaging studies.
- **Explanation & testing**: the main result is a cause, mechanism, or tested
  hypothesis, e.g., "fluid pressure diffusion explains the migration". A
  mechanism offered only as an interpretation of an observation stays under
  Observation & discovery.
- **Synthesis**: generalizes across many events, regions, or studies:
  scaling relations, global compilations, statistical laws, meta-analyses.
- **Method**: proposes, improves, benchmarks, validates, or calibrates an
  analysis method (incl. machine-learning models and magnitude calibration).
- **Resource & operations**: the main product is a resource or an
  operational capability: catalogs, datasets, reference models, software,
  monitoring and early-warning systems, network performance in operation.

### Spatial scope (one per paper)

How far the conclusions reach: **Single event**; **Sequence / episode** (one
sequence, swarm, eruption, or slow-slip episode); **Local area** (one site,
fault zone, volcano, or field, up to ~100 km); **Region** (~100–2000 km, e.g.,
a subduction segment, an orogen, a country); **Continental / global** (or
many regions); **Planetary body**; not applicable for synthetic-only or
generic method papers.

### Time design (one per paper)

- **Snapshot**: one time window treated as static.
- **Time-lapse**: tracks change over time (monitoring, before/after, the
  evolution of a sequence, temporal change of the medium).
- **Historical / paleo**: historical records, paleoseismology, or decades-long
  archives are the core.
- **Real-time**: real-time or near-real-time processing is the core.

### Data origin (one or more)

- **New data acquisition**: the authors deployed instruments or collected new
  data (temporary arrays, nodes, OBS, DAS experiments, field or active-source
  surveys).
- **Existing archive**: data from existing networks or public archives.
- **Reanalysis of published results**: published catalogs, models,
  mechanisms, or results reanalyzed or compiled.
- **Synthetic only**: synthetic data or simulations only.

### Tectonic setting (one to three per paper)

Assigned from the study area, using common knowledge of named regions (e.g.,
northeastern Japan → subduction zone; Ridgecrest → continental transform;
Oklahoma → stable continental interior; Iceland → mid-ocean ridge and
hotspot). Volcanoes and ice shelves take the setting of their region.

- **Subduction zone**: megathrust, forearc, slab (incl. intermediate-depth
  and deep earthquakes), volcanic arc, back-arc.
- **Continental collision**: collision zones and intracontinental orogens
  (Himalaya–Tibet, Zagros, Alps, Tian Shan, Taiwan).
- **Continental transform**: continental strike-slip plate boundaries (San
  Andreas system, North Anatolian, Alpine Fault, Dead Sea).
- **Oceanic transform**: oceanic transform faults and fracture zones.
- **Mid-ocean ridge**: spreading ridges.
- **Continental rift / extension**: rifts and extensional provinces (East
  African Rift, Basin and Range, Aegean, Baikal).
- **Hotspot / intraplate volcanism**: hotspots, plumes, intraplate volcanism
  (Hawaii, Yellowstone, Iceland, Canary Islands).
- **Stable continental interior**: cratons, platforms, intraplate basins and
  failed rifts (central and eastern US incl. Oklahoma, Australia,
  Fennoscandia, North Sea).
- **Passive margin**: rifted continental margins and their basins.
- **Oceanic plate interior**: away from plate boundaries.
- **Deep interior**: lowermost mantle, core, or whole-mantle structure.
- **Global / multi-setting**: global studies or compilations across many
  settings.
- **Planetary (setting)**: other planetary bodies.

Global / multi-setting and Planetary (setting) are used alone. Deep interior
is combined with a surface setting only when the text ties the structure to
a named region.

## 3. Methods

### How methods are recorded

Methods are anchored on results. For each result the abstract reports, the
method that produced it is recorded: the named technique, or the method
implied by the result (e.g., "focal mechanisms show ..." implies mechanism
determination; "a low-velocity zone beneath ..." implies velocity imaging).

- One entry per distinct technique. Pipeline stages (picking, association,
  location, relocation, magnitude, mechanisms) are listed separately when
  the abstract names them.
- Non-waveform techniques count: InSAR or GNSS slip inversion, Coulomb stress
  modeling, ETAS, b-values, paleoseismic trenching, macroseismic analysis.
- Not recorded: generic actions without a result ("we analyze seismic
  data"), methods cited as background, routine preprocessing and quality
  control, synthetic or resolution tests, and uncertainty analysis.
- A technique applied to events of different magnitudes (e.g., mainshock
  vs. aftershocks) or for different targets gives separate entries.
- Source type, magnitude, distance, and data type are recorded for each
  method use.

### Method family

Source families:

- **Detection & cataloging**: event detection, template matching, repeating
  events, catalog building.
- **Picking & association**: phase and polarity picking, phase association.
- **Location**: absolute or relative location, relocation, tremor location.
- **Magnitude & size**: magnitude, moment, yield, size, early-warning
  magnitude.
- **Mechanism & MT**: focal mechanisms, moment tensors, source type.
- **Source spectra & energy**: corner frequency, stress drop, radiated
  energy, source scaling.
- **Rupture kinematics**: finite-fault slip, back-projection, source time
  functions, directivity, rupture speed.
- **Geodetic/tsunami deformation**: coseismic, postseismic, or slow-slip
  deformation and slip from geodetic or tsunami data (incl. viscosity from
  postseismic data).
- **Seismicity statistics & forecasting**: b-value, completeness, rates,
  ETAS, declustering, forecasting and forecast testing.
- **Seismicity patterns**: descriptive spatiotemporal patterns, migration,
  swarms.
- **Stress & triggering**: static, dynamic, or poroelastic stress change and
  triggering.
- **Stress field**: stress tensor inversion, stress state.
- **Event classification**: classification, discrimination, signal
  characterization.
- **Rupture/cycle simulation**: dynamic rupture or earthquake-cycle
  simulation constrained by observations.
- **Paleo & historical**: paleoseismology, historical and macroseismic
  analysis.
- **Non-EQ source modeling**: physical modeling of non-earthquake sources
  (landslide force inversion, glacial, eruption, environmental sources).

Structure families:

- **Body-wave tomography**: travel-time or finite-frequency body-wave
  tomography (local earthquake, teleseismic, Vp/Vs).
- **Surface-wave tomography**: surface-wave dispersion and tomography from
  earthquakes or ambient noise; dispersion inversion for Vs.
- **Waveform inversion & modeling**: full-waveform inversion, adjoint
  tomography, waveform modeling of structure.
- **Interface imaging (RF etc.)**: receiver functions, CCP stacking,
  H-kappa, SS/PP precursors, autocorrelation, other converted or reflected
  phases.
- **Deep-Earth phases & modes**: core and lowermost-mantle phases, inner
  core, normal modes.
- **Anisotropy**: shear-wave splitting, anisotropic tomography or receiver
  functions.
- **Attenuation & scattering**: Q, scattering, coda analysis.
- **Temporal medium change**: dv/v and other temporal changes of the medium.
- **Active-source imaging**: controlled-source reflection, refraction, and
  wide-angle profiling (full-waveform inversion goes to Waveform inversion &
  modeling).
- **Near-surface characterization**: H/V, SPAC, MASW, shallow Vs profiles,
  sediment thickness.
- **Fault-zone structure**: fault geometry from seismicity or imaging,
  fault-zone waves, damage zones. Fault geometry outlined by hypocenters or
  mechanisms also falls here, although its target is Source.
- **Structure interpretation**: interpretation of seismic models
  (temperature, composition, melt, fluids), geodynamic or rock-physics
  modeling constrained by seismic observations, reference models.
- **Joint geophysical inversion**: seismic data inverted jointly with
  non-seismic geophysical data for structure.

**Other method**: anything else.

## 4. Source type, magnitude, and focal event

### Source type

Every type of source whose signals are analyzed (source target) or used as
the energy source (structure target):

- **Tectonic EQ**: natural tectonic earthquakes at any depth.
- **Induced EQ**: fluid injection or extraction, hydraulic fracturing,
  geothermal, reservoir impoundment, CO2 storage, gas fields.
- **Mining**: mining-induced events, rockbursts.
- **Volcanic**: volcano-tectonic, long-period, very-long-period, volcanic
  tremor, eruption signals; only when the abstract ties the events to
  volcanic or magmatic processes, otherwise Tectonic EQ. LFEs and tremor tied
  to magma are Volcanic.
- **Tremor/LFE/slow slip**: tectonic tremor, LFEs, VLFEs, slow slip, slow
  earthquakes, triggered aseismic slip and creep.
- **Explosion**: nuclear, chemical, quarry, and accidental explosions studied
  as sources.
- **Active source**: controlled sources used to probe the medium (airguns,
  vibroseis, shots, hammers).
- **Ambient noise**: the noise wavefield used as a probe (interferometry,
  H/V, noise-based monitoring), without characterizing its generation.
  Noise-only methods get this term even when the abstract does not say so.
- **Landslide**: landslides, rockfalls, debris flows, turbidity currents.
- **Glacial**: icequakes, glacial earthquakes, calving, ice-shelf events.
- **Environmental**: generating processes of continuous signals studied as
  sources: ocean microseisms, surf, rivers, storms, atmosphere, animals,
  traffic, industry.
- **Planetary**: marsquakes, moonquakes, other planetary seismicity.
- **Other non-EQ**: impacts, bolides, re-entry and sonic booms, collapses,
  seiches.

### Magnitude

Magnitudes are recorded for each method use and refer to the events the
method characterizes (source target) or to the earthquakes whose waves were
used (structure target, e.g., "teleseismic events with Mw ≥ 5.5" for
receiver functions).

Each method use gets one representative magnitude:

- the midpoint of a stated range, or the single stated value;
- the bound when only one is stated ("M ≥ 2" → 2; "generally M < 3" → 3);
- for foreshocks, aftershocks, or a sequence where only the mainshock
  magnitude is given: mainshock magnitude minus 2;
- for a well-known named event whose magnitude the abstract omits: the
  widely reported value (USGS or GCMT Mw), only when the labeler is
  confident;
- seismic moment without a magnitude is converted to Mw.

A threshold that splits the events into classes (e.g., small M < 5.5 vs.
large M ≥ 5.5) is not a bound. Phenomena triggered by a separate event
(remote triggering, triggered slow slip) get no estimate from that event.
Without a number, a verbal descriptor sets the class (micro, small,
moderate, large, great); it also takes precedence over the mainshock minus 2
estimate because it describes the analyzed events themselves.

Classes: **M < 2**, **M 2–4**, **M 4–6**, **M 6–8**, **M ≥ 8** (lower edge
inclusive, e.g., 2 ≤ M < 4).

When no discrete earthquakes are involved, the term records why:
**Active source (no M)**, **Ambient noise (no M)**, or **Continuous/other
(no M)** (continuous signals such as tremor episodes or microseisms, or
non-seismic data on structure). Discrete LFEs and slow-slip events with a
magnitude are events.

### Focal event (up to three per paper)

Specific named earthquakes or sequences that are a subject of the study (not
a passing mention), written as "year name" (e.g., "2019 Ridgecrest", "2023
Kahramanmaras"). Studies of regions, multi-event catalogs, or methods have
none.

## 5. Networks

Network terms come from the observation systems the abstract describes (a
network, array, deployment, cable, mission, or data archive); seismic and
non-seismic systems both count. Papers that say nothing about instruments
carry no network terms (2,935 of the 5,272 papers carry at least one).
Attributes of well-known named systems may be filled from knowledge (e.g.,
Hi-net → borehole, permanent).

### Sensor

**Broadband**; **Short-period** (short-period seismometers or geophones, not
nodes); **Nodal geophones** (autonomous nodes, large-N arrays); **Strong
motion** (accelerometers); **DAS / fiber** (DAS and other fiber-optic
sensing on cables); **Rotational**; **Low-cost / MEMS** (MEMS, Raspberry
Shake, smartphones, citizen sensors); **Hydroacoustic** (hydrophones,
floats such as MERMAID); **Infrasound**; **GNSS**; **InSAR / remote sensing**
(InSAR, optical or LiDAR imagery); **Strain / tilt** (strainmeters,
tiltmeters, creepmeters); **Gravity**; **Ocean pressure / tide** (tide
gauges, DART, ocean-bottom pressure); **Analog / historical** (historical
seismograms); **Seismometer (type n/s)** (seismic stations of unstated
type); **Other sensor**.

### Installation setting

**Land surface**; **Borehole**; **Ocean bottom** (OBS, seafloor cables and
geodesy); **Ocean water column** (floats, moored hydrophones);
**Underground** (mines, tunnels, underground labs); **Ice / glacier**;
**Urban** (only when the text stresses an urban setting); **Planetary**;
**Airborne / space** (balloons, satellites).

Onshore networks with no location cue in the text were labeled
inconsistently, sometimes Land surface and sometimes "not stated" (not
shown), so the Land surface node undercounts land networks.

### Deployment

- **Permanent network**: permanent local, regional, or national networks
  and observatories.
- **Global network**: global networks or global datasets.
- **Temporary campaign**: planned temporary deployments, incl. rolling
  arrays such as USArray TA and controlled-source surveys.
- **Rapid response**: deployed after an event or unrest.
- **Industry monitoring**: operator monitoring of injection, geothermal,
  mining, or storage sites.
- **Opportunistic**: infrastructure not built for seismology (telecom or dark
  fiber, even when accessed after an event; smartphones, citizen sensors).
- **Planetary mission**: satellite or planetary missions.
- **Archival**: historical or analog archives.

### Station density

Typical station or channel spacing, from numbers when given, otherwise from
explicit words ("dense", "large-N", "single station"): **Single station**;
**Sparse (≥100 km)**, e.g., global networks; **Regional (10–100 km)**, typical
permanent networks; **Dense (1–10 km)**; **Ultra-dense (≤1 km)**: large-N
nodal arrays, DAS channels, small-aperture arrays.

## 6. Distance and data type

### Distance

Source–receiver distance of the data a method uses (station-pair distance
for noise interferometry): **Near-source** (within a few km or within the
source dimension: in-mine, in-borehole, near-fault arrays); **Local** (up to
~200 km); **Regional** (~200–2000 km, up to ~20°); **Teleseismic** (beyond
~20–30°, incl. global data and core phases).

Distances are taken from the text, or inferred only in these cases:

- methods used at one distance range: SKS splitting, and receiver functions
  or tomography with teleseismic events → Teleseismic; local earthquake
  tomography → Local;
- local events (induced, aftershocks, swarms, volcanic, LFEs, mining)
  recorded by a local network with no other distances involved → Local, or
  Near-source when the sensors sit within a few km of the events;
- controlled-source surveys → Local unless longer offsets are stated.

### Data type

**Seismic waveforms** (seismograms, spectra, noise correlations, DAS, strong
motion); **Picks / catalogs** (existing picks, travel times, catalogs,
mechanism catalogs); **Seismic models** (existing models); **Geodetic**;
**Tsunami**; **Geologic**; **Macroseismic / historical**; **Other data**.

## 7. From labels to the graph

- Terms are pooled per paper. A paper with two method uses carries the terms
  of both, so an edge between two terms does not mean they belong to the
  same method use or network.
- Data origin: Synthetic only is dropped when a real-data origin is also
  listed.
- Focal events: names are merged across spelling variants and aliases (e.g.,
  "2015 Nepal" and "2015 Gorkha"); events studied by at least 5 papers are
  shown.
- Values meaning "not stated", "not applicable", or "unspecified" are not
  shown in the graph, matrix, or partner lists.
