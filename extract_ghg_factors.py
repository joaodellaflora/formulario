"""Extrai fatores relevantes da planilha GHG e grava emission_factors.json + relatório.
Abas processadas: Combustão Móvel, Composição combustíveis, Veículos elétricos, Fatores de conversão, GWP
"""
import pandas as pd
import json
from pathlib import Path

p = Path('Fatores de emissão.xlsx')
alt = Path('ferramenta_ghg_protocol_v2025.0.1 (1).xlsx')
if alt.exists():
    p = alt

print('reading', p)
xls = pd.read_excel(p, sheet_name=None)
out = {}
report = []

# 1) Combustão Móvel
if 'Combustão Móvel' in xls:
    df = xls['Combustão Móvel']
    # detect header row (first row with most non-null)
    best_i = 0
    best_cnt = -1
    for i in range(min(10, len(df))):
        cnt = df.iloc[i].count()
        if cnt > best_cnt:
            best_cnt = cnt; best_i = i
    header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
    data = df.iloc[best_i+1:].copy()
    data.columns = header
    data = data.loc[:, [c for c in data.columns if c]]
    report.append(f"Combustão Móvel: header detected (row {best_i}): {header}")
    count = 0
    for _, row in data.iterrows():
        fuel = str(row.get('Combustível') or row.get('Combustivel') or '').strip()
        if not fuel:
            continue
        unit = str(row.get('Unidade') or '').strip().lower()
        # read gases columns with heuristic
        def getnum(cols):
            for c in cols:
                if c in row and pd.notna(row[c]):
                    try:
                        return float(row[c])
                    except Exception:
                        try:
                            return float(str(row[c]).replace(',', '.'))
                        except Exception:
                            return None
            return None
        co2 = getnum(['CO2 ', 'CO2', 'CO2', 'CO2 (kg)', 'CO2 (g)'])
        ch4 = getnum(['CH4','CH4 ','CH4 (g/km)'])
        n2o = getnum(['N2O','N2O ','N2O (g/km)'])
        entry = {}
        if 'litro' in unit:
            entry['unit'] = 'kg_per_l'
            # assume values are already kg per liter or grams per km?
            # the sheet seems to provide per-liter for CO2 and per-km for CH4/N2O sometimes
            if co2 is not None:
                entry['co2_kg_per_l'] = co2
        else:
            # keep unit raw and store per_unit values
            entry['unit'] = f'per_unit:{unit}'
            if co2 is not None:
                entry['co2_per_unit'] = co2
        if ch4 is not None:
            # if values small likely kg per liter
            if entry.get('unit')=='kg_per_l':
                entry['ch4_kg_per_l'] = ch4
            else:
                entry['ch4_per_unit'] = ch4
        if n2o is not None:
            if entry.get('unit')=='kg_per_l':
                entry['n2o_kg_per_l'] = n2o
            else:
                entry['n2o_per_unit'] = n2o
        out[fuel] = entry
        count += 1
    report.append(f"Combustão Móvel: imported {count} fuels")
else:
    report.append('Combustão Móvel: sheet not found')

# 2) Composição combustíveis
components_map = {}
if 'Composição combustíveis' in xls:
    df = xls['Composição combustíveis']
    # detect header similarly
    best_i = 0; best_cnt = -1
    for i in range(min(10, len(df))):
        cnt = df.iloc[i].count()
        if cnt > best_cnt: best_cnt = cnt; best_i = i
    header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
    data = df.iloc[best_i+1:].copy(); data.columns = header
    data = data.loc[:, [c for c in data.columns if c]]
    report.append(f"Composição combustíveis: header detected (row {best_i}): {header}")
    for _, row in data.iterrows():
        parent = str(row.get('Tipo de combustível') or row.get('Tipo de combustivel') or '').strip()
        fossil = str(row.get('Combustível Fóssil') or row.get('Combustivel Fossil') or '').strip()
        bio = str(row.get('Biocombustível') or '').strip()
        if parent:
            comps = []
            if fossil and fossil!='-': comps.append({'name':fossil, 'fraction':1.0})
            if bio and bio!='-': comps.append({'name':bio, 'fraction':1.0})
            if comps:
                components_map[parent] = comps
    report.append(f"Composição combustíveis: mapped {len(components_map)} entries")
else:
    report.append('Composição combustíveis: sheet not found')

# attach components where relevant
for k, v in components_map.items():
    if k in out:
        out[k]['components'] = v
    else:
        out[k] = {'components': v}

# 3) Veículos elétricos: extract km/kWh to create a placeholder electricity factor
if 'Veículos elétricos' in xls:
    df = xls['Veículos elétricos']
    # detect header
    best_i = 0; best_cnt = -1
    for i in range(min(10, len(df))):
        cnt = df.iloc[i].count()
        if cnt > best_cnt: best_cnt = cnt; best_i = i
    header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
    data = df.iloc[best_i+1:].copy(); data.columns = header
    data = data.loc[:, [c for c in data.columns if c]]
    # find typical km/kWh values
    for _, row in data.iterrows():
        fuel = str(row.get('Combustível') or '').strip()
        km_per_kwh = None
        for col in data.columns:
            if 'Km' in col or 'Km' in str(col) or 'Km/KWh' in col or 'Consumo Km/KWh' in col:
                try:
                    km_per_kwh = float(row[col])
                except Exception:
                    try:
                        km_per_kwh = float(str(row[col]).replace(',','.'))
                    except Exception:
                        km_per_kwh = None
        if fuel and km_per_kwh:
            # we don't have kg per kWh here; store consumption pattern
            out_key = fuel or 'Eletricidade'
            out[out_key] = out.get(out_key, {})
            out[out_key]['unit'] = 'km_per_kwh'
            out[out_key]['km_per_kwh'] = km_per_kwh
    report.append('Veículos elétricos: extracted consumption patterns')
else:
    report.append('Veículos elétricos: sheet not found')

# 4) Fatores de conversão - store as reference
conv = {}
if 'Fatores de conversão' in xls:
    df = xls['Fatores de conversão']
    # heuristic: find rows with unit names
    lines = df.astype(str).fillna('').apply(lambda row: ' | '.join(row.values.tolist()), axis=1)
    conv['raw_preview'] = lines.head(20).tolist()
    report.append('Fatores de conversão: raw preview captured')
else:
    report.append('Fatores de conversão: not found')

# 5) GWP
gwp = {}
if 'GWP' in xls:
    df = xls['GWP']
    # try to find e.g., columns ['Gas','GWP 100a'] etc
    report.append('GWP: sheet found; not parsed in detail')
else:
    report.append('GWP: sheet not found')

# Write outputs
Path('emission_factors.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
Path('factors_import_report.md').write_text('\n'.join(['# Import report']+report), encoding='utf-8')
print('WROTE emission_factors.json (entries=', len(out), ')')
print('\n'.join(report))
