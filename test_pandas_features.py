"""Script de teste para validar as novas funcionalidades com pandas."""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_cleanup():
    """Testa limpeza de registros corrompidos."""
    print('\n=== Testando /api/maintenance/clean ===')
    try:
        r = requests.post(f'{BASE_URL}/api/maintenance/clean', timeout=5)
        print(f'STATUS {r.status_code}')
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f'ERROR: {e}')

def test_summary():
    """Testa relatório de resumo."""
    print('\n=== Testando /api/reports/summary ===')
    try:
        r = requests.get(f'{BASE_URL}/api/reports/summary', timeout=5)
        print(f'STATUS {r.status_code}')
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f'ERROR: {e}')

def test_emissions_report():
    """Testa relatório de emissões."""
    print('\n=== Testando /api/reports/emissions ===')
    try:
        r = requests.get(f'{BASE_URL}/api/reports/emissions', timeout=5)
        print(f'STATUS {r.status_code}')
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f'ERROR: {e}')

def test_filter():
    """Testa filtros avançados."""
    print('\n=== Testando /api/entries/filter ===')
    filters = {
        'min_distance': 10,
        'transport': 'Automovel'
    }
    try:
        r = requests.post(f'{BASE_URL}/api/entries/filter', json=filters, timeout=5)
        print(f'STATUS {r.status_code}')
        results = r.json()
        print(f'Encontradas {len(results)} entradas')
        if results:
            print('Primeira entrada:', json.dumps(results[0], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f'ERROR: {e}')

def test_export_excel():
    """Testa export Excel."""
    print('\n=== Testando /api/export/detailed ===')
    try:
        r = requests.get(f'{BASE_URL}/api/export/detailed', timeout=10)
        print(f'STATUS {r.status_code}')
        if r.status_code == 200:
            with open('test_export.xlsx', 'wb') as f:
                f.write(r.content)
            print('✓ Arquivo test_export.xlsx criado com sucesso!')
        else:
            print(f'Erro: {r.text}')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    print('Testando novas funcionalidades com pandas...')
    print('Certifique-se de que o servidor está rodando (python app.py)')
    
    test_cleanup()
    test_summary()
    test_emissions_report()
    test_filter()
    test_export_excel()
    
    print('\n=== Testes concluídos ===')
