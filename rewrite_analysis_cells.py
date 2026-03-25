"""Rewrite all markdown cells in advanced_NPDB.ipynb with comprehensive analysis.

Replaces all markdown cells with:
- Proper section headings explaining purpose
- Variable glossaries for engineered features
- Granular analysis findings with no team member names
- Detailed linkage validation walkthrough
"""

import json

with open("advanced_NPDB.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# ── New markdown content keyed by cell index ──────────────────────────────

new_markdown = {}

# ── Cell 0: Title ──
new_markdown[0] = """# NPDB Advanced Malpractice Payment Analysis

## Purpose

This notebook performs a multi-layered quantitative analysis of the **National Practitioner Data Bank (NPDB)** Public Use Data File, focusing exclusively on medical malpractice payment records. The analysis spans **1990--2025** and covers:

- **Payment structure:** Separating single vs. multiple payment cases and understanding their different severity profiles
- **Pre-2004 reconstruction:** Validating and applying episode-linkage rules to recover total payment information missing from legacy records
- **Geographic variation:** Hierarchical state-level analysis with a Wisconsin focal comparison against Midwest peer states
- **Temporal trends:** Decade-level trends in claim volume, severity, catastrophic rates, and resolution types
- **Loss distribution fitting:** Identifying the statistical distribution that best characterizes malpractice payment severity
- **Predictive modeling:** GLM severity models and logistic classification of catastrophic claims
- **Time-to-payment analysis:** Measuring the lag between malpractice incident and payment resolution

## Core Analytical Rules

| Rule | Implementation |
|------|---------------|
| **Cohort** | Malpractice records only: `RECTYPE in ['M', 'P']` |
| **Currency** | All monetary values in **CPI-adjusted 2025 US dollars** |
| **Reporting** | Both **counts and percentages** in all summary tables and charts |
| **Payment modes** | Single, Multiple, and Unknown/Unavailable kept as separate categories |
| **Total payments** | Distinguished as **Observed** (post-2004), **Reconstructed** (pre-2004 via linkage), or **Unresolved** |

## Data Source

The NPDB Public Use Data File (`NPDB2510.CSV`) contains **1,895,122 records** across all report types. The malpractice cohort analyzed here comprises **529,830 records** (28% of the full database).

---
"""

# ── Cell 1: Workflow Artifacts ──
new_markdown[1] = """## Project Architecture

This notebook is intentionally thin -- most computation lives in reusable Python modules under `npdb_analysis/`.

| Module | Responsibility |
|--------|---------------|
| `loading.py` | CSV ingestion, column profiling, record-type counting |
| `transforms.py` | Data type corrections, structural missingness detection |
| `features.py` | Feature engineering: CPI adjustment, period bucketing, resolution flags |
| `config.py` | Constants: CPI factors, peer state lists, payment mode mappings |
| `payment_modes.py` | Single/multiple payment separation, practitioner profiling |
| `linkage.py` | Episode key construction, linkage validation, TOTALPMT reconstruction |
| `aggregation.py` | Grouped summaries: by period, state, state-period-mode, mobility |
| `modeling.py` | Distribution fitting, GLM severity, logistic classification, lag analysis |
| `plotting.py` | Reusable chart functions: bar charts, heatmaps, peer-state trends |
"""

# ── Cell 2: Notebook Map ──
new_markdown[2] = """## Notebook Map

The notebook is organized into **12 analytical sections** in execution order. Sections 1--3 are the data foundation and must run first. Sections 4--12 can be independently re-executed once the foundation is in place.

| Section | Title | Purpose |
|---------|-------|---------|
| 1 | Raw Data Load & Initial Audit | Schema shape, record types, raw missingness |
| 2 | Data Transformation & Missingness | Dtype fixes, structural vs. random missingness |
| 3 | Feature Engineering | CPI normalization, period grouping, derived flags |
| 4 | Payment Mode Separation | Single vs. multiple payment analysis (post-2004) |
| 5 | Linkage Validation & Reconstruction | Episode grouping validation, pre-2004 TOTALPMT recovery |
| 6 | Time-Grouped Analysis | Decade-level trends by report year and incident year |
| 7 | Hierarchical State Analysis | State-level variation in payment patterns |
| 8 | Wisconsin & Peer-State Comparison | Midwest focal analysis with 6 comparison states |
| 9 | Practitioner Multi-State Presence | Cross-state practitioner mobility and exposure |
| 10 | Settlement vs. Judgment | Resolution type trends and policy context |
| 11 | Loss Distribution & Severity Modeling | Distribution fitting, GLM, catastrophic classification |
| 12 | Time-to-Payment Analysis | Incident-to-payment lag patterns |
"""

# ── Cell 4: Runtime Check ──
new_markdown[4] = """### Runtime Check

If the import cell above fails, resolve the environment issue before continuing. The rest of this notebook depends on the `npdb_analysis` package being importable and the NPDB CSV file being available at the configured data path.

**Required packages beyond the standard scientific stack:** `statsmodels`, `lifelines`, `scikit-learn`
"""

# ── Cell 5: Section 1 heading ──
new_markdown[5] = """## Section 1: Raw Data Load and Initial Audit

### Purpose
Establish the raw dataset dimensions, understand the multi-record-type architecture of the NPDB, and profile column-level missingness *before* any transformation.

### Key NPDB Record Types

| RECTYPE | Description | Relevance |
|---------|-------------|-----------|
| **M** | Legacy malpractice format (pre-2004) | **Part of analysis cohort** -- lacks TOTALPMT, OUTCOME, PTSEX, PTAGE |
| **P** | Post-2004 malpractice format | **Part of analysis cohort** -- fully populated |
| **C** | Continuous action reports (clinical privileges, society actions) | Excluded from malpractice analysis |
| **A** | Adverse action reports (licensure, DEA, exclusions) | Excluded from malpractice analysis |

### What to Expect
The raw file contains ~1.9M records. Only RECTYPE M + P (~530K records) form the malpractice analysis cohort. The remaining ~1.4M records (C + A types) are non-malpractice and will be filtered out in Section 3.
"""

# ── Cell 10: Finding - Record Type Distribution ──
new_markdown[10] = """### Finding: Record Type Distribution Reveals a Dual-Format Dataset

**Scale:** The NPDB contains **1,895,122 total records** spanning 1990--2025, with 54 columns per record.

**Record Type Breakdown:**

| RECTYPE | Description | Count | Share |
|---------|-------------|-------|-------|
| C | Continuous action reports | 1,314,661 | 69.4% |
| P | Post-2004 malpractice format | 279,158 | 14.7% |
| M | Legacy malpractice format (pre-2004) | 250,672 | 13.2% |
| A | Adverse action reports | 50,631 | 2.7% |

**Critical Structural Insight:** The malpractice cohort (M + P = **529,830 records**, 28.0% of total) forms our analysis universe. The dominance of C-type records (clinical privilege and professional society actions) means nearly 70% of the database is outside our scope -- a common misconception when reporting "NPDB size."

**Missingness Architecture:** The column profile reveals that missingness is overwhelmingly **structural, not random**:
- `TOTALPMT`, `OUTCOME`, `PTSEX`, `PTAGE` are ~85% null -- because they only populate for RECTYPE='P' (14.7% of records)
- `ALGNNATR` and `PAYMENT` are ~72% null -- because they only populate for malpractice records (M+P = 28.0%)
- `HOMECTRY` and `WORKCTRY` are 100% null -- systematically unpopulated in the public-use file

This is not data quality failure; it is the expected consequence of the NPDB's multi-record-type architecture. Analyses must filter to the correct RECTYPE subset before computing any statistics.
"""

# ── Cell 11: Section 2 heading ──
new_markdown[11] = """## Section 2: Data Transformation and Missingness Handling

### Purpose
Apply mandatory data type corrections and characterize missingness patterns by record type to establish which fields are available for which analytical segments.

### Transformations Applied
| Step | Detail |
|------|--------|
| **Dollar columns** | `PAYMENT` and `TOTALPMT` converted from encoded strings to numeric |
| **Coded fields** | `ALGNNATR`, `PAYTYPE`, `OUTCOME`, etc. cast to appropriate types |
| **String normalization** | State codes and category fields cleaned and standardized |
| **Missingness separation** | Structural missingness (by RECTYPE design) distinguished from true data gaps |

### Why This Matters
Many NPDB columns appear to have catastrophic missingness rates (70--85%). Understanding that this is **record-type-driven** rather than random prevents incorrect imputation decisions and ensures analyses use only the fields genuinely available for each data segment.
"""

# ── Cell 16: Finding - Missingness ──
new_markdown[16] = """### Finding: Missingness Is Record-Type Driven -- Not Random

The RECTYPE-stratified missingness table confirms the structural pattern:

**RECTYPE 'P' (post-2004 malpractice)** has near-complete data:
- `OUTCOME`, `PTSEX`, `TOTALPMT`, `PAYNUMBR`: **0.0% missing** -- full coverage
- `PTAGE`: 3.6% missing (10,041 records) -- the only non-trivial gap
- `WORKSTAT`: 20.2% missing -- growing over time, necessitating the STATE composite fallback

**RECTYPE 'M' (legacy malpractice)** has systematic blanks by design:
- `OUTCOME`, `PTSEX`, `PTAGE`, `TOTALPMT`: **100% missing** -- these fields were not collected in the pre-2004 format
- `PAYNUMBR`: 0.01% missing (14 records) -- essentially complete
- `ALGNNATR`: 0.07% missing (171 records) -- essentially complete
- `WORKSTAT`: 3.0% missing -- better coverage than post-2004

**RECTYPE 'A' and 'C'**: 100% missing for all malpractice-specific fields (expected -- these are not malpractice records).

**Implication for Analysis:** Any analysis involving `OUTCOME`, `PTSEX`, `PTAGE`, or `TOTALPMT` is restricted to the **279,158 post-2004 records** (RECTYPE='P'). The full 529,830 malpractice cohort can be used for `PAYMENT`, `PAYTYPE`, `ALGNNATR`, `STATE`, and temporal analyses. This is not a limitation to work around -- it is the fundamental data boundary that shapes every downstream analysis.
"""

# ── Cell 17: Interpretation Checkpoint ──
new_markdown[17] = """### Interpretation Checkpoint

Before proceeding, confirm the expected structural missingness pattern:
- Legacy malpractice records (RECTYPE='M') drive the high missingness in `TOTALPMT`, `OUTCOME`, `PTAGE`, `PTSEX`, and `PAYNUMBR`
- State fields show partial coverage, which is why the composite fallback (WORKSTAT -> LICNSTAT -> HOMESTAT) is required
- Fields like `ALGNNATR` and `PAYMENT` are nearly complete within the malpractice cohort -- the 72% overall null rate is entirely from non-malpractice record types
"""

# ── Cell 18: Section 3 heading ──
new_markdown[18] = """## Section 3: Common Feature Engineering

### Purpose
Filter to the malpractice cohort and create all derived variables used throughout the analysis. Every engineered variable is documented below.

### Variable Glossary: Engineered Features

| Variable | Source | Definition | Used In |
|----------|--------|------------|---------|
| `PAYMENT_ADJ` | `PAYMENT` x CPI factor | Individual payment amount in **2025 dollars** | All sections |
| `TOTALPMT_ADJ` | `TOTALPMT` x CPI factor | Total case payment in **2025 dollars** (post-2004 only) | Sections 4-5 |
| `LOG_PAYMENT_ADJ` | log(`PAYMENT_ADJ`) | Natural log of adjusted payment for distribution fitting | Section 11 |
| `STATE` | WORKSTAT -> LICNSTAT -> HOMESTAT | Composite state: uses work state first, falls back to license then home state | All geographic analyses |
| `PERIOD_10Y` | `ORIGYEAR` bucketed | Report-year decade (e.g., "1990-1999", "2000-2009") | Sections 6-8 |
| `PERIOD_5Y` | `ORIGYEAR` bucketed | Report-year 5-year window (e.g., "1990-1994") | Section 6 |
| `MAL_PERIOD_10Y` | `MALYEAR1` bucketed | Incident-year decade based on when the malpractice occurred | Section 6 |
| `MAL_PERIOD_5Y` | `MALYEAR1` bucketed | Incident-year 5-year window | Section 6 |
| `LAG_YEARS` | `ORIGYEAR` - `MALYEAR1` | Years between malpractice incident and payment report | Section 12 |
| `RESOLUTION_BINARY` | `PAYTYPE` | "Judgment" if PAYTYPE indicates court verdict; "Settlement" otherwise (per NPDB coding guidance) | Sections 10-12 |
| `IS_JUDGMENT` | `RESOLUTION_BINARY` | Binary flag: 1 = Judgment, 0 = Settlement | Sections 6-8 |
| `CATASTROPHIC` | `PAYMENT_ADJ` >= $1,000,000 | Binary flag: 1 = payment exceeds $1M in 2025 dollars | Sections 6-11 |
| `PAYMENT_MODE` | `PAYNUMBR` mapped | "Single Payment" (S), "Multiple Payments" (M), "Unavailable Pre-2004" (RECTYPE M) | Section 4 |
| `PAYNUMBR_STR` | `PAYNUMBR` cleaned | Standardized string version of payment number code | Section 4 |

### CPI Adjustment Methodology
All monetary values are normalized to **2025 US dollars** using the Consumer Price Index for All Urban Consumers (CPI-U). Each record's payment is multiplied by a year-specific CPI factor based on `ORIGYEAR`. Example: a $100,000 payment in 1990 becomes approximately $232,000 in 2025 dollars. This ensures valid cross-decade comparisons.

### State Composite Logic
The NPDB records three state fields with varying completeness:
1. **WORKSTAT** (state where incident occurred) -- preferred but 20% missing in post-2004 records
2. **LICNSTAT** (state of licensure) -- fallback
3. **HOMESTAT** (home state) -- last resort

The `STATE` variable uses the first non-null value in this priority order, achieving **>99.99% coverage**.
"""

# ── Cell 22: Finding - Cohort Baseline ──
new_markdown[22] = """### Finding: Analysis-Ready Cohort Baseline

**Cohort:** 529,830 malpractice records (RECTYPE M + P) with 74 engineered features.

**Key Baseline Metrics (all payments CPI-adjusted to 2025 dollars):**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Mean payment | $379,117 | Pulled upward by catastrophic tail |
| Median payment | $169,650 | Half of all payments are below $170K -- the "typical" case |
| Mean-to-median ratio | 2.24x | Confirms extreme right skew in the payment distribution |
| Catastrophic share (>$1M) | 9.50% | Roughly 1 in 10.5 payments exceeds $1M in 2025 dollars |
| Judgment share | 2.73% | 97.3% of cases resolve without trial verdict |

**Understanding the Mean-to-Median Ratio:**
The mean-to-median ratio of 2.24x is a key indicator of distributional skewness. In a symmetric distribution (like the normal), this ratio would be ~1.0. A ratio of 2.24x means the average is more than double the midpoint, caused by extreme values in the right tail. For context:
- A ratio of 1.0--1.2 = roughly symmetric
- A ratio of 1.5--2.0 = moderately skewed
- A ratio of 2.0+ = heavily skewed (common in insurance loss data)

This has practical consequences: quoting the "average malpractice payment" ($379K) dramatically overstates the typical experience ($170K). The distinction matters for policy discussions, premium setting, and public understanding.

**Data Quality Flags:**

| Quality Metric | Value | Assessment |
|----------------|-------|------------|
| Missing STATE | 0.01% | Excellent -- composite fallback works |
| Missing allegation | 0.03% | Essentially complete |
| Missing OUTCOME | 47.31% | Expected -- exactly the RECTYPE='M' share |
| Payment mode known | 52.69% | Post-2004 records only |
| Observed TOTALPMT | 52.69% | Same boundary -- TOTALPMT only in RECTYPE='P' |

The 9.5% catastrophic share is higher than the commonly cited ~3% figure because CPI adjustment inflates historical payments into 2025 dollars, pushing more records above the $1M threshold.
"""

# ── Cell 23: Section 4 heading ──
new_markdown[23] = """## Section 4: Payment Mode Separation -- Single vs. Multiple Payment Analysis

### Purpose
Analyze the structural difference between cases that generated a single malpractice payment versus cases that generated multiple payments on behalf of the same practitioner. This distinction is only available for post-2004 records (RECTYPE='P') via the `PAYNUMBR` field.

### Key Variable: `PAYNUMBR` (Payment Number)
The NPDB's `PAYNUMBR` field encodes whether a payment record is:
- **S (Single Payment):** The only payment made for this claim -- `PAYMENT` equals `TOTALPMT`
- **M (Multiple Payments):** One of several payments for the same claim -- `TOTALPMT` captures the aggregate
- **U (Unknown):** Payment number status not determined

This field was introduced with the post-2004 format (RECTYPE='P'). For pre-2004 records (RECTYPE='M'), we label the payment mode as **"Unavailable Pre-2004"** since the information was not collected.

### Why This Matters
Multiple-payment cases represent fundamentally different liability patterns:
- They often involve more severe injuries requiring structured settlements
- They may reflect multiple defendants contributing to the same claim
- Their per-record payment amounts understate total case exposure (TOTALPMT captures the full picture)
- The practitioner profiles behind these cases reveal patterns of repeated malpractice involvement

### Practitioner Behavioral Profiles
Multi-payment practitioners are classified into four behavioral profiles based on their record patterns:

| Profile | Criteria | Interpretation |
|---------|----------|---------------|
| **Chronic Repeater** | 3+ reports over 3+ years | Persistent pattern suggesting systemic practice issues |
| **Catastrophic Event** | Mean payment >= $1M with <= 3 reports | Single devastating incident with large payouts |
| **Batch Reporter** | 3+ reports within 1 year | Clustered reporting, possibly a single event with multiple claimants |
| **Moderate Repeater** | 2+ reports (not fitting above) | Lower-frequency repeat involvement |
"""

# ── Cell 35: Finding - Payment Mode ──
new_markdown[35] = """### Finding: Single Payments Dominate, but Multiple-Payment Cases Carry Disproportionate Severity

**Overall Payment Mode Distribution (Post-2004 Records):**

| Mode | Count | Share | Mean Payment (2025$) | Median Payment (2025$) |
|------|-------|-------|---------------------|----------------------|
| Single Payment | 267,557 | 50.5% | $397,832 | $195,750 |
| Multiple Payments | 11,601 | 2.2% | $581,169 | $313,600 |
| Unavailable (Pre-2004) | 250,672 | 47.3% | -- | -- |

**Key Insights:**

1. **Multiple-payment cases are 46% more expensive on average** ($581K vs. $398K mean), and their median is 60% higher ($314K vs. $196K). Cases generating multiple payments typically involve more severe injuries, more defendants, or longer litigation.

2. **Multiple payments account for only 4.2% of post-2004 records but carry outsized financial weight.** With a mean payment 1.46x higher per report and multiple reports per case, these practitioners represent concentrated liability exposure.

3. **The multi-payment practitioner profile** reveals distinct behavioral clusters: practitioners with 19+ reports spanning 8+ years, and practitioners with fewer reports but catastrophic per-payment amounts ($65M total across 5 reports in 3 years -- likely a severe obstetric or neurological case).

4. **Multi-payment share is declining over time:** from 5.1% in 2000--2009 to 4.3% in 2010--2019 to 2.5% in 2020--2029. This could reflect (a) tort reform reducing multi-defendant litigation, (b) faster single-lump settlements, or (c) right-censoring (recent cases have not yet accumulated additional payments).

**Practitioner Profile Classification Results:**
- **Moderate Repeaters** constitute the majority -- practitioners with 2+ reports but without extreme patterns
- **Chronic Repeaters** (3+ reports over 3+ years) represent a persistent risk population
- **Catastrophic Events** (mean payment >= $1M, <= 3 reports) capture practitioners involved in devastating single incidents
- **Batch Reporters** (3+ reports within 1 year) suggest clustered incidents, possibly a single surgical complication affecting multiple patients

The single-payment subset (267,557 records) is now cleanly isolated for loss distribution fitting in Section 11. The multiple-payment subset (11,601 records) informs the linkage validation in Section 5.
"""

# ── Cell 36: Section 5 heading ──
new_markdown[36] = """## Section 5: Linkage Validation and Pre-2004 Total Payment Reconstruction

### Purpose
The NPDB's `TOTALPMT` field (total payment for a claim) is only available in post-2004 records (RECTYPE='P'). For the 250,672 pre-2004 records (RECTYPE='M'), this field is blank. This section develops, validates, and applies an **episode-linkage rule** that reconstructs total payment estimates for pre-2004 records.

### The Problem
Without `TOTALPMT`, pre-2004 records can only report individual `PAYMENT` amounts. For practitioners involved in claims with multiple payments, the individual `PAYMENT` understates total case exposure. We need a way to group related payment records into "episodes" (derived claims) and sum their payments to estimate the total.

### The Approach: Deterministic Episode Linkage

Rather than assuming a claim ID exists, we construct one by grouping records that share the same combination of identifying fields. Two linkage tiers are tested:

**Strict Tier** -- groups records by 6 fields (all must match exactly):

| Key Column | Role |
|------------|------|
| `PRACTNUM` | Same de-identified practitioner |
| `STATE` | Same state of practice |
| `MALYEAR1` | Same incident start year |
| `MALYEAR2` | Same incident end year |
| `ALGNNATR` | Same allegation nature code |
| `PAYTYPE_STR` | Same payment type (settlement vs. judgment) |

Maximum allowed year span between grouped records: **3 years**

**Moderate Tier** -- groups records by 5 fields with looser matching:

| Key Column | Difference from Strict |
|------------|----------------------|
| `PRACTNUM` | Same |
| `STATE` | Same |
| `MALYEAR1` | Same |
| `ALGNNATR` | Same |
| `ORIGYEAR_WINDOW` | Replaces MALYEAR2 + PAYTYPE_STR; groups report years into 3-year windows |

Maximum allowed year span: **5 years**

### How the Episode Key Works (Step by Step)

1. **Key construction:** For each record, concatenate the tier's key columns with `|` separators into a single string (e.g., `"12345|NY|2005|2005|114|S"`). Records with identical keys belong to the same episode.

2. **Episode aggregation:** Group all records sharing the same key. For each episode, compute:
   - `record_count`: how many payment records belong to this episode
   - `payment_sum_adj`: sum of all individual `PAYMENT_ADJ` values in the episode
   - `totalpmt_max_adj`: the maximum observed `TOTALPMT_ADJ` (for validation against ground truth)

3. **Ambiguity detection:** An episode is flagged as **ambiguous** if it contains:
   - Multiple distinct practitioners (should be impossible with PRACTNUM in the key)
   - Multiple distinct states
   - Multiple distinct allegation types
   - Multiple distinct payment types
   - An ORIGYEAR span exceeding the tier's maximum (3 years for strict, 5 for moderate)

4. **Validation (post-2004 only):** For episodes where the true `TOTALPMT` is observed, compare `payment_sum_adj` (our derived total) against `totalpmt_max_adj` (the reported truth). Compute absolute percentage error to measure reconstruction accuracy.

5. **Reconstruction eligibility:** Episodes that are (a) not ambiguous and (b) have at least 1 record are eligible for reconstruction.

### Key Output Variables

| Variable | Definition |
|----------|-----------|
| `EPISODE_KEY` | Deterministic concatenation of tier key columns |
| `LINKAGE_TIER` | Which tier's rules were used ("strict" or "moderate") |
| `TOTALPMT_BEST` | Best available total payment: observed TOTALPMT_ADJ when available, reconstructed sum when not |
| `TOTALPMT_SOURCE` | Provenance tag: "observed" (post-2004 truth), "reconstructed" (derived from linkage), or "unresolved" (could not determine) |
| `EPISODE_PAYMENT_SUM_ADJ` | Sum of all PAYMENT_ADJ values in the derived episode |
| `ambiguous_episode` | Boolean flag: True if the episode fails any consistency check |
| `reconstruction_eligible` | Boolean flag: True if the episode is non-ambiguous and eligible for TOTALPMT reconstruction |
"""

# ── Cell 43: Finding - Linkage Validation ──
new_markdown[43] = """### Finding: Strict Linkage Validation Shows Excellent Reconstruction Accuracy

**Validation Design:** The episode-linkage rule was tested on **post-2004 records where the true TOTALPMT is known**. The derived episode sum (`payment_sum_adj`) was compared to the reported total (`totalpmt_max_adj`) to measure how well the grouping rule recovers the actual claim total.

**Validation Results:**

| Metric | Strict Tier | Moderate Tier |
|--------|-------------|---------------|
| Episodes validated | 261,575 | 263,075 |
| Median absolute % error | 0.00% | 0.00% |
| Mean absolute % error | 0.04% | 0.04% |
| Within 10% accuracy | 93% | 94% |
| Within 25% accuracy | 94% | 95% |
| Ambiguous episodes | 659 (0.25%) | -- |

**Interpreting the Results:**
- A **median error of 0.0%** means over half of derived episodes exactly match the reported TOTALPMT -- the linkage perfectly identified the correct grouping
- The **93% within-10% rate** means that for the vast majority of cases, the reconstructed total is a reliable proxy for the true total
- Only **0.25% of episodes** were flagged as ambiguous under the strict tier, meaning the grouping rules are highly specific

**Why Strict Was Chosen Over Moderate:**
Both tiers perform similarly on accuracy metrics. The strict tier was selected because:
- Its tighter matching rules (requiring exact MALYEAR2 and PAYTYPE match) minimize the risk of incorrectly linking separate cases
- The marginal accuracy gain from moderate (1 percentage point) does not justify the increased risk of false linkages
- With only 0.25% ambiguous episodes, strict linkage already captures the vast majority of cases

**Pre-2004 Reconstruction Results:**

| Source | Records | Mean Total (2025$) | Median Total (2025$) | Share |
|--------|---------|--------------------|--------------------|-------|
| Observed (post-2004) | 279,158 | $423,173 | $205,900 | 52.7% |
| Reconstructed (pre-2004) | 248,568 | $388,730 | $156,600 | 46.9% |
| Unresolved | 2,104 | -- | -- | 0.4% |

The $34K gap in mean between observed and reconstructed ($423K vs. $389K) partly reflects genuinely lower payment levels in earlier decades even after CPI adjustment, and partly the absence of multi-payment linking information pre-2004. Only **2,104 records (0.4%)** could not be resolved -- an acceptably small residual.

**Bottom line:** The `TOTALPMT_BEST` column is validated and safe to use for full-span 1990--2025 analyses. The `TOTALPMT_SOURCE` column provides a provenance tag so any downstream analysis can filter to only observed values if desired.
"""

# ── Cell 44: Reconstruction Rule ──
new_markdown[44] = """### Reconstruction Guardrail

If the strict-linkage validation metrics were poor (e.g., <80% within 10% accuracy), the `TOTALPMT_BEST` column should not be used for interpretive analyses. The notebook is designed so all descriptive sections can still run on report-level `PAYMENT_ADJ` without requiring reconstructed totals.

**For this dataset, validation passed with 93% accuracy, so `TOTALPMT_BEST` is approved for use throughout.**
"""

# ── Cell 45: Section 6 heading ──
new_markdown[45] = """## Section 6: Time-Grouped Analysis

### Purpose
Analyze malpractice payment trends across decades using two complementary time bases:

| Time Base | Variable | What It Captures |
|-----------|----------|-----------------|
| **Report year** | `ORIGYEAR` -> `PERIOD_10Y`, `PERIOD_5Y` | When the payment was reported to the NPDB -- reflects the reporting/payment system |
| **Incident year** | `MALYEAR1` -> `MAL_PERIOD_10Y`, `MAL_PERIOD_5Y` | When the malpractice incident actually occurred -- reflects the legal and medical environment at the time of the event |

### Why Two Time Bases Matter
A malpractice payment reported in 2010 may stem from an incident in 2004. Using only `ORIGYEAR` would attribute this to the 2010s legal environment, when the relevant tort rules were actually those in effect in 2004. Conversely, using only `MALYEAR1` would ignore changes in the payment/reporting system. Both perspectives are needed.

### The Report-Incident Cross-Tab (Heatmap)
The heatmap below cross-tabulates report decade vs. incident decade, revealing the **lag structure** of malpractice payment resolution. Cells along the diagonal (incident and report in the same decade) are contemporaneous. Off-diagonal cells show delayed resolution.
"""

# ── Cell 51: Finding - Time Analysis ──
new_markdown[51] = """### Finding: Claim Volume Is Declining but Severity Keeps Rising -- A Diverging Trend

**By Report Decade (ORIGYEAR, CPI-adjusted to 2025$):**

| Period | Claims | Share | Mean Payment | Median Payment | Catastrophic Rate | Judgment Rate |
|--------|--------|-------|-------------|---------------|-------------------|---------------|
| 1990--1999 | 171,129 | 32.3% | $324,656 | $124,375 | 7.8% | 3.4% |
| 2000--2009 | 170,548 | 32.2% | $404,190 | $184,000 | 10.9% | 3.1% |
| 2010--2019 | 122,994 | 23.2% | $403,144 | $195,300 | 10.7% | 2.2% |
| 2020--2029 | 65,159 | 12.3% | $411,150 | $218,400 | 7.9% | 1.1% |

**Three key patterns emerge:**

1. **Volume decline:** Claims dropped 28% from the 2000s to 2010s and are on pace for another significant drop in the 2020s (though right-censoring partly explains the 2020s figure -- many incidents from this decade have not yet resolved). This aligns with national tort reform trends.

2. **Severity escalation:** Even after CPI adjustment, mean payments rose 27% from the 1990s ($325K) to the 2020s ($411K). The median rose 76% ($124K to $218K). Fewer claims are being filed, but the ones that get paid are more expensive.

3. **Judgment rates are collapsing:** From 3.4% in the 1990s to 1.1% in the 2020s. The malpractice system is moving almost entirely toward settlement resolution, with trial verdicts becoming increasingly rare.

**Report-Year vs. Incident-Year Cross-Tab Insights:**
The heatmap reveals substantial lag structure:
- Incidents from the 1980s were still generating payments in the 1990s
- Incidents from the 1990s were still resolving into the 2000s
- Notably, incidents from 1970--1979 that resolved in the 1990s had a **mean payment of $422K** -- higher than contemporaneous 1990s incidents ($299K). This suggests older cases that finally resolved were the more severe ones (a selection effect: simple cases settle quickly, complex catastrophic cases linger).

**Anomaly:** A small number of records show incident years in the "3990--3999" range, clearly a data entry error. These are excluded from incident-year analyses but retained in report-year analyses.
"""

# ── Cell 52: Section 7 heading ──
new_markdown[52] = """## Section 7: Hierarchical State Analysis

### Purpose
Analyze malpractice payment patterns at the state level, with the ability to drill down by decade and payment mode. The core analytical structure is a three-level groupby:

**`STATE` -> `PERIOD_10Y` -> `PAYMENT_MODE`**

This single hierarchical table supports national comparisons, state drilldowns, and payment-mode decomposition from one consistent structure.

### What Drives State-Level Variation
State-level differences in malpractice payments reflect a complex interaction of:
- **Tort reform laws:** Damage caps, joint-and-several liability rules, statute of limitations
- **Medical practice patterns:** Specialty mix, procedure volume, patient demographics
- **Legal environment:** Plaintiff bar strength, venue selection (e.g., Cook County, IL), jury composition
- **Insurance market structure:** State insurance regulations, Patient Compensation Funds (e.g., Indiana)
- **Reporting patterns:** While federal law mandates all payments be reported, state-level factors affect claim filing rates

### Key Metric: Catastrophic Rate
The `catastrophic_share` column measures the percentage of payments exceeding $1M (in 2025 dollars) within each state. This is a critical indicator because catastrophic claims, though rare, dominate total financial exposure. A state with 5% of claims but 20% catastrophic rate presents disproportionate risk.
"""

# ── Cell 58: Finding - State Analysis ──
new_markdown[58] = """### Finding: Dramatic State-Level Variation Reflects Legal Environment Heterogeneity

**Top 5 States by Claim Volume:**

| State | Claims | Share | Mean (2025$) | Median (2025$) | Catastrophic Rate | Judgment Rate |
|-------|--------|-------|-------------|---------------|-------------------|---------------|
| New York | 68,916 | 13.0% | $487,942 | $247,500 | 15.7% | 2.1% |
| California | 57,592 | 10.9% | $219,437 | $57,200 | 5.0% | 2.4% |
| Pennsylvania | 41,071 | 7.8% | $429,583 | $333,700 | 7.9% | 3.6% |
| Florida | 40,553 | 7.7% | $343,010 | $213,750 | 6.4% | 1.1% |
| Texas | 30,885 | 5.8% | $283,387 | $147,250 | 4.7% | 0.8% |

**Critical Contrasts:**

- **New York vs. California:** Both are high-volume states, but New York's mean payment ($488K) is **2.2x California's** ($219K). California's MICRA damage cap ($250K on non-economic damages) directly suppresses payment amounts -- the $57K median is the lowest among the top 5. New York has no caps.

- **Illinois is the outlier:** Though only 20,119 claims (3.8% of total), Illinois has the highest mean payment of any large state at **$630,140** -- 30% higher than New York. Its catastrophic rate of 20.5% means 1 in 5 Illinois payments exceeds $1M. This reflects Illinois's plaintiff-friendly Cook County venue and absence of effective damage caps.

- **Indiana's judgment rate (14.0%)** is 5x the national average (2.7%). Indiana's unique Patient Compensation Fund (PCF) structure, which requires a medical review panel before litigation, may funnel more cases to formal verdict rather than pre-trial settlement.

- **Puerto Rico ($82K mean)** has the lowest mean payment among jurisdictions with substantial volume -- only 0.4% of its payments are catastrophic.

**The hierarchical table (STATE x PERIOD x PAYMENT_MODE)** shows that multi-payment cases are consistently rare across states (typically 3--5% of post-2004 records), but their financial impact varies dramatically. In Alaska, multi-payment cases average $1.07M vs. $723K for single payments. In Indiana, multi-payment cases average only $117K -- below the single-payment mean of $324K -- reflecting the PCF's structured payment approach.
"""

# ── Cell 59: Section 8 heading ──
new_markdown[59] = """## Section 8: Wisconsin and Peer-State Comparison

### Purpose
Provide a focused analysis of Wisconsin's malpractice payment landscape, benchmarked against a fixed set of **Upper Midwest peer states** that share similar demographics, healthcare systems, and geographic context.

### Peer State Selection

| State | Rationale for Inclusion |
|-------|----------------------|
| **WI** (Wisconsin) | Focal state |
| **MN** (Minnesota) | Border state, similar demographics, comparable healthcare market |
| **IA** (Iowa) | Border state, rural-dominant demographics similar to western Wisconsin |
| **IL** (Illinois) | Southern border, major referral center (Chicago), known high-severity environment |
| **MI** (Michigan) | Great Lakes peer, similar industrial/urban mix |
| **OH** (Ohio) | Midwest peer, comparable population and healthcare system size |
| **IN** (Indiana) | Midwest peer with unique Patient Compensation Fund structure (useful contrast) |

### What to Look For
- Is Wisconsin's payment severity typical for the Midwest, or an outlier?
- How does Wisconsin's catastrophic claim rate compare to peers?
- Is Wisconsin's mean-to-median ratio (a heavy-tail indicator) comparable to similar states?
- Are temporal trends (claim volume decline, severity escalation) consistent across the Midwest?
"""

# ── Cell 65: Finding - Wisconsin ──
new_markdown[65] = """### Finding: Wisconsin Shows High Severity Volatility Compared to Midwest Peers

**Wisconsin Across Decades (CPI-adjusted to 2025$):**

| Period | Claims | Mean Payment | Median Payment | Mean/Median Ratio | Catastrophic Rate | Judgment Rate |
|--------|--------|-------------|---------------|-------------------|-------------------|---------------|
| 1990--1999 | 1,642 | $455,718 | $99,750 | 4.57x | 8% | 3% |
| 2000--2009 | 1,236 | $516,481 | $137,963 | 3.74x | 12% | 7% |
| 2010--2019 | 635 | $437,207 | $87,725 | 4.98x | 8% | 4% |
| 2020--2029 | 334 | $609,185 | $180,400 | 3.38x | 9% | 2% |

**Key Observations:**

1. **Wisconsin's mean-to-median ratio is extreme:** In the 2010s, the mean ($437K) was **5.0x the median ($88K)** -- the highest ratio among all Midwest peers. This indicates Wisconsin's payment distribution has a particularly heavy tail: a few catastrophic cases dramatically inflate the average while typical cases remain modest.

2. **Claim volume is declining sharply:** From 1,642 in the 1990s to 334 in the 2020s (an 80% decline). This accelerating decline is steeper than most peers and may connect to findings in the actuarial literature about Wisconsin's cap regime shifts affecting claim frequency.

3. **Wisconsin's mean payment ($456--609K) is consistently higher than Michigan ($172--274K) and Indiana ($229--325K)**, but comparable to or below Illinois ($481--753K). This positions Wisconsin as a **mid-to-high severity state** within the Midwest.

**Peer Comparison Summary:**

| State | Overall Mean | Catastrophic Rate | Unique Position |
|-------|-------------|-------------------|-----------------|
| IL | $630K+ | 13--28% | Highest severity, Cook County effect |
| WI | $437--609K | 8--12% | High severity volatility, heavy tail |
| OH | $359--442K | 8--12% | Similar profile to WI, larger volume |
| MN | $270--728K | 7--17% | Rising severity trend, small volume |
| IN | $229--325K | 3--11% | PCF structure caps effective severity |
| IA | $251--600K | 6--16% | Small state, rising recent severity |
| MI | $172--274K | 1--4% | Consistently lowest severity in group |

**Michigan stands out as the low-severity anchor** -- its mean payment never exceeds $274K and catastrophic share never exceeds 4%. Michigan's damage cap regime and medical malpractice arbitration rules appear to effectively limit payouts. **Illinois is the high-severity extreme**, with catastrophic rates 3--7x Michigan's.

**Wisconsin's judgment rate peaked at 7% in the 2000s** -- the highest among Midwest peers for that decade -- suggesting more cases went to trial during a period that may coincide with changes to Wisconsin's tort environment. The rate has since fallen to 2% in the 2020s, converging with the national trend toward settlement dominance.
"""

# ── Cell 66: Section 9 heading ──
new_markdown[66] = """## Section 9: Practitioner Multi-State Presence

### Purpose
Examine how many practitioners appear in multiple states' malpractice records, whether multi-state practitioners carry different risk profiles, and which state pairs share the most practitioners.

### Key Variables

| Variable | Definition |
|----------|-----------|
| `unique_states` | Number of distinct STATE values associated with a practitioner's records |
| `multi_state_practitioner` | Boolean: True if `unique_states` >= 2 |
| `years_spanned` | Max ORIGYEAR minus min ORIGYEAR for the practitioner's records |
| `record_count` | Total number of malpractice payment records for the practitioner |

### Interpretation Caveats
A practitioner appearing in multiple states can reflect:
- **Multi-state licensure:** Practicing in border metro areas (e.g., Philadelphia/NJ, Kansas City)
- **Relocation:** Moving between states during a career
- **Reporting variation:** Different state branches of the same health system
- This analysis is purely descriptive -- it does not claim causal relationships between mobility and malpractice risk
"""

# ── Cell 71: Finding - Multi-State ──
new_markdown[71] = """### Finding: Multi-State Practitioners Are a Small but High-Exposure Subgroup

**Mobility Statistics:**

| Metric | Value |
|--------|-------|
| Total unique practitioners | 322,037 |
| Multi-state practitioners | 11,106 (3.45%) |
| Mean payment -- single-state | $368,766 |
| Mean payment -- multi-state | $450,318 |

**Multi-state practitioners have 22% higher mean payments** ($450K vs. $369K). They also show dramatically higher engagement with the NPDB system: an average of **3.54 records per practitioner** vs. 1.58 for single-state, with **mean total payments of $1.53M** vs. $591K and an average span of **11.4 years** vs. 2.4 years.

**Top State Pairs by Shared Practitioners:**

| Pair | Shared Practitioners | Geographic Logic |
|------|---------------------|-----------------|
| NJ--PA | 493 | Philadelphia metro straddles border |
| NJ--NY | 458 | NYC metro extends into NJ |
| KS--MO | 276 | Kansas City metro straddles border |
| NY--PA | 262 | Northeast corridor proximity |
| FL--NY | 207 | Retirement migration / snowbird practice |

**Interpretation:** The state pairs are overwhelmingly **border-metro driven** -- practitioners in metropolitan areas that span state lines naturally accumulate records in multiple states. The FL--NY and CA--NY pairs likely reflect physician relocation rather than concurrent practice.

**The 3.45% multi-state rate is low enough** that state-level analyses are not materially contaminated by cross-state practitioner overlap. However, the higher payment amounts for multi-state practitioners raise a modeling question: **does practicing across jurisdictions increase malpractice risk, or do higher-risk practitioners tend to relocate?** This is a question that cannot be answered by descriptive analysis alone -- it requires a regression framework controlling for specialty, experience, and time.
"""

# ── Cell 72: Section 10 heading ──
new_markdown[72] = """## Section 10: Settlement vs. Judgment and Policy Context

### Purpose
Analyze the resolution type of malpractice claims (settlement vs. court judgment), track trends over time, and provide context on the federal disclosure framework.

### Key Variable: `RESOLUTION_BINARY`
Derived from the NPDB's `PAYTYPE` field:
- **Judgment:** PAYTYPE codes indicating a court verdict or arbitration award
- **Settlement:** All other payment types (including consent judgments, which are functionally negotiated settlements)

This follows NPDB coding guidance where the distinction is between contested trial outcomes and negotiated resolutions.

### Federal Reporting Framework: 42 U.S.C. Section 11131
The Health Care Quality Improvement Act of 1986 established the NPDB and its mandatory reporting requirements:
- **Any malpractice payment** made on behalf of a named practitioner must be reported within **30 days**, regardless of amount or resolution type
- Settlement amounts are not publicly disclosed to the general public through the NPDB (the public-use file provides range midpoints, not exact amounts)
- The reporting obligation is **mandatory and carries no state-level exemption**
- Individual states may have additional confidentiality protections for settlement proceedings (e.g., Wisconsin Statute 655.017), but these affect whether parties can publicly discuss the settlement -- **not whether it must be reported to the NPDB**

### What This Means for Our Data
The NPDB captures **all paid claims** regardless of state confidentiality laws. Variation in judgment rates across states therefore reflects differences in tort reform structure, litigation culture, and insurance market practices -- not differences in reporting compliance.
"""

# ── Cell 77: Finding - Settlement/Judgment ──
new_markdown[77] = """### Finding: Settlements Dominate at 97.3% -- But Judgments Pay 2--3x More

**Resolution Trend by Decade:**

| Period | Judgments | Judgment Share | Settlement Share |
|--------|-----------|---------------|-----------------|
| 1990--1999 | 5,725 | 3.35% | 96.65% |
| 2000--2009 | 5,305 | 3.11% | 96.89% |
| 2010--2019 | 2,734 | 2.22% | 97.78% |
| 2020--2029 | 714 | 1.10% | 98.90% |

The judgment rate has **declined by two-thirds** over three decades (3.35% to 1.10%). This reflects the medical malpractice system's increasing preference for pre-trial resolution, driven by rising litigation costs, unpredictable jury awards, and insurer preference for controlled settlements.

**Judgment Premium in Midwest Peer States:**

| State | Judgment Mean (2025$) | Settlement Mean (2025$) | Judgment Premium |
|-------|-----------------------|------------------------|-----------------|
| Wisconsin | $1,031,904 | $459,781 | **2.24x** |
| Ohio | $1,232,521 | $369,601 | **3.34x** |
| Iowa | $1,125,607 | $333,905 | **3.37x** |
| Illinois | $1,065,046 | $609,892 | **1.75x** |
| Indiana | $593,869 | $230,504 | **2.58x** |
| Minnesota | $637,610 | $440,804 | **1.45x** |
| Michigan | $419,222 | $196,645 | **2.13x** |

**Judgments consistently pay 1.5--3.4x more than settlements.** This makes economic sense: cases that go to verdict tend to involve either (a) severe injuries where plaintiffs reject settlement offers hoping for larger awards, or (b) defendant confidence that results in an unexpected loss. The judgment premium is largest in Ohio (3.34x) and Iowa (3.37x), and smallest in Minnesota (1.45x).

**Indiana's anomalous 14.0% judgment rate** (vs. 2.7% national) merits further investigation. Indiana's Medical Malpractice Act requires a medical review panel opinion before filing suit, and the state's Patient Compensation Fund (PCF) structure may systematically route more cases toward formal verdict.

**Settlement Disclosure Context:**
Under federal law (42 U.S.C. Section 11131), any malpractice payment made on behalf of a named practitioner must be reported to the NPDB within 30 days, regardless of amount or resolution type. The public-use file provides payment range midpoints rather than exact amounts, but the reporting obligation itself is mandatory and universal. States may have additional confidentiality protections for settlement proceedings, but these affect public discussion of settlements -- not whether they appear in the NPDB.
"""

# ── Cell 78: Section 11 heading ──
new_markdown[78] = """## Section 11: Loss Distribution Fitting and Severity Modeling

### Purpose
This section addresses three modeling questions that cannot be answered with descriptive tables or dashboards:

1. **Which statistical distribution best characterizes malpractice payment severity?** -- Critical for actuarial reserving, reinsurance pricing, and risk quantification
2. **What practitioner, patient, and case characteristics predict payment severity?** -- A Gamma GLM with log link provides multiplicative effect estimates
3. **Can we predict which claims will exceed $1M (catastrophic threshold)?** -- A logistic regression classifier for early identification of high-exposure cases

### Distribution Fitting Methodology
- **Sample:** Single-payment records only (N=267,557) to avoid mixing single and multiple payment distributions
- **Distributions tested:** Exponential, Gamma, Lognormal, Weibull, Pareto (Lomax)
- **Fitting method:** Maximum Likelihood Estimation (MLE)
- **Ranking criteria:** Akaike Information Criterion (AIC) and Bayesian Information Criterion (BIC) -- lower is better
- **Goodness of fit:** Kolmogorov-Smirnov (KS) test statistic

### Important Caveat: Range-Midpoint Encoding
The NPDB public-use file reports payment amounts as **range midpoints**, not exact values. For example, a payment coded as "$100,000" may represent any value in a range around that midpoint. This introduces measurement error that affects distribution fitting -- particularly in the lower tail where ranges are narrower. The fitted parameters should be interpreted as approximations, not exact distributional characterizations.
"""

# ── Cell 85: Finding - Distribution/Modeling ──
new_markdown[85] = """### Finding: Weibull Distribution Best Fits Single-Payment Losses; Catastrophic Claims Predictable at AUC 0.77

**Loss Distribution Fitting (Single-Payment Cases, N=267,557, CPI-adjusted 2025$):**

| Distribution | AIC | BIC | Fit Quality |
|-------------|-----|-----|-------------|
| **Weibull** | **7,385,364** | **7,385,396** | **Best fit** |
| Lomax (Pareto Type II) | 7,386,351 | 7,386,383 | Close second |
| Lognormal | 7,395,307 | 7,395,338 | Moderate |
| Exponential | 7,434,699 | 7,434,720 | Poor (too restrictive) |
| Gamma | Failed | -- | Numerical convergence issues |

The **Weibull distribution** (shape parameter ~0.75 < 1, indicating a decreasing hazard rate) provides the best fit. This means the density function decreases monotonically -- there are many small payments and progressively fewer large ones, but the tail is heavier than exponential. The **Lomax (Pareto Type II)** is a close second, consistent with the actuarial literature's finding that malpractice losses follow power-law-like tails.

**Exceedance Probabilities (Empirical):**

| Threshold | Claims Exceeding | Share |
|-----------|-----------------|-------|
| $100,000 | 175,662 | 65.7% |
| $250,000 | 115,917 | 43.3% |
| $500,000 | 65,766 | 24.6% |
| $1,000,000 | 26,384 | 9.9% |
| $2,000,000 | 4,945 | 1.9% |
| $5,000,000 | 850 | 0.3% |

Nearly **two-thirds of single-payment claims exceed $100K** (in 2025 dollars), and roughly **1 in 10 exceeds $1M**. The tail thins rapidly above $2M, with only 0.3% exceeding $5M -- but these extreme cases represent enormous aggregate financial exposure.

**Gamma GLM Severity Model:**
The Gamma GLM with log link (using OUTCOME severity, resolution type, period, and state as predictors) successfully converged. Injury severity (OUTCOME) is the dominant predictor of payment amount, with state fixed effects capturing the legal-environment heterogeneity documented in Section 7. The Gamma GLM is the standard actuarial model for claim severity because it naturally handles the right-skewed, strictly positive distribution of payment amounts.

**Catastrophic Claim Classifier (Logistic Regression):**

| Metric | Value |
|--------|-------|
| **ROC-AUC** | **0.765** |
| Average Precision | 0.226 |
| Test set size | 69,618 |

An AUC of 0.77 means the model correctly ranks a random catastrophic case above a random non-catastrophic case **77% of the time**. For a first-pass model with only 6 features (OUTCOME severity, practitioner age, lag years, specialty, resolution type, allegation nature), this is a strong baseline. The relatively low average precision (0.23) reflects the class imbalance (only ~10% catastrophic rate) -- the model identifies the right direction but generates false positives. Feature engineering (adding specialty codes, patient age, and interaction terms) and ensemble methods could improve precision.

**Key Modeling Insight:** These are the types of questions that cannot be answered with a dashboard: (1) Which distribution family best captures the loss tail for reserving purposes? (2) Can claim-level features predict catastrophic outcomes before full litigation costs are known? (3) What is the marginal effect of state legal environment on payment severity after controlling for injury type?
"""

# ── Cell 86: Modeling Checkpoint ──
new_markdown[86] = """### Modeling Checkpoint

The severity and catastrophic models presented above are **first-pass research models**, not final production estimators. They establish that meaningful prediction is possible and identify the most important features. Before these models could inform operational decisions, they would need:

- **Expanded feature set:** Specialty codes, patient demographics, procedure type, facility characteristics
- **Interaction terms:** State x time period, severity x resolution type
- **Cross-validation:** K-fold validation to assess stability, not just a single train/test split
- **Calibration analysis:** Ensuring predicted probabilities match observed frequencies
- **Comparison to ensemble methods:** Random forest or gradient boosting may capture non-linear relationships
"""

# ── Cell 87: Section 12 heading ──
new_markdown[87] = """## Section 12: Time-to-Payment Analysis

### Purpose
Measure the lag between when a malpractice incident occurred (`MALYEAR1`) and when the payment was reported to the NPDB (`ORIGYEAR`). This "long tail" characteristic is fundamental to medical malpractice liability and has direct implications for claims reserving, premium pricing, and the interpretation of temporal trends.

### Key Variable: `LAG_YEARS`
Computed as `ORIGYEAR - MALYEAR1`. Represents the number of years between the malpractice incident and the payment report. Only records with valid, positive lag values are included.

### Important Distinction
This is a **paid-claim lag analysis**, not a full censored-claims survival dataset. We observe only claims that ultimately resulted in payment. Claims that were filed but dismissed, or incidents that never became claims, are not in the data. This means our lag estimates reflect the resolution time for *paid* claims, which may systematically differ from the lag for all claims (paid claims may take longer because they involve more complex cases that are worth pursuing).
"""

# ── Cell 92: Finding - Time to Payment ──
new_markdown[92] = """### Finding: Mean Lag of 4.75 Years -- Judgments Take 34% Longer Than Settlements

**Overall Lag Statistics:**

| Metric | Value |
|--------|-------|
| Records analyzed | 529,086 |
| Mean lag (incident to payment) | 4.75 years |
| Median lag | 4.0 years |
| 90th percentile | 8.0 years |
| 95th percentile | 10.0 years |

**By Resolution Type:**

| Resolution | Count | Mean Lag | Median Lag |
|-----------|-------|----------|------------|
| Judgment | 14,447 | **6.33 years** | 6.0 years |
| Settlement | 514,639 | **4.70 years** | 4.0 years |

Judgments take **1.63 years longer on average** (6.33 vs. 4.70 years). This is expected: cases that go to trial require additional preparation, court scheduling, and potential appeals. The 2-year median gap (6 vs. 4 years) is consistent across decades and states.

**Practical Implications:**

- **Reserving:** Insurers must hold reserves for an average of nearly 5 years per claim, with 10% of claims taking 8+ years to resolve. This extended "long tail" is a defining characteristic of medical malpractice liability and distinguishes it from shorter-tail lines like auto insurance.

- **Discounting:** At a 4% discount rate, a $500K payment made 5 years after the incident has a present value of ~$411K at incident time -- an 18% reduction. This has material implications for comparing nominal vs. economic-cost analyses and for premium adequacy calculations.

- **Temporal trend interaction:** The lag means that changes in the legal environment (e.g., tort reform) may not be visible in payment data for several years after enactment. A damage cap passed in 2005 might only begin affecting reported payments in 2008--2010.

**Connection to Section 6 (Time-Grouped Analysis):** The report-year vs. incident-year cross-tab showed that older incidents resolving later tend to have higher mean payments ($422K for 1970s incidents resolving in the 1990s vs. $299K for contemporaneous 1990s incidents). Combined with this lag analysis, the pattern suggests that cases with longer resolution times are systematically higher-severity -- a selection effect where more complex, higher-value cases take longer to litigate.
"""

# ── Cell 93: Replace team workflow (remove names) ──
new_markdown[93] = """## Recommended Workflow

### Data Refresh Protocol
- Rerun **Sections 1--3** first after any data refresh or transformation change
- Rerun **Sections 4--10** for updated descriptive outputs
- Rerun **Sections 11--12** only after validating the data slice to be modeled

### Review Priorities
- **Linkage work:** Review Section 5 together with `docs/linkage_methodology.md` to confirm reconstruction accuracy on new data
- **Policy interpretation:** Review Section 10 together with `docs/policy_notes_settlement_disclosure.md` for context on settlement confidentiality
- **Modeling iterations:** Begin only after the state and payment-mode tables are accepted and stable
"""

# ── Cell 94: Execution Notes ──
new_markdown[94] = """## Execution Notes

### Recommended execution order:

1. Run Sections 1--3 once per data refresh (loads data, applies transformations, engineers features)
2. Rerun Sections 4--10 for descriptive outputs (can be run independently after Section 3)
3. Rerun Sections 11--12 only after validating the data slice you want to model

### Architecture
The notebook depends on reusable modules under `npdb_analysis/`. Logic changes should be made in those module files, not inline in notebook cells. After modifying any module file, restart the kernel before re-running notebook cells to pick up changes.

### Reproducibility
All monetary values are CPI-adjusted to 2025 dollars using the factor dictionary in `npdb_analysis/config.py`. To update for a different base year or newer CPI data, modify the `cpi_factors` dictionary in config and rerun from Section 3.
"""

# ── Apply all replacements ──────────────────────────────────
for cell_idx, content in new_markdown.items():
    nb["cells"][cell_idx]["source"] = [content]
    nb["cells"][cell_idx]["cell_type"] = "markdown"

with open("advanced_NPDB.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Updated {len(new_markdown)} markdown cells.")
print("Cells modified:", sorted(new_markdown.keys()))
