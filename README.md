# Automatização de emissão

Pequena aplicação Flask para cadastro de entradas relacionadas a deslocamentos e consulta de aeroportos.

Como rodar (Windows / PowerShell)

1. Crie um virtualenv usando seu Python 3.12 (exemplo):

```powershell
$PY = 'C:\\Users\\joaog\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
$PY -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Inicie a aplicação (background):

```powershell
& '.\run_app.ps1'
# Ou em foreground para ver logs no terminal:
& '.\run_app.ps1' -Foreground
```

3. Acesse no navegador:

```
http://127.0.0.1:5000/
```

Arquivos importantes
- `app.py` - aplicação Flask
- `run_app.ps1` - script PowerShell para iniciar a aplicação (usa `.venv` se existir)
- `requirements.txt` - dependências Python

Logs
- `logs/server_out.log` e `logs/server_err.log`

Contribuição rápida

- Evite commitar ambientes virtuais (`.venv` já está no `.gitignore`).
- Antes de abrir PR, rode os testes (se houver) e garanta que a aplicação inicia localmente.

Contato
- João Della Flora <joaogabrielcasarotto@gmail.com>
# Formulário de Deslocamento

Página simples para coletar dados de deslocamento: origem, destino, distância (km), meio de transporte, tipo de combustível (quando aplicável), subtipo do veículo (quando aplicável) e ano do veículo.

Como usar
- Abra `index.html` no navegador.
- Preencha o formulário e clique em "Salvar".
- As entradas são salvas no armazenamento local do navegador (localStorage).
- Use "Exportar CSV" para baixar um arquivo com os dados.
- Use "Limpar todos os dados" para remover todas as entradas salvas.
 - Abra `index.html` no navegador.
 - Preencha o formulário e clique em "Salvar".
 - As entradas são salvas no servidor backend (rota `POST /api/entries`).
 - Use "Exportar CSV" para baixar um arquivo com os dados.
 - Use "Limpar todos os dados" para remover todas as entradas salvas.

Notas técnicas
 - O campo "Tipo de combustível" e "Ano do veículo" aparecem somente quando o meio de transporte é: Automovel, Carro de aplicativo/taxi, Motocicleta, Ônibus Municipal ou Ônibus Intermunicipal.
 - O campo "Subtipo do veículo" aparece quando aplicável (por exemplo, para "Automovel" permite escolher entre Flex, Híbrido, Híbrido plug-in ou Não se aplica; para Motocicleta mostra "Não se aplica").
 - Quando o transporte for "Automovel" ou "Motocicleta", o campo "Subtipo do veículo" é obrigatório e o formulário não será enviado se não estiver preenchido.
 - Observação sobre cálculo de emissões: se um consumo não for informado no formulário, o backend assume eficiência padrão de 12 km/L para veículos movidos a combustível líquido.
- Arquivos:
  - `index.html` - página principal
  - `styles.css` - estilos
  - `script.js` - lógica de interação, armazenamento e exportação
