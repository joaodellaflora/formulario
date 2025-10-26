# Instalação Manual de Pandas e OpenPyXL

O ambiente venv atual tem problemas com certificados SSL durante a instalação de pandas.

## Opção 1: Usar o Python do sistema (recomendado)

```powershell
# Instalar no Python do sistema (C:\Users\joaog\AppData\Local\Programs\Python\Python312\python.exe)
& "C:\Users\joaog\AppData\Local\Programs\Python\Python312\python.exe" -m pip install pandas openpyxl
```

## Opção 2: Baixar wheels manualmente

1. Acesse: https://pypi.org/project/pandas/#files
2. Baixe o arquivo `.whl` para Windows Python 3.12 (ex: `pandas-2.2.3-cp312-cp312-win_amd64.whl`)
3. Acesse: https://pypi.org/project/openpyxl/#files
4. Baixe `openpyxl-3.1.5-py2.py3-none-any.whl`
5. Instale localmente:

```powershell
cd "C:\Users\joaog\Downloads"
& "C:\Users\joaog\Documents\Automatização de emissão\.venv\bin\python.exe" -m pip install pandas-2.2.3-cp312-cp312-win_amd64.whl
& "C:\Users\joaog\Documents\Automatização de emissão\.venv\bin\python.exe" -m pip install openpyxl-3.1.5-py2.py3-none-any.whl
```

## Opção 3: Usar conda (se disponível)

```powershell
conda install pandas openpyxl
```

## Após instalação

Execute o script de teste:

```powershell
python test_pandas_features.py
```

## Nota sobre o código

O código em `app.py` foi atualizado com as seguintes melhorias usando pandas:
- `/api/maintenance/clean` - Limpa registros corrompidos do data.json
- `/api/reports/summary` - Estatísticas agregadas de entradas
- `/api/reports/emissions` - Relatório de emissões totais
- `/api/entries/filter` - Filtragem avançada
- `/api/export/detailed` - Export Excel com múltiplas abas

Todos os endpoints funcionam normalmente mesmo sem pandas instalado no venv, mas requer pandas para executar.
