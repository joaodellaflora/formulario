#!/usr/bin/env python3
"""
Importa coordenadas (lat/lon) da planilha XLSX original
Lê colunas B:L por padrão (onde você informou que as coordenadas estão em E-L)
Tenta detectar automaticamente quais colunas representam latitude/longitude e gera
`data/airport_coords.json` com o mapeamento IATA -> {lat, lon}.

Uso:
  python scripts\import_coords_from_xlsx.py "C:/path/to/Fatores de emissao (1).xlsx"

Requer: pandas + openpyxl
"""
import sys
from pathlib import Path
import json
import unicodedata

try:
    import pandas as pd
except Exception as e:
    print('Pandas não está instalado. Instale com: pip install pandas openpyxl')
    raise


def normalize(s):
    if pd.isna(s):
        return ''
    s2 = str(s)
    s2 = unicodedata.normalize('NFKD', s2)
    return ' '.join(s2.split()).strip()


def detect_lat_lon_columns(df):
    # prefer columns with names containing lat/lon
    cols = list(df.columns)
    lat_col = None
    lon_col = None
    for c in cols:
        lc = c.lower()
        if 'lat' in lc and lat_col is None:
            lat_col = c
        if 'lon' in lc or 'lng' in lc or 'long' in lc and lon_col is None:
            lon_col = c
    if lat_col and lon_col:
        return lat_col, lon_col

    # fallback: find two numeric columns where values are in lat/lon ranges
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    # try all pairs
    for i in range(len(numeric_cols)):
        for j in range(i+1, len(numeric_cols)):
            a = df[numeric_cols[i]].dropna()
            b = df[numeric_cols[j]].dropna()
            if a.empty or b.empty:
                continue
            # check percent values in ranges
            a_good = a.between(-90,90).mean() > 0.9
            b_good = b.between(-180,180).mean() > 0.9
            if a_good and b_good:
                return numeric_cols[i], numeric_cols[j]
            # try swapped
            a_good = a.between(-180,180).mean() > 0.9
            b_good = b.between(-90,90).mean() > 0.9
            if a_good and b_good:
                return numeric_cols[j], numeric_cols[i]

    return None, None


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path(r"C:\Users\joaog\Documents\Automatização de emissão\Fatores de emissão (1).xlsx")
    if not path.exists():
        print('Arquivo não encontrado:', path)
        sys.exit(2)

    print('Lendo planilha:', path)
    # read columns B:L
    df = pd.read_excel(path, sheet_name='Aeroportos', usecols='B:L', engine='openpyxl', dtype=object)
    # normalize headers
    df.columns = [normalize(c) for c in df.columns]
    # expected: columns include airport (IATA), airport name, city, plus coordinate columns
    # try to find IATA column (airport code)
    col_iata = None
    for c in df.columns:
        if c and ('iata' in c.lower() or c.lower()=='airport' or 'code' in c.lower()):
            col_iata = c
            break
    if not col_iata:
        # fallback: first non-empty column (assume it's IATA as in previous script)
        col_iata = df.columns[0]

    lat_col, lon_col = detect_lat_lon_columns(df)
    if not lat_col or not lon_col:
        print('Não consegui detectar automaticamente colunas de latitude/longitude. Colunas encontradas:')
        print(df.columns.tolist())
        print('Por favor confirme quais colunas contêm lat e lon e reexecute com --lat "COL" --lon "COL"')
        sys.exit(3)

    print('Usando colunas:', col_iata, lat_col, lon_col)

    coords = {}
    for _, row in df.iterrows():
        iata = row.get(col_iata)
        if pd.isna(iata) or not str(iata).strip():
            continue
        key = str(iata).strip().upper()
        try:
            lat = row.get(lat_col)
            lon = row.get(lon_col)
            if pd.isna(lat) or pd.isna(lon):
                continue
            lat = float(lat)
            lon = float(lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                # skip invalid
                continue
            coords[key] = {'lat': lat, 'lon': lon}
        except Exception:
            continue

    out = Path('data/airport_coords.json')
    out.parent.mkdir(exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)

    print(f'Gerado {out} com {len(coords)} coordenadas')


if __name__ == '__main__':
    main()
