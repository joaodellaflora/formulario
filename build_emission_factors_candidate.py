"""Constrói um emission_factors.auto.json candidato usando heurísticas:
 - coleta nomes canônicos da aba 'Listas'
 - busca valores em 'Fatores de Emissão', 'Fatores de conversao', 'Fatores Variaveis'
 - prioriza colunas com 'CO2' e unidade que contenha 'kg' ou 'g' e indica se é per L ou per km
 - salva emission_factors.auto.json e factors_import_report.md
"""
import pandas as pd
import json
from pathlib import Path
import re
import unicodedata

p = Path('ferramenta_ghg_protocol_v2025.0.1 (1).xlsx')
if not p.exists():
    p = Path('Fatores de emissão.xlsx')

xls = pd.read_excel(p, sheet_name=None, header=None)

# helper
def normalize(s):
    if pd.isna(s): return ''
    s = str(s)
    s2 = unicodedata.normalize('NFKD', s)
    s2 = ''.join(c for c in s2 if not unicodedata.combining(c))
    return s2.strip()

def to_num(v):
    # handle pandas Series or arrays (duplicate column labels can return Series)
    try:
        import numpy as _np
        if isinstance(v, (pd.Series, list, tuple, _np.ndarray)):
            # pick first non-null scalar
            for item in v:
                if not pd.isna(item):
                    v = item
                    break
            else:
                return None
    except Exception:
        pass
    try:
        if pd.isna(v):
            return None
    except Exception:
        # if pd.isna errors, fallback to string check
        if v is None:
            return None
    try:
        return float(v)
    except Exception:
        s = str(v).strip().replace(',','.')
        m = re.search(r'[-+]?[0-9]*\.?[0-9]+', s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None

report = []
out = {}

# 1) collect candidate names from 'Listas' (first 200 rows)
if 'Listas' in xls:
    df_listas = xls['Listas']
    names = set()
    for r in range(min(200, df_listas.shape[0])):
        for c in range(min(200, df_listas.shape[1])):
            v = df_listas.iat[r,c]
            if pd.isna(v): continue
            s = normalize(v).lower()
            # heuristics: names often have 'gasolina' or 'diesel' or 'etanol' or 'GLP' etc
            if any(k in s for k in ['gasolina','diesel','etanol','gpl','glp','biodiesel','hvo','metanol','aviacao','aviao','biomet']):
                names.add(v)
    report.append(f'Collected {len(names)} candidate names from Listas')
else:
    names = set()
    report.append('Listas sheet not found')

# fallback: from fuel_locations.json
floc = Path('fuel_locations.json')
if floc.exists() and not names:
    j = json.loads(floc.read_text(encoding='utf-8'))
    for rec in j:
        val = rec.get('value')
        if val:
            s = normalize(val).lower()
            if any(k in s for k in ['gasolina','diesel','etanol','gpl','glp','biodiesel','hvo','metanol','aviacao','aviao','biomet']):
                names.add(val)
    report.append(f'Collected {len(names)} candidate names from fuel_locations.json')

# candidate sheets to search
search_sheets = ['Fatores de Emissão', 'Fatores de conversao', 'Fatores Variaveis', 'Fatores Variáveis', 'Fatores de Emissao']
available_sheets = list(xls.keys())
report.append(f'Workbook sheets: {available_sheets}')

for name in sorted(names):
    out[name] = {'unit': 'unknown', 'source': None}
    lname = normalize(name).lower()
    found_any = False
    for sheet in search_sheets:
        if sheet not in xls: continue
        df = xls[sheet]
        # detect header
        best_i = 0; best_cnt = -1
        for i in range(min(12, len(df))):
            cnt = df.iloc[i].count()
            if cnt>best_cnt: best_cnt=cnt; best_i=i
        header = df.iloc[best_i].fillna('').astype(str).str.strip().tolist()
        data = df.iloc[best_i+1:].copy()
        data.columns = header
        # search rows where any column contains name or partial
        for idx, row in data.iterrows():
            row_text = ' '.join([str(x) for x in row.values if pd.notna(x)]).lower()
            if lname in normalize(row_text).lower():
                # try extract CO2/CH4/N2O numbers
                rec = {}
                rec['_sheet'] = sheet
                rec['_row'] = int(idx)+1
                # try columns
                for col in data.columns:
                    cc = str(col)
                    val = row.get(col)
                    num = to_num(val)
                    if num is None: continue
                    if re.search(r'co2', cc, re.I):
                        rec['co2'] = num
                        rec['co2_col'] = cc
                    if re.search(r'ch4', cc, re.I):
                        rec['ch4'] = num
                        rec['ch4_col'] = cc
                    if re.search(r'n2o', cc, re.I):
                        rec['n2o'] = num
                        rec['n2o_col'] = cc
                    if re.search(r'kg\s*/\s*l|kg/l|kg per l|kg por l|kg por litro|kg/litro', cc, re.I):
                        rec['unit_hint'] = 'kg_per_l'
                    if re.search(r'kg\s*/\s*km|kg/km|g/km|g\s*/\s*km', cc, re.I):
                        rec['unit_hint'] = 'kg_per_km'
                if 'co2' in rec or 'co2' in rec:
                    out[name]['source'] = rec
                    # set normalized unit
                    if rec.get('unit_hint')=='kg_per_l':
                        out[name]['unit']='kg_per_l'
                        if 'co2' in rec:
                            out[name]['co2_kg_per_l'] = rec['co2'] if rec['co2']>1 else rec['co2']
                    elif rec.get('unit_hint')=='kg_per_km':
                        out[name]['unit']='kg_per_km'
                        out[name]['co2_kg_per_km'] = rec.get('co2')
                    else:
                        # default assume kg per l if number magnitude reasonable
                        v = rec.get('co2')
                        if v and v>0 and v<100:
                            out[name]['unit']='kg_per_l'
                            out[name]['co2_kg_per_l']=v
                        else:
                            out[name]['_raw_co2']=v
                    found_any = True
                    break
        if found_any: break
    if not found_any:
        out[name]['note'] = 'not found in candidate sheets'

# save candidate file (do not overwrite final emission_factors.json)
Path('emission_factors.auto.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
rep = ['# factors import report', ''] + report
Path('factors_import_report.md').write_text('\n'.join(rep), encoding='utf-8')
print('Wrote emission_factors.auto.json entries=', len(out))
print('Wrote factors_import_report.md')
