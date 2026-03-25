"""Project-wide constants for NPDB analysis."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "NpdbPublicUseDataCsv" / "NPDB2510.CSV"

MALPRACTICE_RECORD_TYPES = ("M", "P")
CURRENCY_COLUMNS = ("PAYMENT", "TOTALPMT")

NULLABLE_NUMERIC_COLUMNS = (
    "PRACTAGE",
    "GRAD",
    "ALGNNATR",
    "ALEGATN1",
    "ALEGATN2",
    "OUTCOME",
    "MALYEAR1",
    "MALYEAR2",
    "NUMBPRSN",
    "PTAGE",
    "AAYEAR",
    "AACLASS1",
    "AACLASS2",
    "AACLASS3",
    "AACLASS4",
    "AACLASS5",
    "AAEFYEAR",
    "AASIGYR",
    "FUNDPYMT",
    "PRACTNUM",
    "ACCRRPTS",
    "NPMALRPT",
    "NPLICRPT",
    "NPCLPRPT",
    "NPPSMRPT",
    "NPDEARPT",
    "NPEXCRPT",
    "NPGARPT",
    "NPCTMRPT",
    "TYPE",
    "REPTYPE",
)

CATEGORY_COLUMNS = (
    "RECTYPE",
    "WORKSTAT",
    "HOMESTAT",
    "LICNSTAT",
    "PAYNUMBR",
    "PAYTYPE",
    "PYRRLTNS",
    "PTSEX",
    "PTTYPE",
    "AALENTYP",
    "BASISCD1",
    "BASISCD2",
    "BASISCD3",
    "BASISCD4",
    "BASISCD5",
)

ALLEGATION_GROUP_MAP = {
    1: "Diagnosis Related",
    10: "Anesthesia Related",
    20: "Surgery Related",
    30: "Medication Related",
    40: "IV & Blood Products Related",
    50: "Obstetrics Related",
    60: "Treatment Related",
    70: "Monitoring Related",
    80: "Equipment/Product Related",
    90: "Other Miscellaneous",
    100: "Behavioral Health Related",
}

PAYMENT_MODE_MAP = {
    "S": "Single Payment",
    "M": "Multiple Payments",
    "U": "Unknown Payment Mode",
}

PAYTYPE_BINARY_MAP = {
    "J": "Judgment",
    "S": "Settlement/Non-Judgment",
    "U": "Settlement/Non-Judgment",
    "B": "Settlement/Non-Judgment",
    "O": "Settlement/Non-Judgment",
}

NPDB_PEER_STATES = ("WI", "MN", "IA", "IL", "MI", "IN", "OH")

# Reused from the existing notebook to keep the 2025-dollar baseline aligned.
CPI_FACTORS_2025 = {
    1990: 2.32,
    1991: 2.22,
    1992: 2.16,
    1993: 2.10,
    1994: 2.04,
    1995: 1.99,
    1996: 1.93,
    1997: 1.89,
    1998: 1.86,
    1999: 1.82,
    2000: 1.76,
    2001: 1.71,
    2002: 1.69,
    2003: 1.65,
    2004: 1.60,
    2005: 1.55,
    2006: 1.50,
    2007: 1.46,
    2008: 1.41,
    2009: 1.42,
    2010: 1.39,
    2011: 1.35,
    2012: 1.32,
    2013: 1.30,
    2014: 1.28,
    2015: 1.28,
    2016: 1.26,
    2017: 1.24,
    2018: 1.21,
    2019: 1.18,
    2020: 1.17,
    2021: 1.12,
    2022: 1.03,
    2023: 1.00,
    2024: 0.97,
    2025: 0.95,
}

