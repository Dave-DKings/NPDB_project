"""Check how ALGNNATR is being mapped in the allegation analysis cells"""
import json

nb = json.load(open('analysis_NPDB.ipynb', 'r', encoding='utf-8'))

# Find cells with allegation mapping or ALGNNATR
for i, c in enumerate(nb['cells']):
    if c['cell_type'] != 'code':
        continue
    src = ''.join(c['source'])
    if 'algnnatr_map' in src.lower() or 'allegation_map' in src.lower() or 'ALGNNATR' in src:
        lines = src.split('\n')
        clean = '\n'.join(''.join(ch if ord(ch) < 128 else '?' for ch in l) for l in lines[:40])
        print(f"=== Cell {i} ({len(lines)} lines) ===")
        print(clean)
        print()
