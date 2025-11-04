from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
from functools import lru_cache
import urllib.request
import urllib.parse

AIRPORTS_FILE = 'data/airports.json'
AIRPORT_COORDS_FILE = 'data/airport_coords.json'

app = Flask(__name__, static_folder='.', static_url_path='')

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


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@lru_cache(maxsize=1)
def load_airports():
    if not os.path.exists(AIRPORTS_FILE):
        return []
    try:
        with open(AIRPORTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


@lru_cache(maxsize=1)
def load_airport_coords():
    if not os.path.exists(AIRPORT_COORDS_FILE):
        return {}
    try:
        with open(AIRPORT_COORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_airport_coords(d: dict):
    try:
        # ensure directory exists
        dirn = os.path.dirname(AIRPORT_COORDS_FILE)
        if dirn and not os.path.exists(dirn):
            os.makedirs(dirn, exist_ok=True)
        with open(AIRPORT_COORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        # clear cached loader so subsequent calls read the new file
        try:
            load_airport_coords.cache_clear()
        except Exception:
            pass
        return True
    except Exception:
        return False


def normalize_for_search(s: str):
    if not s:
        return ''
    import unicodedata
    s2 = unicodedata.normalize('NFKD', s)
    s2 = ''.join(c for c in s2 if not unicodedata.combining(c))
    return ' '.join(s2.split()).strip().lower()


@app.route('/api/airports', methods=['GET'])
def api_airports():
    q = (request.args.get('q') or '').strip()
    airports = load_airports()
    if not q:
        # return first N
        return jsonify(airports[:20])
    qn = normalize_for_search(q)
    results = []
    for a in airports:
        # match against country, airport name, city
        country = normalize_for_search(a.get('country') or '')
        airport = normalize_for_search(a.get('airport') or '')
        city = normalize_for_search(a.get('city') or '')
        if country.startswith(qn) or airport.startswith(qn) or qn in airport or city.startswith(qn) or qn in city:
            results.append(a)
        if len(results) >= 20:
            break
    return jsonify(results)


@app.route('/api/airports/countries', methods=['GET'])
def api_airports_countries():
    airports = load_airports()
    seen = []
    for a in airports:
        country = a.get('country') or ''
        if country and country not in seen:
            seen.append(country)
    return jsonify(sorted(seen))


@app.route('/api/airports/cities', methods=['GET'])
def api_airports_cities():
    country = (request.args.get('country') or '').strip()
    airports = load_airports()
    cities = set()
    for a in airports:
        if not country or (a.get('country') or '').strip().lower() == country.strip().lower():
            city = a.get('city') or ''
            if city:
                cities.add(city)
    return jsonify(sorted(cities))


@app.route('/api/airports/list', methods=['GET'])
def api_airports_list():
    country = (request.args.get('country') or '').strip()
    city = (request.args.get('city') or '').strip()
    res = []
    for a in load_airports():
        if country and (a.get('country') or '').strip().lower() != country.strip().lower():
            continue
        if city and (a.get('city') or '').strip().lower() != city.strip().lower():
            continue
        res.append(a)
    return jsonify(res)


@app.route('/api/coords', methods=['GET'])
def api_coords():
    iata = (request.args.get('iata') or '').strip().upper()
    if not iata:
        return jsonify({'error': 'missing iata parameter'}), 400
    coords = load_airport_coords()
    v = coords.get(iata)
    if not v:
        # fallback: try to resolve from airports list (city/country/name) using Nominatim
        airports = load_airports()
        candidate = None
        for a in airports:
            if (a.get('airport') or '').strip().upper() == iata:
                candidate = a
                break
        if candidate:
            # build query using airport name, city and country
            qparts = []
            if candidate.get('airport'):
                qparts.append(candidate.get('airport'))
            if candidate.get('city'):
                qparts.append(candidate.get('city'))
            if candidate.get('country'):
                qparts.append(candidate.get('country'))
            q = ' '.join(qparts).strip()
            if q:
                try:
                    params = urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 1})
                    url = f'https://nominatim.openstreetmap.org/search?{params}'
                    req = urllib.request.Request(url, headers={'User-Agent': 'AutomatizacaoEmissao/1.0 (+https://example.org)'} )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        raw = resp.read().decode('utf-8')
                        arr = json.loads(raw or '[]')
                        if arr and isinstance(arr, list):
                            first = arr[0]
                            lat = float(first.get('lat'))
                            lon = float(first.get('lon'))
                            # persist into coords and return
                            newcoords = dict(coords)
                            newcoords[iata] = {'lat': lat, 'lon': lon}
                            save_airport_coords(newcoords)
                            return jsonify(newcoords[iata])
                except Exception:
                    # network / parse error — fall through to not found
                    pass
        return jsonify({'error': 'not found'}), 404
    return jsonify(v)


@app.route('/api/entries', methods=['GET'])
def get_entries():
    return jsonify(load_data())


@app.route('/api/entries', methods=['POST'])
def add_entry():
    # Debug: log content-type and raw body to help diagnose client POST issues
    try:
        raw = request.get_data(as_text=True)
    except Exception:
        raw = None
    print('add_entry: content-type=', getattr(request, 'content_type', None))
    if raw is not None:
        # print only the first 2000 chars to avoid huge logs
        print('add_entry: raw body (truncated 2000):', raw[:2000])
    try:
        if raw:
            payload = json.loads(raw)
        else:
            payload = request.get_json() or {}
    except Exception as e:
        print('add_entry: error parsing JSON:', e)
        return jsonify({'error': 'invalid json'}), 400
    import unicodedata
    origin = payload.get('origin', '').strip()
    destination = payload.get('destination', '').strip()
    distance = payload.get('distance', '')
    transport = (payload.get('transport') or '').strip()
    # normalize transport for robust comparisons (remove diacritics, lower-case)
    transport_norm = unicodedata.normalize('NFKD', transport).encode('ascii', 'ignore').decode('ascii').strip().lower()
    print('add_entry: transport_norm=', transport_norm)
    print('add_entry: payload=', payload)
    # server-side fallback: if main distance is missing, try to read distance
    # from any post-transport fields (postFlight, postTrain, postMetro).
    if distance == '' or distance is None:
        for k in ('postFlight', 'postTrain', 'postMetro'):
            pd = payload.get(k)
            if pd and isinstance(pd, dict):
                d2 = pd.get('distance')
                if d2 not in (None, ''):
                    distance = d2
                    # also copy into payload so subsequent logic and saved entry include it
                    try:
                        payload['distance'] = distance
                    except Exception:
                        pass
                    print(f"add_entry: populated distance from {k}: {distance}")
                    break
    # Validation rules:
    # - 'Aéreo' : origin/destination/distance may be omitted (flight object used instead)
    # - 'Trem'  : origin/destination may be omitted, but distance is required
    # - Others  : require origin, destination and distance
    if transport_norm == 'aereo' or transport.lower() == 'aéreo':
        # no-op: flight details expected instead
        pass
    elif transport_norm == 'trem' or transport_norm == 'metro':
        if distance == '' or distance is None:
            print('add_entry: missing distance for Trem/Metro:', {'distance': distance, 'transport': transport})
            return jsonify({'error': 'missing fields'}), 400
    else:
        if not origin or not destination or distance == '':
            print('add_entry: missing fields:', {'origin': origin, 'destination': destination, 'distance': distance, 'transport': transport})
            return jsonify({'error': 'missing fields'}), 400
    entry = payload.copy()
    entry['createdAt'] = datetime.utcnow().isoformat() + 'Z'
    data = load_data()
    data.append(entry)
    save_data(data)
    return jsonify(entry)


@app.route('/api/entries/<int:idx>', methods=['DELETE'])
def delete_entry(idx):
    data = load_data()
    if 0 <= idx < len(data):
        data.pop(idx)
        save_data(data)
        return '', 204
    return jsonify({'error': 'not found'}), 404


@app.route('/api/entries', methods=['DELETE'])
def clear_entries():
    save_data([])
    return '', 204


if __name__ == '__main__':
    # ensure data file exists
    if not os.path.exists(DATA_FILE):
        save_data([])
    app.run(debug=True)

