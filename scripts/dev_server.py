#!/usr/bin/env python3
"""
Servidor de desenvolvimento usando apenas stdlib para testar /api/entries
Roda em http://127.0.0.1:5000 e serve arquivos estáticos do diretório raiz.
Endpoints implementados:
 - GET / -> serve index.html
 - GET /api/entries -> retorna data.json
 - POST /api/entries -> recebe JSON, valida similar ao app.py, escreve em data.json

Uso: python scripts/dev_server.py
"""
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse
from datetime import datetime
from urllib.parse import parse_qs
import unicodedata

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Handler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        raw = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        p = urlparse(self.path)
        # support airports endpoints used by the frontend
        if p.path.startswith('/api/airports'):
            # load airports data
            airports = []
            try:
                with open('data/airports.json', 'r', encoding='utf-8') as f:
                    airports = json.load(f)
            except Exception:
                airports = []

            qs = parse_qs(p.query)
            # /api/airports/countries
            if p.path == '/api/airports/countries':
                seen = []
                for a in airports:
                    country = a.get('country') or ''
                    if country and country not in seen:
                        seen.append(country)
                seen.sort()
                self._send_json(seen)
                return

            # /api/airports/cities?country=...
            if p.path == '/api/airports/cities':
                country = (qs.get('country', [''])[0] or '').strip()
                cities = set()
                for a in airports:
                    if not country or (a.get('country') or '').strip().lower() == country.strip().lower():
                        city = a.get('city') or ''
                        if city:
                            cities.add(city)
                self._send_json(sorted(cities))
                return

            # /api/airports/list?country=&city=
            if p.path == '/api/airports/list':
                country = (qs.get('country', [''])[0] or '').strip()
                city = (qs.get('city', [''])[0] or '').strip()
                res = []
                for a in airports:
                    if country and (a.get('country') or '').strip().lower() != country.strip().lower():
                        continue
                    if city and (a.get('city') or '').strip().lower() != city.strip().lower():
                        continue
                    res.append(a)
                self._send_json(res)
                return

            # /api/airports?q=
            if p.path == '/api/airports':
                q = (qs.get('q', [''])[0] or '').strip()
                if not q:
                    self._send_json(airports[:20])
                    return
                qn = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore').decode('ascii').lower()
                results = []
                for a in airports:
                    country = (a.get('country') or '')
                    airport = (a.get('airport') or '')
                    city = (a.get('city') or '')
                    hay = ' '.join([country, airport, city]).lower()
                    if qn in unicodedata.normalize('NFKD', hay).encode('ascii', 'ignore').decode('ascii'):
                        results.append(a)
                    if len(results) >= 20:
                        break
                self._send_json(results)
                return

        if p.path == '/api/entries':
            data = load_data()
            self._send_json(data)
            return
        # default: serve static files
        if p.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == '/api/entries':
            ct = self.headers.get('Content-Type')
            length = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(length).decode('utf-8') if length else ''
            print('dev_server: content-type=', ct)
            print('dev_server: raw body (truncated 2000)=', raw[:2000])
            try:
                payload = json.loads(raw) if raw else {}
            except Exception as e:
                print('dev_server: error parsing JSON:', e)
                self._send_json({'error': 'invalid json'}, 400)
                return

            import unicodedata
            origin = (payload.get('origin') or '').strip()
            destination = (payload.get('destination') or '').strip()
            distance = payload.get('distance', '')
            transport = (payload.get('transport') or '').strip()
            transport_norm = unicodedata.normalize('NFKD', transport).encode('ascii', 'ignore').decode('ascii').strip().lower()
            print('dev_server: transport_norm=', transport_norm)

            # server-side fallback: if main distance missing, try to read distance
            # from any post-transport fields (postFlight, postTrain, postMetro)
            if distance == '' or distance is None:
                for k in ('postFlight', 'postTrain', 'postMetro'):
                    pd = payload.get(k)
                    if pd and isinstance(pd, dict):
                        d2 = pd.get('distance')
                        if d2 not in (None, ''):
                            distance = d2
                            try:
                                payload['distance'] = distance
                            except Exception:
                                pass
                            print('dev_server: populated distance from', k, distance)
                            break

            # Validation rules similar to app.py:
            # - 'Aéreo'/'aereo' : flight details expected (origin/destination optional)
            # - 'Trem'/'trem'    : only distance is required
            # - Others           : require origin, destination and distance
            if transport_norm == 'aereo':
                pass
            elif transport_norm == 'trem' or transport_norm == 'metro':
                if distance == '' or distance is None:
                    print('dev_server: missing distance for Trem/Metro', {'distance': distance, 'transport': transport})
                    self._send_json({'error': 'missing fields'}, 400)
                    return
            else:
                if not origin or not destination or distance == '':
                    print('dev_server: missing fields', {'origin': origin, 'destination': destination, 'distance': distance, 'transport': transport})
                    self._send_json({'error': 'missing fields'}, 400)
                    return

            entry = payload.copy()
            entry['createdAt'] = datetime.utcnow().isoformat() + 'Z'
            data = load_data()
            data.append(entry)
            save_data(data)
            self._send_json(entry, 201)
            return

        # not found
        self._send_json({'error': 'not found'}, 404)


if __name__ == '__main__':
    import sys
    # ensure data file exists
    if not os.path.exists(DATA_FILE):
        save_data([])
    port = 5000
    if len(sys.argv) >= 2:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    addr = ('127.0.0.1', port)
    print(f'dev_server: serving on http://{addr[0]}:{addr[1]}')
    try:
        with socketserver.TCPServer(addr, Handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print('\ndev_server: shutting down')
    except OSError as e:
        print('dev_server: could not start server:', e)
