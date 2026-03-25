"""Fix the dict keys in ALGNNATR maps in analysis_NPDB.ipynb"""
import json

nb = json.load(open('analysis_NPDB.ipynb', 'r', encoding='utf-8'))

for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code':
        continue
    new_src = []
    changed_allg = False
    for line in c['source']:
        if '1: \'Diagnosis Related\'' in line:
            new_src.append("    '1': 'Diagnosis Related',\n")
            changed_allg = True
        elif '2: \'Treatment Related\'' in line:
            new_src.append("    '2': 'Treatment Related',\n")
            changed_allg = True
        elif '3: \'Surgery Related\'' in line:
            new_src.append("    '3': 'Surgery Related',\n")
            changed_allg = True
        elif '4: \'Medication Related\'' in line:
            new_src.append("    '4': 'Medication Related',\n")
            changed_allg = True
        elif '5: \'IV & Blood Products\'' in line:
            new_src.append("    '5': 'IV & Blood Products',\n")
            changed_allg = True
        elif '6: \'Obstetrics Related\'' in line:
            new_src.append("    '6': 'Obstetrics Related',\n")
            changed_allg = True
        elif '7: \'Monitoring Related\'' in line:
            new_src.append("    '7': 'Monitoring Related',\n")
            changed_allg = True
        elif '8: \'Anesthesia Related\'' in line:
            new_src.append("    '8': 'Anesthesia Related',\n")
            changed_allg = True
        elif '9: \'Equipment/Product Related\'' in line:
            new_src.append("    '9': 'Equipment/Product Related',\n")
            changed_allg = True
        elif '10: \'Behavioral Health\'' in line:
            new_src.append("    '10': 'Behavioral Health',\n")
            changed_allg = True
        elif '11: \'Other Misc\'' in line:
            new_src.append("    '11': 'Other Misc',\n")
            changed_allg = True
        elif '12: \'Breach of Confidentiality\'' in line:
            new_src.append("    '12': 'Breach of Confidentiality'\n")
            changed_allg = True
        elif "allg_outcome['ALGNNATR'] = allg_outcome['ALGNNATR'].astype(str).str.strip()" in line:
            new_src.append("allg_outcome['ALGNNATR'] = allg_outcome['ALGNNATR'].astype(float).fillna(-1).astype(int).astype(str).str.strip().replace('-1', np.nan)\n")
            changed_allg = True
        elif "allg_stats['ALGNNATR'] = allg_stats['ALGNNATR'].astype(str).str.strip()" in line:
            new_src.append("allg_stats['ALGNNATR'] = allg_stats['ALGNNATR'].astype(float).fillna(-1).astype(int).astype(str).str.strip().replace('-1', np.nan)\n")
            changed_allg = True
        elif "cat_allg['ALGNNATR'] = cat_allg['ALGNNATR'].astype(str).str.strip()" in line:
            new_src.append("cat_allg['ALGNNATR'] = cat_allg['ALGNNATR'].astype(float).fillna(-1).astype(int).astype(str).str.strip().replace('-1', np.nan)\n")
            changed_allg = True
        else:
            new_src.append(line)
    
    if changed_allg:
        c['source'] = new_src
        print(f"Fixed ALGNNATR mapping in Cell {i}")

json.dump(nb, open('analysis_NPDB.ipynb', 'w', encoding='utf-8'), indent=1)
