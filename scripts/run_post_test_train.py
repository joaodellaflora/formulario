#!/usr/bin/env python3
"""
Envia um POST de teste com transporte 'Trem' para o dev server.
Uso: python scripts/run_post_test_train.py [port]
"""
import json
import sys
import urllib.request
from pathlib import Path

port = 5001
if len(sys.argv) >= 2:
    try:
        port = int(sys.argv[1])
    except Exception:
        pass

url = f'http://127.0.0.1:{port}/api/entries'

sample = {
    'origin': 'Estação Central',
    'destination': 'Estação Final',
    'distance': '42.7',
    'transport': 'Trem'
}

# marcar que usou transporte após o trem
sample['postTrain'] = {
    'transport': 'Automovel',
    'fuel': 'Gasolina Automotiva (comercial)',
    'year': '2019',
    'distance': '12.3'
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
    sys.exit(1)

print('\nLast entries in data.json:')
txt = Path('data.json').read_text(encoding='utf-8')
print(txt[-2000:])
