import pandas as pd, json
from pathlib import Path
p = Path(r"C:\Users\joaog\Documents\Automatização de emissão\Fatores de emissão.xlsx")
if not p.exists():
    print('XLSX not found:', p)
    raise SystemExit(2)

xls = pd.read_excel(p, sheet_name=None)
if 'Combustão Móvel' not in xls:
    print('sheet Combustão Móvel not found, sheets:', list(xls.keys()))
    raise SystemExit(3)

df = xls['Combustão Móvel']
factors = {}
for _, row in df.iterrows():
    fuel = str(row.get('Combustível') or '').strip()
    unit = str(row.get('Unidade') or '').strip().lower()
    if not fuel:
        continue
    # only process rows with unit in liters (litro)
    if unit.startswith('litro'):
        try:
            co2 = float(row.get('CO2 ') if not pd.isna(row.get('CO2 ')) else 0)
        except Exception:
            continue
        entry = {'unit':'kg_per_l', 'co2_kg_per_l': co2}
        try:
            ch4 = row.get('CH4')
            if not pd.isna(ch4): entry['ch4_kg_per_l'] = float(ch4)
        except Exception:
            pass
        try:
            n2o = row.get('N2O')
            if not pd.isna(n2o): entry['n2o_kg_per_l'] = float(n2o)
        except Exception:
            pass
        factors[fuel] = entry

out = Path('emission_factors.json')
out.write_text(json.dumps(factors, ensure_ascii=False, indent=2), encoding='utf-8')
print('WROTE', out, 'entries=', len(factors))
