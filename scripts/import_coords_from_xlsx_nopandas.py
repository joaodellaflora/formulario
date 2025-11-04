#!/usr/bin/env python3
"""
Extrai colunas B:L da planilha XLSX (sheet 'Aeroportos') sem depender de pandas/openpyxl.
Gera data/airport_coords.json mapeando IATA -> {lat, lon} quando possível.

Uso:
  python scripts\import_coords_from_xlsx_nopandas.py "Fatores de emissão (1).xlsx"

Este script usa apenas a stdlib (zipfile + xml.etree) e tenta detectar colunas de lat/lon.
"""
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET
import json
import re


def col_letter(cell_ref):
    m = re.match(r'([A-Z]+)(\d+)', cell_ref)
    return m.group(1) if m else None


def col_index(letter):
    # A -> 1, B -> 2, ...
    result = 0
    for ch in letter:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def get_sheet_filename(z, sheet_name):
    # read xl/workbook.xml to find sheet id -> r:id
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    sheets = wb.find('ns:sheets', ns)
    target_rid = None
    for s in sheets.findall('ns:sheet', ns):
        name = s.attrib.get('name')
        if name and name.lower() == sheet_name.lower():
            target_rid = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            break
    if not target_rid:
        return None
    # read relationships
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    for rel in rels.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
        if rel.attrib.get('Id') == target_rid:
            return 'xl/' + rel.attrib.get('Target')
    return None


def parse_shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():
        return []
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    strings = []
    for si in ss.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
        # concatenated t elements
        text_parts = []
        for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
            text_parts.append(t.text or '')
        strings.append(''.join(text_parts))
    return strings


def parse_sheet(z, sheet_file, start_col=2, end_col=12):
    # start_col=2 => B, end_col=12 => L
    data = []
    ss = parse_shared_strings(z)
    tree = ET.fromstring(z.read(sheet_file))
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    for row in tree.findall('.//' + ns + 'row'):
        rownum = int(row.attrib.get('r', '0'))
        row_vals = {}
        for c in row.findall(ns + 'c'):
            r = c.attrib.get('r')  # e.g., B2
            col = col_letter(r)
            idx = col_index(col)
            if idx < start_col or idx > end_col:
                continue
            v = c.find(ns + 'v')
            cell_val = None
            if v is not None and v.text is not None:
                if c.attrib.get('t') == 's':
                    # shared string
                    si = int(v.text)
                    cell_val = ss[si] if si < len(ss) else ''
                else:
                    cell_val = v.text
            else:
                # check for inlineStr
                is_node = c.find(ns + 'is')
                if is_node is not None:
                    t = is_node.find(ns + 't')
                    cell_val = t.text if t is not None else ''
            row_vals[idx] = cell_val
        if row_vals:
            # build list for columns start_col..end_col
            row_list = [row_vals.get(i, '') for i in range(start_col, end_col+1)]
            data.append(row_list)
    return data


def detect_lat_lon_by_header(headers):
    lat_idx = None
    lon_idx = None
    for i, h in enumerate(headers):
        if not h:
            continue
        lh = h.lower()
        if 'lat' in lh and lat_idx is None:
            lat_idx = i
        if ('lon' in lh or 'lng' in lh or 'long' in lh) and lon_idx is None:
            lon_idx = i
    return lat_idx, lon_idx


def try_detect_by_values(rows):
    # rows is list of lists for columns B..L
    import math
    cols = list(zip(*rows)) if rows else []
    candidates = []
    for i, col in enumerate(cols):
        nums = []
        for v in col[:200]:
            try:
                if v is None:
                    continue
                s = str(v).strip()
                if s == '':
                    continue
                nums.append(float(s))
            except Exception:
                pass
        if not nums:
            candidates.append(None)
            continue
        # percent of values in lat range
        lat_frac = sum(1 for x in nums if -90 <= x <= 90) / len(nums)
        lon_frac = sum(1 for x in nums if -180 <= x <= 180) / len(nums)
        candidates.append((lat_frac, lon_frac))
    # find pair where one col has high lat_frac and other high lon_frac
    best = (None, None)
    for i in range(len(candidates)):
        for j in range(len(candidates)):
            if i == j:
                continue
            a = candidates[i]
            b = candidates[j]
            if a and b:
                if a[0] > 0.8 and b[1] > 0.8:
                    return i, j
                if a[1] > 0.8 and b[0] > 0.8:
                    return j, i
    return None, None


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('Fatores de emissão (1).xlsx')
    if not path.exists():
        print('Arquivo não encontrado:', path)
        sys.exit(2)
    z = zipfile.ZipFile(path)
    sheet_file = get_sheet_filename(z, 'Aeroportos')
    if not sheet_file:
        print('Sheet "Aeroportos" não encontrada. Sheets disponíveis:')
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        sheets = wb.find('ns:sheets', ns)
        for s in sheets.findall('ns:sheet', ns):
            print('-', s.attrib.get('name'))
        sys.exit(3)

    print('Lendo sheet file:', sheet_file)
    rows = parse_sheet(z, sheet_file, start_col=2, end_col=12)  # B..L
    if not rows:
        print('Nenhuma linha encontrada na área B:L')
        sys.exit(4)
    headers = [str(x).strip() if x is not None else '' for x in rows[0]]
    data_rows = rows[1:]
    lat_idx, lon_idx = detect_lat_lon_by_header(headers)
    if lat_idx is None or lon_idx is None:
        lat_idx, lon_idx = try_detect_by_values(data_rows)
    if lat_idx is None or lon_idx is None:
        print('Não foi possível detectar colunas lat/lon automaticamente. Cabeçalhos B:L:')
        print(headers)
        sys.exit(5)

    # detect iata column: look for header with 'iata' or 'code' or 'iata code' or fallback to first column (B)
    iata_idx = None
    for i, h in enumerate(headers):
        if not h:
            continue
        hh = h.lower()
        if 'iata' in hh or 'code' in hh or 'sigla' in hh:
            iata_idx = i
            break
    if iata_idx is None:
        iata_idx = 0

    coords = {}
    for r in data_rows:
        try:
            iata = str(r[iata_idx]).strip()
            if not iata:
                continue
            lat = r[lat_idx]
            lon = r[lon_idx]
            if lat is None or lon is None:
                continue
            latf = float(str(lat).strip())
            lonf = float(str(lon).strip())
            if not (-90 <= latf <= 90 and -180 <= lonf <= 180):
                continue
            coords[iata.upper()] = {'lat': latf, 'lon': lonf}
        except Exception:
            continue

    out = Path('data/airport_coords.json')
    out.parent.mkdir(exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)

    print(f'Gerado {out} com {len(coords)} coordenadas')


if __name__ == '__main__':
    main()
