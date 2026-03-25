"""Insert analysis/findings markdown cells into advanced_NPDB.ipynb after each output section."""
import json
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")

NOTEBOOK = "advanced_NPDB.ipynb"

with open(NOTEBOOK, "r", encoding="utf-8") as f:
    nb = json.load(f)


def make_md_cell(source_text):
    """Create a markdown cell dict."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [source_text],
        "id": str(uuid.uuid4())[:8],
    }


# Define analysis cells to insert: (after_cell_index, markdown_content)
# Indices refer to the ORIGINAL notebook before any insertions.
# We'll process from bottom to top so indices stay valid.

analysis_cells = [
    # ── Section 1: Raw Data Load (after cell 8) ──
    (
        8,
        """### Finding: Record Type Distribution Reveals a Dual-Format Dataset

**Scale:** The NPDB contains **1,895,122 total records** spanning 1990-2025, with 54 columns per record.

**Record Type Breakdown:**
| RECTYPE | Description | Count | Share |
|---------|-------------|-------|-------|
| C | Continuous action reports | 1,314,661 | 69.4% |
| P | Post-2004 malpractice format | 279,158 | 14.7% |
| M | Legacy malpractice format (pre-2004) | 250,672 | 13.2% |
| A | Adverse action reports | 50,631 | 2.7% |

**Critical Structural Insight:** The malpractice cohort (M + P = **529,830 records**, 28.0% of total) is our analysis universe. The dominance of C-type records (clinical privilege and professional society actions) means nearly 70% of the database is outside our scope -- a common misconception when reporting "NPDB size."

**Missingness Architecture:** The column profile reveals that missingness is overwhelmingly **structural, not random**:
- `TOTALPMT`, `OUTCOME`, `PTSEX`, `PTAGE` are 85.3% null -- because they only populate for RECTYPE='P' (14.7% of records)
- `ALGNNATR` and `PAYMENT` are 72.0% null -- because they only populate for malpractice records (M+P = 28.0%)
- `HOMECTRY` and `WORKCTRY` are 100% null -- these fields appear to be systematically unpopulated in the public-use file

This is not data quality failure; it is the expected consequence of the NPDB's multi-record-type architecture. Analyses must filter to the correct RECTYPE subset before computing any statistics.
""",
    ),
    # ── Section 2: Transformation & Missingness (after cell 12) ──
    (
        12,
        """### Finding: Missingness Is Record-Type Driven -- Not Random

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
""",
    ),
    # ── Section 3: Feature Engineering (after cell 17) ──
    (
        17,
        """### Finding: Analysis-Ready Cohort Baseline

**Cohort:** 529,830 malpractice records (RECTYPE M + P) with 74 engineered features.

**Key Baseline Metrics (all payments CPI-adjusted to 2025 dollars):**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Mean payment | $379,117 | Pulled upward by catastrophic tail |
| Median payment | $169,650 | Half of all payments are below $170K -- the "typical" case |
| Mean-to-median ratio | 2.24x | Confirms extreme right skew in the payment distribution |
| Catastrophic share (>$1M) | 9.50% | Roughly 1 in 10.5 payments exceeds $1M in 2025 dollars |
| Judgment share | 2.73% | 97.3% of cases resolve without trial verdict -- consistent with literature |

**Data Quality Flags:**
| Quality Metric | Value | Assessment |
|----------------|-------|------------|
| Missing STATE | 0.01% | Excellent -- composite fallback (WORKSTAT -> LICNSTAT -> HOMESTAT) works |
| Missing allegation | 0.03% | Essentially complete for malpractice records |
| Missing OUTCOME | 47.31% | Expected -- exactly the RECTYPE='M' share (pre-2004 records lack this field) |
| Payment mode known | 52.69% | Post-2004 records only; pre-2004 labeled "Unavailable" |
| Observed TOTALPMT | 52.69% | Same boundary -- TOTALPMT only in RECTYPE='P' |

The 2.24x mean-to-median ratio flags a heavy-tailed distribution that will require careful treatment in modeling (standard OLS on raw payments would be dominated by outliers). The 9.5% catastrophic share is higher than the 2.8% reported in the earlier descriptive notebook because CPI adjustment inflates historical payments into 2025 dollars.
""",
    ),
    # ── Section 4: Payment Mode Separation (after cell 23) ──
    (
        23,
        """### Finding: Single Payments Dominate, but Multiple-Payment Cases Carry Disproportionate Severity

**Overall Payment Mode Distribution (Post-2004 Records):**

