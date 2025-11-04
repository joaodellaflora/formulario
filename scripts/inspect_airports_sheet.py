#!/usr/bin/env python3
"""
Mostra cabeçalhos e primeiras linhas da sheet 'Aeroportos' (colunas B:L) do XLSX
Uso:
  python scripts\inspect_airports_sheet.py "Fatores de emissão (1).xlsx"
"""
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET
import re


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
    print('Cabeçalhos B:L:')
    print(headers)
    print('\nPrimeiras 10 linhas (B:L):')
    for r in rows[1:11]:
        print(r)


if __name__ == '__main__':
    main()
