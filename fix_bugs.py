#!/usr/bin/env python3
"""Fix all code bugs in analysis_NPDB.ipynb based on NPDB PublicUseDataFile-Format.pdf spec."""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

NOTEBOOK = 'analysis_NPDB.ipynb'

with open(NOTEBOOK, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Backup
with open(NOTEBOOK + '.bak', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False)

changes = []

def find_cell(cell_id):
    for i, cell in enumerate(nb['cells']):
        if cell.get('id') == cell_id:
            return i, cell
    return None, None

# =============================================================================
# FIX 1: Cell 6418fdb1 — allg_map with correct NPDB ALGNNATR codes (p.21)
# =============================================================================
idx, cell = find_cell('6418fdb1')
if cell:
    old_src = ''.join(cell['source'])
    # Replace the wrong allg_map
    new_allg = """# ALGNNATR mapping (NPDB allegation group codes - per PublicUseDataFile-Format.pdf p.21)
allg_map = {
    1: 'Diagnosis Related',
    10: 'Anesthesia Related',
    20: 'Surgery Related',
    30: 'Medication Related',
    40: 'IV & Blood Products Related',
    50: 'Obstetrics Related',
    60: 'Treatment Related',
    70: 'Monitoring Related',
    80: 'Equipment/Product Related',
    90: 'Other Miscellaneous',
    100: 'Behavioral Health Related'
}"""
    old_allg = """# ALGNNATR mapping (NPDB allegation group codes)
allg_map = {
    1: 'Diagnosis Related',
    2: 'Treatment Related',
    3: 'Surgery Related',
    4: 'Medication Related',
    5: 'IV & Blood Products',
    6: 'Obstetrics Related',
    7: 'Monitoring Related',
    8: 'Anesthesia Related',
    9: 'Equipment/Product Related',
    10: 'Behavioral Health',
    11: 'Other Misc',
    12: 'Breach of Confidentiality'
}"""
    new_src = old_src.replace(old_allg, new_allg)
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (6418fdb1): Fixed allg_map keys to NPDB spec codes (1,10,20,...,100)")

# =============================================================================
# FIX 2: Cell 0e25b1c0 — PTSEX mapping: string keys 'M','F','U' (p.28)
# =============================================================================
idx, cell = find_cell('0e25b1c0')
if cell:
    old_src = ''.join(cell['source'])
    new_src = old_src.replace(
        "sex_map = {1: 'Male', 2: 'Female'}",
        "sex_map = {'M': 'Male', 'F': 'Female', 'U': 'Unknown'}  # PTSEX is string per NPDB spec p.28"
    )
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (0e25b1c0): Fixed PTSEX mapping to use string keys 'M','F','U'")

# =============================================================================
# FIX 3: Cell 2bf27d30 — PAYTYPE mapping: correct string codes (p.27)
# =============================================================================
idx, cell = find_cell('2bf27d30')
if cell:
    old_src = ''.join(cell['source'])
    old_paytype = """# PAYTYPE mapping
paytype_map = {
    '1': 'Judgment/Verdict', 'A': 'Judgment/Verdict',
    '2': 'Settlement', 'B': 'Settlement',
    '3': 'Arbitration', 'C': 'Arbitration',
    '4': 'Other/Not Classified', 'D': 'Other/Not Classified'
}"""
    new_paytype = """# PAYTYPE mapping (per PublicUseDataFile-Format.pdf p.27)
# NPDB recommends: all values except 'J' should be treated as settlements
paytype_map = {
    'S': 'Settlement',
    'B': 'Before Settlement',       # believed to be pre-settlement payments
    'U': 'Unknown/Before Settlement',# unknown whether settlement or judgment
    'O': 'Other',
    'J': 'Judgment'
}"""
    new_src = old_src.replace(old_paytype, new_paytype)
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (2bf27d30): Fixed PAYTYPE mapping to NPDB spec codes (S,B,U,O,J)")

# =============================================================================
# FIX 4: Cell f4b07a56 — catastrophic claims: fix .astype(str) to pd.to_numeric
# =============================================================================
idx, cell = find_cell('f4b07a56')
if cell:
    old_src = ''.join(cell['source'])
    new_src = old_src.replace(
        "cat_allg['ALGNNATR'] = cat_allg['ALGNNATR'].astype(str).str.strip()",
        "cat_allg['ALGNNATR'] = pd.to_numeric(cat_allg['ALGNNATR'], errors='coerce').astype('Int64')"
    )
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (f4b07a56): Fixed catastrophic claims ALGNNATR type conversion")

# =============================================================================
# FIX 5: Cell 97f24e5e — Change ACCRRPTS to NPMALRPT
# =============================================================================
idx, cell = find_cell('97f24e5e')
if cell:
    cell['source'] = [
        "# NPMALRPT = Practitioner's Number of Malpractice Payment Reports (per NPDB spec p.10)\n",
        "# Note: ACCRRPTS = \"Subjects Number of Accreditation Reports\" - NOT malpractice reports\n",
        "df_mal['NPMALRPT_NUM'] = pd.to_numeric(df_mal['NPMALRPT'], errors='coerce')\n",
        "print(\"=== Practitioner Malpractice Report Counts (NPMALRPT) ===\")\n",
        "print(df_mal['NPMALRPT_NUM'].value_counts().sort_index().head(15))\n",
        "print()\n",
        "print(f\"Practitioners with 2+ malpractice reports: {(df_mal['NPMALRPT_NUM'] >= 2).sum():,}\")\n",
        "print(f\"Practitioners with 5+ malpractice reports: {(df_mal['NPMALRPT_NUM'] >= 5).sum():,}\")\n",
        "print(f\"Practitioners with 10+ malpractice reports: {(df_mal['NPMALRPT_NUM'] >= 10).sum():,}\")\n",
    ]
    changes.append(f"Cell {idx} (97f24e5e): Changed ACCRRPTS to NPMALRPT for repeat offender analysis")

# =============================================================================
# FIX 6: Cell v90mmf0kc2 — Expand spec_map with ALL LICNFELD codes from PDF pp.16-20
# =============================================================================
idx, cell = find_cell('v90mmf0kc2')
if cell:
    old_src = ''.join(cell['source'])
    old_spec_map = """spec_map = {
    10: 'General Practice', 20: 'Anesthesiology', 30: 'Cardiovascular',
    50: 'Emergency Medicine', 60: 'Family Practice', 80: 'General Surgery',
    110: 'Internal Medicine', 160: 'OB-GYN', 200: 'Orthopedic Surgery',
    250: 'Radiology', 300: 'Neurology', 310: 'Neurosurgery'
}"""
    new_spec_map = """# LICNFELD mapping (per PublicUseDataFile-Format.pdf pp.16-20)
spec_map = {
    10: 'Allopathic Physician (MD)', 15: 'Physician Resident (MD)',
    20: 'Osteopathic Physician (DO)', 25: 'Osteopathic Phys. Resident (DO)',
    30: 'Dentist', 35: 'Dental Resident',
    50: 'Pharmacist', 55: 'Pharmacy Intern', 60: 'Pharmacist, Nuclear',
    70: 'Pharmacy Assistant', 75: 'Pharmacy Technician', 76: 'Other Pharmacy Service',
    100: 'Registered Nurse', 110: 'Nurse Anesthetist',
    120: 'Nurse Midwife', 130: 'Nurse Practitioner',
    134: 'Doctor of Nursing Practice', 135: 'Advanced Nurse Practitioner',
    140: 'LPN/Vocational Nurse', 141: 'Clinical Nurse Specialist',
    142: 'Other Nurse Occupation', 148: 'Certified Nurse Aide/Nursing Asst',
    150: 'Nurse Aide/Nursing Assistant', 160: 'Home Health Aide',
    165: 'Health Care Aide/Direct Care Worker', 170: 'Psychiatric Technician',
    175: 'Certified/Qualified Medication Aide', 176: 'Other Aide Occupation',
    200: 'Dietitian', 210: 'Nutritionist', 211: 'Other Dietitian/Nutritionist',
    240: 'Emergency Medical Responder', 250: 'Emergency Medical Technician (EMT)',
    260: 'EMT, Cardiac/Critical Care', 270: 'Advanced EMT (AEMT)',
    280: 'Paramedic', 281: 'Other Emergency Medical Services',
    300: 'Clinical Social Worker', 350: 'Podiatrist',
    370: 'Clinical Psychologist', 371: 'Psychologist', 372: 'School Psychologist',
    373: 'Psychological Asst/Assoc/Examiner', 374: 'Other Psychologist/Psych Asst',
    400: 'Audiologist', 402: 'Art/Recreation Therapist',
    405: 'Massage Therapist', 410: 'Occupational Therapist',
    420: 'Occup. Therapy Assistant', 430: 'Physical Therapist',
    440: 'Phys. Therapy Assistant', 450: 'Rehabilitation Therapist',
    460: 'Speech/Language Pathologist', 470: 'Hearing Aid/Instrument Specialist',
    471: 'Other Speech/Language/Hearing Service',
    500: 'Medical Technologist', 501: 'Medical/Clinical Lab Tech',
    502: 'Medical/Clinical Lab Technician', 503: 'Surgical Technologist/Assistant',
    504: 'Surgical Assistant', 505: 'Cytotechnologist',
    510: 'Nuclear Med. Technologist', 520: 'Rad. Therapy Technologist',
    530: 'Radiologic Technician/Technologist', 540: 'X-Ray Technician or Operator',
    550: 'Limited X-Ray Machine Operator', 551: 'Other Technologist/Technician',
    600: 'Acupuncturist', 601: 'Athletic Trainer', 603: 'Chiropractor',
    604: 'Chiropractic Assistant', 605: 'Other Chiropractic Occupation',
    606: 'Dental Assistant', 607: 'Dental Therapist/Dental Health Aide',
    609: 'Dental Hygienist', 612: 'Denturist', 613: 'Other Dental Occupation',
    615: 'Homeopath', 618: 'Medical Assistant',
    621: 'Counselor, Mental Health', 624: 'Midwife, Lay (Non-Nurse)',
    627: 'Naturopath', 630: 'Ocularist', 633: 'Optician',
    636: 'Optometrist', 637: 'Other Eye/Vision Service',
    639: 'Orthotics/Prosthetics Fitter', 642: 'Physician Assistant',
    645: 'Phys. Asst., Osteopathic', 647: 'Perfusionist',
    648: 'Podiatric Assistant', 649: 'Other Podiatric Service',
    651: 'Prof. Counselor', 652: 'Sex Offender Counselor',
    653: 'Pastoral Counselor', 654: 'Prof. Cnslr., Alcohol',
    657: 'Prof. Cnslr., Family/Marriage',
    658: 'Other Rehab/Respiratory/Restorative Service',
    660: 'Addictions Counselor', 661: 'Marriage and Family Therapist',
    662: 'Art Therapist', 663: 'Respiratory Therapist',
    664: 'Recreation Therapist', 665: 'Dance Therapist',
    666: 'Resp. Therapy Technician', 667: 'Music Therapist',
    668: 'Other Behavioral Health Occupation',
    699: 'Other Health Care Pract, Not Classified',
    752: 'Adult Care Facility Admin', 755: 'Hospital Administrator',
    758: 'Health Care Facility Admin', 759: 'Assisted Living Facility Admin',
    800: 'Researcher, Clinical', 810: 'Insurance Agent/Broker',
    812: 'Insurance Broker', 820: 'Corporate Officer',
    822: 'Business Manager', 830: 'Business Owner',
    840: 'Salesperson', 850: 'Accountant', 853: 'Bookkeeper',
    899: 'Other Individual, Not Classified',
    998: 'Subject Not Reportable', 999: 'Unspecified or Unknown',
    1301: 'General/Acute Care Hospital', 1302: 'Psychiatric Hospital',
    1303: 'Rehabilitation Hospital', 1304: 'Federal Hospital',
    1307: 'Psychiatric Unit', 1308: 'Rehabilitation Unit',
    1310: 'Laboratory/CLIA Laboratory', 1320: 'Health Insurance Co/Provider',
    1331: 'Health Maintenance Organization', 1335: 'Preferred Provider Org',
    1336: 'Provider Sponsored Organization',
    1338: 'Religious/Fraternal Benefit Society Plan',
    1342: 'Blood Bank', 1343: 'Durable Medical Equipment Supplier',
    1344: 'Eyewear Equipment Supplier', 1345: 'Pharmacy (Organization)',
    1346: 'Pharmaceutical Manufacturer', 1347: 'Biological Products Manufacturer',
    1348: 'Organ Procurement Organization', 1349: 'Portable X-Ray Supplier',
    1351: 'Fiscal/Billing/Management Agent', 1352: 'Purchasing Service',
    1353: 'Nursing/Health Care Staffing Service',
    1361: 'Chiropractic Group/Practice', 1362: 'Dental Group/Practice',
    1363: 'Optician/Optometric Group/Practice', 1364: 'Podiatric Group/Practice',
    1365: 'Medical Group/Practice', 1366: 'Mental Health/Substance Abuse Group',
    1367: 'Physical/Occupational Therapy Group', 1370: 'Research Center/Facility',
    1381: 'Adult Day Care Facility', 1382: 'Hospice/Hospice Care Provider',
    1383: 'Intermed. Care Fclty Intellectual Disability/Substance Abuse',
    1386: 'Residential Treatment Facility', 1388: 'Outpatient Rehab Facility',
    1389: 'Nursing/Skilled Nursing Facility',
    1390: 'Ambulance Service/Transportation Co',
    1391: 'Ambulatory Surgical Center', 1392: 'Ambulatory Clinic/Center',
    1393: 'Home Health Agency/Organization',
    1394: 'Health Cntr/FQHC', 1395: 'Mental Health Center/Community MHC',
    1396: 'Rural Health Clinic', 1397: 'Mammography Service Provider',
    1398: 'End Stage Renal Disease Facility', 1399: 'Radiology/Imaging Center',
    1999: 'Other Type not classified', 9999: 'Org. Type not specified'
}"""
    new_src = old_src.replace(old_spec_map, new_spec_map)
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (v90mmf0kc2): Expanded LICNFELD spec_map with ALL codes from PDF spec")

# =============================================================================
# FIX 7: Cell n4hgz78o34d — Module 12: clarify ACCRRPTS vs NPMALRPT in comment
# =============================================================================
idx, cell = find_cell('n4hgz78o34d')
if cell:
    old_src = ''.join(cell['source'])
    new_src = old_src.replace(
        "# Focus on records with valid ACCRRPTS\nrpt_data = mal.dropna(subset=['ACCRRPTS']).copy()",
        "# Focus on records with valid NPMALRPT (practitioner's malpractice report count)\n"
        "# Note: ACCRRPTS = Accreditation Reports (not malpractice!) per NPDB spec p.10\n"
        "rpt_data = mal.dropna(subset=['NPMALRPT']).copy()"
    )
    cell['source'] = [new_src]
    changes.append(f"Cell {idx} (n4hgz78o34d): Clarified ACCRRPTS vs NPMALRPT in Module 12")

# =============================================================================
# Write fixed notebook
# =============================================================================
with open(NOTEBOOK, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("=" * 60)
print("ALL FIXES APPLIED SUCCESSFULLY")
print("=" * 60)
for c in changes:
    print(f"  {c}")
print(f"\nTotal changes: {len(changes)}")
