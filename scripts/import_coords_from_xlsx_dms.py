#!/usr/bin/env python3
"""
Extrai coordenadas em formato DMS (Graus/Minutos/Segundos + hemisfério) da sheet 'Aeroportos'
colunas B:L e gera data/airport_coords.json com decimal degrees.

Uso:
  python scripts\import_coords_from_xlsx_dms.py "Fatores de emissão (1).xlsx"

Este script manipula casos comuns: N/S para latitude e L/O (Leste/Oeste) para longitude.
"""
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET
import re
import json


def col_letter(cell_ref):
    m = re.match(r'([A-Z]+)(\d+)', cell_ref)
    return m.group(1) if m else None


def col_index(letter):
    result = 0
    for ch in letter:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


def parse_shared_strings(z):
    if 'xl/sharedStrings.xml' not in z.namelist():
        return []
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    strings = []
    for si in ss.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
        text_parts = []
        for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
            text_parts.append(t.text or '')
        strings.append(''.join(text_parts))
    return strings


def get_sheet_filename(z, sheet_name):
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
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    for rel in rels.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
        if rel.attrib.get('Id') == target_rid:
            return 'xl/' + rel.attrib.get('Target')
    return None


def parse_sheet(z, sheet_file, start_col=2, end_col=12):
    data = []
    ss = parse_shared_strings(z)
    tree = ET.fromstring(z.read(sheet_file))
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    for row in tree.findall('.//' + ns + 'row'):
        row_vals = {}
        for c in row.findall(ns + 'c'):
            r = c.attrib.get('r')
            col = col_letter(r)
            idx = col_index(col)
            if idx < start_col or idx > end_col:
                continue
            v = c.find(ns + 'v')
            cell_val = None
            if v is not None and v.text is not None:
                if c.attrib.get('t') == 's':
                    si = int(v.text)
                    cell_val = ss[si] if si < len(ss) else ''
                else:
                    cell_val = v.text
            else:
                is_node = c.find(ns + 'is')
                if is_node is not None:
                    t = is_node.find(ns + 't')
                    cell_val = t.text if t is not None else ''
            row_vals[idx] = cell_val
        if row_vals:
            row_list = [row_vals.get(i, '') for i in range(start_col, end_col+1)]
            data.append(row_list)
    return data


def dms_to_decimal(deg, minutes, seconds, hemi):
    try:
        d = float(str(deg).strip()) if deg is not None and str(deg).strip() != '' else 0.0
        m = float(str(minutes).strip()) if minutes is not None and str(minutes).strip() != '' else 0.0
        s = float(str(seconds).strip()) if seconds is not None and str(seconds).strip() != '' else 0.0
    except Exception:
        return None
    dec = d + m/60.0 + s/3600.0
    if isinstance(hemi, str):
        h = hemi.strip().upper()
        if h in ('S', 'O', 'W'):
            dec = -abs(dec)
    return dec


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('Fatores de emissão (1).xlsx')
    if not path.exists():
        print('Arquivo não encontrado:', path)
        return
    z = zipfile.ZipFile(path)
    sheet_file = get_sheet_filename(z, 'Aeroportos')
    if not sheet_file:
        print('Sheet "Aeroportos" não encontrada')
        return
    rows = parse_sheet(z, sheet_file, start_col=2, end_col=12)
    if not rows:
        print('Nenhuma linha em B:L')
        return

    headers = rows[0]
    # expected headers: País, Sigla, Cidade, Graus, Minutos, Segundos, N/S, Graus, Minutos, Segundos, L/O
    coords = {}
    for r in rows[1:]:
        try:
            country = r[0]
            iata = r[1]
            city = r[2]
            lat_deg = r[3]
            lat_min = r[4]
            lat_sec = r[5]
            lat_hemi = r[6]
            lon_deg = r[7]
            lon_min = r[8]
            lon_sec = r[9]
            lon_hemi = r[10]
            if not iata or str(iata).strip() == '':
                continue
            iata_code = str(iata).strip().upper()
            lat = dms_to_decimal(lat_deg, lat_min, lat_sec, lat_hemi)
            lon = dms_to_decimal(lon_deg, lon_min, lon_sec, lon_hemi)
            if lat is None or lon is None:
                continue
            coords[iata_code] = {'lat': round(lat, 6), 'lon': round(lon, 6)}
        except Exception:
            continue

    out = Path('data/airport_coords.json')
    out.parent.mkdir(exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        json.dump(coords, f, ensure_ascii=False, indent=2)

    print(f'Gerado {out} com {len(coords)} coordenadas (DMS -> decimal)')


if __name__ == '__main__':
    main()
