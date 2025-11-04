#!/usr/bin/env python3
"""
Testa cálculos de distância haversine entre aeroportos usando data/airport_coords.json
Uso: python scripts\test_distance.py GRU GIG
Se não houver argumentos, roda alguns pares de exemplo.
"""
import sys
import math
import json
from pathlib import Path


def haversine_km(a,b):
    lat1, lon1 = math.radians(a['lat']), math.radians(a['lon'])
    lat2, lon2 = math.radians(b['lat']), math.radians(b['lon'])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6371.0
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(h))


coords = json.load(open(Path('data/airport_coords.json'), encoding='utf-8'))

def get(iata):
    key = iata.upper()
    if key not in coords:
        raise KeyError(f'{key} not found')
    return coords[key]

pairs = []
if len(sys.argv) >= 3:
    pairs.append((sys.argv[1], sys.argv[2]))
else:
    pairs = [('GRU','GIG'), ('GRU','LHR'), ('GRU','JFK'), ('LAX','JFK'), ('SCL','EZE')]

for a,b in pairs:
    try:
        ca = get(a); cb = get(b)
        d = haversine_km(ca, cb)
        print(f'{a} -> {b}: {d:.1f} km')
    except Exception as e:
        print(a,b,'error:', e)
