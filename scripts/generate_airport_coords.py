#!/usr/bin/env python3
"""
Gera `data/airport_coords.json` consultando o Nominatim (OpenStreetMap) para cada IATA em
`data/airports.json` e persistindo os pares { IATA: {lat, lon} } localmente.

Uso:
  python scripts\generate_airport_coords.py [--delay 1.0] [--max 100] [--force]

Notas:
- Este script REQUER conexão com a internet.
- Respeite a política de uso do Nominatim: use um `User-Agent` identificável e delays (padrão 1s).
- Se quiser uma solução totalmente offline, forneça um arquivo CSV com lat/lon por IATA (por exemplo OurAirports) e eu adapto o script para usar esse arquivo.
"""
import argparse
import json
import time
import urllib.request
import urllib.parse
import os
from pathlib import Path

USER_AGENT = 'AutomatizacaoEmissao/1.0 (contato: voce@exemplo.com)'


def load_airports(path='data/airports.json'):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f'Aquivo não encontrado: {p}')
    with p.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_existing_coords(path='data/airport_coords.json'):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_coords(d, path='data/airport_coords.json'):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def geocode_query(q, timeout=10):
    params = urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 1})
    url = f'https://nominatim.openstreetmap.org/search?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8')
        arr = json.loads(raw or '[]')
        if arr and isinstance(arr, list):
            first = arr[0]
            return float(first.get('lat')), float(first.get('lon'))
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=float, default=1.0, help='Segundos entre requisições (padrão 1.0)')
    parser.add_argument('--max', type=int, default=0, help='Máximo de aeroportos a processar (0 = todos)')
    parser.add_argument('--force', action='store_true', help='Re-geocodificar mesmo se já existir coords')
    parser.add_argument('--timeout', type=float, default=10.0, help='Timeout HTTP em segundos')
    args = parser.parse_args()

    airports = load_airports()
    coords = load_existing_coords()

    total = 0
    processed = 0
    for a in airports:
        iata = (a.get('airport') or '').strip().upper()
        if not iata:
            continue
        total += 1
    print(f'Aeroportos encontrados: {total}')

    for idx, a in enumerate(airports, start=1):
        iata = (a.get('airport') or '').strip().upper()
        if not iata:
            continue
        if args.max and processed >= args.max:
            break
        if (iata in coords) and not args.force:
            print(f'[{idx}/{total}] Pulando {iata} (já tem coords)')
            processed += 1
            continue
        # build query
        parts = []
        if a.get('airport'):
            parts.append(a.get('airport'))
        if a.get('city'):
            parts.append(a.get('city'))
        if a.get('country'):
            parts.append(a.get('country'))
        q = ' '.join(parts).strip()
        if not q:
            print(f'[{idx}/{total}] Sem informação textual para {iata} — pulando')
            continue
        try:
            print(f'[{idx}/{total}] Geocodificando {iata}: "{q}"')
            res = geocode_query(q, timeout=args.timeout)
            if res:
                lat, lon = res
                coords[iata] = {'lat': lat, 'lon': lon}
                save_coords(coords)
                print(f'  -> {iata} = {lat},{lon} (salvo)')
            else:
                print(f'  -> sem resultado para {iata}')
        except Exception as e:
            print(f'  -> erro ao geocodificar {iata}: {e}')
        processed += 1
        time.sleep(args.delay)

    print(f'Processados: {processed}. Arquivo salvo em data/airport_coords.json')


if __name__ == '__main__':
    main()