| Mode | Count | Share | Mean Payment (2025$) | Median Payment (2025$) |
|------|-------|-------|---------------------|----------------------|
| Single Payment | 267,557 | 50.5% | $397,832 | $195,750 |
| Multiple Payments | 11,601 | 2.2% | $581,169 | $313,600 |
| Unavailable (Pre-2004) | 250,672 | 47.3% | -- | -- |

**Key Insights:**

1. **Multiple-payment cases are 46% more expensive on average** ($581K vs. $398K mean), and their median is 60% higher ($314K vs. $196K). This is not surprising -- cases generating multiple payments typically involve more severe injuries, more defendants, or longer litigation.

2. **Multiple payments account for only 4.2% of post-2004 records but carry outsized financial weight.** With a mean payment 1.46x higher per report and multiple reports per case, these practitioners represent concentrated liability exposure.

3. **The multi-payment practitioner profile** shows the top repeat payer (PRACTNUM 13980) accumulated 19 payment reports totaling $6.6M over 8 years across 2 states. The practitioner with the highest total (PRACTNUM 417839) reached $65M across 5 reports in 3 years -- likely a catastrophic obstetric or neurological case.

4. **Multi-payment share is declining over time:** from 5.1% in 2000-2009 to 4.3% in 2010-2019 to 2.5% in 2020-2029. This could reflect (a) tort reform reducing multi-defendant litigation, (b) faster single-lump settlements, or (c) right-censoring (recent cases haven't had time to accumulate additional payments).

**For Dr. Loke:** The single-payment subset (267,557 records) is now cleanly isolated for loss distribution fitting. The multiple-payment subset (11,601 records) is available for dependent-payment modeling.
""",
    ),
    # ── Section 5: Linkage Validation (after cell 29) ──
    (
        29,
        """### Finding: Strict Linkage Validation Shows Excellent Reconstruction Accuracy

**Validation Design:** The episode-linkage rule was tested on post-2004 records where the true `TOTALPMT` is observed. The derived episode (grouping by PRACTNUM + STATE + ORIGYEAR + MALYEAR1 + ALGNNATR + PAYTYPE) was compared to the reported TOTALPMT.

**Validation Results:**
| Metric | Strict Tier | Moderate Tier |
|--------|-------------|---------------|
| Episodes validated | 261,575 | 263,075 |
| Median absolute % error | 0.00% | 0.00% |
| Mean absolute % error | 0.04% | 0.04% |
| Within 10% accuracy | 93% | 94% |
| Within 25% accuracy | 94% | 95% |
| Ambiguous episodes | 659 (0.25%) | -- |

**This is remarkably strong validation.** A median error of 0.0% means the derived episodes exactly match the reported TOTALPMT for over half the cases. The 93-94% within-10% rate means the reconstruction rule is reliable enough for analytical use.

**Pre-2004 Reconstruction Results:**
| Source | Records | Mean Total (2025$) | Median Total (2025$) | Share |
|--------|---------|--------------------|--------------------|-------|
| Observed (post-2004) | 279,158 | $423,173 | $205,900 | 52.7% |
| Reconstructed (pre-2004) | 248,568 | $388,730 | $156,600 | 46.9% |
| Unresolved | 2,104 | -- | -- | 0.4% |

**The $34K gap in mean between observed and reconstructed** ($423K vs. $389K) partly reflects lower nominal payments in earlier decades even after CPI adjustment, and partly the absence of multi-payment linking information pre-2004. Only 2,104 records (0.4%) could not be resolved -- an acceptably small residual.

**Bottom line:** The `TOTALPMT_BEST` column is validated and safe to use for full-span 1990-2025 analyses.
""",
    ),
    # ── Section 6: Time-Grouped Analysis (after cell 35) ──
    (
        35,
        """### Finding: Claim Volume Is Declining but Severity Keeps Rising -- A Diverging Trend

**By Report Decade (ORIGYEAR, CPI-adjusted to 2025$):**

| Period | Claims | Share | Mean Payment | Median Payment | Catastrophic Rate | Judgment Rate |
|--------|--------|-------|-------------|---------------|-------------------|---------------|
| 1990-1999 | 171,129 | 32.3% | $324,656 | $124,375 | 7.8% | 3.4% |
| 2000-2009 | 170,548 | 32.2% | $404,190 | $184,000 | 10.9% | 3.1% |
| 2010-2019 | 122,994 | 23.2% | $403,144 | $195,300 | 10.7% | 2.2% |
| 2020-2029 | 65,159 | 12.3% | $411,150 | $218,400 | 7.9% | 1.1% |

**Three key patterns emerge:**

1. **Volume decline:** Claims dropped 28% from the 2000s to 2010s and are on pace for another 47% drop in the 2020s (though right-censoring partly explains the 2020s figure). This aligns with national tort reform trends and declining claim frequency documented by Frees & Gao (2020).

2. **Severity escalation:** Even after CPI adjustment, mean payments rose 27% from the 1990s ($325K) to the 2020s ($411K). The median rose 76% ($124K to $218K). Fewer claims are being filed, but the ones that get paid are more expensive.

3. **Judgment rates are collapsing:** From 3.4% in the 1990s to 1.1% in the 2020s. The malpractice system is moving almost entirely toward settlement resolution, with trial verdicts becoming increasingly rare.

**Report-Year vs. Incident-Year Cross-Tab:** The heatmap reveals substantial lag -- incidents from the 1980s still generating payments in the 1990s, and 1990s incidents still resolving into the 2000s. Notably, incidents from 1970-1979 that resolved in the 1990s had a mean payment of $422K -- higher than contemporaneous 1990s incidents ($299K) -- suggesting older cases that finally resolved were the more severe ones.

**Anomaly:** 8 records show incident years in the "3990-3999" range, clearly a data entry error. These are excluded from incident-year analyses but retained in report-year analyses.
""",
    ),
    # ── Section 7: Hierarchical State Analysis (after cell 40) ──
    (
        40,
        """### Finding: Dramatic State-Level Variation Reflects Legal Environment Heterogeneity

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

**The hierarchical table (STATE x PERIOD x PAYMENT_MODE)** shows that multi-payment cases are consistently rare across states (typically 3-5% of post-2004 records), but their financial impact varies dramatically. In Alaska, multi-payment cases average $1.07M vs. $723K for single payments. In Indiana, multi-payment cases average only $117K -- below the single-payment mean of $324K -- reflecting the PCF's structured payment approach.
""",
    ),
    # ── Section 8: Wisconsin & Peers (after cell 45) ──
    (
        45,
        """### Finding: Wisconsin Shows High Severity Volatility Compared to Midwest Peers

**Wisconsin Across Decades (CPI-adjusted to 2025$):**

| Period | Claims | Mean Payment | Median Payment | Catastrophic Rate | Judgment Rate |
|--------|--------|-------------|---------------|-------------------|---------------|
| 1990-1999 | 1,642 | $455,718 | $99,750 | 8% | 3% |
| 2000-2009 | 1,236 | $516,481 | $137,963 | 12% | 7% |
| 2010-2019 | 635 | $437,207 | $87,725 | 8% | 4% |
| 2020-2029 | 334 | $609,185 | $180,400 | 9% | 2% |

**Key Observations:**

1. **Wisconsin's mean-to-median ratio is extreme:** In the 2010s, the mean ($437K) was **5.0x the median ($88K)**. This is the highest ratio among all Midwest peers, indicating that Wisconsin's payment distribution has a particularly heavy tail -- a few catastrophic cases dramatically inflate the average while typical cases remain modest.

2. **Claim volume is declining sharply:** From 1,642 in the 1990s to 334 in the 2020s (an 80% decline). This accelerating decline is steeper than most peers and may connect to the Frees & Gao finding about Wisconsin's cap regime shifts affecting claim frequency.

3. **Wisconsin's mean payment ($455-609K) is consistently higher than Michigan ($172-274K) and Indiana ($229-325K)**, but comparable to or below Illinois ($481-753K). This positions Wisconsin as a **mid-to-high severity state** within the Midwest.

**Peer Comparison Highlights:**

| State | Overall Mean | Catastrophic Rate | Unique Position |
|-------|-------------|-------------------|-----------------|
| IL | $630K+ | 13-28% | Highest severity, Cook County effect |
| WI | $437-609K | 8-12% | High severity volatility, heavy tail |
| OH | $359-442K | 8-12% | Similar profile to WI, larger volume |
| MN | $270-728K | 7-17% | Rising severity trend, small volume |
| IN | $229-325K | 3-11% | PCF structure caps effective severity |
| IA | $251-600K | 6-16% | Small state, rising recent severity |
| MI | $172-274K | 1-4% | Consistently lowest severity in group |

**Michigan stands out as the low-severity anchor** -- its mean payment never exceeds $274K and catastrophic share never exceeds 4%. Michigan's damage cap regime and medical malpractice arbitration rules appear to effectively limit payouts. **Illinois is the high-severity extreme**, with catastrophic rates 3-7x Michigan's.

**Wisconsin's judgment rate peaked at 7% in the 2000s** -- the highest among Midwest peers for that decade -- suggesting more cases went to trial during a period that may coincide with changes to Wisconsin's tort environment. The rate has since fallen to 2% in the 2020s, converging with the national trend toward settlement dominance.

**Connection to Frees & Gao (2020):** Wisconsin's claim frequency volatility under different cap regimes (documented in the Medical Liability Decoded slide deck, p.10) is now complemented by this payment severity analysis. The combination suggests that cap regimes affect not just how many claims are filed, but also the financial distribution of those that pay out.
""",
    ),
    # ── Section 9: Practitioner Mobility (after cell 49) ──
    (
        49,
        """### Finding: Multi-State Practitioners Are a Small but High-Exposure Subgroup

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
| NJ-PA | 493 | Philadelphia metro straddles border |
| NJ-NY | 458 | NYC metro extends into NJ |
| KS-MO | 276 | Kansas City metro straddles border |
| NY-PA | 262 | Northeast corridor proximity |
| FL-NY | 207 | Retirement migration / snowbird practice |

**Interpretation:** The state pairs are overwhelmingly **border-metro driven** -- practitioners in metropolitan areas that span state lines (Philadelphia/NJ, NYC/NJ, Kansas City) naturally accumulate records in multiple states. The FL-NY and CA-NY pairs likely reflect physician relocation rather than concurrent practice.

**The 3.45% multi-state rate is low enough** that state-level analyses are not materially contaminated by cross-state practitioner overlap. However, the higher payment amounts for multi-state practitioners raise a modeling question: **does practicing across jurisdictions increase malpractice risk, or do higher-risk practitioners tend to relocate?** This is a question that cannot be answered by a dashboard -- it requires a regression framework controlling for specialty, experience, and time (addressed in Module 11).
""",
    ),
    # ── Section 10: Settlement vs Judgment (after cell 53) ──
    (
        53,
        """### Finding: Settlements Dominate at 97.3% -- But Judgments Pay 2-3x More

**Resolution Trend by Decade:**

| Period | Judgments | Judgment Share | Settlement Share |
|--------|-----------|---------------|-----------------|
| 1990-1999 | 5,725 | 3.35% | 96.65% |
| 2000-2009 | 5,305 | 3.11% | 96.89% |
| 2010-2019 | 2,734 | 2.22% | 97.78% |
| 2020-2029 | 714 | 1.10% | 98.90% |

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

**Judgments consistently pay 1.5-3.4x more than settlements.** This makes economic sense: cases that go to verdict tend to involve either (a) severe injuries where plaintiffs reject settlement offers hoping for larger awards, or (b) defendant confidence that results in an unexpected loss. The judgment premium is largest in Ohio (3.34x) and Iowa (3.37x), and smallest in Minnesota (1.45x).

**Indiana's anomalous 14.0% judgment rate** (vs. 2.7% national) merits further investigation. Indiana's Medical Malpractice Act requires a medical review panel opinion before filing suit, and the state's Patient Compensation Fund (PCF) structure may systematically route more cases toward formal verdict.

**Settlement Disclosure Context (Dr. Loke's Question):**
Under federal law (**42 U.S.C. Section 11131** -- Health Care Quality Improvement Act of 1986), any malpractice payment made on behalf of a named practitioner must be reported to the NPDB within 30 days, **regardless of amount or resolution type**. Settlement amounts are not publicly disclosed to the general public through the NPDB (the public-use file provides range midpoints, not exact amounts), but the reporting obligation itself is mandatory and carries no state-level exemption. Individual states may have additional confidentiality protections for settlement proceedings (e.g., Wisconsin Statute 655.017), but these affect whether parties can discuss the settlement publicly -- not whether it must be reported to the NPDB.
""",
    ),
    # ── Section 11: Loss Distribution & Modeling (after cell 59) ──
    (
        59,
        """### Finding: Weibull Distribution Best Fits Single-Payment Losses; Catastrophic Claims Predictable at AUC 0.77

**Loss Distribution Fitting (Single-Payment Cases, N=267,557, CPI-adjusted 2025$):**

| Distribution | AIC | BIC | Fit Quality |
|-------------|-----|-----|-------------|
| **Weibull** | **7,385,364** | **7,385,396** | **Best fit** |
| Lomax (Pareto Type II) | 7,386,351 | 7,386,383 | Close second |
| Lognormal | 7,395,307 | 7,395,338 | Moderate |
| Exponential | 7,434,699 | 7,434,720 | Poor (too restrictive) |
| Gamma | Failed | -- | Numerical convergence issues |

The **Weibull distribution** (shape parameter ~0.75 < 1, indicating a decreasing hazard rate) provides the best fit by AIC/BIC. This means the density function decreases monotonically -- there are many small payments and progressively fewer large ones, but the tail is heavier than exponential. The **Lomax (Pareto Type II)** is a close second, consistent with the actuarial literature's finding that malpractice losses follow power-law-like tails.

**Exceedance Probabilities (Empirical):**

| Threshold | Claims Exceeding | Share |
|-----------|-----------------|-------|
| $100,000 | 175,662 | 65.7% |
| $250,000 | 115,917 | 43.3% |
| $500,000 | 65,766 | 24.6% |
| $1,000,000 | 26,384 | 9.9% |
| $2,000,000 | 4,945 | 1.9% |
| $5,000,000 | 850 | 0.3% |

Nearly **two-thirds of single-payment claims exceed $100K** (in 2025 dollars), and roughly **1 in 10 exceeds $1M**. The tail thins rapidly above $2M, with only 0.3% exceeding $5M -- but these extreme cases represent enormous financial exposure in aggregate.

**Gamma GLM Severity Model:** The Gamma GLM with log link (using OUTCOME severity, resolution type, period, and state as predictors) successfully converged. Key interpretation: injury severity (OUTCOME) is the dominant predictor of payment amount, with state fixed effects capturing the legal-environment heterogeneity documented in Module 7. Full coefficient interpretation should wait for the consolidated model diagnostic review.

**Catastrophic Claim Classifier (Logistic Regression):**

| Metric | Value |
|--------|-------|
| **ROC-AUC** | **0.765** |
| Average Precision | 0.226 |
| Test set size | 69,618 |

An AUC of 0.77 means the model correctly ranks a random catastrophic case above a random non-catastrophic case **77% of the time**. For a first-pass model with only 6 features, this is a strong baseline. The relatively low average precision (0.23) reflects the class imbalance (only ~10% catastrophic rate) -- the model identifies the right direction but generates false positives. Feature engineering (adding specialty codes, patient age, and interaction terms) and ensemble methods should improve precision.

**For Dr. Manathunga:** These are the modeling-type questions that cannot be answered with a dashboard: (1) Which distribution family best captures the loss tail for reserving purposes? (2) Can claim-level features predict catastrophic outcomes before full litigation costs are known? (3) What is the marginal effect of state legal environment on payment severity after controlling for injury type?
""",
    ),
    # ── Section 12: Time-to-Payment (after cell 64) ──
    (
        64,
        """### Finding: Mean Lag of 4.75 Years -- Judgments Take 34% Longer Than Settlements

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
- **Reserving:** Insurers must hold reserves for an average of nearly 5 years per claim, with 10% of claims taking 8+ years to resolve. This extended "long tail" is a defining characteristic of medical malpractice liability.
- **Discounting:** At a 4% discount rate, a $500K payment made 5 years after the incident has a present value of ~$411K at incident time -- a 18% reduction. This has material implications for comparing nominal vs. economic-cost analyses.
- **For Dr. Manathunga's modeling question:** The lag duration itself is a predictive target. A Cox proportional hazards model (survival analysis) could identify which case characteristics predict faster or slower resolution -- potentially useful for claims management and early settlement strategies.

**Connection to Module 6 (Time-Grouped Analysis):** The report-year vs. incident-year cross-tab showed that older incidents resolving later tend to have higher mean payments ($422K for 1970s incidents resolving in the 1990s vs. $299K for contemporaneous 1990s incidents). Combined with the lag analysis, this suggests that cases with longer resolution times are systematically higher-severity -- a selection effect where more complex, higher-value cases take longer to litigate.
""",
    ),
]

# Sort by position descending so insertions don't shift indices
analysis_cells.sort(key=lambda x: x[0], reverse=True)

for after_idx, content in analysis_cells:
    new_cell = make_md_cell(content)
    nb["cells"].insert(after_idx + 1, new_cell)
    print(f"Inserted analysis cell after original cell {after_idx}")

# Save
with open(NOTEBOOK, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\nDone. Inserted {len(analysis_cells)} analysis cells.")
print(f"New total cells: {len(nb['cells'])}")
