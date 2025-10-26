import json

# Criar entradas válidas
entries = [
    {
        "origin": "Rua sei la",
        "destination": "Rua qual",
        "distance": "45",
        "transport": "Automovel",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Flex",
        "year": "2025",
        "tipo_frota_de_veiculos": "Automóvel flex a gasolina",
        "createdAt": "2025-10-11T17:32:16.245785"
    },
    {
        "origin": "Rua 1",
        "destination": "Rua 2",
        "distance": "66",
        "transport": "Automovel",
        "fuel": "Etanol Hidratado",
        "vehicleSubtype": "Flex",
        "year": "2015",
        "tipo_frota_de_veiculos": "Automóvel flex a etanol",
        "createdAt": "2025-10-11T17:32:34.638241"
    },
    {
        "origin": "Rua 3",
        "destination": "Rua 4",
        "distance": "55",
        "transport": "Automovel",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Não se aplica",
        "year": "2014",
        "tipo_frota_de_veiculos": "Automóvel a gasolina",
        "createdAt": "2025-10-11T17:48:44.670215"
    },
    {
        "origin": "Rua 5",
        "destination": "Rua 6",
        "distance": "66",
        "transport": "Automovel",
        "fuel": "Etanol Hidratado",
        "vehicleSubtype": "Não se aplica",
        "year": "2013",
        "tipo_frota_de_veiculos": "Automóvel a etanol",
        "createdAt": "2025-10-11T17:49:06.060106"
    },
    {
        "origin": "Rua 6",
        "destination": "Rua 7",
        "distance": "12",
        "transport": "Automovel",
        "fuel": "Óleo Diesel (comercial)",
        "vehicleSubtype": "Não se aplica",
        "year": "2015",
        "tipo_frota_de_veiculos": "Veículo comercial leve a Diesel",
        "createdAt": "2025-10-11T17:55:40.793785"
    },
    {
        "origin": "huh",
        "destination": "hu",
        "distance": "55",
        "transport": "Motocicleta",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Não se aplica",
        "year": "2013",
        "tipo_frota_de_veiculos": "Motocicleta flex a gasolina",
        "createdAt": "2025-10-11T18:00:57.313653"
    },
    {
        "origin": "uyugg",
        "destination": "gyguyg",
        "distance": "655",
        "transport": "Motocicleta",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Não se aplica",
        "year": "2017",
        "tipo_frota_de_veiculos": "Motocicleta flex a gasolina",
        "createdAt": "2025-10-11T18:05:15.778811"
    },
    {
        "origin": "t6tt6",
        "destination": "seseses",
        "distance": "55",
        "transport": "Automovel",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Flex",
        "year": "2025",
        "balsaType": "",
        "tipo_frota_de_veiculos": "Automóvel flex a gasolina",
        "createdAt": "2025-10-12T20:18:34.638686"
    },
    {
        "origin": "Rua foi la",
        "destination": "Rua sei la",
        "distance": "55",
        "transport": "Automovel",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Flex",
        "year": "2014",
        "balsaType": "",
        "tipo_frota_de_veiculos": "Automóvel flex a gasolina",
        "createdAt": "2025-10-14T00:06:07.881643"
    },
    {
        "origin": "jijijij",
        "destination": "okook",
        "distance": "10",
        "transport": "Automovel",
        "fuel": "Gasolina Automotiva (comercial)",
        "vehicleSubtype": "Flex",
        "year": "2020",
        "balsaType": "",
        "tipo_frota_de_veiculos": "Automóvel flex a gasolina",
        "createdAt": "2025-10-14T00:27:59.076686"
    }
]

# Salvar
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f'Created clean data.json with {len(entries)} entries')
