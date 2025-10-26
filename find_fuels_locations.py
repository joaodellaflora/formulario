import pandas as pd
from pathlib import Path
import unicodedata

p = Path('ferramenta_ghg_protocol_v2025.0.1 (1).xlsx')
if not p.exists(): p = Path('Fatores de emissão.xlsx')

keywords = ['gasolina','gasolina automotiva','diesel','óleo diesel','etanol','biodiesel','glp','gás natural','gpl','diesel rodoviario','gás']

def normalize_text(s):
    if pd.isna(s): return ''
    s = str(s).lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s

xls = pd.read_excel(p, sheet_name=None, header=None)
results = []
for sheet, df in xls.items():
    for r in range(min(200, df.shape[0])):
        for c in range(min(200, df.shape[1])):
            v = df.iat[r, c]
            if pd.isna(v): continue
            s = normalize_text(v)
            for kw in keywords:
                if kw in s:
                    results.append({'sheet': sheet, 'row': r+1, 'col': c+1, 'value': str(v)})
                    break
    # limit to first many

Path('fuel_locations.json').write_text(pd.Series(results).to_json(orient='values', force_ascii=False), encoding='utf-8')
print('Done. total found=', len(results))
if len(results)>0:
    for r in results[:40]:
        print(r)
else:
    print('No occurrences found of fuel keywords')
