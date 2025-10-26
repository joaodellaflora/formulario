"""Limpa data.json removendo entradas corrompidas."""
import json

# Ler e filtrar entradas válidas
entries = []
try:
    with open('data.json', 'r', encoding='utf-8-sig') as f:
        content = f.read()
        # Tentar parsear
        try:
            data = json.loads(content)
            # Filtrar apenas entradas sem _calculation_record
            for entry in data:
                if isinstance(entry, dict) and not entry.get('_calculation_record'):
                    # Verificar se tem campos obrigatórios
                    if 'origin' in entry and 'destination' in entry:
                        entries.append(entry)
        except:
            pass
except:
    pass

# Salvar limpo
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f'Cleaned data.json: kept {len(entries)} valid entries')
