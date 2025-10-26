import json
from pathlib import Path
import shutil

base = Path('.')
auto = base / 'emission_factors.auto.json'
final = base / 'emission_factors.json'
backup = base / 'emission_factors.json.bak'

if not auto.exists():
    print('auto file not found')
    raise SystemExit(1)

shutil.copyfile(final, backup) if final.exists() else None

f = json.loads(auto.read_text(encoding='utf-8'))
# automatic aliases
aliases = {}
# map pura -> comercial if comercial exists
if 'Gasolina Automotiva (comercial)' in f and 'Gasolina Automotiva (pura)' in f:
    # if pura empty, copy comercial
    if f['Gasolina Automotiva (pura)'].get('unit') in (None, 'unknown'):
        f['Gasolina Automotiva (pura)'] = f['Gasolina Automotiva (comercial)']
        print('Copied comercial -> pura')

# try find electricity-like key
elec_key = None
for k in f.keys():
    if 'eletric' in k.lower() or 'energia eletr' in k.lower() or 'en. eletr' in k.lower():
        elec_key = k; break
if elec_key:
    print('Found electricity candidate:', elec_key)
    # map generic 'Eletricidade' to this key
    if 'Eletricidade' not in f or f['Eletricidade'].get('unit') in (None, 'unknown'):
        f['Eletricidade'] = f[elec_key]
        print('Mapped Eletricidade ->', elec_key)
else:
    print('No electricity candidate found')

# write to final (backup already saved)
final.write_text(json.dumps(f, ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote final emission_factors.json with', len(f), 'entries')

# run tests
import subprocess, sys
subprocess.run([sys.executable, 'test_api_calculate_verbose.py'])

# restore backup if existed
if backup.exists():
    shutil.copyfile(backup, final)
    print('Restored original emission_factors.json from backup')
else:
    print('No backup existed; left new emission_factors.json')
