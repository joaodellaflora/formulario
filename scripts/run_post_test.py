#!/usr/bin/env python3
"""
Envia um POST de teste para http://127.0.0.1:5000/api/entries usando stdlib
Imprime status e o conteúdo atual de data.json após o POST.

Uso: python scripts/run_post_test.py
"""
import json
import urllib.request
from pathlib import Path

import sys

port = 5000
if len(sys.argv) >= 2:
    try:
        port = int(sys.argv[1])
    except Exception:
        pass
url = f'http://127.0.0.1:{port}/api/entries'
sample = {
    'origin': 'Rua Teste',
    'destination': 'Rua Alvo',
    'distance': '12.5',
    'transport': 'Automovel',
    'fuel': 'Gasolina Automotiva (comercial)',
    'vehicleSubtype': 'Flex',
    'year': '2022'
}

data = json.dumps(sample).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8')
        print('POST response code:', resp.getcode())
        print('POST response body:', body)
except Exception as e:
    print('Error during POST:', e)

print('\nCurrent data.json:')
print(Path('data.json').read_text(encoding='utf-8'))
