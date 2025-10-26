"""Script para corrigir arquivos JSON corrompidos."""
import json
import sys

def fix_json_file(filepath):
    """Tenta corrigir e validar um arquivo JSON."""
    print(f'\nProcessando {filepath}...')
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        print(f'✓ {filepath} está válido (já tinha {len(data)} itens)')
        return True
    except json.JSONDecodeError as e:
        print(f'✗ Erro em {filepath}: {e}')
        print('Tentando corrigir...')
        
        # Ler conteúdo bruto
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read().strip()
        
        # Se é array, tentar recuperar
        if content.startswith('['):
            # Remover última vírgula solta e fechar array
            if content.endswith(','):
                content = content[:-1] + ']'
            elif not content.endswith(']'):
                # Achar última entrada completa
                last_brace = content.rfind('}')
                if last_brace > 0:
                    content = content[:last_brace+1] + '\n]'
            
            # Tentar parsear de novo
            try:
                data = json.loads(content)
                # Salvar corrigido
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f'✓ {filepath} corrigido! ({len(data)} itens recuperados)')
                return True
            except json.JSONDecodeError as e2:
                print(f'✗ Não foi possível corrigir automaticamente: {e2}')
                return False
        else:
            print('✗ Formato não reconhecido')
            return False

if __name__ == '__main__':
    files = [
        'data.json',
        'calculation_results.json'
    ]
    
    success_count = 0
    for f in files:
        if fix_json_file(f):
            success_count += 1
    
    print(f'\n{"="*50}')
    print(f'Resultado: {success_count}/{len(files)} arquivos OK')
    
    if success_count == len(files):
        print('✓ Todos os arquivos estão válidos!')
        sys.exit(0)
    else:
        print('✗ Alguns arquivos ainda têm problemas')
        sys.exit(1)
