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
