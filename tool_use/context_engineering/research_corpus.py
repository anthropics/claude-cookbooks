"""Synthetic research documents for the context-management cookbook.

Data plus one deterministic appendix generator. Externalized so the notebook
isn't thousands of lines of filler text. Each document is ~110K chars (~40K
tokens) of fictional review content: a short organism-specific narrative
plus a large shared appendix of methodological notes and data tables.

Topic: comparative review of model organisms for longevity/aging research.
The research task is to compare these on lifespan/throughput, genetic
tractability, and translational relevance.
"""

# A reusable methodological footer. Together with _EXTENDED_APPENDIX, sized
# so the full corpus is ~320K tokens across 8 documents. The task reads them
# in two batches of 4 (high-throughput organisms, then low-throughput), so
# each batch adds ~160K to context: past the 150K compaction trigger on the
# first batch, past the 200K reference line after both.
_METHODS_FOOTER = """

## Methodological considerations (standardized across this review series)

| Dimension               | Low-throughput models | High-throughput models |
|-------------------------|-----------------------|------------------------|
| Cohort size per study   | 10-50                 | 500-10,000+            |
| Lifespan assay duration | months-years          | days-weeks             |
| Genetic intervention    | knock-in / conditional| RNAi / CRISPR screens  |
| Husbandry cost (USD/yr) | high (thousands/cage) | low (dollars/vial)     |
| Automated phenotyping   | limited               | extensive              |
| Single-cell compatible  | yes                   | yes                    |
| Human orthology (avg %) | 70-85                 | 40-65                  |
| Regulatory burden       | IACUC required        | minimal or none        |

### Reporting standards referenced

Studies cited in this review were filtered for: (1) explicit strain/genotype
reporting, (2) cohort sizes permitting survival analysis with log-rank power
> 0.8, (3) husbandry conditions documented per MIAME-like standards for the
organism, and (4) mortality criteria defined prospectively rather than post
hoc. Studies not meeting these criteria are noted but given less weight in
the synthesis.

### Interventions covered in the comparison set

Across the eight organisms in this review series, the following classes of
longevity intervention have been tested with sufficient replication to
permit cross-species comparison:
- Dietary restriction (caloric, protein, specific-nutrient)
- mTOR inhibition (rapamycin and analogues)
- Insulin/IGF-1 signaling reduction (genetic and pharmacological)
- Senolytic compounds (dasatinib + quercetin, navitoclax, fisetin)
- Mitochondrial modulation (NAD+ precursors, mitochondrial uncouplers)
- Proteostasis enhancers (autophagy inducers, HSF-1 activation)

Where an organism lacks published data on a given intervention class, we
note it explicitly rather than extrapolating from related species.

### Detailed intervention-response matrix

The following table summarizes published effect magnitudes (median lifespan
change as a percentage relative to matched controls) for each intervention
class. Blank cells indicate insufficient published data; cells marked †
indicate a single study or conflicting reports across studies. Values are
illustrative composites synthesized for this review and should not be used
for meta-analytic purposes without consulting primary sources.

| Intervention class    | Effect range    | Replication | Dose-response | Sex-specificity |
|-----------------------|-----------------|-------------|---------------|-----------------|
| Dietary restriction   | +10 to +50%     | high        | bell-shaped   | variable        |
| mTOR inhibition       | +5 to +25%      | high        | monotonic     | often F>M       |
| IIS reduction         | +20 to +100%    | high        | threshold     | often F>M       |
| Senolytics            | +5 to +15% †    | low-moderate| unclear       | unclear         |
| NAD+ precursors       | 0 to +10% †     | moderate    | saturating    | not reported    |
| Autophagy inducers    | +10 to +30%     | moderate    | monotonic     | variable        |

Interpretation caveats: effect sizes frequently compress moving from
short-lived to longer-lived organisms, a pattern attributed to
evolutionary canalization of aging pathways in long-lived species and to
ceiling effects in interventions that target early-mortality hazards rather
than late-life decline. Cross-species comparisons should weight relative
rank ordering over absolute magnitudes.

### Husbandry and environment standardization

Husbandry variables with documented lifespan effects that must be controlled
or reported: temperature (particularly for poikilotherms, where a 5°C shift
can alter lifespan by 30% or more), diet composition and feeding schedule,
housing density and social structure, light/dark cycle, microbiome status
(gnotobiotic vs. conventional), and handling frequency. For this review, we
preferred studies that held these variables fixed within an experiment and
reported them explicitly. Inter-lab variance attributable to husbandry is
a known confound; where available, we note when an effect has been
replicated across independent facilities.

### Statistical approach to survival curves

Survival data in the source literature were analyzed with a mix of log-rank,
Wilcoxon (Gehan-Breslow), and parametric accelerated failure time models.
These methods weight early vs. late deaths differently and can give
discordant p-values on the same data. Where possible we report effect
sizes (median lifespan ratio, or hazard ratio with confidence interval)
rather than p-values alone. Studies that report only "p < 0.05" without an
effect size were down-weighted in the synthesis.

### Censoring and competing risks

Censoring (loss to follow-up, escaped animals, accidental death) and
competing risks (cancer vs. non-cancer mortality, in mammalian models) were
handled variably across the source literature. We flag cases where high
censoring rates (>15% of cohort) or unmodeled competing risks could bias
median-lifespan estimates. In invertebrate models, competing-risk issues
are less prominent because most deaths are attributed to generalized
age-related decline rather than specific pathologies.

### Biomarkers and surrogate endpoints

Many studies, particularly in long-lived models where full lifespan curves
are impractical, report surrogate endpoints: senescence marker accumulation
(SA-β-gal, p16INK4a), epigenetic clock readouts, functional decline
measures (grip strength, rotarod, memory tasks), or pathology scores at a
fixed age. The correlation between these surrogates and eventual lifespan
varies across organisms and interventions. We note surrogate-endpoint-only
studies separately from those with mortality data.

### Dose and timing considerations

Intervention effects are sensitive to dose (most interventions have an
optimum beyond which effects attenuate or reverse) and to timing
(initiation in early adulthood typically yields larger effects than
late-onset initiation). Where source studies systematically varied dose or
onset timing, we report the strongest reproducible condition; where they
did not, we note that the reported effect may not represent the optimum.

### Sex-specific reporting

Sex differences in lifespan response are common and sometimes large (mTOR
inhibition in mice, for instance, has shown larger female effects in
multiple studies). Studies that pooled sexes without separate reporting, or
that used only one sex, are flagged. Sex-specific effects are a source of
inter-study heterogeneity that is frequently under-discussed in primary
literature.

### Cross-species translation caveats

Effect sizes for a given intervention often shrink as you move from
short-lived to long-lived organisms, a pattern sometimes attributed to
evolutionary canalization of aging pathways in longer-lived species. This
review does not attempt meta-analytic effect-size pooling across organisms;
instead we report per-organism findings and flag where effect-size
discordance is notable. Readers designing translational pipelines should
treat invertebrate hits as hypothesis-generating and expect effect-size
attenuation in mammals.

### Funding and conflict-of-interest notes

Primary studies were not filtered by funding source, but industry-sponsored
studies and studies from labs with commercial interests in a tested
compound are flagged where disclosed. Publication bias toward positive
results is a known issue in intervention-testing literature; the magnitude
of this bias is difficult to estimate but likely larger for pharmacological
interventions than for genetic ones.
### Selected primary references (illustrative, synthetic)

The following synthetic reference list represents the class of study cited
in each dimension of this review. These are not real citations; they stand
in for the typical literature density in each organism's aging field.

1. Strain-specific lifespan baselines under defined media: three independent
   replications across two facilities, n=120-200 per arm, standard husbandry.
   Reported median lifespan CV across replications: 8-12%.
2. Dietary restriction protocol comparison (every-other-day vs. continuous
   caloric restriction vs. protein restriction): single-lab dose-response,
   n=80 per condition, four diet arms plus ad-lib control.
3. Conditional genetic intervention with adult-onset induction, separating
   developmental from adult effects: two-arm design (induced vs. vehicle),
   n=100 per arm, onset at young adulthood, survival + healthspan readouts.
4. Pharmacological screen across 12 candidate geroprotectors: single-dose
   pilot, n=40 per compound arm, followed by dose-response on the top 3
   hits, n=80 per dose arm.
5. Cross-facility reproducibility study: same strain, same nominal protocol,
   run at 3-4 independent labs, blind analysis. Inter-lab median lifespan
   CV reported alongside intra-lab CV.
6. Sex-stratified intervention study: same compound, male and female cohorts
   run in parallel, n=100 per sex-arm, survival analysis with sex-by-
   treatment interaction term.
7. Biomarker validation against mortality: longitudinal measurement of 4-6
   candidate surrogate endpoints, correlated with subsequent individual
   lifespan in the same cohort, n=150, mixed-effects modeling.
8. Late-onset intervention efficacy: compound initiated at 50%, 70%, and 85%
   of median lifespan, n=60 per onset-arm, testing for effect attenuation
   with delayed start.

### Reviewer notes on data quality

The source literature for each organism varies substantially in quality and
depth. Short-lived invertebrates have the largest and most-reproduced
intervention literature, but also the most heterogeneous husbandry
practices. Mammalian models have stricter protocol standardization (in part
driven by IACUC oversight) but far fewer independent replications per
intervention due to cost. Long-lived or unconventional models (killifish,
naked mole-rat, primates) have the thinnest literature and the greatest
uncertainty around effect-size estimates. These gradients in data quality
should inform how much weight is placed on cross-species concordance.

### Glossary of terms used in this review

- **Median lifespan**: age at which 50% of a cohort has died; more robust to
  outliers than mean, standard primary endpoint.
- **Maximum lifespan**: age of the longest-lived individual or the 90th/95th
  percentile; more variable, sensitive to cohort size.
- **Healthspan**: duration of life spent without significant functional
  impairment; operationalized variably across studies.
- **Hazard rate**: instantaneous probability of death at a given age,
  conditional on survival to that age.
- **Gompertz parameter**: the rate of exponential increase in hazard with
  age; captures "rate of aging" as distinct from baseline vulnerability.
- **Negligible senescence**: hazard rate that does not increase with age
  over the observed range; documented in a few species.


## Appendix: Primary Study Data Tables (Synthetic)

The following tables compile the quantitative data underlying the narrative
review above. All values are synthetic composites representative of the
published literature but not drawn from any single source.

### Table A1: Lifespan baselines by strain and condition

| Strain/Line | Condition | Median (units) | 95th %ile | n | Lab | Year |
|-------------|-----------|----------------|-----------|-----|-----|------|
| Reference-A | standard  | see narrative  | +25-35%   | 120 | L1  | 2019 |
| Reference-A | DR        | +18-25%        | +30-45%   | 100 | L1  | 2019 |
| Reference-A | rapa-low  | +8-12%         | +15-22%   | 80  | L1  | 2020 |
| Reference-A | rapa-high | +15-22%        | +22-30%   | 80  | L1  | 2020 |
| Reference-B | standard  | +3% vs A       | similar   | 150 | L2  | 2020 |
| Reference-B | DR        | +20-28%        | +35-48%   | 130 | L2  | 2020 |
| Reference-B | rapa-low  | +10-15%        | +18-25%   | 90  | L2  | 2021 |
| Reference-B | rapa-high | +18-25%        | +25-35%   | 90  | L2  | 2021 |
| Long-lived-C| standard  | +45-60%        | +55-75%   | 100 | L3  | 2018 |
| Long-lived-C| DR        | +50-68%        | +65-85%   | 100 | L3  | 2019 |
| Short-lived-D| standard | -20-28%        | -15-20%   | 80  | L1  | 2021 |
| Short-lived-D| DR       | +5-10%         | +10-18%   | 70  | L1  | 2021 |
| Outcross-E  | standard  | -5 to +5%      | variable  | 200 | L4  | 2022 |
| Outcross-E  | DR        | +12-20%        | +20-32%   | 180 | L4  | 2022 |
| Outcross-E  | IIS-KD    | +35-55%        | +45-70%   | 120 | L4  | 2022 |
| Outcross-F  | standard  | +2 to +8%      | +5-12%    | 150 | L5  | 2023 |
| Outcross-F  | DR        | +15-22%        | +22-35%   | 140 | L5  | 2023 |
| Outcross-F  | senolytic | +4-9%          | +8-15%    | 90  | L5  | 2023 |

### Table A2: Intervention effect magnitudes across replication cohorts

| Intervention      | Cohort | Effect (median %) | 95% CI       | p (log-rank) | Facility |
|-------------------|--------|-------------------|--------------|--------------|----------|
| Caloric DR 30%    | 1      | +22               | [+14, +30]   | <0.001       | A        |
| Caloric DR 30%    | 2      | +19               | [+11, +27]   | <0.001       | B        |
| Caloric DR 30%    | 3      | +25               | [+16, +34]   | <0.001       | A        |
| Caloric DR 40%    | 1      | +28               | [+18, +38]   | <0.001       | A        |
| Caloric DR 40%    | 2      | +15               | [+5, +25]    | 0.003        | B        |
| Protein DR        | 1      | +14               | [+6, +22]    | 0.001        | C        |
| Protein DR        | 2      | +11               | [+2, +20]    | 0.02         | C        |
| mTOR inhib. low   | 1      | +9                | [+2, +16]    | 0.01         | A        |
| mTOR inhib. low   | 2      | +12               | [+4, +20]    | 0.003        | B        |
| mTOR inhib. low   | 3      | +7                | [-1, +15]    | 0.08         | D        |
| mTOR inhib. high  | 1      | +18               | [+9, +27]    | <0.001       | A        |
| mTOR inhib. high  | 2      | +21               | [+12, +30]   | <0.001       | B        |
| IIS reduction     | 1      | +42               | [+30, +54]   | <0.001       | A        |
| IIS reduction     | 2      | +55               | [+40, +70]   | <0.001       | E        |
| IIS reduction     | 3      | +38               | [+25, +51]   | <0.001       | B        |
| NAD+ precursor    | 1      | +4                | [-4, +12]    | 0.3          | A        |
| NAD+ precursor    | 2      | +7                | [-1, +15]    | 0.08         | F        |
| Senolytic combo   | 1      | +11               | [+2, +20]    | 0.02         | A        |
| Senolytic combo   | 2      | +6                | [-3, +15]    | 0.2          | C        |
| Autophagy induce  | 1      | +16               | [+7, +25]    | <0.001       | B        |
| Autophagy induce  | 2      | +19               | [+10, +28]   | <0.001       | B        |
| Mito uncoupler    | 1      | +8                | [+0, +16]    | 0.05         | A        |
| Mito uncoupler    | 2      | +5                | [-3, +13]    | 0.2          | D        |

### Table A3: Healthspan measures at matched chronological fractions

| Measure              | 25% | 50% | 75% | 90% | Control | Intervention | Delta |
|----------------------|-----|-----|-----|-----|---------|--------------|-------|
| Locomotor score      | 95  | 82  | 61  | 38  | --      | --           | --    |
| Locomotor (DR)       | 96  | 88  | 74  | 52  | 61/38   | 74/52        | +13/+14|
| Locomotor (IIS-KD)   | 96  | 90  | 78  | 58  | 61/38   | 78/58        | +17/+20|
| Stress resistance    | 88  | 76  | 58  | 35  | --      | --           | --    |
| Stress res (DR)      | 90  | 82  | 70  | 48  | 58/35   | 70/48        | +12/+13|
| Reproductive output  | 100 | 65  | 15  | 2   | --      | --           | --    |
| Repro (DR)           | 85  | 48  | 10  | 1   | 65/15   | 48/10        | -17/-5 |
| Tissue integrity     | 92  | 78  | 55  | 30  | --      | --           | --    |
| Tissue int (mTOR-i)  | 94  | 84  | 68  | 45  | 55/30   | 68/45        | +13/+15|
| Cognitive proxy      | 90  | 75  | 52  | 28  | --      | --           | --    |
| Cognitive (DR)       | 91  | 80  | 64  | 40  | 52/28   | 64/40        | +12/+12|

### Table A4: Pathology incidence at terminal necropsy

| Pathology class       | Incidence ctrl | Incidence DR | Incidence IIS | Incidence mTOR-i |
|-----------------------|----------------|--------------|---------------|------------------|
| Neoplasia (all)       | 32%            | 24%          | 19%           | 28%              |
| Neoplasia (malignant) | 18%            | 12%          | 10%           | 15%              |
| Cardiac pathology     | 22%            | 14%          | 16%           | 18%              |
| Renal pathology       | 28%            | 19%          | 22%           | 24%              |
| Hepatic pathology     | 15%            | 10%          | 12%           | 11%              |
| Neurodegeneration     | 12%            | 8%           | 9%            | 10%              |
| Sarcopenia (severe)   | 45%            | 30%          | 28%           | 35%              |
| Osteoporosis          | 35%            | 22%          | 25%           | 30%              |
| Multimorbidity (3+)   | 38%            | 22%          | 20%           | 28%              |

### Table A5: Cross-facility reproducibility metrics

| Intervention    | Labs reporting | Concordant direction | Pooled effect | I² (heterogeneity) |
|-----------------|----------------|----------------------|---------------|--------------------|
| Caloric DR      | 12             | 12/12 (100%)         | +21% [17,25]  | 28%                |
| Protein DR      | 6              | 5/6 (83%)            | +12% [7,17]   | 42%                |
| mTOR inhib.     | 9              | 8/9 (89%)            | +14% [10,18]  | 35%                |
| IIS reduction   | 8              | 8/8 (100%)           | +45% [35,55]  | 48%                |
| NAD+ precursor  | 7              | 4/7 (57%)            | +5% [-1,11]   | 61%                |
| Senolytics      | 5              | 3/5 (60%)            | +8% [1,15]    | 55%                |
| Autophagy ind.  | 4              | 4/4 (100%)           | +17% [11,23]  | 22%                |

### Extended methods: husbandry protocol details

The standardized husbandry protocol followed across replication cohorts
specified: temperature maintained at the organism-appropriate standard
±0.5°C with continuous monitoring; 12:12 light:dark cycle with dawn/dusk
ramping over 30 minutes; feeding on a fixed schedule with defined-composition
diet (batch-matched across cohorts within a study); housing at standard
density with group-housing where species-appropriate; handling limited to
protocol-required transfers and health checks on a fixed schedule;
microbiome status documented (conventional vs. specific-pathogen-free vs.
gnotobiotic) and held fixed within a study; humidity maintained at
organism-standard range; ambient noise and vibration minimized and logged;
health checks by blinded personnel; mortality criteria defined prospectively
(failure to respond to gentle mechanical stimulus after three attempts, or
equivalent species-standard); censoring recorded with reason (escape,
accidental death, euthanasia for humane endpoint, equipment failure);
necropsy performed on a random 20% subsample plus all animals reaching
the 95th percentile of cohort survival.

Deviations from the standard protocol were logged and reported. The most
common deviation classes across studies: unplanned temperature excursions
(2-4°C for <6h, affecting 3-8% of study-days), feeding schedule shifts
during facility holidays, and handling-frequency changes during cohort
size reduction. Studies with deviation rates >10% of study-days were
flagged and down-weighted in pooled analyses.

### Table A6: Transcriptomic signatures of intervention response

| Gene class              | Direction | DR   | mTOR-i | IIS-KD | Senolytic | Autophagy |
|-------------------------|-----------|------|--------|--------|-----------|-----------|
| Ribosomal proteins      | down      | -35% | -28%   | -42%   | -8%       | -22%      |
| Mitochondrial ETC       | up        | +18% | +12%   | +25%   | +4%       | +15%      |
| Autophagy machinery     | up        | +22% | +30%   | +28%   | +10%      | +45%      |
| Proteasome subunits     | up        | +15% | +18%   | +20%   | +8%       | +12%      |
| Lipid metabolism        | mixed     | var  | var    | var    | var       | var       |
| Immune/inflammatory     | down      | -20% | -15%   | -25%   | -35%      | -12%      |
| Cell cycle              | down      | -12% | -18%   | -22%   | -8%       | -15%      |
| DNA repair              | up        | +8%  | +6%    | +12%   | +5%       | +10%      |
| Stress response (HSP)   | up        | +25% | +20%   | +30%   | +12%      | +18%      |
| Senescence markers      | down      | -15% | -10%   | -18%   | -40%      | -8%       |
| ECM remodeling          | mixed     | var  | var    | var    | var       | var       |
| Insulin/IGF signaling   | down      | -18% | -12%   | -55%   | -5%       | -10%      |
| mTOR pathway            | down      | -22% | -48%   | -28%   | -6%       | -20%      |
| AMPK signaling          | up        | +28% | +15%   | +20%   | +8%       | +25%      |
| Sirtuin targets         | up        | +20% | +10%   | +18%   | +5%       | +12%      |
| FOXO targets            | up        | +32% | +18%   | +58%   | +10%      | +22%      |

### Table A7: Epigenetic age acceleration under interventions

| Clock type         | Tissue   | Ctrl accel | DR accel | mTOR-i accel | IIS accel |
|--------------------|----------|------------|----------|--------------|-----------|
| Horvath-like       | liver    | 1.00       | 0.78     | 0.85         | 0.72      |
| Horvath-like       | muscle   | 1.00       | 0.82     | 0.88         | 0.75      |
| Horvath-like       | brain    | 1.00       | 0.88     | 0.92         | 0.85      |
| PhenoAge-like      | liver    | 1.00       | 0.72     | 0.80         | 0.68      |
| PhenoAge-like      | muscle   | 1.00       | 0.75     | 0.82         | 0.70      |
| GrimAge-like       | blood    | 1.00       | 0.68     | 0.78         | 0.65      |
| Species-specific   | whole    | 1.00       | 0.75     | 0.82         | 0.70      |

### Table A8: Functional decline trajectories (longitudinal)

| Function         | Age 25% | Age 50% | Age 75% | Age 90% | Half-life (% of max lifespan) |
|------------------|---------|---------|---------|---------|-------------------------------|
| Max locomotor    | 98      | 85      | 62      | 35      | 58%                           |
| Endurance        | 95      | 78      | 52      | 25      | 52%                           |
| Grip/strength    | 96      | 80      | 55      | 28      | 54%                           |
| Coordination     | 94      | 75      | 48      | 22      | 50%                           |
| Learning rate    | 92      | 72      | 45      | 20      | 48%                           |
| Memory retention | 95      | 78      | 52      | 25      | 52%                           |
| Stress recovery  | 90      | 68      | 40      | 15      | 45%                           |
| Wound healing    | 98      | 82      | 58      | 30      | 55%                           |
| Immune response  | 95      | 75      | 48      | 20      | 50%                           |
| Metabolic flex   | 92      | 70      | 42      | 18      | 47%                           |

### Notes on data interpretation for cross-review synthesis

The data tables above are synthetic composites structured to reflect the
typical data density and heterogeneity of the aging-intervention literature
for each organism. They are intended to support the comparative synthesis
in the main text, not to substitute for primary-source consultation.

Key interpretation caveats: (1) effect magnitudes are expressed as percentage
change in median lifespan relative to matched controls, which is the most
commonly reported metric but obscures changes in lifespan distribution shape;
(2) facility-to-facility variance is substantial and often under-reported;
(3) sex differences are common and the tables above pool sexes unless
otherwise noted; (4) the transcriptomic and epigenetic data represent
average fold-changes across studies and will vary by tissue, timepoint,
and intervention dose; (5) functional decline trajectories are organism-
specific and the normalized percentages above are illustrative of typical
shapes, not direct cross-species comparisons.

## Appendix B: Detailed Experimental Protocols (Synthetic)

### B1. Standard lifespan assay protocol

**Preparation phase (days -14 to 0):**
Expand the starting population under standard conditions for at least two
generations prior to cohort collection to minimize parental-age effects.
Collect age-synchronized individuals at the organism-appropriate
developmental stage (L4/pupae/weaning equivalent). Randomize to treatment
arms using a block design that balances plating/caging order across arms.
Record batch, parental identity (where applicable), and collection timestamp.

**Intervention phase (day 0 onwards):**
Initiate intervention at young adulthood unless testing late-onset effects.
For dietary interventions, transition over 3-5 days to avoid acute stress
confounds. For pharmacological interventions, dose via the
organism-standard route (food, water, injection, gavage) at the target
concentration, with vehicle control matched for all non-drug components.
For genetic interventions with inducible systems, confirm induction
efficiency in a pilot cohort before the lifespan cohort begins.

**Monitoring phase:**
Score survival at organism-appropriate intervals (daily for short-lived
organisms, 2-3× weekly for long-lived). Use blinded scoring where feasible.
Define death operationally and prospectively (see main text). Record
censoring events with category. For long studies, rotate scoring personnel
on a fixed schedule to average out scorer-specific biases.

**Termination criteria:**
Continue until fewer than 10% of the starting cohort remains, or until
a pre-specified maximum duration (typically 150% of expected median
lifespan). Animals remaining at termination are censored as
"study-end-alive."

### B2. Healthspan battery protocol

Run the healthspan battery at 25%, 50%, 75%, and 90% of expected median
lifespan. Use a separate longitudinal cohort from the survival cohort to
avoid handling effects on lifespan. The standard battery includes:
locomotor assessment (organism-appropriate: open-field, climbing, swimming,
or equivalent), stress-resistance challenge (heat, oxidative, or osmotic at
a sub-lethal dose), and where applicable, cognitive/behavioral assessment.
Normalize all measures to the young-adult baseline within-cohort.
Report raw and normalized values.

### B3. Tissue collection and molecular analysis protocol

At each healthspan timepoint, euthanize a subset (n=8-12) for tissue
collection. Collect at a fixed circadian time to control for diurnal
variation. Flash-freeze or fix within 5 minutes of euthanasia. For
transcriptomics, process all samples in a single batch per timepoint to
avoid batch effects; if multiple batches are unavoidable, include
technical replicates that span batches. For epigenetic clocks, use the
organism-specific clock where available; where not, report which proxy
clock was used and its validation status in the target species.

### B4. Statistical analysis plan

Pre-specify the primary endpoint (median lifespan change) and the primary
test (log-rank). Secondary endpoints (90th percentile lifespan, hazard
ratio from Cox model, healthspan measures) should be declared prospectively
with multiple-comparison correction for the family of secondary tests.
Report effect sizes with confidence intervals, not just p-values.
For cross-cohort pooling, use random-effects meta-analysis and report
heterogeneity (I²). For longitudinal healthspan data, use mixed-effects
models with individual as random effect and age × treatment as the
interaction of interest.

### B5. Quality control and reproducibility checklist

Before publication, verify: (1) all protocol deviations logged and
reported; (2) censoring rate <15% of cohort and reasons categorized;
(3) survival curves include number-at-risk; (4) raw data deposited in
an organism-appropriate repository; (5) strain, source, and generation
number documented; (6) housing conditions, diet composition, and
environmental parameters specified to reproducible detail; (7) blinding
status stated for scoring and analysis; (8) power calculation provided
for the primary endpoint; (9) pre-registration or protocol-freeze date
documented; (10) conflicts of interest disclosed.

## Appendix C: Annotated Literature Summary (Synthetic)

### C1. Foundational intervention studies

| # | Study design | Key finding | Effect size | Replication status |
|---|--------------|-------------|-------------|--------------------|
| 1 | Single-lab DR dose-response | Bell-shaped response, optimum at 30-40% restriction | +22% at optimum | High (>10 labs) |
| 2 | Multi-site mTOR inhibitor trial | Late-onset initiation still effective | +14% late-onset | High (ITP + 3 labs) |
| 3 | IIS pathway genetic reduction | Largest single-pathway effect | +40-60% genetic | High (many labs) |
| 4 | Senolytic pilot | Modest lifespan, larger healthspan effect | +8% lifespan | Moderate (5 labs, mixed) |
| 5 | NAD+ precursor supplementation | Small, inconsistent effects | +3-7% variable | Low (conflicting reports) |
| 6 | Mitochondrial uncoupler low-dose | Hormetic effect at low dose only | +8% at low dose | Moderate (3 labs) |
| 7 | Autophagy induction genetic | Robust effect, pathway-conserved | +18-25% | High (>8 labs) |
| 8 | Combined DR + mTOR-i | Sub-additive (overlapping pathways) | +26% combo vs +22% DR | Moderate (2 labs) |
| 9 | Combined IIS + DR | Additive to super-additive | +65% combo | Moderate (3 labs) |
| 10 | Sex-stratified mTOR-i | Consistent female advantage | F: +18%, M: +10% | High (many labs) |

### C2. Mechanistic studies

| # | Mechanism tested | Approach | Outcome | Strength of evidence |
|---|------------------|----------|---------|---------------------|
| 1 | DR → mTOR suppression | Epistasis + phospho-western | DR effect blunted on mTOR-KD background | Strong |
| 2 | IIS → FOXO activation | FOXO-null epistasis | IIS lifespan effect abolished | Strong |
| 3 | Senolytics → SASP reduction | Conditioned-media transfer | SASP reduction sufficient for partial effect | Moderate |
| 4 | mTOR-i → autophagy | Autophagy-reporter + inhibitor epistasis | Autophagy required for ~60% of effect | Strong |
| 5 | DR → ribosomal suppression | Ribo-seq + genetic RP-KD | RP-KD partially phenocopies DR | Moderate |
| 6 | IIS → proteostasis | Aggregation reporters | IIS-KD reduces aggregation burden | Strong |
| 7 | NAD+ → sirtuin activation | Sirtuin-null epistasis | Effect abolished on Sir2-null | Moderate (effect small anyway) |
| 8 | Mito uncoupler → ROS hormesis | ROS scavenger co-treatment | Effect blunted by scavenger | Moderate |

### C3. Translational-pipeline case studies

| Candidate | Discovery organism | Mouse validation | Primate/human data | Current status |
|-----------|-------------------|------------------|--------------------|---------------|
| Rapamycin | Yeast (TOR1) | ITP positive, multi-site | Limited (dog, marmoset ongoing) | Clinical trials (healthy aging) |
| Metformin | Observational (human) | Mixed in mouse | TAME trial planned | Awaiting RCT |
| Senolytic D+Q | Cell culture | Healthspan positive, lifespan modest | Early human trials | Phase 2 |
| NMN/NR | Yeast/worm (Sir2) | Mixed | Safety established, efficacy unclear | Supplements, no RCT |
| 17α-estradiol | Screening (ITP) | ITP positive (male-specific) | None | Preclinical |
| Acarbose | Screening (ITP) | ITP positive | Diabetes drug, no aging RCT | Preclinical for aging |
| Spermidine | Yeast autophagy screen | Positive (autophagy-dependent) | Observational cohort positive | Early trials |
| Canagliflozin | Screening (ITP) | ITP positive | Diabetes drug | Preclinical for aging |

### C4. Negative and null results (often under-reported)

| Intervention | Why tested | Result | Published? |
|--------------|------------|--------|-----------|
| Resveratrol | Sirtuin activator hypothesis | Null in ITP, mixed elsewhere | Yes (ITP) |
| Antioxidant cocktail | Oxidative damage theory | Null or negative | Yes (multiple) |
| Growth hormone | Somatotropic axis | Negative (shortens lifespan) | Yes |
| High-dose vitamin E | Antioxidant hypothesis | Null | Yes |
| Telomerase activation | Telomere hypothesis | Cancer risk in some models | Partially |
| Young blood plasma | Parabiosis follow-up | Mixed, mostly null for lifespan | Yes |

## Appendix D: Intervention Case Study Abstracts (Synthetic)

### Case D1: DR dose-response across five strains
Cohorts of five genetic backgrounds (n=100/strain/dose) were subjected to
0%, 20%, 30%, 40%, and 50% caloric restriction initiated at young adulthood.
All five strains showed a bell-shaped response peaking at 30-40% restriction.
The Long-lived-C strain showed the flattest curve (benefit ceiling at +25%)
while the Short-lived-D strain showed the steepest response (+45% at optimum).
Interaction between genetic background and DR dose was significant (p<0.001),
supporting the model that baseline aging rate sets the ceiling for DR benefit.

### Case D2: Late-onset rapamycin at three initiation times
Rapamycin at the optimal dose was initiated at 50%, 70%, and 85% of median
lifespan (n=80/arm). 50%-onset yielded +16% median extension; 70%-onset
yielded +10%; 85%-onset yielded +4% (n.s.). Healthspan measures showed a
similar attenuation pattern. The result supports a window-of-opportunity
model for mTOR inhibition, with declining returns as tissue damage
accumulates. Sex-stratified analysis confirmed the female advantage
(F: +19% at 50%-onset vs M: +13%).

### Case D3: IIS reduction tissue-specific requirements
Tissue-restricted IIS knockdown in four tissue classes (neurons, intestine,
muscle, hypodermis; n=120/tissue/genotype) identified intestine-specific
knockdown as sufficient for ~70% of the whole-organism lifespan extension.
Neuronal knockdown contributed ~20%; muscle and hypodermis showed no
independent contribution. Double knockdown of intestine+neuron recapitulated
>90% of the constitutive effect, consistent with a two-tissue requirement
model. FOXO-null epistasis confirmed FOXO-dependence for all tissue effects.

### Case D4: Senolytic efficacy across age-of-initiation
D+Q combination senolytics were initiated at young adulthood, middle age,
or old age (n=90/arm). Young-onset showed no lifespan benefit (+2%, n.s.)
but modest healthspan improvement. Middle-age onset showed +8% lifespan
and larger healthspan effects. Old-age onset showed +11% lifespan
(largest effect) and the biggest gains in late-life function. This inverted
dose-timing relationship is consistent with the senolytic mechanism:
senescent cell burden is highest at old age, so clearance has the most
to work with.

### Case D5: Combination intervention additivity matrix
Pairwise combinations of DR, rapamycin, and IIS-KD were tested alongside
single interventions (n=100/arm, 7 arms total). DR+rapamycin was
sub-additive (+24% vs predicted +36% from independence), consistent with
shared pathway action on mTOR. DR+IIS-KD was approximately additive (+62%
vs predicted +64%). Rapamycin+IIS-KD was additive (+56% vs predicted +59%).
The triple combination yielded +68%, only marginally better than the best
double. Pathway epistasis analysis supported a model with partial overlap
between DR/mTOR and near-independence of IIS.

"""


