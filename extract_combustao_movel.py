"""Extrai fatores diretamente da aba 'Combustão móvel' do workbook GHG.
Gera emission_factors.json com chaves nome_do_combustivel -> { unit, co2_kg_per_l, ch4_kg_per_l, n2o_kg_per_l }
Também tenta extrair fatores per-km da aba 'Fatores de Emissão' se presente.
"""
import pandas as pd
import json
from pathlib import Path
import unicodedata

p = Path('ferramenta_ghg_protocol_v2025.0.1 (1).xlsx')
if not p.exists():
    p = Path('Fatores de emissão.xlsx')

print('Using file', p)
xls = pd.read_excel(p, sheet_name=None)
print('Sheets:', list(xls.keys()))

out = {}
report = []

# helper normalize
def norm_key(s):
    if s is None: return ''
    s = str(s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.strip()

# header detection
def detect_header(df):
    best_i = 0; best_cnt = -1
    for i in range(min(10, len(df))):
        cnt = df.iloc[i].count()
        if cnt > best_cnt:
            best_cnt = cnt; best_i = i
    header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
    data = df.iloc[best_i+1:].copy()
    data.columns = header
    data = data.loc[:, [c for c in data.columns if c]]
    return header, data

# 1) Combustão móvel
sheet_name = 'Combustão móvel'
if sheet_name in xls:
    hdr, data = detect_header(xls[sheet_name])
    report.append(f"Combustão móvel header row cols={len(hdr)}")
    # Try common column names
    # candidates: 'Ano','Combustível','Unidade','CO2 ','CH4','N2O'
    for _, row in data.iterrows():
        fuel = None
        for c in ['Combustível','Combustivel','Combustível ']:
            if c in data.columns:
                val = row.get(c)
                if pd.notna(val):
                    fuel = str(val).strip(); break
        if not fuel:
            continue
        unit = None
        for c in ['Unidade','Unidade ']:
            if c in data.columns:
                v = row.get(c)
                if pd.notna(v):
                    unit = str(v).strip().lower(); break
        # find co2/ch4/n2o columns heuristically
        def find_val(cols):
            for c in cols:
                if c in data.columns and pd.notna(row.get(c)):
                    try:
                        return float(row.get(c))
                    except Exception:
                        try:
                            return float(str(row.get(c)).replace(',','.'))
                        except Exception:
                            return None
            return None
        co2 = find_val(['CO2 ','CO2','CO2 (kg)','CO2 (g)'])
        ch4 = find_val(['CH4','CH4 ','CH4 (g/km)','CH4 (kg)'])
        n2o = find_val(['N2O','N2O ','N2O (g/km)','N2O (kg)'])
        entry = {}
        if unit and 'litro' in unit:
            entry['unit'] = 'kg_per_l'
            if co2 is not None:
                entry['co2_kg_per_l'] = co2
            if ch4 is not None:
                entry['ch4_kg_per_l'] = ch4
            if n2o is not None:
                entry['n2o_kg_per_l'] = n2o
        else:
            # store raw if unit not liter (e.g., m3)
            entry['unit'] = unit or 'unknown'
            if co2 is not None:
                entry['co2_raw'] = co2
            if ch4 is not None:
                entry['ch4_raw'] = ch4
            if n2o is not None:
                entry['n2o_raw'] = n2o
        out[fuel] = entry
    report.append('Combustão móvel: extracted %d fuels' % len(out)
                  )
else:
    report.append('Combustão móvel sheet not found')

# 2) Fatores de Emissão (attempt per-km factors)
sheet2 = 'Fatores de Emissão'
if sheet2 in xls:
    hdr2, data2 = detect_header(xls[sheet2])
    report.append('Fatores de Emissão header len %d' % len(hdr2))
    # try to find rows where first col is fuel and columns include co2 per km
    # heuristic: look for a column name containing 'CO2' and 'per km' or similar
    for _, row in data2.iterrows():
        # try to find a fuel name
        fuel = None
        for c in data2.columns:
            if 'Combust' in str(c) or 'Combustivel' in str(c) or 'Combust	6vel' in str(c):
                v = row.get(c)
                if pd.notna(v): fuel = str(v).strip(); break
        if not fuel:
            # try first non-null
            for c in data2.columns:
                v = row.get(c)
                if pd.notna(v) and isinstance(v, str) and len(str(v))>2:
                    fuel = str(v).strip(); break
        if not fuel:
            continue
        # find co2 per km
        co2_km = None
        for c in data2.columns:
            if 'CO2' in str(c) and ('km' in str(c).lower() or '/km' in str(c)):
                val = row.get(c)
                if pd.notna(val):
                    try: co2_km = float(val); break
                    except: 
                        try: co2_km = float(str(val).replace(',','.')); break
                        except: pass
        if co2_km is not None:
            out.setdefault(fuel, {})['unit'] = 'kg_per_km'
            out[fuel]['co2_kg_per_km'] = co2_km
    report.append('Fatores de Emissão: merged per-km factors if found')
else:
    report.append('Fatores de Emissão sheet not present')

# write
Path('emission_factors.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
Path('factors_import_report.md').write_text('# Import report\n' + '\n'.join(report), encoding='utf-8')
print('Done. entries=', len(out))
print('\n'.join(report))
