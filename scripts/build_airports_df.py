#!/usr/bin/env python3
"""
Script para extrair lista de aeroportos da planilha XLSX fornecida.

Assunções:
- A planilha tem nome de aba 'Aeroportos'.
- As colunas B, C e D correspondem, respectivamente, a: IATA, Nome do aeroporto, Cidade.

Uso:
    python scripts/build_airports_df.py "C:/Users/joaog/Documents/Automatização de emissão/Fatores de emissão (1).xlsx"

Saídas:
- data/airports.csv
- data/airports.json

Se quiser outra correspondência de colunas, edite este script.
"""
import sys
from pathlib import Path
import unicodedata
import json

try:
    import pandas as pd
except Exception as e:
    print('Pandas não está instalado. Instale com: pip install pandas openpyxl')
    raise


def normalize_text(s):
    if pd.isna(s):
        return ''
    s2 = str(s)
    s2 = unicodedata.normalize('NFKD', s2)
    s2 = ''.join(c for c in s2 if not unicodedata.combining(c))
    return ' '.join(s2.split()).strip().lower()


def build_airports(xlsx_path: Path, sheet_name='Aeroportos'):
    print(f'Lendo {xlsx_path} sheet={sheet_name} (colunas B-D)')
    # usecols='B:D' lê colunas B, C e D
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, usecols='B:D', dtype=str, engine='openpyxl')
    # renomear colunas: assumimos B=País, C=Nome do aeroporto, D=Cidade/município
    df.columns = ['country', 'airport', 'city']
    # limpar
    df['country'] = df['country'].fillna('').astype(str).str.strip()
    df['airport'] = df['airport'].fillna('').astype(str).str.strip()
    df['city'] = df['city'].fillna('').astype(str).str.strip()
    # normalização para busca
    df['normalized_airport'] = df['airport'].apply(normalize_text)
    df['normalized_city'] = df['city'].apply(normalize_text)

    # remover linhas sem código/nome do aeroporto
    df = df[df['airport'] != '']

    # deduplicar por código/nome do aeroporto (coluna 'airport') para manter todos os aeroportos
    # em vez de agrupar por país — anteriormente usamos 'iata' como chave e isso
    # fazia com que apenas um aeroporto por país fosse mantido.
    df_final = df.drop_duplicates(subset=['airport', 'city']).reset_index(drop=True)

    out_dir = Path('data')
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / 'airports.csv'
    json_path = out_dir / 'airports.json'
    df_final.to_csv(csv_path, index=False, encoding='utf-8')
    # write json array
    # write records with consistent keys
    records = []
    for r in df_final.to_dict(orient='records'):
        records.append({
            'country': r.get('country',''),
            'airport': r.get('airport',''),
            'city': r.get('city',''),
            'normalized_airport': r.get('normalized_airport',''),
            'normalized_city': r.get('normalized_city',''),
        })
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f'Gerado {csv_path} ({len(records)} aeroportos) e {json_path}')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path(r"C:\Users\joaog\Documents\Automatização de emissão\Fatores de emissão (1).xlsx")
    if not path.exists():
        print('Arquivo não encontrado:', path)
        sys.exit(2)
    build_airports(path)
