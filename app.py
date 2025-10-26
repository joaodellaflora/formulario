from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
from functools import lru_cache

AIRPORTS_FILE = 'data/airports.json'

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


@app.route('/api/entries', methods=['GET'])
def get_entries():
    return jsonify(load_data())


@app.route('/api/entries', methods=['POST'])
def add_entry():
    payload = request.get_json() or {}
    origin = payload.get('origin', '').strip()
    destination = payload.get('destination', '').strip()
    distance = payload.get('distance', '')
    transport = (payload.get('transport') or '').strip()
    # For non-air transport, require origin/destination/distance.
    # For 'Aéreo', these can be optional because flight details are provided separately.
    if transport != 'Aéreo':
        if not origin or not destination or distance == '':
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

