#!/usr/bin/env python3
"""
Append an example 'Trem' entry directly to data.json (bypasses server).
Uso: python scripts/append_train_entry.py
"""
import json
from pathlib import Path
from datetime import datetime

DATA_FILE = Path('data.json')

entry = {
    'origin': 'Estação Central',
    'destination': 'Estação Final',
    'distance': '42.7',
    'transport': 'Trem',
}

entry['postTrain'] = {
    'transport': 'Automovel',
    'fuel': 'Gasolina Automotiva (comercial)',
    'year': '2019',
    'distance': '12.3'
}

entry['createdAt'] = datetime.utcnow().isoformat() + 'Z'

data = []
if DATA_FILE.exists():
    try:
        data = json.loads(DATA_FILE.read_text(encoding='utf-8') or '[]')
    except Exception:
        data = []

data.append(entry)
DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('Appended train entry to data.json')
print(DATA_FILE.read_text(encoding='utf-8')[-1000:])