def _appendix_tables_b_c() -> str:
    """Generate appendix Tables B1-B5 and C1-C4.

    Deterministic (seeded hash, no imports), so repeat kernel runs are
    identical and COMPACTION_PROBES stay pinned. These are the B- and
    C-series tables referenced by the research task prompt; the A-series
    and Case D1-D5 studies live in _METHODS_FOOTER above.

    Sized so _METHODS_FOOTER + _EXTENDED_APPENDIX adds ~105K chars to each
    document, bringing the full 8-document corpus to ~320K tokens.
    """
    interventions = [
        "DR-caloric",
        "DR-protein",
        "mTOR-rapa",
        "IIS-daf2",
        "IIS-insr",
        "NAD-NMN",
        "seno-DQ",
        "auto-spermd",
        "AMPK-metformin",
        "seno-fisetin",
        "SIRT-resv",
        "epi-OSK",
        "mito-uncpl",
    ]
    tissues = ["liver", "muscle", "brain", "heart", "kidney", "adipose"]
    timepoints = ["25%", "50%", "75%", "90%", "95%"]
    ages = ["young", "early-mid", "mid", "late-mid", "late"]

    def _h(*parts) -> int:
        # Small deterministic integer hash so table cells are stable run-to-run.
        v = 0x811C9DC5
        for p in parts:
            for b in str(p).encode():
                v = ((v ^ b) * 0x01000193) & 0xFFFFFFFF
        return v

    out: list[str] = []
    add = out.append

    add("\n\n## Appendix B: Longitudinal biomarker panels\n")
    add(
        "The B-series tables report biomarker levels across the lifespan "
        "fraction for each intervention arm, sampled at matched chronological "
        "fractions to permit cross-intervention comparison. Values are "
        "arbitrary units normalized to young-control = 100.\n"
    )

    add("\n### Table B1: Inflammatory marker panel (IL-6, TNF-α, CRP composite)\n\n")
    add(
        "| Intervention     | Tissue  | "
        + " | ".join(f"{t:>5}" for t in timepoints)
        + " | Slope | Late/Young |\n"
    )
    add(
        "|------------------|---------|"
        + "|".join("-------" for _ in timepoints)
        + "|-------|------------|\n"
    )
    for iv in interventions:
        for ts in tissues:
            h = _h("B1", iv, ts)
            base = 100 + (h % 30)
            slope = 0.4 + (h % 60) / 100
            vals = [base + int(slope * f * 70) for f in (0.25, 0.5, 0.75, 0.9, 0.95)]
            add(
                f"| {iv:<16} | {ts:<7} | "
                + " | ".join(f"{v:>5}" for v in vals)
                + f" | {slope:>5.2f} | {vals[-1] / vals[0]:>10.2f} |\n"
            )

    add("\n### Table B2: Oxidative stress panel (MDA, 8-OHdG, protein carbonyls)\n\n")
    add("| Intervention     | Tissue  | Baseline | Peak | Peak-age | Decline-rate | AUC |\n")
    add("|------------------|---------|----------|------|----------|--------------|-----|\n")
    for iv in interventions:
        for ts in tissues:
            h = _h("B2", iv, ts)
            baseline = 80 + (h % 40)
            peak = baseline + 30 + (h % 50)
            peak_age = ages[h % len(ages)]
            decline = 0.1 + (h % 40) / 100
            auc = (baseline + peak) * 5 // 2 + (h % 100)
            add(
                f"| {iv:<16} | {ts:<7} | {baseline:>8} | {peak:>4} | {peak_age:<8} | {decline:>12.2f} | {auc:>3} |\n"
            )

    add("\n### Table B3: Mitochondrial function (membrane potential, OCR, ATP)\n\n")
    add(
        "| Intervention     | Tissue  | MMP-25% | MMP-75% | OCR-25% | OCR-75% | ATP-ratio | Coupling |\n"
    )
    add(
        "|------------------|---------|---------|---------|---------|---------|-----------|----------|\n"
    )
    for iv in interventions:
        for ts in tissues:
            h = _h("B3", iv, ts)
            mmp25, mmp75 = 95 + (h % 10), 50 + (h % 35)
            ocr25, ocr75 = 100 + (h % 15), 55 + (h % 30)
            atp = 0.5 + (h % 50) / 100
            coup = 0.6 + (h % 35) / 100
            add(
                f"| {iv:<16} | {ts:<7} | {mmp25:>7} | {mmp75:>7} | {ocr25:>7} | {ocr75:>7} | {atp:>9.2f} | {coup:>8.2f} |\n"
            )

    add("\n### Table B4: Proteostasis markers (aggregates, autophagy flux, UPS)\n\n")
    add(
        "| Intervention     | Tissue  | Aggr-young | Aggr-old | LC3-ratio | p62-clear | 20S-act | Net-score |\n"
    )
    add(
        "|------------------|---------|------------|----------|-----------|-----------|---------|-----------|\n"
    )
    for iv in interventions:
        for ts in tissues:
            h = _h("B4", iv, ts)
            ay, ao = 5 + (h % 10), 25 + (h % 40)
            lc3 = 0.8 + (h % 60) / 100
            p62 = 0.3 + (h % 50) / 100
            ups = 70 + (h % 30)
            net = (lc3 + p62) * 50 - (ao - ay)
            add(
                f"| {iv:<16} | {ts:<7} | {ay:>10} | {ao:>8} | {lc3:>9.2f} | {p62:>9.2f} | {ups:>7} | {net:>9.1f} |\n"
            )

    add("\n### Table B5: Senescence marker accumulation (SA-β-gal+, p16, p21, SASP)\n\n")
    add(
        "| Intervention     | Tissue  | "
        + " | ".join(f"βgal-{t}" for t in timepoints)
        + " | p16-fold | SASP-idx |\n"
    )
    add(
        "|------------------|---------|"
        + "|".join("--------" for _ in timepoints)
        + "|----------|----------|\n"
    )
    for iv in interventions:
        for ts in tissues:
            h = _h("B5", iv, ts)
            base = 2 + (h % 5)
            vals = [base + int((h % 30) * f * 0.8) for f in (0.25, 0.5, 0.75, 0.9, 0.95)]
            p16 = 1.0 + (h % 80) / 20
            sasp = 10 + (h % 60)
            add(
                f"| {iv:<16} | {ts:<7} | "
                + " | ".join(f"{v:>6}" for v in vals)
                + f" | {p16:>8.1f} | {sasp:>8} |\n"
            )

    add("\n\n## Appendix C: Pharmacokinetic and dosing data\n")
    add(
        "The C-series tables report dose-response characterization and "
        "pharmacokinetic parameters for intervention compounds across the "
        "tissue panel. Doses are in organism-scaled mg/kg equivalents.\n"
    )

    add("\n### Table C1: Dose-response characterization\n\n")
    add(
        "| Intervention     | Dose-tier | Lifespan-Δ | Health-Δ | Toxicity | ED50   | Hill-n | Therap-idx |\n"
    )
    add(
        "|------------------|-----------|------------|----------|----------|--------|--------|------------|\n"
    )
    dose_tiers = ["0.1x", "0.3x", "1.0x", "3.0x", "10x", "30x"]
    for iv in interventions:
        for dose in dose_tiers:
            h = _h("C1", iv, dose)
            lsp = -5 + (h % 35)
            hlt = -3 + (h % 30)
            tox = h % 40
            ed50 = 0.5 + (h % 80) / 20
            hill = 0.8 + (h % 30) / 20
            ti = max(1, 20 - tox // 2 + (h % 10))
            add(
                f"| {iv:<16} | {dose:<9} | {lsp:>+10} | {hlt:>+8} | {tox:>8} | {ed50:>6.2f} | {hill:>6.2f} | {ti:>10} |\n"
            )

    add("\n### Table C2: Tissue distribution and half-life\n\n")
    add(
        "| Intervention     | Tissue  | Cmax   | Tmax-h | t½-h  | AUC    | F-bioavail | Tissue/plasma |\n"
    )
    add(
        "|------------------|---------|--------|--------|-------|--------|------------|---------------|\n"
    )
    for iv in interventions:
        for ts in tissues:
            h = _h("C2", iv, ts)
            cmax = 10 + (h % 200)
            tmax = 0.5 + (h % 40) / 10
            thalf = 2 + (h % 60)
            auc = cmax * thalf + (h % 500)
            fbio = 0.1 + (h % 80) / 100
            tpr = 0.2 + (h % 60) / 20
            add(
                f"| {iv:<16} | {ts:<7} | {cmax:>6} | {tmax:>6.1f} | {thalf:>5} | {auc:>6} | {fbio:>10.2f} | {tpr:>13.2f} |\n"
            )

    add("\n### Table C3: Age-dependent pharmacokinetic shifts\n\n")
    add(
        "| Intervention     | Age-tier | Cl-shift | Vd-shift | t½-shift | AUC-shift | F-shift | Dose-adj |\n"
    )
    add(
        "|------------------|----------|----------|----------|----------|-----------|---------|----------|\n"
    )
    for iv in interventions:
        for age in ages:
            h = _h("C3", iv, age)
            cl = -30 + (h % 50)
            vd = -15 + (h % 35)
            th = -5 + (h % 40)
            auc = -10 + (h % 60)
            fs = -20 + (h % 40)
            adj = 0.5 + (h % 100) / 100
            add(
                f"| {iv:<16} | {age:<8} | {cl:>+8} | {vd:>+8} | {th:>+8} | {auc:>+9} | {fs:>+7} | {adj:>8.2f} |\n"
            )

    add("\n### Table C4: Drug-drug interaction matrix (combination arms)\n\n")
    add(
        "| Drug-A           | Drug-B           | PK-interact | PD-interact | Lifespan-combo | Additivity | CI    | Recommend |\n"
    )
    add(
        "|------------------|------------------|-------------|-------------|----------------|------------|-------|-----------|\n"
    )
    rec_labels = ["avoid", "monitor", "safe", "prefer"]
    for i, iva in enumerate(interventions):
        for ivb in interventions[i + 1 :]:
            h = _h("C4", iva, ivb)
            pk = ["none", "minor", "moderate", "major"][h % 4]
            pd = ["antagonist", "independent", "additive", "synergist"][h % 4]
            combo = -5 + (h % 50)
            addv = 0.5 + (h % 100) / 100
            ci = 0.3 + (h % 140) / 100
            rec = rec_labels[h % 4]
            add(
                f"| {iva:<16} | {ivb:<16} | {pk:<11} | {pd:<11} | {combo:>+14} | {addv:>10.2f} | {ci:>5.2f} | {rec:<9} |\n"
            )

    add(
        "\nInterpretation: the B- and C-series tables are synthetic composites "
        "intended to reflect the data density of a comprehensive intervention "
        "characterization study. They support the comparative synthesis but "
        "should not be cited as primary findings.\n"
    )

    return "".join(out)


_EXTENDED_APPENDIX = _appendix_tables_b_c()


CORPUS: dict[str, str] = {
    # ─────────────────────────────────────────────────────────────────────
    "/research/celegans_review.md": """# Model Organism Review: Caenorhabditis elegans in Aging Research

Caenorhabditis elegans is a 1mm soil nematode that has been a workhorse of
aging biology since Klass's 1977 lifespan screens. It remains the most
widely used invertebrate model for longevity genetics, with the largest
curated set of lifespan-extending mutations of any organism.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Wild-type median lifespan | ~18 days at 20°C (N2 reference strain) |
| Maximum reported lifespan | >100 days (daf-2; daf-16 suppressor backgrounds, rare) |
| Generation time | 3 days (egg to egg-laying adult) |
| Typical cohort size | 100-500 animals/condition |
| Time to lifespan result | 4-6 weeks for a complete survival curve |

The short lifespan enables longitudinal designs that are impractical in
mammals: a single graduate student can run complete survival curves for 20
genotypes per month. Automated lifespan platforms (WormBot, the Lifespan
Machine) push throughput to thousands of animals per experiment with
machine-scored death calls, though these platforms have a known bias toward
scoring death in animals that stop moving but are still touch-responsive,
inflating lifespan estimates by roughly 10-15% relative to manual scoring
in three independent validation studies.

## Genetic tractability

The C. elegans toolkit is the most mature among invertebrate models.
Notable capabilities:

- **RNAi by feeding**: genome-wide libraries exist (Ahringer, Vidal). A
  lifespan RNAi screen covering ~85% of the genome is feasible in a single
  lab over 6-12 months. Tissue-specific RNAi (rde-1 rescue strains) allows
  knockdown restricted to intestine, muscle, neurons, or germline.
- **CRISPR knock-in**: routinely achieves defined edits in <2 weeks. The
  self-excising cassette (SEC) method is the community standard as of 2020.
- **Mosaic analysis and tissue-specific Cre drivers**: less developed than
  in Drosophila but functional.
- **Transgenic reporters**: the fully mapped 302-neuron connectome plus
  single-cell transcriptomic atlases across the lifespan make spatial
  expression analysis unusually tractable.

The daf-2/daf-16 insulin/IGF-1 signaling axis was first characterized here;
daf-2(e1370) roughly doubles lifespan and remains a benchmark intervention.
More than 200 single-gene mutations have published lifespan effects.

## Translational relevance

Human orthology averages around 40% at the gene level, rising to ~60-80%
for conserved pathway components (insulin signaling, autophagy, mTOR). The
major translational caveats:

- No adaptive immune system. Immunosenescence findings don't translate.
- Post-mitotic soma after L4: no adult stem cell niches outside the germline,
  limiting relevance to mammalian tissue homeostasis.
- Poikilothermic: temperature interacts strongly with lifespan (cold extends
  life), complicating comparison to homeotherms.
- Behavioral aging is difficult to resolve finely; "healthspan" metrics are
  less standardized than in mammals.

Three worm-to-human translational wins are frequently cited: the IGF-1
pathway (FOXO variants associate with human longevity), mitochondrial
electron transport chain hypomorphs (mirrored in human mitochondrial
disease cohorts), and dietary restriction (the worm DR response predicted
mammalian outcomes reasonably well).

## Summary assessment

C. elegans is the throughput champion. For initial genetic screens and
mechanistic pathway dissection it remains unmatched. It is not the organism
for validating a translational hypothesis before a mammalian study; use it
to generate hypotheses, not to confirm them.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/drosophila_review.md": """# Model Organism Review: Drosophila melanogaster in Aging Research

Drosophila melanogaster, the common fruit fly, has been a genetic model for
over a century and an aging model since Pearl's demographic work in the
1920s. It occupies a useful middle ground: more complex than C. elegans
(tissue diversity, a functional heart, behavioral repertoire) but still
short-lived enough for full-lifespan experiments.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Wild-type median lifespan | ~60-80 days (Canton-S, 25°C) |
| Maximum reported lifespan | ~120 days (dietary restriction, some genotypes) |
| Generation time | 10 days (egg to eclosion) |
| Typical cohort size | 100-200 flies/condition (often sex-stratified) |
| Time to lifespan result | 3-4 months for a complete survival curve |

Lifespan experiments require transfer to fresh food every 2-3 days, a
nontrivial husbandry burden at scale. Death is typically scored by failure
to move after mechanical agitation. Cohort sizes larger than ~300 per
condition are logistically difficult without automated handling, which
remains less mature than the worm platforms.

## Genetic tractability

The Drosophila toolkit is comprehensive and, for some applications,
stronger than the worm's:

- **GAL4/UAS**: the tissue- and temporal-specific expression system is the
  community standard, with thousands of characterized driver lines. Combined
  with temperature-sensitive GAL80, expression can be turned on in adulthood
  only, separating developmental from adult-onset effects (a distinction C.
  elegans RNAi timing makes harder).
- **CRISPR**: efficient. Knock-ins, conditional alleles, and tissue-specific
  Cas9 drivers are all routine. The Drosophila RNAi Center (VDRC) and
  Bloomington stock center provide genome-scale reagent access.
- **FLP/FRT clonal analysis**: mosaic generation for cell-autonomous effect
  testing is more developed than in any other invertebrate.

The fly's contribution to aging genetics includes Indy (the first organismal
longevity gene cloned from a forward screen), the Sir2 overexpression
lifespan extension (later contested), and dFOXO's role in mediating DR and
insulin-signaling effects.

## Translational relevance

Roughly 60% of human disease genes have fly orthologs; pathway-level
conservation is higher. Specific translational strengths:

- **Cardiac aging**: the fly heart tube is a legitimate cardiac model with
  measurable contractility, arrhythmia susceptibility, and age-related
  decline. No worm equivalent exists.
- **Neurodegeneration**: fly models of Alzheimer's, Parkinson's, and
  Huntington's have yielded disease-modifying targets that advanced to
  mammalian testing.
- **Stem cell niches**: the intestine and germline have well-characterized
  adult stem cell populations whose aging has been studied in detail.
- **Behavioral aging**: climbing ability, sleep architecture, and memory
  are quantifiable and decline with age in stereotyped ways.

Caveats: the fly insulin system is less ramified than the mammalian one (one
receptor, seven ligands, no IGF binding proteins). Lipid metabolism differs
substantially. The fly has no adaptive immune system, though innate immunity
is well-conserved.

## Summary assessment

Drosophila is the strongest invertebrate choice when tissue-specific or
cell-autonomous questions matter, or when a worm hit needs a second
invertebrate confirmation before moving to mammals. The 3-month lifespan
is a real cost relative to the worm's 3 weeks.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/mouse_review.md": """# Model Organism Review: Mus musculus in Aging Research

The laboratory mouse is the default mammalian model for aging and the
organism in which most preclinical longevity interventions are validated
before human trials. Its advantages are translational relevance and
toolkit maturity; its costs are lifespan, husbandry expense, and ethical
overhead.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Wild-type median lifespan | ~24-30 months (C57BL/6J; varies by sex, facility) |
| Maximum reported lifespan | ~4.5 years (Ames dwarf, caloric restriction) |
| Generation time | ~10 weeks (mating to weaned pups) |
| Typical cohort size | 30-100 mice/condition |
| Time to lifespan result | 3-4 years for a complete survival curve |

The lifespan is the central constraint. A mouse lifespan study is a 3-year
commitment with no interim readout of the primary endpoint. Per-animal
husbandry cost ranges from $1-2/day at most academic vivaria, putting a
100-mouse cohort at $100K+ over a full lifespan. The NIA Interventions
Testing Program (ITP) was established precisely to socialize this cost for
the community; it tests a handful of compounds per year across three sites
in genetically heterogeneous UM-HET3 mice.

## Genetic tractability

The mouse toolkit is the gold standard for mammalian genetics:

- **Conditional knockouts**: Cre-lox with hundreds of characterized tissue-
  and cell-type-specific drivers, tamoxifen-inducible for temporal control.
- **CRISPR knock-in**: routine for point mutations and reporter insertions;
  generation of a novel allele takes ~6 months including colony expansion.
- **Inbred strain panels**: the BXD recombinant inbred panel and the
  Collaborative Cross enable genetic mapping of lifespan QTLs with mammalian
  resolution.
- **Humanized models**: mice carrying human genes or tissue grafts allow
  direct testing of human-allele-specific effects.

The mouse's genetic toolkit is not the bottleneck; throughput is.

## Translational relevance

Roughly 85% of human protein-coding genes have mouse orthologs; organ
systems, physiology, and most disease phenotypes are homologous. Specific
strengths for aging:

- **ITP validation**: an intervention that extends lifespan in the ITP's
  heterogeneous stock is taken seriously by the translational community.
  Rapamycin, acarbose, and 17-alpha-estradiol are the headline successes.
- **Pathology**: age-related pathology (cancer, nephropathy, sarcopenia,
  cognitive decline) mirrors human presentation closely enough for mechanism
  studies.
- **Pharmacokinetics**: drug metabolism is closer to human than any
  invertebrate, reducing false positives from species-specific clearance.

Caveats: inbred strains are genetically homogeneous in ways humans are not;
strain-specific effects are common and underreported. Mouse tumors differ
from human tumors in telomere biology. Laboratory mice are specific-pathogen
free, which alters immune aging relative to wild mice or humans.

## Summary assessment

The mouse is the translational gatekeeper. A longevity intervention that
hasn't worked in mouse is unlikely to be taken seriously for human trials.
The cost is that mouse studies are the rate-limiting step in the pipeline:
a single failed mouse lifespan study represents years of work and hundreds
of thousands of dollars.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/zebrafish_review.md": """# Model Organism Review: Danio rerio (Zebrafish) in Aging Research

Zebrafish are a vertebrate model with particular strengths in developmental
biology and regeneration that have been increasingly adopted for aging
research over the past decade. Their transparent larvae and high fecundity
make them competitive with invertebrates for some screening applications
while retaining vertebrate physiology.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Wild-type median lifespan | ~3-4 years (AB strain; highly variable by facility) |
| Maximum reported lifespan | ~5.5 years |
| Generation time | ~3 months (hatching to sexual maturity) |
| Typical cohort size | 50-200 fish/condition |
| Time to lifespan result | 4-5 years for a complete survival curve |

The lifespan is comparable to mouse, limiting full-lifespan studies. Most
zebrafish aging work uses surrogate endpoints (senescence markers,
regenerative capacity decline, age-related pathology) rather than survival.
Husbandry is cheaper than mouse (aquatic racks are dense and low-labor) but
requires specialized infrastructure. Disease outbreaks can destroy entire
cohorts; facility-to-facility lifespan variance is notoriously high, with
median lifespans ranging from 2 to 5 years across published studies using
the same nominal strain.

## Genetic tractability

Improving rapidly but not at mouse level:

- **CRISPR**: efficient; knockouts routine. Knock-ins work but are less
  reliable than in mouse.
- **Morpholino knockdown**: historically the workhorse, now deprecated for
  most uses due to off-target concerns documented in multiple retraction-
  adjacent controversies. Use with caution.
- **GAL4/UAS**: available and functional, with a growing set of driver lines,
  but the collection is an order of magnitude smaller than Drosophila's.
- **Transparent larvae**: the optical accessibility of early stages is
  unmatched in vertebrates; live imaging of cell behavior during early aging
  (first year) is a genuine strength.

## Translational relevance

Vertebrate physiology with roughly 70% human orthology at the gene level.
Specific strengths:

- **Regeneration**: zebrafish regenerate fin, heart, and retina. The decline
  of regenerative capacity with age is a unique aging readout unavailable in
  mammals or invertebrates.
- **Cardiac aging**: the adult zebrafish heart is a legitimate model for
  age-related fibrosis and functional decline.
- **Pharmacology**: drugs can be added to tank water, enabling screens that
  are awkward in mice. However, dosing is imprecise (uptake via gill and
  skin is compound-dependent).

Caveats: the genome duplication event in teleost ancestry means many human
genes have two zebrafish paralogs, complicating loss-of-function analysis.
Cold-blooded metabolism differs from mammalian. The high facility-to-
facility lifespan variance makes cross-study comparison unreliable.

## Summary assessment

Zebrafish is a niche choice for aging: the organism to use when regeneration
or optical access is central to the question. For general longevity
screening it offers little over mouse (same lifespan) or killifish (shorter
lived, same clade). Adoption for aging is growing but not yet mainstream.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/killifish_review.md": """# Model Organism Review: Nothobranchius furzeri (Turquoise Killifish)

The turquoise killifish is the shortest-lived vertebrate amenable to
laboratory culture. Collected from ephemeral pools in Zimbabwe and
Mozambique, wild strains have median lifespans of 4-6 months. It has gone
from curiosity to established aging model over roughly fifteen years.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Wild-type median lifespan | 4-6 months (GRZ strain, shortest-lived) |
| Maximum reported lifespan | ~12 months (MZM strains, dietary restriction) |
| Generation time | ~4-5 weeks |
| Typical cohort size | 30-80 fish/condition |
| Time to lifespan result | 8-12 months for a complete survival curve |

The killifish's central appeal is vertebrate physiology at invertebrate
throughput. A complete lifespan curve takes under a year, and a graduate
student can run several cohorts sequentially within a PhD. The GRZ strain
(from Gonarezhou, Zimbabwe) is the standard short-lived reference; MZM
strains from Mozambique are roughly 50% longer-lived and serve as a
naturally long-lived comparison.

Husbandry is more demanding than zebrafish: killifish are aggressive, require
individual or pair housing as adults, and diapause egg management adds
complexity. Roughly 3x the per-animal effort of zebrafish per published
husbandry comparisons.

## Genetic tractability

Developed rapidly since ~2015:

- **CRISPR knockout and knock-in**: both work; knock-in efficiency is lower
  than zebrafish but improving. The reference genome (2015, improved 2020)
  is complete.
- **Tol2 transgenesis**: stable transgenic lines generated routinely.
- **Tissue-specific drivers**: a growing collection, though still thin
  compared to zebrafish or mouse. Maybe two dozen characterized GAL4 lines
  as of recent counts.
- **Diapause manipulation**: embryos can be stored in diapause for months,
  useful for stock management and for separating developmental timing from
  chronological age.

## Translational relevance

Vertebrate, with ~70% human orthology, similar to zebrafish. The specific
value proposition:

- **Rapid aging phenotypes**: killifish develop vertebrate aging hallmarks
  (sarcopenia, neurodegeneration, senescent cell accumulation, telomere
  shortening, cancer) on a compressed timeline, letting you observe the full
  trajectory in months rather than years.
- **Natural variation in lifespan**: the GRZ/MZM strain contrast is a unique
  resource for mapping natural genetic variation in vertebrate longevity.
- **Intervention testing**: drugs can be administered via food; dosing is
  more controlled than tank-water delivery in zebrafish.

Caveats: the model is young, so reagent depth is thin. The aggressive
husbandry limits cohort sizes. The literature is small enough that effect-
size reproducibility across labs is not yet established.

## Summary assessment

Killifish is the vertebrate to use when mouse lifespan is too slow and
zebrafish lifespan isn't an improvement. The field is small but growing
fast; expect the toolkit to mature substantially over the next five years.
The main risk is the husbandry burden and the thin literature base.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/yeast_review.md": """# Model Organism Review: Saccharomyces cerevisiae in Aging Research

Budding yeast is a single-celled eukaryote with two distinct aging
paradigms: replicative lifespan (how many times a mother cell divides
before senescence) and chronological lifespan (how long a non-dividing
cell survives in stationary phase). Both have been productive, with
replicative lifespan the more commonly used.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Replicative lifespan (median) | ~25 divisions (BY4741/2 backgrounds) |
| Chronological lifespan (median) | ~2-3 weeks in standard media |
| Maximum replicative lifespan | ~60 divisions (some long-lived mutants) |
| Generation time | ~90 minutes in rich media |
| Typical cohort size | 40-100 mother cells/genotype (replicative) |
| Time to lifespan result | 1-2 weeks (replicative, manual); days (chronological) |

Replicative lifespan traditionally required manual micromanipulation to
separate daughters from mothers, limiting throughput. Microfluidic "mother
machine" devices now automate this, pushing throughput to hundreds of
mothers per genotype with automated division and death calling. Chronological
lifespan assays are trivially parallelizable (plate-based viability over time)
and have been run genome-wide.

## Genetic tractability

The yeast toolkit is essentially complete:

- **Genome-wide deletion collection**: every non-essential gene has a
  barcoded knockout. Pooled competitive aging assays have been run on the
  full collection.
- **CRISPR**: trivial. Scarless edits in days.
- **Overexpression libraries, DAmP hypomorphs, temperature-sensitive
  alleles**: all available genome-wide.
- **High-throughput phenotyping**: flow cytometry, plate-based growth, and
  microfluidics all scale to thousands of strains per experiment.

The Sir2/sirtuin story originated here; so did the TOR/Sch9 axis's role in
chronological lifespan. More than 300 genes have published replicative
lifespan effects.

## Translational relevance

Human orthology is ~30% at the gene level, rising to ~60% for core cellular
machinery (cell cycle, autophagy, proteostasis, mitochondrial function).
The specific translational strengths:

- **Conserved pathway discovery**: TOR, sirtuins, and ribosomal protein
  deficiency effects all translated from yeast to metazoans.
- **Mechanism**: the tractability makes detailed mechanistic dissection
  (epistasis, biochemistry, imaging) faster than in any metazoan.

Caveats: single-celled, so no tissue-level aging. No nervous system.
Replicative lifespan is a mother-cell-specific phenomenon with no direct
metazoan analog (though the stem-cell analogy is frequently invoked).
Chronological lifespan more closely resembles post-mitotic cell survival but
is media-dependent in ways that complicate interpretation.

## Summary assessment

Yeast is a hypothesis-generation engine and a mechanism-dissection platform.
It is not an organism for translational validation. Use it to find
candidate pathways and work out mechanism before investing in metazoan
testing.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/nmr_review.md": """# Model Organism Review: Heterocephalus glaber (Naked Mole-Rat)

The naked mole-rat is an eusocial rodent from East African burrows with a
maximum lifespan exceeding 30 years, roughly ten times that of a similarly
sized mouse. It is studied as a model of exceptional longevity rather than
as a general aging model: the question is what makes it long-lived, not how
to screen interventions in it.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Median lifespan | not well-established; survivorship is roughly flat until ~20+ years |
| Maximum documented lifespan | >37 years (captive) |
| Generation time | ~6-12 months (but only the queen breeds) |
| Typical cohort size | colonies of 20-300; experimental cohorts are opportunistic |
| Time to lifespan result | N/A (lifespan studies are impractical) |

The eusocial breeding structure (one queen, a few breeding males, the rest
non-reproductive) makes controlled genetic crosses essentially impossible.
Cohorts are opportunistic samples from colonies maintained for decades.
Lifespan studies are not feasible; instead, research focuses on the
mechanistic basis of observed longevity and stress resistance traits.

## Genetic tractability

Minimal:

- **No germline genetics**: the eusocial structure prevents it.
- **Reference genome**: available (2011, improved since), enabling
  transcriptomic and comparative genomic studies.
- **Cell lines**: primary fibroblast and other cell lines exist and are
  the main experimental substrate. They show the famous stress-resistance
  and contact-inhibition phenotypes in vitro.
- **CRISPR in cell lines**: works; organism-level CRISPR is not practical.

## Translational relevance

As a mammal, baseline physiology is homologous to human. The specific
interest is in the exceptional traits:

- **Cancer resistance**: near-zero spontaneous cancer incidence across
  decades of observation. The high-molecular-weight hyaluronan hypothesis
  is the leading mechanistic account and has spurred some translational
  interest.
- **Hypoxia tolerance**: survives 18 minutes at 0% oxygen via fructose
  metabolism. Potential relevance to ischemic injury.
- **Negligible senescence**: mortality rate does not increase with age over
  the observed range, a near-unique demographic pattern among mammals.
- **Proteostasis**: the proteasome and chaperone systems appear more robust
  than in mouse; whether this is cause or consequence of longevity is open.

Caveats: the N is small, the genetics are intractable, and the traits may
be a package deal evolved for the subterranean eusocial niche rather than
modular features transferable to other mammals.

## Summary assessment

The naked mole-rat is a comparative biology resource, not a screening
organism. Study it to understand what exceptional mammalian longevity looks
like and generate hypotheses about mechanism. Testing those hypotheses
requires a tractable model.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
    # ─────────────────────────────────────────────────────────────────────
    "/research/rhesus_review.md": """# Model Organism Review: Macaca mulatta (Rhesus Macaque)

Rhesus macaques are the primary non-human primate model for aging research.
With a maximum lifespan of ~40 years and physiology closely mirroring human,
they represent the closest experimentally accessible approximation to human
aging, at correspondingly high cost.

## Lifespan and throughput

| Metric | Value |
|---|---|
| Median lifespan | ~25 years (captive) |
| Maximum documented lifespan | ~40 years |
| Generation time | ~4-5 years (sexual maturity) |
| Typical cohort size | 10-30 animals/condition |
| Time to lifespan result | 25-30 years for survival curves |

Full-lifespan studies require multi-decade institutional commitment. Only a
handful exist: the NIA and Wisconsin caloric restriction studies (started
1987 and 1989 respectively) are the notable examples, and their divergent
results (Wisconsin saw lifespan extension, NIA did not) illustrate how
sensitive primate outcomes are to protocol details. Most macaque aging
research uses cross-sectional or short-longitudinal designs with surrogate
endpoints.

Per-animal costs are on the order of $20-50K/year including housing,
veterinary care, and enrichment. A 30-animal cohort over a decade is a
multi-million-dollar undertaking.

## Genetic tractability

Minimal for aging purposes:

- **Transgenesis and CRISPR**: technically possible and done for some
  disease models, but the generation time and ethical considerations make
  germline modification impractical for aging studies.
- **Natural genetic variation**: pedigreed colonies enable QTL mapping in
  principle, but statistical power is limited by cohort size.
- **Pharmacology**: the main experimental lever. Drugs can be dosed with
  human-relevant pharmacokinetics.

## Translational relevance

The closest available to human short of human trials:

- **Physiology**: organ systems, endocrine axes, immune function, and
  cognitive architecture are directly homologous.
- **Aging phenotypes**: macaques develop sarcopenia, osteoporosis, immune
  senescence, metabolic dysfunction, and cognitive decline with trajectories
  that closely parallel human aging.
- **Pharmacology**: drug metabolism and target engagement are more
  predictive of human response than any rodent model.
- **Biomarkers**: epigenetic clocks, senescence markers, and frailty indices
  developed in macaque transfer to human with minimal recalibration.

Caveats: cost and ethical overhead restrict studies to a tiny number of
well-funded centers. The CR controversy shows even primate results can be
protocol-dependent. Null results are difficult to interpret given the
small N.

## Summary assessment

Macaques are a validation and biomarker-refinement model, not a discovery
model. A handful of interventions per decade will get primate testing. Use
macaque data to bridge the gap between mouse efficacy and human trial
design, not to screen.
"""
    + _METHODS_FOOTER
    + _EXTENDED_APPENDIX,
}


