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

Clone the repository into Colab:

```python
!git clone https://github.com/Dave-DKings/NPDB_project.git /content/npdb_project
```

Then place the NPDB CSV at one of these locations:

```text
/content/npdb_project/NpdbPublicUseDataCsv/NPDB2510.CSV
/content/NPDB2510.CSV
```

The notebook bootstrap cell will look for both locations automatically. You can also override the path with:

```python
import os
os.environ["NPDB_DATA_PATH"] = "/full/path/to/NPDB2510.CSV"
```
