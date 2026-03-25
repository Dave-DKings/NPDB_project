# NPDB Project

Advanced analysis workflow for the National Practitioner Data Bank malpractice-payment dataset.

## Main Artifacts

- `advanced_NPDB.ipynb`: structured notebook orchestrating the analysis workflow
- `npdb_analysis/`: reusable Python modules for cleaning, feature engineering, linkage, aggregation, plotting, and modeling
- `docs/`: methodology notes for linkage, Wisconsin peer selection, and settlement-policy interpretation

## Repository Notes

- The raw CSV `NpdbPublicUseDataCsv/NPDB2510.CSV` is excluded from Git by default because it exceeds GitHub's normal file-size limit.
- If you want the raw CSV versioned in GitHub, use Git LFS instead of standard Git.

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Then open and run:

```text
advanced_NPDB.ipynb
```

## Colab Setup

If you clone this repository into Colab, also place the NPDB CSV at:

```text
NpdbPublicUseDataCsv/NPDB2510.CSV
```

or update the data path in `npdb_analysis/config.py`.