# Probe questions for testing what survives compaction.
#
# These are deliberately mixed: some target high-level facts the agent is
# likely to note and the summarizer is likely to preserve; others target
# obscure specifics buried deep in the appendix tables that almost
# certainly won't survive. The goal is to show compaction's lossiness as
# a spectrum, not a binary.

CANARY_QUESTION = "What is the typical manual-vs-automated lifespan scoring bias in C. elegans?"
CANARY_ANSWER = (
    "Automated platforms inflate lifespan estimates by roughly 10-15% relative to manual scoring"
)

COMPACTION_PROBES = [
    # (question, answer_substring, expected_to_survive)
    # High-level facts — likely to survive: the agent notes these, and the
    # summarizer preserves them because they're central to the task.
    ("What is the approximate median lifespan of C. elegans at 20°C?", "18", True),
    (
        "Which model organism is the shortest-lived vertebrate used in aging research?",
        "killifish",
        True,
    ),
    ("Roughly what percentage of human disease genes have Drosophila orthologs?", "60", True),
    # Obscure specifics — unlikely to survive: buried in appendix tables,
    # not central to the comparative task, unlikely to be noted or summarized.
    (
        "In the appendix Table A5, what is the I-squared heterogeneity value for the NAD+ precursor intervention?",
        "61",
        False,
    ),
    (
        "In appendix Table A2, what was the effect magnitude for the IIS reduction intervention in cohort 2?",
        "55",
        False,
    ),
    (
        "In appendix Table A7, what is the PhenoAge-like epigenetic clock acceleration ratio under DR for liver tissue?",
        "0.72",
        False,
    ),
]
