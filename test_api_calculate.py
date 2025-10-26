import requests
import json

tests = [
    { 'origin':'A','destination':'B','distance':10,'transport':'Automóvel','fuel':'Gasolina Automotiva (pura)','efficiency_km_per_l':12 },
    { 'origin':'C','destination':'D','distance':50,'transport':'Ônibus','fuel':'Óleo Diesel (puro)','efficiency_km_per_l':4 },
    { 'origin':'E','destination':'F','distance':100,'transport':'Eletricidade','fuel':'Eletricidade','efficiency_km_per_l':0 }
]

url = 'http://127.0.0.1:5000/api/calculate'
for t in tests:
    try:
        r = requests.post(url, json=t, timeout=5)
        print('STATUS', r.status_code, r.text)
    except Exception as e:
        print('ERROR calling API:', e)
