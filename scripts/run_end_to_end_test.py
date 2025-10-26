import json
import os
import sys
import pathlib

# ensure project root is on sys.path so we can import app
proj_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(proj_root))

from app import app

DATA_FILE = 'data.json'

sample = {
    'origin': 'Brasil / Salvador (SSA)',
    'destination': 'Brasil / Rio de Janeiro (GIG)',
    'distance': 1000,
    'transport': 'Aéreo',
    'year': 2025,
    'notes': 'Teste automatizado'
}

with app.test_client() as client:
    # ensure data file exists and is empty for test clarity
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception:
            existing = []
    else:
        existing = []

    print('Antes do POST, entradas em data.json =', len(existing))

    resp = client.post('/api/entries', json=sample)
    print('\nPOST /api/entries ->', resp.status_code)
    try:
        print('Resposta:', resp.get_json())
    except Exception:
        print('Resposta (raw):', resp.data)

    # ler data.json agora
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            after = json.load(f)
    else:
        after = []

    print('\nDepois do POST, entradas em data.json =', len(after))
    print('\nÚltima entrada:')
    if after:
        print(json.dumps(after[-1], ensure_ascii=False, indent=2))
    else:
        print('Nenhuma entrada encontrada')
