import json
from pathlib import Path

airports = json.load(open(Path('data/airports.json'), encoding='utf-8'))
coords = json.load(open(Path('data/airport_coords.json'), encoding='utf-8'))

iata_airports = set()
for a in airports:
    code = a.get('airport') or a.get('iata') or a.get('code')
    if code:
        iata_airports.add(str(code).strip().upper())

iata_coords = set(coords.keys())

missing = sorted(list(iata_airports - iata_coords))
extra = sorted(list(iata_coords - iata_airports))

print('airports.json:', len(iata_airports), 'unique IATA')
print('airport_coords.json:', len(iata_coords), 'entries')
print('missing coords for', len(missing), 'IATA')
if missing:
    print('Missing sample:', missing[:20])
print('extra coords (not in airports.json):', len(extra))
if extra:
    print('Extra sample:', extra[:20])
